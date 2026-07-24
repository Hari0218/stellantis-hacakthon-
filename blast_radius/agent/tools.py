import networkx as nx
from typing import List, Dict, Set
from blast_radius.graph.models import NodeType, EdgeType

class GraphTools:
    def __init__(self, graph: nx.DiGraph):
        self.G = graph
        
    def get_dependents(self, node_id: str) -> List[str]:
        """Returns direct dependents (predecessors) of a node"""
        if node_id not in self.G:
            return []
        
        preds = []
        for p in self.G.predecessors(node_id):
            edge_data = self.G.get_edge_data(p, node_id)
            preds.append({"node": p, "edge_type": edge_data.get('type')})
        return preds

    def get_tests_for_node(self, node_id: str) -> List[str]:
        """Finds tests covering the given node (or its parent service)"""
        if node_id not in self.G:
            return []
            
        tests = []
        # Find which service this belongs to
        service_node = None
        
        # 1. if it's already a service
        node_type = self.G.nodes[node_id].get('type')
        if node_type == NodeType.SERVICE:
            service_node = node_id
        elif node_type == NodeType.FILE:
            # check predecessors with BELONGS_TO
            for p in self.G.successors(node_id): # file -> belongs_to -> service
                if self.G.get_edge_data(node_id, p).get('type') == EdgeType.BELONGS_TO.value:
                    service_node = p
                    break
        elif node_type == NodeType.FUNCTION:
            defined_in = self.G.nodes[node_id].get('defined_in')
            if defined_in:
                for p in self.G.successors(defined_in):
                    if self.G.get_edge_data(defined_in, p).get('type') == EdgeType.BELONGS_TO.value:
                        service_node = p
                        break
                        
        if service_node:
            for p in self.G.predecessors(service_node):
                if self.G.get_edge_data(p, service_node).get('type') == EdgeType.TESTS.value:
                    tests.append(p)
                    
        return tests

    def get_team_for_service(self, service_node: str) -> str:
        if service_node not in self.G:
            return "Unknown"
        for s in self.G.successors(service_node):
            if self.G.get_edge_data(service_node, s).get('type') == EdgeType.OWNS.value:
                return s
        return "Unknown"
