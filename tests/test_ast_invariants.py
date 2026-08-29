"""AST Normalization Invariants & Context Semantic Preservation Test Suite.

WHAT IS THIS?
-------------
Verifies:
1. Location stripping: lineno, col_offset, end_lineno, end_col_offset are cleanly stripped.
2. Context preservation: ast.Load, ast.Store, ast.Del semantic contexts are preserved.
3. Operator and constant semantics: Literal constants and AST node types are preserved.
"""

import ast
from pydocsync.ast_extract import (
    CanonicalASTNormalizer,
    canonicalize_node,
    extract_symbols_from_source,
)
from pydocsync.fingerprint import generate_fingerprints


def test_location_metadata_stripping_invariance():
    """Verify that shifting line numbers and column offsets results in identical normalized AST."""
    code_a = """
def sample_fn(x: int) -> int:
    y = x + 10
    return y
"""

    code_b = """


def sample_fn(x: int) -> int:
        y = x + 10
        return y
"""

    sym_a = extract_symbols_from_source(code_a)[0]
    sym_b = extract_symbols_from_source(code_b)[0]

    fp_a = generate_fingerprints(sym_a)
    fp_b = generate_fingerprints(sym_b)

    assert fp_a.code == fp_b.code
    assert fp_a.api == fp_b.api
    assert fp_a.types == fp_b.types


def test_context_semantics_preservation():
    """Verify that Load vs Store vs Del produces distinct AST dumps."""
    node_load = ast.Name(id="x", ctx=ast.Load())
    node_store = ast.Name(id="x", ctx=ast.Store())
    node_del = ast.Name(id="x", ctx=ast.Del())

    normalizer = CanonicalASTNormalizer()
    canon_load = normalizer.visit(node_load)
    canon_store = normalizer.visit(node_store)
    canon_del = normalizer.visit(node_del)

    dump_load = ast.dump(canon_load)
    dump_store = ast.dump(canon_store)
    dump_del = ast.dump(canon_del)

    assert dump_load != dump_store
    assert dump_load != dump_del
    assert dump_store != dump_del
    assert "Load" in dump_load
    assert "Store" in dump_store
    assert "Del" in dump_del


def test_constant_preservation():
    """Verify that constant literals are preserved across normalization."""
    code_10 = "def f(): return 10"
    code_20 = "def f(): return 20"

    sym_10 = extract_symbols_from_source(code_10)[0]
    sym_20 = extract_symbols_from_source(code_20)[0]

    fp_10 = generate_fingerprints(sym_10)
    fp_20 = generate_fingerprints(sym_20)

    assert fp_10.code != fp_20.code
