"""Multi-Representation Fingerprint Generator for PyDocSync.

WHAT IS THIS?
-------------
Calculates discrete, deterministic SHA-256 fingerprints for:
- CODE (Normalized implementation AST)
- API (Signature structure, parameter names/kinds, default values)
- TYPE (Type annotations on parameters and return)
- DOC (Normalized docstring)
- RAISE_TYPE (Exception class names)
- RAISE_DETAIL (Exception message string literals & constraints)
- EXAMPLE (Doctest code blocks)
"""

import ast
import hashlib
import re
from dataclasses import asdict, dataclass
from typing import Any

from pydocsync.ast_extract import SymbolRepresentation


@dataclass
class FingerprintSet:
    """Container for discrete representation fingerprints of a single symbol."""

    code: str
    api: str
    types: str
    doc: str
    raise_type: str
    raise_detail: str
    example: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_str(val: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(val.encode("utf-8")).hexdigest()


def compute_code_fingerprint(sym: SymbolRepresentation) -> str:
    """Hash the normalized AST body."""
    ast_dump = ast.dump(sym.canonical_body_ast, include_attributes=False)
    return _hash_str(ast_dump)


def compute_api_fingerprint(sym: SymbolRepresentation) -> str:
    """Extract signature parameter structure, order, kinds, and default values."""
    node = sym.raw_node
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if isinstance(node, ast.ClassDef):
            # Class signature: bases + keywords + decorators
            bases = [ast.unparse(b) for b in node.bases]
            keywords = [f"{kw.arg}={ast.unparse(kw.value)}" for kw in node.keywords]
            decs = [ast.unparse(d) for d in node.decorator_list]
            return _hash_str(f"class:{node.name}:bases={bases}:kw={keywords}:decs={decs}")
        return _hash_str(sym.name)

    args = node.args
    components: list[str] = []

    # Decorators
    for d in node.decorator_list:
        components.append(f"dec:{ast.unparse(d)}")

    # Positional-only args
    for arg in getattr(args, "posonlyargs", []):
        components.append(f"posonly:{arg.arg}")

    # Standard args
    for arg in args.args:
        components.append(f"arg:{arg.arg}")

    # Defaults (aligned from the right)
    for default in args.defaults:
        components.append(f"default:{ast.unparse(default)}")

    # Vararg (*args)
    if args.vararg:
        components.append(f"vararg:{args.vararg.arg}")

    # Keyword-only args & defaults
    for kwarg, default in zip(args.kwonlyargs, args.kw_defaults):
        default_str = ast.unparse(default) if default is not None else "None"
        components.append(f"kwonly:{kwarg.arg}={default_str}")

    # Kwarg (**kwargs)
    if args.kwarg:
        components.append(f"kwarg:{args.kwarg.arg}")

    return _hash_str("|".join(components))


def compute_type_fingerprint(sym: SymbolRepresentation) -> str:
    """Extract parameter and return type annotations."""
    node = sym.raw_node
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _hash_str("none")

    type_parts: list[str] = []
    args = node.args
    all_args = getattr(args, "posonlyargs", []) + args.args + args.kwonlyargs
    if args.vararg:
        all_args.append(args.vararg)
    if args.kwarg:
        all_args.append(args.kwarg)

    for arg in all_args:
        if arg.annotation:
            type_parts.append(f"{arg.arg}:{ast.unparse(arg.annotation)}")
        else:
            type_parts.append(f"{arg.arg}:untyped")

    if node.returns:
        type_parts.append(f"return:{ast.unparse(node.returns)}")
    else:
        type_parts.append("return:untyped")

    return _hash_str("|".join(type_parts))


def compute_doc_fingerprint(sym: SymbolRepresentation) -> str:
    """Hash normalized docstring text."""
    if not sym.docstring:
        return _hash_str("__EMPTY_DOC__")
    # Normalize whitespace across lines
    lines = [line.strip() for line in sym.docstring.strip().splitlines() if line.strip()]
    normalized_doc = "\n".join(lines)
    return _hash_str(normalized_doc)


class ExceptionVisitor(ast.NodeVisitor):
    """Inspects AST for raise statements and extracts exception types and message literals."""

    def __init__(self) -> None:
        self.raise_types: list[str] = []
        self.raise_details: list[str] = []

    def visit_Raise(self, node: ast.Raise) -> None:
        if node.exc is None:
            self.raise_types.append("BareRaise")
            self.raise_details.append("reraise")
            return

        if isinstance(node.exc, ast.Name):
            self.raise_types.append(node.exc.id)
            self.raise_details.append("")
        elif isinstance(node.exc, ast.Call):
            func_name = ast.unparse(node.exc.func)
            self.raise_types.append(func_name)
            # Extract first string literal argument if present
            detail = ""
            if node.exc.args:
                first_arg = node.exc.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    detail = first_arg.value
                elif isinstance(first_arg, ast.JoinedStr):
                    # Normalized f-string template
                    parts: list[str] = []
                    for val in first_arg.values:
                        if isinstance(val, ast.Constant):
                            parts.append(str(val.value))
                        else:
                            parts.append("{var}")
                    detail = "".join(parts)
                else:
                    detail = ast.unparse(first_arg)
            self.raise_details.append(detail)
        else:
            self.raise_types.append(ast.unparse(node.exc))
            self.raise_details.append("")

        self.generic_visit(node)


def compute_raise_fingerprints(sym: SymbolRepresentation) -> tuple[str, str]:
    """Return (RAISE_TYPE_FINGERPRINT, RAISE_DETAIL_FINGERPRINT)."""
    visitor = ExceptionVisitor()
    visitor.visit(sym.raw_node)
    type_hash = _hash_str(",".join(sorted(visitor.raise_types)) if visitor.raise_types else "__NO_RAISES__")
    detail_hash = _hash_str("|".join(sorted(visitor.raise_details)) if visitor.raise_details else "__NO_DETAILS__")
    return type_hash, detail_hash


def compute_example_fingerprint(sym: SymbolRepresentation) -> str | None:
    """Extract runnable doctest example lines from docstring."""
    if not sym.docstring:
        return None
    # Find all doctest lines starting with >>> or ...
    doctest_lines = re.findall(r"^\s*(?:>>>|\.\.\.)\s+(.+)$", sym.docstring, flags=re.MULTILINE)
    if not doctest_lines:
        return None
    return _hash_str("\n".join(doctest_lines))


def generate_fingerprints(sym: SymbolRepresentation) -> FingerprintSet:
    """Generate all 7 discrete representation fingerprints for a symbol."""
    raise_type, raise_detail = compute_raise_fingerprints(sym)
    return FingerprintSet(
        code=compute_code_fingerprint(sym),
        api=compute_api_fingerprint(sym),
        types=compute_type_fingerprint(sym),
        doc=compute_doc_fingerprint(sym),
        raise_type=raise_type,
        raise_detail=raise_detail,
        example=compute_example_fingerprint(sym),
    )
