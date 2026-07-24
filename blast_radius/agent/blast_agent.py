import os
from typing import List, Dict, Set, Any
import networkx as nx
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from blast_radius.graph.models import NodeType
from blast_radius.agent.tools import GraphTools
from blast_radius.agent.risk_scorer import RiskScorer
from blast_radius.ingestion.diff_parser import ChangedSymbol

class BlastResult(BaseModel):
    affected_nodes: List[str]
    affected_services: List[str]
    affected_teams: List[str]
    recommended_tests: List[str]
    risk_score: int
    risk_band: str
    explanation: str

class BlastAgent:
    def __init__(self, graph: nx.DiGraph):
        self.G = graph
        self.tools = GraphTools(graph)
        self.scorer = RiskScorer(self.tools)
        
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def _get_llm_reasoning(self, caller: str, caller_type: str, changed_node: str, change_type: str) -> str:
        """Use LLM to determine if the caller is broken by this specific change."""
        if not self.model:
            return f"Deterministic rule: {caller} depends on {changed_node} which had a {change_type}."
            
        prompt = f"""
        Code dependency impact check:
        Node '{changed_node}' had a change of type '{change_type}'.
        Node '{caller}' (type: {caller_type}) depends on '{changed_node}'.
        
        Does this change break '{caller}'? 
        Answer 'YES' or 'NO' and provide a brief 1-sentence explanation.
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            return text
        except Exception as e:
            return f"Deterministic fallback (LLM error): depends on {changed_node}."

    def run_analysis(self, changed_symbols: List[ChangedSymbol]) -> BlastResult:
        """
        Walk BFS blast radius starting from the changed symbols.
        Determine affected nodes, teams, tests, and calculate risk.
        """
        frontier = []
        for sym in changed_symbols:
            # Simplistic mapping of symbol to node in graph
            # In a real app we map fine-grained AST identifiers to graph IDs.
            # Here for demo, if it's a file logic change, we take the file node.
            # If it's a schema change we take the service.
            
            # Normalizing to unix path just in case
            norm_file = sym.file.replace('\\\\', '/')
            if sym.change_type == "LOGIC_CHANGE":
                frontier.append(norm_file)
            else:
                # for demo, treat the service as the source of impact
                norm_service = sym.service.replace('\\\\', '/')
                if norm_service in self.G:
                    frontier.append(norm_service)
                else:
                    frontier.append(norm_file)
                    
        visited = set()
        affected_nodes = []
        affected_services = set()
        affected_teams = set()
        recommended_tests = set()
        
        # We'll build up a single explanation based on the worst change and its fanout
        explanations = []

        while frontier:
            node = frontier.pop(0)
            if node in visited:
                continue
            visited.add(node)
            
            if node not in self.G:
                continue
                
            affected_nodes.append(node)
            ntype = self.G.nodes[node].get('type')
            
            if ntype == NodeType.SERVICE:
                affected_services.add(node)
                team = self.tools.get_team_for_service(node)
                affected_teams.add(team)
            elif ntype == NodeType.FILE:
                # attempt to find belonging service
                for succ in self.G.successors(node):
                    if self.G.get_edge_data(node, succ).get('type') == 'BELONGS_TO':
                        affected_services.add(succ)
                        team = self.tools.get_team_for_service(succ)
                        affected_teams.add(team)
                        # Re-queue the owning service itself so we keep walking
                        # into any other service that CALLS_API this one —
                        # otherwise blast radius stops dead at the file boundary
                        # and cross-service impact never gets discovered.
                        if succ not in visited:
                            frontier.append(succ)
            
            tests = self.tools.get_tests_for_node(node)
            recommended_tests.update(tests)
            
            # Explore dependents (predecessors in our directed dependency graph)
            deps = self.tools.get_dependents(node)
            for dep in deps:
                dep_node = dep['node']
                frontier.append(dep_node)

        # Risk Score
        risk_data = self.scorer.calculate_risk(changed_symbols, affected_nodes)
        
        # LLM Summary (Single shot summary of the blast radius)
        if self.model and changed_symbols and affected_services:
            summary_prompt = f"""
            You are an AI code impact analyzer.
            Changes: {[f"{c.change_type} in {c.file}" for c in changed_symbols]}
            Affected dependent services: {list(affected_services)}
            
            Provide a concise 1-sentence plain-English explanation of exactly what breaks and why this matters.
            """
            try:
                resp = self.model.generate_content(summary_prompt)
                explanation = resp.text.strip().replace('\\n', ' ')
            except Exception:
                explanation = f"Change affects {len(affected_nodes)} components across {len(affected_services)} services."
        else:
            explanation = f"Change affects {len(affected_nodes)} components across {len(affected_services)} services."

        return BlastResult(
            affected_nodes=affected_nodes,
            affected_services=list(affected_services),
            affected_teams=list(affected_teams),
            recommended_tests=list(recommended_tests),
            risk_score=risk_data['score'],
            risk_band=risk_data['band'],
            explanation=explanation
        )