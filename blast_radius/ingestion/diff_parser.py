import re
from typing import List, Dict

class ChangedSymbol:
    def __init__(self, name: str, file: str, service: str, change_type: str):
        self.name = name
        self.file = file
        self.service = service
        self.change_type = change_type

    def __repr__(self):
        return f"ChangedSymbol(name='{self.name}', file='{self.file}', service='{self.service}', change_type='{self.change_type}')"

def parse_unified_diff(diff_text: str) -> List[Dict]:
    """
    Very naive unified diff parser to simulate extracting affected lines.
    Returns a list of dicts: {"file": str, "added_lines": list, "removed_lines": list}
    """
    files = []
    current_file = None
    added = []
    removed = []
    
    lines = diff_text.split('\n')
    for line in lines:
        if line.startswith("+++ b/"):
            if current_file:
                files.append({"file": current_file, "added_lines": added, "removed_lines": removed})
            current_file = line[6:]
            added = []
            removed = []
        elif line.startswith("+++ "):
            # Fallback if no b/ prefix
            if current_file:
                files.append({"file": current_file, "added_lines": added, "removed_lines": removed})
            current_file = line[4:]
            added = []
            removed = []
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
            
    if current_file:
        files.append({"file": current_file, "added_lines": added, "removed_lines": removed})
        
    return files
