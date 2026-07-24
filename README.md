# 💥 Blast Radius — AI-Powered Code Impact Analyzer

> **CodeHunters Hackathon 2026** — Team submission by Hari

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![Gemini](https://img.shields.io/badge/Gemini-1.5--Flash-4285F4?style=flat-square&logo=google)](https://aistudio.google.com/)
[![NetworkX](https://img.shields.io/badge/NetworkX-Graph%20Analysis-orange?style=flat-square)](https://networkx.org/)

---

## 🚀 What is Blast Radius?

**Blast Radius** answers the question every engineer dreads at 2 AM before a release:

> *"If I merge this PR right now — what exactly breaks?"*

It ingests a **git diff** (or a full codebase zip), statically analyzes every dependency, runs a BFS blast-radius walk across a multi-layer code graph, and uses **Gemini 1.5 Flash** to produce a plain-English explanation of exactly what breaks and why — all in under 3 seconds.

---

## 🎯 The Problem

Modern microservice codebases are a tangled web. A one-line change to a shared schema can silently break 6 downstream services. Teams discover this during incidents, not during code review. Existing tools are either:

- Too **slow** (full CI runs take 20–40 min)
- Too **shallow** (linters don't understand cross-service impact)
- Too **manual** (engineers mentally trace dependencies themselves)

Blast Radius solves this with **static analysis + graph reasoning + LLM** — in seconds, before the merge.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📦 **Zip Upload** | Upload your entire codebase as a `.zip` — graph built from your real code, not a mock |
| 🕸 **Dependency Graph** | Interactive force-directed graph of services, files, routes, DB tables, and test coverage |
| 🧠 **LLM Reasoning** | Gemini 1.5 Flash explains the impact in one plain-English sentence |
| 📊 **Smart Risk Scoring** | Deterministic score (0–100) based on fan-out, API exposure, coverage gaps, and change severity |
| 🔴 **Proportional Severity** | Score 0–30 → LOW, 31–65 → MEDIUM, 66–100 → HIGH — never cry wolf |
| 🔬 **Change Classification** | Detects SCHEMA_CHANGE, SIGNATURE_CHANGE, NEW_ENDPOINT, DELETED_ENDPOINT, LOGIC_CHANGE |
| 👥 **Team Impact** | CODEOWNERS-aware — tells you which team owns the affected service |
| 🧪 **Test Recommendations** | Surfaces exact pytest targets that must be run |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      BLAST RADIUS                           │
│                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ Git Diff │───▶│   Ingestion  │───▶│  Change Classify │  │
│  │  / ZIP   │    │  diff_parser │    │  (AST heuristic) │  │
│  └──────────┘    └──────────────┘    └────────┬─────────┘  │
│                                               │             │
│  ┌────────────────────────────────────────────▼──────────┐  │
│  │               Graph Builder (NetworkX DiGraph)         │  │
│  │  • ASTAnalyzer  — imports, functions, call graph       │  │
│  │  • RouteExtractor — FastAPI/Flask endpoints            │  │
│  │  • DatabaseExtractor — SQLAlchemy ORM tables           │  │
│  │  • TestMapper — pytest test coverage links             │  │
│  │  • CIMapper — GitHub Actions job coverage              │  │
│  │  • CodeownersParser — team ownership                   │  │
│  │  • ServiceCallExtractor — cross-service HTTP calls     │  │
│  └────────────────────────────────────────────┬──────────┘  │
│                                               │             │
│  ┌────────────────────────────────────────────▼──────────┐  │
│  │               BlastAgent (BFS Walk)                    │  │
│  │  • Starts from changed symbols                         │  │
│  │  • Walks dependents recursively                        │  │
│  │  • Collects affected nodes, services, teams, tests     │  │
│  └────────────────────────────────────────────┬──────────┘  │
│                                               │             │
│  ┌──────────────────┐    ┌────────────────────▼──────────┐  │
│  │   RiskScorer     │    │   Gemini 1.5 Flash             │  │
│  │  fan-out * 3     │    │  1-sentence impact summary     │  │
│  │  coverage_gap * 5│    │  (graceful fallback if no key) │  │
│  │  api_public * 15 │    └───────────────────────────────┘  │
│  │  severity * 10   │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🖥️ Frontend

Built with **React 19 + Vite + react-force-graph-2d**:

- **Full-page dashboard** — sticky left control panel, scrollable right content
- **Live force-directed graph** — 680px canvas, glowing affected nodes, animated particles on hot edges
- **Change Scale banner** — Minor / Moderate / Major change at a glance
- **Risk circle** — color-coded by score (green/amber/red)
- **Change type pills** — SCHEMA_CHANGE, SIGNATURE_CHANGE, etc.
- **Scrollable dependency section** — affected services, teams, and test commands

---

## 📁 Project Structure

```
stellantis-hacakthon-/
├── blast_radius/
│   ├── api/
│   │   └── main.py             # FastAPI: /analyze, /analyze-zip, /graph
│   ├── agent/
│   │   ├── blast_agent.py      # BFS blast-radius walk + Gemini LLM
│   │   ├── risk_scorer.py      # Deterministic 0-100 risk score
│   │   └── tools.py            # Graph traversal helpers
│   ├── analyzer/
│   │   ├── static_analyzer.py  # AST import/function/call extraction
│   │   ├── route_extractor.py  # FastAPI/Flask route detection
│   │   ├── db_extractor.py     # SQLAlchemy ORM table detection
│   │   ├── test_mapper.py      # Pytest coverage mapping
│   │   └── service_call_extractor.py  # Cross-service HTTP calls
│   ├── coverage/
│   │   ├── ci_mapper.py        # GitHub Actions CI job coverage
│   │   └── codeowners_parser.py # Team ownership
│   ├── graph/
│   │   ├── builder.py          # Full graph construction pipeline
│   │   └── models.py           # NodeType, EdgeType enums
│   └── ingestion/
│       ├── diff_parser.py      # Unified diff parser
│       └── classifier.py       # Change type classification
├── frontend/
│   └── src/
│       ├── App.jsx             # Dashboard wiring
│       ├── api.js              # analyzeDiff / analyzeZip / fetchGraph
│       └── components/
│           ├── DiffInput.jsx   # Diff textarea + zip upload
│           ├── BlastGraph.jsx  # Force-directed dep graph
│           └── SummaryPanel.jsx # Risk score + impact details
├── seed/                       # Sample microservice codebase for demo
└── requirements.txt
```

---

## 🧠 How the Risk Score Works

```
score = min(100,
    fan_out       × 3   +   # how many components affected
    coverage_gap  × 5   +   # affected nodes with no tests
    api_public    × 15  +   # public API endpoint affected?
    severity      × 10      # SCHEMA=3×, SIGNATURE=2×, LOGIC=1×
)
```

| Score | Band | Meaning |
|-------|------|---------|
| 0–30  | 🟢 LOW | Isolated change, safe to ship |
| 31–65 | 🟡 MEDIUM | Review recommended, run targeted tests |
| 66–100| 🔴 HIGH | Full regression required, loop in all affected teams |

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API key from [aistudio.google.com](https://aistudio.google.com/apikey)

### Setup

```bash
# 1. Clone
git clone https://github.com/Hari0218/stellantis-hacakthon-
cd stellantis-hacakthon-

# 2. Backend
cp .env.example .env
# Add your GEMINI_API_KEY to .env
pip install -r requirements.txt
uvicorn blast_radius.api.main:app --reload --host 0.0.0.0 --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** 🎉

---

## 🎮 Usage

### Option A — Quick Demo (no zip)
1. Paste any git unified diff in the left panel
2. Click **Analyze Impact**
3. See: risk score, affected services, teams, tests to run, and LLM explanation

### Option B — Full Codebase Analysis (zip)
1. Zip your Python microservice repo
2. Upload the `.zip` in the Change Ingestion panel
3. Paste your diff
4. Click **Analyze Impact**
5. The graph is built from **your real code** — affected nodes glow red/amber/green

### Change Types Detected

| Change Type | Trigger | Default Severity |
|---|---|---|
| `SCHEMA_CHANGE` | SQLAlchemy `Column()` added/removed | HIGH |
| `DELETED_ENDPOINT` | `@app.xxx` route removed | HIGH |
| `SIGNATURE_CHANGE` | `def name(...)` changed | MEDIUM |
| `NEW_ENDPOINT` | `@app.xxx` route added | LOW |
| `LOGIC_CHANGE` | Any other code change | LOW |

---

## 🛠️ API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | JSON body: `{diff, repo_path}` |
| `POST` | `/analyze-zip` | Multipart: `diff` + `zipfile_upload` |
| `GET`  | `/graph` | Full graph as node-link JSON |
| `GET`  | `/health` | Health check |

---

## 🏆 Why This Wins

1. **Real static analysis** — not keyword matching; actual AST parsing of imports, function calls, DB models, API routes
2. **Cross-layer graph** — 7 analyzers build a single unified DiGraph spanning files → functions → routes → DB → tests → CI → teams
3. **Works on any Python codebase** — upload a zip, get results in seconds
4. **LLM reasoning that degrades gracefully** — Gemini adds context; works offline too via deterministic fallback
5. **Honest scoring** — mathematical formula, not vibes; teams can trust the result

---

## 👤 Team

**CodeHunters** — Built for the Stellantis Hackathon 2026

---

*Built with ❤️, caffeine, and a healthy fear of production incidents.*
