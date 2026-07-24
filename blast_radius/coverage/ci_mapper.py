import os
import yaml
from typing import List, Tuple

class CIMapper:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # list of (job_name, covered_service_or_file)
        self.ci_jobs = []

    def parse_ci_workflows(self):
        wf_dir = os.path.join(self.repo_root, ".github", "workflows")
        if not os.path.exists(wf_dir):
            return
            
        for root_dir, _, files in os.walk(wf_dir):
            for file in files:
                if file.endswith((".yml", ".yaml")):
                    self._parse_file(os.path.join(root_dir, file))
                    
    def _parse_file(self, filepath: str):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                
            jobs = data.get("jobs", {})
            for job_name, job_data in jobs.items():
                steps = job_data.get("steps", [])
                for step in steps:
                    run_cmd = step.get("run", "")
                    if "pytest" in run_cmd:
                        # naive extraction: look for seed/tests/test_{service}.py
                        parts = run_cmd.split()
                        for p in parts:
                            if "test_" in p:
                                # example map: pytest seed/tests/test_vehicle_catalog.py
                                # This tests the vehicle_catalog service.
                                self.ci_jobs.append((job_name, p))
        except Exception as e:
            print(f"Error parsing CI {filepath}: {e}")
