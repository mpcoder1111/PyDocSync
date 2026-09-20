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
    expected_exports = {
        "__version__",
        "check",
        "init",
        "init_report",
        "accept",
        "refresh",
        "SyncResult",
        "SyncFailure",
        # Added by specs 009/010 (structured results, typed errors, config/exclusion errors):
        "Problem",
        "ProblemKind",
        "StaleRecord",
        "InitResult",
        "SymbolRef",
        "PyDocSyncError",
        "AmbiguousSymbolError",
        "ConfigError",
        "FileExcludedError",
        "InitIncompleteError",
        "InvalidArgumentError",
        "SourceProblemsError",
    }
    assert set(pydocsync.__all__) == expected_exports
    assert pydocsync.__version__ == "0.4.0"
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


def test_cli_help_shows_every_command_with_usage_guidance():
    """The CLI help lists all commands and says how to use them (workflow, examples, exit codes)."""
    top = subprocess.run([sys.executable, "-m", "pydocsync", "--help"], capture_output=True, text=True)
    assert top.returncode == 0
    assert top.stdout.startswith("usage: pydocsync ")
    for command in ("check", "init", "accept", "refresh"):
        assert command in top.stdout
    for guidance in ("typical workflow", "exit codes", ".pydocsync.json", 'pydocsync accept --symbol'):
        assert guidance in top.stdout

    examples = {
        "check": "pydocsync check --fail-on-stale --require-baseline",
        "init": "pydocsync init --dry-run",
        "accept": "--file app/commands.py",
        "refresh": "pydocsync refresh --reason",
    }
    for command, example in examples.items():
        sub = subprocess.run([sys.executable, "-m", "pydocsync", command, "--help"], capture_output=True, text=True)
        assert sub.returncode == 0
        assert sub.stdout.startswith(f"usage: pydocsync {command}")
        assert "examples:" in sub.stdout and example in sub.stdout, command


def test_cli_version_flag_reports_the_package_version():
    """`pydocsync --version` prints the installed version."""
    res = subprocess.run([sys.executable, "-m", "pydocsync", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == f"pydocsync {pydocsync.__version__}"
