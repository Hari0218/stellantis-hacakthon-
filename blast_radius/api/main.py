from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
import os

from blast_radius.graph.builder import build_graph
from blast_radius.ingestion.classifier import ChangeClassifier
from blast_radius.agent.blast_agent import BlastAgent

app = FastAPI(title="Blast Radius API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory lazily-loaded graph
GRAPH_CACHE = None

def get_or_build_graph(repo_path: str) -> nx.DiGraph:
    global GRAPH_CACHE
    if GRAPH_CACHE is None:
        GRAPH_CACHE = build_graph(repo_path)
    return GRAPH_CACHE

class AnalyzeRequest(BaseModel):
    diff: str
    repo_path: str = "seed/"

@app.post("/analyze")
def analyze_diff(req: AnalyzeRequest):
    if not os.path.exists(req.repo_path):
        raise HTTPException(status_code=400, detail=f"Repo path '{req.repo_path}' does not exist.")
        
    try:
        # Build the graph
        G = get_or_build_graph(req.repo_path)
        
        # 1. Parse and classify diff
        classifier = ChangeClassifier(req.repo_path)
        changed_symbols = classifier.classify_diff(req.diff)
        
        if not changed_symbols:
            return {
                "affected_nodes": [],
                "affected_services": [],
                "affected_teams": [],
                "recommended_tests": [],
                "risk_score": 0,
                "risk_band": "NONE",
                "explanation": "No actionable changes detected in the diff."
            }

        # 2. Run agent blast radius walk
        agent = BlastAgent(G)
        result = agent.run_analysis(changed_symbols)
        
        # Convert to dict
        return result.model_dump()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
def get_graph():
    """Returns the full graph in node-link JSON format for the visualization tool."""
    # We assume repo_path is seed/ for this endpoint
    G = get_or_build_graph("seed/")
    # networkx >=3.6 renamed the default edges key from "links" to "edges";
    # pin it to "links" since that's what the frontend (BlastGraph.jsx) expects.
    data = nx.node_link_data(G, edges="links")
    return data

@app.get("/health")
def health():
    return {"status": "ok"}