import sys
import os
from blast_radius.graph.builder import build_graph

def run_validation(repo_path: str):
    print("Building Dependency Graph...")
    G = build_graph(repo_path)
    
    print(f"\n--- Graph Built: {G.number_of_nodes()} Nodes, {G.number_of_edges()} Edges ---")
    
    # Simple summary by NodeType (ignoring un-typed nodes for now)
    type_counts = {}
    for n, data in G.nodes(data=True):
        t = data.get('type')
        if t:
            t_str = str(t)
            type_counts[t_str] = type_counts.get(t_str, 0) + 1
    
    for t_str, count in type_counts.items():
        print(f"{t_str}: {count}")

    print("\n--- Validating Ground Truth Dependencies ---")
    
    # 1. Check if api_gateway imports/calls vehicle_catalog
    norm_api = os.path.normpath("api_gateway/main.py").replace('\\', '/')
    has_edge = G.has_edge(norm_api, 'vehicle_catalog')
    print(f"[ASSERT] api_gateway calls vehicle_catalog API: {'PASS' if has_edge else 'FAIL'}")

    # 2. Check if DB orders exist
    has_db = "DB:order" in G
    print(f"[ASSERT] order_service DB schema extracted (DB:order): {'PASS' if has_db else 'FAIL'}")
    
    # 3. Check if test maps to order_service
    test_node = os.path.normpath("tests/test_order_service.py").replace('\\', '/')
    has_test = G.has_edge(test_node, 'order_service')
    print(f"[ASSERT] test_order_service.py covers order_service: {'PASS' if has_test else 'FAIL'}")
    
    # 4. Check if CODEOWNERS applied
    has_team = G.has_edge('order_service', '@Team-Orders')
    print(f"[ASSERT] @Team-Orders owns order_service: {'PASS' if has_team else 'FAIL'}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validator.py <repo_path>")
        sys.exit(1)
    run_validation(sys.argv[1])
