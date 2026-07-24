import os
from typing import List, Tuple

class CodeownersParser:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # list of (path_pattern, team_name)
        self.owners = []

    def parse(self):
        co_path = os.path.join(self.repo_root, "CODEOWNERS")
        if not os.path.exists(co_path):
            return
            
        try:
            with open(co_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    parts = line.split()
                    if len(parts) >= 2:
                        path_pattern = parts[0].strip('/')
                        team = parts[1]
                        self.owners.append((path_pattern, team))
        except Exception as e:
            print(f"Error parsing CODEOWNERS: {e}")
