"""Layer 1: Unit tests for AST normalization and multi-representation fingerprinting."""

import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.fingerprint import generate_fingerprints


def test_comment_and_whitespace_invariance():
    """Verify that comments and whitespace changes do not alter CODE_FINGERPRINT."""
    src1 = '''def calc(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''
    src2 = '''def calc(a: int, b: int) -> int:
    """Add two numbers."""
    # This is an inline comment
    
    return a + b
'''
    sym1 = extract_symbols_from_source(src1)[0]
    sym2 = extract_symbols_from_source(src2)[0]

    fp1 = generate_fingerprints(sym1)
    fp2 = generate_fingerprints(sym2)

    assert fp1.code == fp2.code
    assert fp1.api == fp2.api
    assert fp1.types == fp2.types
    assert fp1.doc == fp2.doc


def test_default_value_alters_api_not_type():
    """Verify that changing default parameter value changes API but preserves TYPE."""
    src1 = '''def fetch(url: str, timeout: int = 30) -> str:
    """Fetch URL."""
    return url
'''
    src2 = '''def fetch(url: str, timeout: int = 60) -> str:
    """Fetch URL."""
    return url
'''
    sym1 = extract_symbols_from_source(src1)[0]
    sym2 = extract_symbols_from_source(src2)[0]

    fp1 = generate_fingerprints(sym1)
    fp2 = generate_fingerprints(sym2)

    assert fp1.api != fp2.api, "Default value change MUST alter API_FINGERPRINT"
    assert fp1.types == fp2.types, "Default value change MUST NOT alter TYPE_FINGERPRINT"


def test_exception_detail_vs_type_fingerprint():
    """Verify that changing exception string literal changes RAISE_DETAIL but keeps RAISE_TYPE."""
    src1 = '''def validate(x: int) -> None:
    if x < 3:
        raise ValueError("minimum 3 items")
'''
    src2 = '''def validate(x: int) -> None:
    if x < 5:
        raise ValueError("minimum 5 items")
'''
    sym1 = extract_symbols_from_source(src1)[0]
    sym2 = extract_symbols_from_source(src2)[0]

    fp1 = generate_fingerprints(sym1)
    fp2 = generate_fingerprints(sym2)

    assert fp1.raise_type == fp2.raise_type, "Exception class name (ValueError) unchanged"
    assert fp1.raise_detail != fp2.raise_detail, "Constraint message changed from 3 to 5"


def test_doctest_example_fingerprint_extraction():
    """Verify that runnable doctests are extracted into EXAMPLE_FINGERPRINT."""
    src = '''def square(x: int) -> int:
    """Square a number.

    Example:
        >>> square(4)
        16
    """
    return x * x
'''
    sym = extract_symbols_from_source(src)[0]
    fp = generate_fingerprints(sym)
    assert fp.example is not None

    src_no_ex = '''def square(x: int) -> int:
    """Square a number."""
    return x * x
'''
    sym_no_ex = extract_symbols_from_source(src_no_ex)[0]
    fp_no_ex = generate_fingerprints(sym_no_ex)
    assert fp_no_ex.example is None
