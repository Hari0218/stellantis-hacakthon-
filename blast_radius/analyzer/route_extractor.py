import ast
import os
from collections import defaultdict
from typing import List, Dict, Tuple

class RouteExtractor:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # list of (file_path, function_name, method, path)
        self.endpoints = []

    def _get_relative_path(self, filepath: str) -> str:
        return os.path.relpath(filepath, self.repo_root).replace("\\", "/")

    def visit_file(self, filepath: str):
        if not filepath.endswith(".py"):
            return
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            rel_path = self._get_relative_path(filepath)
            
            visitor = _RouteVisitor(rel_path)
            visitor.visit(tree)
            
            self.endpoints.extend(visitor.endpoints)
            
        except Exception as e:
            print(f"Error parsing routes in {filepath}: {e}")

    def analyze_directory(self, dir_path: str):
        abs_dir = os.path.abspath(dir_path)
        for root, _, files in os.walk(abs_dir):
            for file in files:
                if file.endswith(".py"):
                    self.visit_file(os.path.join(root, file))

class _RouteVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.endpoints = []

    def visit_FunctionDef(self, node):
        self._check_decorators(node)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self._check_decorators(node)
        self.generic_visit(node)

    def _check_decorators(self, node):
        # We are looking for things like @app.get("/path")
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ("get", "post", "put", "delete", "patch"):
                    # Basic assumption: it's a route if the decorator is a known HTTP method and it has args
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        path = decorator.args[0].value
                        method = decorator.func.attr.upper()
                        self.endpoints.append((self.rel_path, node.name, method, path))
