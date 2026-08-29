"""AST Extraction and Canonical Normalization Engine for PyDocSync.

WHAT IS THIS?
-------------
Extracts Python functions and class methods into SymbolRepresentation models,
performing canonical AST normalization (stripping location metadata while preserving
semantic AST attributes like ctx and stripping leading docstrings).
"""

import ast
from dataclasses import dataclass
from typing import Any


@dataclass
class SymbolRepresentation:
    """Structured representation of a Python callable or class symbol."""

    name: str
    qualname: str
    symbol_type: str  # "function", "async_function", "method", "class"
    lineno: int
    raw_node: ast.AST
    canonical_body_ast: ast.AST
    docstring: str | None
    is_public: bool


class CanonicalASTNormalizer(ast.NodeTransformer):
    """Normalizes AST by stripping location metadata while preserving semantic attributes."""

    def generic_visit(self, node: ast.AST) -> ast.AST:
        # Strip location metadata safely
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
            if getattr(node, attr, None) is not None:
                try:
                    delattr(node, attr)
                except AttributeError:
                    pass
        return super().generic_visit(node)


def canonicalize_node(node: ast.AST) -> ast.AST:
    """Create a deep copy of an AST node with stripped location metadata."""
    node_copy = ast.parse(ast.unparse(node)) if hasattr(ast, "unparse") else node
    normalizer = CanonicalASTNormalizer()
    return normalizer.visit(node_copy)


def strip_leading_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    """Remove leading docstring statement from a function/class body list."""
    if not body:
        return body
    first_stmt = body[0]
    if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant) and isinstance(first_stmt.value.value, str):
        return body[1:]
    return body


class SymbolVisitor(ast.NodeVisitor):
    """Walks Python module AST and collects all callable and class symbol representations."""

    def __init__(self) -> None:
        self.symbols: list[SymbolRepresentation] = []
        self._scope_stack: list[str] = []

    def _get_qualname(self, name: str) -> str:
        if self._scope_stack:
            return f"{'.'.join(self._scope_stack)}.{name}"
        return name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_callable(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_callable(node, is_async=True)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qualname = self._get_qualname(node.name)
        docstring = ast.get_docstring(node)
        cleaned_body = strip_leading_docstring(list(node.body))
        
        # Build synthetic class container for body
        class_body_container = ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=cleaned_body,
            decorator_list=node.decorator_list,
        )
        canonical_body = canonicalize_node(class_body_container)

        self.symbols.append(
            SymbolRepresentation(
                name=node.name,
                qualname=qualname,
                symbol_type="class",
                lineno=node.lineno,
                raw_node=node,
                canonical_body_ast=canonical_body,
                docstring=docstring,
                is_public=not node.name.startswith("_"),
            )
        )

        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def _process_callable(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        qualname = self._get_qualname(node.name)
        docstring = ast.get_docstring(node)
        cleaned_body = strip_leading_docstring(list(node.body))
        
        func_body_container = ast.Module(body=cleaned_body, type_ignores=[])
        canonical_body = canonicalize_node(func_body_container)
        
        sym_type = "method" if self._scope_stack else ("async_function" if is_async else "function")

        self.symbols.append(
            SymbolRepresentation(
                name=node.name,
                qualname=qualname,
                symbol_type=sym_type,
                lineno=node.lineno,
                raw_node=node,
                canonical_body_ast=canonical_body,
                docstring=docstring,
                is_public=not node.name.startswith("_"),
            )
        )


def extract_symbols_from_source(source_code: str) -> list[SymbolRepresentation]:
    """Parse Python source code and extract canonical symbol representations."""
    tree = ast.parse(source_code)
    visitor = SymbolVisitor()
    visitor.visit(tree)
    return visitor.symbols
