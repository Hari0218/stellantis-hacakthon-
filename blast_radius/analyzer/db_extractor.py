import ast
import os
from collections import defaultdict
from typing import List, Tuple

class DatabaseExtractor:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # list of (file_path, class_name, tablename)
        self.tables = []

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
            
            visitor = _DBVisitor(rel_path)
            visitor.visit(tree)
            
            self.tables.extend(visitor.tables)
            
        except Exception as e:
            print(f"Error parsing DB usage in {filepath}: {e}")

    def analyze_directory(self, dir_path: str):
        abs_dir = os.path.abspath(dir_path)
        for root, _, files in os.walk(abs_dir):
            for file in files:
                if file.endswith(".py"):
                    self.visit_file(os.path.join(root, file))

class _DBVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.tables = []

    def visit_ClassDef(self, node):
        is_model = any(
            isinstance(b, ast.Name) and b.id == "Base" for b in node.bases
        )
        if is_model:
            # Find __tablename__
            tablename = node.name.lower()
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(stmt.value, ast.Constant):
                                tablename = stmt.value.value
            self.tables.append((self.rel_path, node.name, tablename))
        self.generic_visit(node)
