import ast
import os
from collections import defaultdict
from typing import List, Dict, Any, Tuple

class ASTAnalyzer:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        
        # Raw extracted data
        # file_path -> list of (module_name, name)
        self.imports = defaultdict(list)
        
        # file_path -> dict(function_name -> list of called function names)
        # Note: function_name includes class name if it's a method
        self.function_calls = defaultdict(lambda: defaultdict(list))
        
        # file_path -> list of function names defined
        self.defined_functions = defaultdict(list)

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
            
            visitor = _FileVisitor(rel_path)
            visitor.visit(tree)
            
            self.imports[rel_path] = visitor.imports
            self.defined_functions[rel_path] = visitor.defined_functions
            self.function_calls[rel_path] = visitor.function_calls
            
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")

    def analyze_directory(self, dir_path: str):
        abs_dir = os.path.abspath(dir_path)
        for root, _, files in os.walk(abs_dir):
            for file in files:
                if file.endswith(".py"):
                    self.visit_file(os.path.join(root, file))

class _FileVisitor(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.imports = []
        self.defined_functions = []
        self.function_calls = defaultdict(list)
        
        self.current_function = None
        self.current_class = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append((alias.name, None))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append((module, alias.name))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node):
        return self._visit_function(node)
        
    def visit_AsyncFunctionDef(self, node):
        return self._visit_function(node)

    def _visit_function(self, node):
        func_name = node.name
        if self.current_class:
            func_name = f"{self.current_class}.{node.name}"
            
        self.defined_functions.append(func_name)
        
        old_func = self.current_function
        self.current_function = func_name
        self.generic_visit(node)
        self.current_function = old_func

    def visit_Call(self, node):
        if self.current_function:
            # Very simplistic call extraction: just look at the func name if it's a Name or Attribute
            if isinstance(node.func, ast.Name):
                self.function_calls[self.current_function].append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                self.function_calls[self.current_function].append(node.func.attr)
        self.generic_visit(node)
