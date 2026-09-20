"""AST Extraction and Canonical Normalization Engine for PyDocSync.

WHAT IS THIS?
-------------
Extracts Python functions and class methods into SymbolRepresentation models,
performing canonical AST normalization (stripping location metadata while preserving
semantic AST attributes like ctx and stripping leading docstrings). Also assigns each symbol a
per-file unique baseline key and loads source files into symbols, reporting unreadable or
unparseable files as structured problems instead of skipping them.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydocsync.problems import Problem, ProblemKind


@dataclass
class SymbolRepresentation:
    """Structured representation of a Python callable or class symbol.

    `qualname` is the name as written in source (e.g. `Box.size`) and may repeat within a file
    (redefinitions, `@overload`, property getter and setter). `key` is the per-file unique
    baseline key: the first definition keeps `qualname`, later ones are `qualname#2`, `qualname#3`.
    """

    name: str
    qualname: str
    symbol_type: str  # "function", "async_function", "method", "class"
    lineno: int
    raw_node: ast.AST
    canonical_body_ast: ast.AST
    docstring: str | None
    is_public: bool
    key: str = ""

    def __post_init__(self) -> None:
        # Default the baseline key to the qualified name; extraction disambiguates duplicates.
        if not self.key:
            self.key = self.qualname


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
        
        # Build synthetic class container for body. A class whose body was only a docstring would
        # become empty, which cannot be unparsed/re-parsed (it made the whole file unparseable);
        # `pass` is semantically identical, so it is used as the placeholder body.
        class_body_container = ast.ClassDef(
            name=node.name,
            bases=node.bases,
            keywords=node.keywords,
            body=cleaned_body or [ast.Pass()],
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


def assign_unique_keys(symbols: list[SymbolRepresentation]) -> None:
    """Give every symbol a per-file unique baseline key, in source order.

    The first definition of a qualified name keeps its plain name (identical to the keys written
    by v0.3.0). Later definitions of the same name (redefinitions, `@overload` stubs, property
    setters) become `name#2`, `name#3`, ... so they no longer overwrite each other's records.
    `#` cannot occur in a Python identifier, so keys never collide with real names.

    Args:
        symbols: Symbols in source order; their `key` attributes are updated in place.
    """
    seen: dict[str, int] = {}
    for sym in symbols:
        seen[sym.qualname] = seen.get(sym.qualname, 0) + 1
        occurrence = seen[sym.qualname]
        sym.key = sym.qualname if occurrence == 1 else f"{sym.qualname}#{occurrence}"


def extract_symbols_from_source(source_code: str) -> list[SymbolRepresentation]:
    """Parse Python source code and extract canonical symbol representations.

    Args:
        source_code: Python source text.

    Returns:
        Symbols in source order, each with a per-file unique `key`.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    tree = ast.parse(source_code)
    visitor = SymbolVisitor()
    visitor.visit(tree)
    assign_unique_keys(visitor.symbols)
    return visitor.symbols


def load_symbols(abs_path: Path, rel_path: Path) -> tuple[list[SymbolRepresentation], Problem | None]:
    """Read and parse one Python file, reporting failure as a Problem instead of skipping it.

    Only conditions caused by the input file are caught (I/O, decoding, syntax, oversized nesting);
    anything else is a bug in PyDocSync and propagates.

    Args:
        abs_path: Absolute path of the file to read.
        rel_path: Path relative to the scan root, used in the reported problem.

    Returns:
        `(symbols, None)` on success, or `([], problem)` when the file could not be evaluated.
    """
    display = rel_path.as_posix()
    try:
        source = abs_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [], Problem(ProblemKind.SOURCE_UNREADABLE, display, None, f"{type(err).__name__}: {err}")

    try:
        return extract_symbols_from_source(source), None
    except SyntaxError as err:
        reason = f"SyntaxError line {err.lineno}: {err.msg}" if err.lineno else f"SyntaxError: {err.msg}"
        return [], Problem(ProblemKind.SOURCE_UNPARSEABLE, display, err.lineno, reason)
    except (ValueError, RecursionError) as err:
        # ValueError: NUL bytes on older interpreters; RecursionError: pathologically nested source.
        return [], Problem(ProblemKind.SOURCE_UNPARSEABLE, display, None, f"{type(err).__name__}: {err}")
