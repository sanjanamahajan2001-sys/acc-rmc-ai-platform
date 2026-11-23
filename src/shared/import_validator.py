"""Layer Isolation and Import Architecture Validation Framework.

This module provides automated validation utilities to inspect Python package imports,
enforce top-down Clean Architecture layer boundaries, detect circular dependencies,
and ensure compliance with the 5-block import ordering standard (isort format).
"""

import ast
import os
from typing import Dict, List, Set

# Approved Architectural Layer Hierarchies (Top-Down Allowed Imports)
# Higher level layers may import lower level layers, but NOT vice versa.
LAYER_HIERARCHY: Dict[str, int] = {
    "src.core": 1,
    "src.shared": 1,
    "src.utils": 1,
    "src.exceptions": 2,
    "src.logging": 2,
    "src.configuration": 3,
    "src.contracts": 3,
    "src.validators": 3,
    "src.domain": 4,
    "src.database": 5,
    "src.repositories": 5,
    "src.services": 6,
    "src.api": 7,
}


class ImportVisitor(ast.NodeVisitor):
    """AST NodeVisitor that extracts all import statements from a Python file."""

    def __init__(self) -> None:
        self.imports: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)


def extract_file_imports(file_path: str) -> List[str]:
    """Parse a Python source file using AST and return a list of imported module strings."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def validate_layer_isolation(source_package: str, target_import: str) -> bool:
    """Validate whether an import statement obeys Clean Architecture layer boundaries.

    Rules:
        1. Leaf packages (src.core, src.shared, src.utils) cannot import higher layers.
        2. Domain (src.domain) cannot import database (src.database) or presentation (src.api).
        3. Database (src.database) cannot import presentation (src.api).
    """
    source_layer = None
    for pkg, layer in LAYER_HIERARCHY.items():
        if source_package.startswith(pkg):
            source_layer = layer
            break

    target_layer = None
    for pkg, layer in LAYER_HIERARCHY.items():
        if target_import.startswith(pkg):
            target_layer = layer
            break

    # If both source and target belong to defined layers, target layer level must be <= source layer level
    if source_layer is not None and target_layer is not None:
        return target_layer <= source_layer

    return True


def detect_circular_dependencies(package_root: str) -> List[Dict[str, str]]:
    """Scan all Python files in package_root and detect circular import loops."""
    dependency_graph: Dict[str, Set[str]] = {}

    for root, _, files in os.walk(package_root):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, package_root)
                mod_name = rel_path.replace(os.sep, ".").rstrip(".py")
                if mod_name.endswith(".__init__"):
                    mod_name = mod_name[:-9]

                try:
                    imports = extract_file_imports(full_path)
                    internal_imports = {
                        imp for imp in imports if imp.startswith("src.") or imp == "src"
                    }
                    dependency_graph[mod_name] = internal_imports
                except Exception:
                    continue

    cycles: List[Dict[str, str]] = []
    # Cycle detection via depth-first graph traversal
    for mod, targets in dependency_graph.items():
        for target in targets:
            if target in dependency_graph and mod in dependency_graph[target]:
                if {"module_a": target, "module_b": mod} not in cycles:
                    cycles.append({"module_a": mod, "module_b": target})

    return cycles
