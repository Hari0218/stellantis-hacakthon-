from typing import Dict, List, Any
from blast_radius.ingestion.diff_parser import ChangedSymbol
from blast_radius.graph.models import NodeType

class RiskScorer:
    """
    Deterministic risk scorer based on fan-out, test coverage gap, 
    API exposure, and change severity.
    """
    
    SEVERITY_WEIGHTS = {
        "SCHEMA_CHANGE": 3,
        "DELETED_ENDPOINT": 3,
        "SIGNATURE_CHANGE": 2,
        "LOGIC_CHANGE": 1,
        "NEW_ENDPOINT": 1
    }

    def __init__(self, tools_instance):
        self.tools = tools_instance

    def calculate_risk(self, changed_symbols: List[ChangedSymbol], blast_radius_nodes: List[str]) -> Dict[str, Any]:
        """
        score = min(100, fan_out*3 + coverage_gap*5 + api_public*15 + severity*10)
        Band: 0-30 LOW, 31-65 MEDIUM, 66-100 HIGH
        """
        
        fan_out = len(blast_radius_nodes)
        
        coverage_gap = 0
        api_public = 0
        max_severity = 1
        
        for br_node in blast_radius_nodes:
            # check if it is covered by a test
            tests = self.tools.get_tests_for_node(br_node)
            if not tests:
                coverage_gap += 1
                
            # check if an API endpoint was affected
            if self.tools.G.nodes.get(br_node, {}).get("type") == NodeType.API_ENDPOINT:
                api_public = 1
                
        for cs in changed_symbols:
            w = self.SEVERITY_WEIGHTS.get(cs.change_type, 1)
            if w > max_severity:
                max_severity = w
                
        score = (fan_out * 3) + (coverage_gap * 5) + (api_public * 15) + (max_severity * 10)
        score = min(100, score)
        
        if score <= 30:
            band = "LOW"
        elif score <= 65:
            band = "MEDIUM"
        else:
            band = "HIGH"
            
        return {
            "score": score,
            "band": band,
            "fan_out": fan_out,
            "coverage_gap": coverage_gap,
            "api_public_affected": bool(api_public),
            "max_severity_multiplier": max_severity
        }
