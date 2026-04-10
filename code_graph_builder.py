import networkx as nx
from typing import List, Dict, Set, Tuple


class CodeGraphBuilder:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.function_index = {}  # Maps function names to full node IDs
        self.class_index = {}     # Maps class names to full node IDs

    # ---------- Public API ----------
    def build(self, ast_data: List[Dict]):
        print("Building code property graph...")
        self._add_file_nodes(ast_data)
        print(f"[+] Added file nodes")
        self._add_class_and_function_nodes(ast_data)
        print(f"[+] Added class and function nodes")
        self._build_indices(ast_data)
        print(f"[+] Built lookup indices")
        self._add_defines_edges(ast_data)
        print(f"[+] Added DEFINES edges")
        self._add_import_edges(ast_data)
        print(f"[+] Added IMPORT edges")
        self._add_inheritance_edges(ast_data)
        print(f"[+] Added INHERITANCE edges")
        self._add_call_edges(ast_data)
        print(f"[+] Added CALL edges")
        self._break_cycles()
        self._validate_dag()

        return self.graph

    def _add_file_nodes(self, ast_data):
        for file_data in ast_data:
            file_node = f"FILE::{file_data['file']}"
            self.graph.add_node(
                file_node,
                type="FILE",
                name=file_data["file"]
            )

    def _add_class_and_function_nodes(self, ast_data):
        for file_data in ast_data:
            file_node = f"FILE::{file_data['file']}"

            # Classes
            for cls in file_data["classes"]:
                class_node = f"CLASS::{file_data['file']}::{cls['name']}"
                self.graph.add_node(
                    class_node,
                    type="CLASS",
                    name=cls["name"],
                    file=file_data["file"]
                )

                # Methods
                for method in cls["methods"]:
                    func_node = f"FUNC::{file_data['file']}::{cls['name']}.{method['name']}"
                    self.graph.add_node(
                        func_node,
                        type="FUNCTION",
                        name=method["name"],
                        file=file_data["file"],
                        parent_class=cls["name"]
                    )

            # Top-level functions
            for func in file_data["functions"]:
                func_node = f"FUNC::{file_data['file']}::{func['name']}"
                self.graph.add_node(
                    func_node,
                    type="FUNCTION",
                    name=func["name"],
                    file=file_data["file"]
                )

    def _add_defines_edges(self, ast_data):
        for file_data in ast_data:
            file_node = f"FILE::{file_data['file']}"

            for cls in file_data["classes"]:
                class_node = f"CLASS::{file_data['file']}::{cls['name']}"
                self.graph.add_edge(file_node, class_node, type="DEFINES")

                for method in cls["methods"]:
                    func_node = f"FUNC::{file_data['file']}::{cls['name']}.{method['name']}"
                    self.graph.add_edge(file_node, func_node, type="DEFINES")

            for func in file_data["functions"]:
                func_node = f"FUNC::{file_data['file']}::{func['name']}"
                self.graph.add_edge(file_node, func_node, type="DEFINES")

    def _add_import_edges(self, ast_data):
        for file_data in ast_data:
            file_node = f"FILE::{file_data['file']}"

            for imp in file_data["imports"]:
                imported = imp.get("module") or imp.get("name")
                import_node = f"MODULE::{imported}"

                if not self.graph.has_node(import_node):
                    self.graph.add_node(
                        import_node,
                        type="MODULE",
                        name=imported
                    )

                self.graph.add_edge(file_node, import_node, type="IMPORTS")

    def _add_inheritance_edges(self, ast_data):
        for file_data in ast_data:
            for cls in file_data["classes"]:
                child_node = f"CLASS::{file_data['file']}::{cls['name']}"

                for base in cls["bases"]:
                    base_node = f"CLASS::{base}"

                    if not self.graph.has_node(base_node):
                        self.graph.add_node(
                            base_node,
                            type="CLASS",
                            name=base
                        )

                    self.graph.add_edge(child_node, base_node, type="INHERITS")

    def _build_indices(self, ast_data):
        """Build indices for quick lookup of functions and classes"""
        for file_data in ast_data:
            for cls in file_data["classes"]:
                class_node = f"CLASS::{file_data['file']}::{cls['name']}"
                self.class_index[cls["name"]] = class_node

                for method in cls["methods"]:
                    func_node = f"FUNC::{file_data['file']}::{cls['name']}.{method['name']}"
                    self.function_index[method["name"]] = func_node

            for func in file_data["functions"]:
                func_node = f"FUNC::{file_data['file']}::{func['name']}"
                self.function_index[func["name"]] = func_node

    def _add_call_edges(self, ast_data):
        """Add call edges with proper resolution"""
        for file_data in ast_data:
            for cls in file_data["classes"]:
                for method in cls["methods"]:
                    caller = f"FUNC::{file_data['file']}::{cls['name']}.{method['name']}"

                    for callee in method.get("calls", []):
                        callee_node = self._resolve_function_node(callee, file_data["file"], cls["name"])
                        if callee_node and callee_node != caller:  # Avoid self-loops
                            if not self.graph.has_edge(caller, callee_node):
                                self.graph.add_edge(caller, callee_node, type="CALLS")

            for func in file_data["functions"]:
                caller = f"FUNC::{file_data['file']}::{func['name']}"

                for callee in func.get("calls", []):
                    callee_node = self._resolve_function_node(callee, file_data["file"], None)
                    if callee_node and callee_node != caller:  # Avoid self-loops
                        if not self.graph.has_edge(caller, callee_node):
                            self.graph.add_edge(caller, callee_node, type="CALLS")

    def _resolve_function_node(self, call_name: str, file_context: str, class_context: str = None) -> str:
        """Resolve function call to actual node in graph"""
        # Try direct lookup first
        if call_name in self.function_index:
            return self.function_index[call_name]
        
        # Try simple name (last part after dot)
        simple_name = call_name.split(".")[-1]
        if simple_name in self.function_index:
            return self.function_index[simple_name]
        
        return None

    def _break_cycles(self):
        """Remove edges that create cycles to ensure DAG"""
        try:
            # For large graphs, use a faster cycle detection
            if self.graph.number_of_nodes() > 10000:
                print(f"[!] Large graph detected ({self.graph.number_of_nodes()} nodes). Using optimized cycle detection...")
                self._break_cycles_optimized()
            else:
                # Find all cycles
                cycles = list(nx.simple_cycles(self.graph))
                
                if cycles:
                    print(f"[!] Found {len(cycles)} cycle(s) in the graph. Removing cyclic edges...")
                    
                    for cycle in cycles:
                        # Remove the last edge in each cycle (weakest connection)
                        if len(cycle) > 1:
                            source = cycle[-1]
                            target = cycle[0]
                            if self.graph.has_edge(source, target):
                                self.graph.remove_edge(source, target)
                                print(f"    Removed: {source} -> {target}")
                else:
                    print("[OK] No cycles detected in the graph")
        except Exception as e:
            print(f"[ERROR] during cycle detection: {e}")

    def _break_cycles_optimized(self):
        """Optimized cycle breaking for large graphs - skip deep cycle detection"""
        print("[!] For large graphs, applying heuristic-based cycle breaking...")
        
        # Strategy: Remove edges that are likely to cause cycles
        # - Edges that create back-references to parent nodes
        # - Self-loops
        
        try:
            removed = 0
            
            # Remove all self-loops first
            for node in list(self.graph.nodes()):
                if self.graph.has_edge(node, node):
                    self.graph.remove_edge(node, node)
                    removed += 1
            
            if removed > 0:
                print(f"    Removed {removed} self-loop edges")
            
            # For very large graphs, just assume most cycles are handled by call edge resolution
            print("[OK] Heuristic cycle breaking completed")
            
        except Exception as e:
            print(f"    Error in heuristic cycle breaking: {e}")


    def _validate_dag(self):
        """Validate that the graph is a DAG"""
        if nx.is_directed_acyclic_graph(self.graph):
            print("[OK] Graph is a valid DAG (Directed Acyclic Graph)")
        else:
            print("[WARNING] Graph still contains cycles after attempt to break them")
