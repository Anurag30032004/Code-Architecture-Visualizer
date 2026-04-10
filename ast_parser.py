import ast
import os
from typing import Dict, List, Any


class ASTParser(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path

        self.structure = {
            "file": os.path.basename(file_path),
            "module": file_path.replace(os.sep, "."),
            "imports": [],
            "classes": [],
            "functions": [],
            "function_calls": []
        }

        self.current_class = None
        self.current_function = None

    # ---------- Imports ----------
    def visit_Import(self, node):
        for alias in node.names:
            self.structure["imports"].append({
                "type": "import",
                "module": alias.name,
                "alias": alias.asname
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.structure["imports"].append({
                "type": "from_import",
                "module": node.module,
                "name": alias.name,
                "alias": alias.asname
            })
        self.generic_visit(node)

    # ---------- Classes ----------
    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "bases": [self._get_name(base) for base in node.bases],
            "methods": [],
            "lineno": node.lineno
        }

        self.current_class = class_info
        self.structure["classes"].append(class_info)

        self.generic_visit(node)
        self.current_class = None

    # ---------- Functions ----------
    def visit_FunctionDef(self, node):
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "returns": self._get_name(node.returns),
            "lineno": node.lineno,
            "calls": []
        }

        self.current_function = func_info

        if self.current_class:
            self.current_class["methods"].append(func_info)
        else:
            self.structure["functions"].append(func_info)

        self.generic_visit(node)
        self.current_function = None

    # ---------- Function Calls ----------
    def visit_Call(self, node):
        call_name = self._get_call_name(node.func)

        call_info = {
            "function": call_name,
            "lineno": node.lineno,
            "inside": self.current_function["name"]
            if self.current_function else None
        }

        self.structure["function_calls"].append(call_info)

        if self.current_function:
            self.current_function["calls"].append(call_name)

        self.generic_visit(node)

    # ---------- Helpers ----------
    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return None

    def _get_call_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_call_name(node.value)}.{node.attr}"
        return "unknown"

def parse_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    parser = ASTParser(file_path)
    parser.visit(tree)

    return parser.structure

def parse_project(root_dir: str) -> List[Dict[str, Any]]:
    ast_data = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                ast_data.append(parse_file(file_path))

    return ast_data




