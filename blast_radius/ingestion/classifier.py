from typing import List, Dict
import ast
import os
from blast_radius.ingestion.diff_parser import ChangedSymbol, parse_unified_diff

class ChangeClassifier:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        
    def classify_diff(self, diff_text: str) -> List[ChangedSymbol]:
        """
        Classifies the exact nature of the change based on the diff and AST.
        """
        parsed_files = parse_unified_diff(diff_text)
        results = []
        
        for f_dict in parsed_files:
            filepath = f_dict["file"]
            added = f_dict["added_lines"]
            removed = f_dict["removed_lines"]
            
            # Simple heuristic without re-parsing entire AST diff tree for demonstration:
            # 1. New route decorator -> NEW_ENDPOINT
            # 2. Def signature changed -> SIGNATURE_CHANGE
            # 3. SQLAlchemy model field -> SCHEMA_CHANGE
            # 4. Otherwise -> LOGIC_CHANGE
            
            service_name = filepath.split('/')[0] if '/' in filepath else 'unknown'
            
            # check for Schema (SQLAlchemy field addition/removal) -> typical lines are Column(...)
            if any("Column(" in line for line in added) or any("Column(" in line for line in removed):
                results.append(ChangedSymbol("DB_Model_Field", filepath, service_name, "SCHEMA_CHANGE"))
                continue
                
            # check for Endpoints (app.get etc) added/removed
            if any(("@app." in line for line in added)):
                results.append(ChangedSymbol("API_Route", filepath, service_name, "NEW_ENDPOINT"))
                continue
                
            if any(("@app." in line for line in removed)):
                results.append(ChangedSymbol("API_Route", filepath, service_name, "DELETED_ENDPOINT"))
                continue
                
            # check for signature changes (def name(args))
            if any("def " in line for line in added) and any("def " in line for line in removed):
                # We assume it's modifying an existing function signature
                results.append(ChangedSymbol("function_signature", filepath, service_name, "SIGNATURE_CHANGE"))
                continue
            
            # We assume it's just logic change
            # Get the exact function using AST by parsing the actual file on disk. 
            # In a real tool this uses line numbers from diff context headers.
            # Here we just output a logic change for the file.
            results.append(ChangedSymbol("function_logic", filepath, service_name, "LOGIC_CHANGE"))
            
        return results

if __name__ == "__main__":
    test_diff = \"\"\"
--- a/vehicle_catalog/main.py
+++ b/vehicle_catalog/main.py
@@ -10,10 +10,10 @@
-def get_vehicle_by_vin(db: Session, vin: str) -> Vehicle:
+def get_vehicle_by_vin(db: Session, vin: str, status: str = "active") -> Vehicle:
\"\"\"
    classifier = ChangeClassifier(".")
    res = classifier.classify_diff(test_diff)
    print(res)
