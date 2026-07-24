from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
import os
import zipfile
import shutil
import tempfile

from blast_radius.graph.builder import build_graph
from blast_radius.ingestion.classifier import ChangeClassifier
from blast_radius.agent.blast_agent import BlastAgent

app = FastAPI(title="Blast Radius API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_CACHE = None
UPLOAD_DIR = tempfile.mkdtemp(prefix="blast_radius_upload_")


def get_or_build_graph(repo_path: str = "seed/", force_rebuild: bool = False) -> nx.DiGraph:
    global GRAPH_CACHE
    if GRAPH_CACHE is None or force_rebuild:
        GRAPH_CACHE = build_graph(repo_path)
    return GRAPH_CACHE


def graph_to_json(G: nx.DiGraph) -> dict:
    return nx.node_link_data(G, edges="links")


class AnalyzeRequest(BaseModel):
    diff: str
    repo_path: str = "seed/"


def _run_analysis(diff: str, repo_path: str, G: nx.DiGraph = None):
    if not os.path.exists(repo_path):
        raise HTTPException(status_code=400, detail=f"Repo path '{repo_path}' does not exist.")
    try:
        if G is None:
            G = get_or_build_graph(repo_path)

        classifier = ChangeClassifier(repo_path)
        changed_symbols = classifier.classify_diff(diff)

        if not changed_symbols:
            graph_data = graph_to_json(G)
            return {
                "affected_nodes": [], "affected_services": [],
                "affected_teams": [], "recommended_tests": [],
                "risk_score": 0, "risk_band": "NONE",
                "explanation": "No actionable changes detected in the diff.",
                "change_scale": "minimal", "change_types": [],
                "graph": graph_data
            }

        agent = BlastAgent(G)
        result = agent.run_analysis(changed_symbols)
        result_dict = result.model_dump()

        # Determine change scale
        change_types = list({s.change_type for s in changed_symbols})
        major_types = {"SCHEMA_CHANGE", "DELETED_ENDPOINT", "SIGNATURE_CHANGE"}
        if any(ct in major_types for ct in change_types) or result_dict["risk_band"] == "HIGH":
            change_scale = "major"
        elif result_dict["risk_band"] == "MEDIUM":
            change_scale = "moderate"
        else:
            change_scale = "minor"

        result_dict["change_scale"] = change_scale
        result_dict["change_types"] = change_types
        # Always include the graph so frontend can render from the correct codebase
        result_dict["graph"] = graph_to_json(G)
        return result_dict

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
def analyze_diff(req: AnalyzeRequest):
    return _run_analysis(req.diff, req.repo_path)


@app.post("/analyze-zip")
async def analyze_zip(
    diff: str = Form(...),
    zipfile_upload: UploadFile = File(...)
):
    extract_dir = tempfile.mkdtemp(dir=UPLOAD_DIR)
    zip_path = os.path.join(extract_dir, "codebase.zip")
    repo_path = os.path.join(extract_dir, "repo")
    os.makedirs(repo_path, exist_ok=True)

    try:
        contents = await zipfile_upload.read()
        with open(zip_path, "wb") as f:
            f.write(contents)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(repo_path)

        G = build_graph(repo_path)
        result = _run_analysis(diff, repo_path, G=G)
        return result
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


@app.get("/graph")
def get_graph():
    G = get_or_build_graph("seed/")
    return graph_to_json(G)


@app.get("/health")
def health():
    return {"status": "ok"}