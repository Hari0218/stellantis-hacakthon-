import ast
import os
from typing import List, Tuple, Dict, Optional


class ServiceCallExtractor:
    """
    Detects real inter-service HTTP calls by statically finding base-URL
    string constants (e.g. INVENTORY_SERVICE_URL = "http://localhost:8002")
    or URL lookup dicts (e.g. SERVICE_URLS = {"vehicle_catalog": "http://..."})
    and then finding where those names are actually *used* in the file
    (httpx.get(f"{INVENTORY_SERVICE_URL}/reserve"), SERVICE_URLS["order_service"],
    SERVICE_URLS.get("auth_service"), etc).

    This replaces hand-picked/hardcoded "service A calls service B" edges with
    something derived from the actual code, so it generalizes to any service
    added to the repo later, not just the two relationships that existed in
    the original seed demo.
    """

    def __init__(self, repo_root: str, known_services: List[str]):
        self.repo_root = os.path.abspath(repo_root)
        self.known_services = set(known_services)

        # list of (source_file, target_service)
        self.service_calls: List[Tuple[str, str]] = []

    def _get_relative_path(self, filepath: str) -> str:
        return os.path.relpath(filepath, self.repo_root).replace("\\", "/")

    def _match_service(self, const_name: str) -> Optional[str]:
        """Guess the service a constant name like INVENTORY_SERVICE_URL refers to."""
        guess = const_name.lower()
        if guess.endswith("_url"):
            guess = guess[:-4]
        if guess in self.known_services:
            return guess
        if f"{guess}_service" in self.known_services:
            return f"{guess}_service"
        for svc in self.known_services:
            if svc.replace("_service", "") == guess.replace("_service", ""):
                return svc
        return None

    def visit_file(self, filepath: str):
        if not filepath.endswith(".py"):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            rel_path = self._get_relative_path(filepath)
        except Exception as e:
            print(f"Error parsing service calls in {filepath}: {e}")
            return

        url_const_to_service: Dict[str, str] = {}
        dict_var_service_map: Dict[str, Dict[str, str]] = {}

        # Step 1: find module/function-level URL constants and URL lookup dicts.
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue

                if (
                    isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    and node.value.value.startswith("http")
                    and target.id.upper().endswith("_URL")
                ):
                    svc = self._match_service(target.id)
                    if svc:
                        url_const_to_service[target.id] = svc

                elif isinstance(node.value, ast.Dict):
                    mapping = {}
                    for k, v in zip(node.value.keys, node.value.values):
                        if (
                            isinstance(k, ast.Constant)
                            and isinstance(k.value, str)
                            and isinstance(v, ast.Constant)
                            and isinstance(v.value, str)
                            and v.value.startswith("http")
                        ):
                            svc = k.value if k.value in self.known_services else self._match_service(k.value)
                            if svc:
                                mapping[k.value] = svc
                    if mapping:
                        dict_var_service_map[target.id] = mapping

        if not url_const_to_service and not dict_var_service_map:
            return

        # Step 2: find where those constants/dicts are actually referenced.
        found_services = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in url_const_to_service:
                found_services.add(url_const_to_service[node.id])

            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id in dict_var_service_map:
                    key_node = node.slice
                    if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                        mapping = dict_var_service_map[node.value.id]
                        if key_node.value in mapping:
                            found_services.add(mapping[key_node.value])

            elif isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in dict_var_service_map
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                ):
                    mapping = dict_var_service_map[node.func.value.id]
                    if node.args[0].value in mapping:
                        found_services.add(mapping[node.args[0].value])

        for svc in found_services:
            self.service_calls.append((rel_path, svc))

    def analyze_directory(self, dir_path: str):
        abs_dir = os.path.abspath(dir_path)
        for root, _, files in os.walk(abs_dir):
            for file in files:
                if file.endswith(".py"):
                    self.visit_file(os.path.join(root, file))