"""Public API, Typing, and CLI Invocation Verification Suite for PyDocSync.

WHAT IS THIS?
-------------
Verifies:
1. Top-level imports: from pydocsync import check, init, accept, SyncResult, SyncFailure
2. Package versioning: pydocsync.__version__ == "0.2.0"
3. python -m pydocsync invocation
4. Minimal public API encapsulation (internal modules not required for standard usage)
"""

import subprocess
import sys
from pathlib import Path
import pytest
import pydocsync
from pydocsync import SyncFailure, SyncResult, accept, check, init


def test_public_api_exports():
    """Verify that pydocsync exports only the approved public API surface."""
    expected_exports = {"__version__", "check", "init", "accept", "SyncResult", "SyncFailure"}
    assert set(pydocsync.__all__) == expected_exports
    assert pydocsync.__version__ == "0.2.0"
    assert callable(check)
    assert callable(init)
    assert callable(accept)


def test_public_api_check_execution(tmp_path: Path):
    """Verify programmatic check() on a clean repository."""
    sample_file = tmp_path / "sample.py"
    sample_file.write_text(
        '''def add_nums(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
''',
        encoding="utf-8",
    )

    # Initialize baseline
    init_count = init(root_dir=tmp_path)
    assert init_count == 1

    # Check baseline
    res = check(root_dir=tmp_path)
    assert isinstance(res, SyncResult)
    assert res.is_synchronized is True
    assert res.failure_count == 0
    assert len(res.failures) == 0


def test_python_module_cli_invocation():
    """Verify python -m pydocsync invocation with --help."""
    result = subprocess.run(
        [sys.executable, "-m", "pydocsync", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[2],
    )
    assert result.returncode == 0
    assert "PyDocSync: Representation Synchronization CLI" in result.stdout
    assert "check" in result.stdout
    assert "init" in result.stdout
    assert "accept" in result.stdout
