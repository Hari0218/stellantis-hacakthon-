import ast
import os
from typing import List, Tuple

class TestMapper:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # list of (test_file_path, imported_module)
        self.test_maps = []

    def _get_relative_path(self, filepath: str) -> str:
        return os.path.relpath(filepath, self.repo_root).replace("\\", "/")

    def visit_file(self, filepath: str):
        if not filepath.endswith(".py") or "tests" not in filepath:
            return
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
            rel_path = self._get_relative_path(filepath)
            
            visitor = _TestVisitor(rel_path)
            visitor.visit(tree)
            
            self.test_maps.extend(visitor.tested_modules)
            
        except Exception as e:
            print(f"Error parsing Test files in {filepath}: {e}")

    def analyze_directory(self, dir_path: str):
        abs_dir = os.path.abspath(dir_path)
        for root, _, files in os.walk(abs_dir):
            for file in files:
                if file.endswith(".py") and file.startswith("test_"):
                    self.visit_file(os.path.join(root, file))

class _TestVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.tested_modules = []

    def visit_Import(self, node):
        for alias in node.names:
            if not alias.name.startswith("pytest"):
                self.tested_modules.append((self.rel_path, alias.name))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and not node.module.startswith("pytest"):
            # store the top-level module to indicate mapping to that service
            self.tested_modules.append((self.rel_path, node.module.split('.')[0]))
        self.generic_visit(node)
