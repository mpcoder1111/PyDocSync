"""Layer 4: AI Agent Workflow Tests.

WHAT IS THIS?
-------------
Simulates the complete AI agent lifecycle:
1. AI Agent modifies a function (adding an exception constraint).
2. Pytest guard triggers PYDOCSYNC001 failure with actionable instructions.
3. AI Agent reviews and runs `pydocsync accept --symbol ... --reason "..."`.
4. Pytest guard re-runs and reaches 100% green state.
"""

from pathlib import Path
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.baseline import BaselineManager
from pydocsync.cli import accept_symbol_review, scan_and_check
from pydocsync.fingerprint import generate_fingerprints


def test_ai_agent_self_correction_workflow(tmp_path: Path):
    """Simulate end-to-end AI agent detection, failure report, CLI accept, and test resolution."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    mod_file = pkg_dir / "service.py"

    # Step 1: Initial synchronized state
    initial_code = '''def process_item(item_id: str) -> bool:
    """Process item by ID."""
    return len(item_id) > 0
'''
    mod_file.write_text(initial_code, encoding="utf-8")

    mgr = BaselineManager(root_dir=tmp_path)
    sym = extract_symbols_from_source(initial_code)[0]
    fp = generate_fingerprints(sym)
    mgr.record_symbol_baseline("pkg/service.py", sym, fp)

    # Initial scan should be 100% clean
    assert scan_and_check(root_dir=tmp_path) == []

    # Step 2: AI Agent modifies code (alters internal threshold constant) without updating doc
    drifted_code = '''def process_item(item_id: str) -> bool:
    """Process item by ID."""
    max_len = 50
    return len(item_id) <= max_len
'''
    mod_file.write_text(drifted_code, encoding="utf-8")

    # Step 3: Pytest guard detects drift and emits PYDOCSYNC001 failure
    failures = scan_and_check(root_dir=tmp_path)
    assert len(failures) == 1
    assert failures[0].symbol.qualname == "process_item"

    # Step 4: AI Agent verifies doc is still accurate and executes CLI accept
    audit_reason = "Internal buffer optimization; external item processing contract unchanged"
    accepted = accept_symbol_review("process_item", reason=audit_reason, root_dir=tmp_path)
    assert accepted is True

    # Step 5: Guard re-runs and passes with updated baseline
    resolved_failures = scan_and_check(root_dir=tmp_path)
    assert resolved_failures == []

    # Step 6: Verify metadata recorded the audit reason
    baseline = mgr.load_module_baseline("pkg/service.py")
    assert baseline["process_item"].status == "acknowledged"
    assert baseline["process_item"].review_reason == audit_reason
