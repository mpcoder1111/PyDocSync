"""Layer 3: Integration tests for distributed baseline management and gated creation."""

from pathlib import Path
import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.baseline import BaselineManager
from pydocsync.fingerprint import generate_fingerprints


def test_baseline_save_and_load(tmp_path: Path):
    """Verify that symbol baselines are saved into modular JSON lockfiles and correctly reloaded."""
    src = '''def parse_page(path: str) -> dict:
    """Parse a page into structured dict."""
    return {"path": path}
'''
    sym = extract_symbols_from_source(src)[0]
    fp = generate_fingerprints(sym)

    mgr = BaselineManager(root_dir=tmp_path)
    module_rel = "logseq_toolkit/parser.py"

    # Record baseline
    rec = mgr.record_symbol_baseline(module_rel, sym, fp)
    assert rec.status == "synchronized"

    # Reload from disk
    loaded = mgr.load_module_baseline(module_rel)
    assert "parse_page" in loaded
    assert loaded["parse_page"].code == fp.code
    assert loaded["parse_page"].api == fp.api

    # Verify path was modular
    expected_json = tmp_path / ".project" / "pydocsync" / "logseq_toolkit" / "parser.json"
    assert expected_json.exists(), f"Expected JSON at {expected_json}"


def test_gated_baseline_creation_blocks_missing_doc(tmp_path: Path):
    """Verify that public symbols without docstrings cannot establish a baseline."""
    src = '''def undocumented_func(x: int) -> int:
    return x * 2
'''
    sym = extract_symbols_from_source(src)[0]
    fp = generate_fingerprints(sym)

    mgr = BaselineManager(root_dir=tmp_path)
    module_rel = "pkg/mod.py"

    with pytest.raises(ValueError, match="Gating violation"):
        mgr.record_symbol_baseline(module_rel, sym, fp, enforce_gating=True)
