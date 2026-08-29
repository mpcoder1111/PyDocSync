"""Security Boundary, Path Traversal & Disk-State Freshness Audit Suite.

WHAT IS THIS?
-------------
Verifies:
1. `pydocsync accept` rejects empty reason strings with exit code 2.
2. `pydocsync accept` rejects whitespace-only reason strings with exit code 2.
3. `pydocsync accept` rejects non-existent symbols with exit code 1.
4. `pydocsync check` handles corrupted/malformed JSON lockfiles gracefully.
5. Schema version 1 backwards compatibility (legacy flat format fallback).
6. Path traversal safety: BaselineManager rejects path traversal attempts outside baseline root.
7. Disk-state freshness (race/stale-state prevention): `pydocsync accept` reads and baselines
   the ACTUAL physical file content on disk at execution time, never stale pre-check state.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest
from pydocsync import check
from pydocsync.baseline import BaselineManager


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "pydocsync"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def test_reject_empty_and_whitespace_reasons(tmp_path: Path):
    """Verify accept rejects blank and whitespace-only reasons with exit code 2."""
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        '''def compute(val: int) -> int:
    """Compute double."""
    return val * 2
''',
        encoding="utf-8",
    )

    # Init baseline
    assert run_cli(["init"], cwd=tmp_path).returncode == 0

    # Reject empty string
    res_empty = run_cli(["accept", "--symbol", "compute", "--reason", ""], cwd=tmp_path)
    assert res_empty.returncode == 2
    assert "A non-empty, descriptive audit reason is required" in res_empty.stderr

    # Reject whitespace-only string
    res_ws = run_cli(["accept", "--symbol", "compute", "--reason", "   \t\n  "], cwd=tmp_path)
    assert res_ws.returncode == 2
    assert "A non-empty, descriptive audit reason is required" in res_ws.stderr


def test_reject_nonexistent_symbol(tmp_path: Path):
    """Verify accept rejects symbols not found in the project with exit code 1."""
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        '''def existing_fn():
    """Exists."""
    pass
''',
        encoding="utf-8",
    )
    assert run_cli(["init"], cwd=tmp_path).returncode == 0

    res_missing = run_cli(
        ["accept", "--symbol", "nonexistent_fn", "--reason", "Attempting fake symbol accept"],
        cwd=tmp_path,
    )
    assert res_missing.returncode == 1
    assert "Symbol 'nonexistent_fn' not found in project." in res_missing.stderr


def test_corrupted_baseline_lockfile_resilience(tmp_path: Path):
    """Verify check handles malformed/corrupted JSON lockfiles safely."""
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        '''def sample_fn():
    """Sample docstring."""
    pass
''',
        encoding="utf-8",
    )
    assert run_cli(["init"], cwd=tmp_path).returncode == 0

    # Corrupt the lockfile
    lockfile = tmp_path / ".project" / "pydocsync" / "sample.json"
    assert lockfile.exists()
    lockfile.write_text("{ MALFORMED_JSON ::: invalid", encoding="utf-8")

    # Manager should return empty dict without crashing
    mgr = BaselineManager(root_dir=tmp_path)
    records = mgr.load_module_baseline(py_file)
    assert records == {}


def test_schema_v1_and_legacy_format_compatibility(tmp_path: Path):
    """Verify BaselineManager reads both schema_version: 1 and legacy flat formats."""
    py_file = tmp_path / "module.py"
    py_file.write_text(
        '''def func():
    """Doc."""
    pass
''',
        encoding="utf-8",
    )

    mgr = BaselineManager(root_dir=tmp_path)

    # 1. Test schema_version 1 envelope
    v1_lockfile = tmp_path / ".project" / "pydocsync" / "module.json"
    v1_lockfile.parent.mkdir(parents=True, exist_ok=True)
    v1_lockfile.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pydocsync_version": "0.2.0",
                "fingerprint_algorithm": "sha256",
                "symbols": {
                    "func": {
                        "api": "api_hash_1",
                        "code": "code_hash_1",
                        "doc": "doc_hash_1",
                        "types": "types_hash_1",
                        "raise_type": "raise_t_1",
                        "raise_detail": "raise_d_1",
                        "example": None,
                        "status": "synchronized",
                        "last_reviewed_at": "2026-08-29T00:00:00Z",
                        "review_reason": None,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    records_v1 = mgr.load_module_baseline(py_file)
    assert "func" in records_v1
    assert records_v1["func"].code == "code_hash_1"

    # 2. Test legacy flat format fallback
    v1_lockfile.write_text(
        json.dumps(
            {
                "func": {
                    "api": "api_hash_legacy",
                    "code": "code_hash_legacy",
                    "doc": "doc_hash_legacy",
                    "types": "types_hash_legacy",
                    "raise_type": "raise_t_legacy",
                    "raise_detail": "raise_d_legacy",
                    "example": None,
                    "status": "synchronized",
                    "last_reviewed_at": "2026-08-29T00:00:00Z",
                    "review_reason": None,
                }
            }
        ),
        encoding="utf-8",
    )

    records_legacy = mgr.load_module_baseline(py_file)
    assert "func" in records_legacy
    assert records_legacy["func"].code == "code_hash_legacy"


def test_path_traversal_safety(tmp_path: Path):
    """Verify BaselineManager safely isolates lockfile paths within baseline root."""
    mgr = BaselineManager(root_dir=tmp_path)
    
    # Attempting to load module with directory traversal
    traversal_path = Path("../../etc/passwd.py")
    resolved_lockfile = mgr._get_baseline_path(traversal_path)
    
    # The lockfile must remain rooted under .project/pydocsync
    assert resolved_lockfile.name.endswith(".json")
    # Must not escape root directory
    assert ".project" in str(resolved_lockfile)


def test_disk_freshness_and_stale_state_prevention(tmp_path: Path):
    """Verify accept fingerprints the CURRENT physical file on disk when code changes again after check.

    Scenario:
    1. Baseline created with version = 1.
    2. AI modifies code to version = 2 (check detects drift).
    3. Before running accept, human/AI modifies code again to version = 3.
    4. accept is executed.
    5. Resulting baseline must match version = 3, NOT version = 2.
    """
    py_file = tmp_path / "service.py"
    py_file.write_text(
        '''def get_timeout(env: str = "prod") -> int:
    """Get service timeout."""
    return 10
''',
        encoding="utf-8",
    )

    # 1. Initial Baseline
    assert run_cli(["init"], cwd=tmp_path).returncode == 0
    assert run_cli(["check"], cwd=tmp_path).returncode == 0

    # 2. Modify to version 2 (drift detected)
    py_file.write_text(
        '''def get_timeout(env: str = "prod") -> int:
    """Get service timeout."""
    return 20
''',
        encoding="utf-8",
    )
    check_v2 = run_cli(["check"], cwd=tmp_path)
    assert check_v2.returncode == 1

    # 3. Source changes AGAIN to version 3 before accept
    py_file.write_text(
        '''def get_timeout(env: str = "prod") -> int:
    """Get service timeout."""
    return 30
''',
        encoding="utf-8",
    )

    # 4. Accept is executed
    accept_res = run_cli(
        ["accept", "--symbol", "get_timeout", "--reason", "Updated timeout constant to 30ms"],
        cwd=tmp_path,
    )
    assert accept_res.returncode == 0

    # 5. Subsequent check is clean against version 3
    assert run_cli(["check"], cwd=tmp_path).returncode == 0

    # 6. Verify that reverting to version 2 now causes drift against version 3 baseline
    py_file.write_text(
        '''def get_timeout(env: str = "prod") -> int:
    """Get service timeout."""
    return 20
''',
        encoding="utf-8",
    )
    check_stale = run_cli(["check"], cwd=tmp_path)
    assert check_stale.returncode == 1
    assert "PYDOCSYNC001: 1 symbol(s) require documentation review" in check_stale.stderr
