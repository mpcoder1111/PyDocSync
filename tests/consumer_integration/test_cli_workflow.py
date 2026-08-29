"""End-to-End CLI Workflow Test for External Consumer Projects.

WHAT IS THIS?
-------------
Tests PyDocSync CLI execution exclusively via subprocess (simulating an external developer
or AI coding agent running pydocsync from command line):
1. `pydocsync init` -> Generates baseline lockfiles.
2. `pydocsync check` -> Clean pass (exit code 0).
3. Simulate AI code drift -> `pydocsync check` fails with `PYDOCSYNC001` (exit code 1).
4. `pydocsync accept` -> Acknowledges with audit reason -> `pydocsync check` passes (exit code 0).
5. Argument validation -> Missing args returns exit code 2.
"""

import subprocess
import sys
from pathlib import Path
from .consumer_fixtures import create_cli_app_project, create_data_pipeline_project


def run_pydocsync_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Execute pydocsync CLI via python -m pydocsync in specified cwd."""
    cmd = [sys.executable, "-m", "pydocsync"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def test_cli_app_lifecycle_workflow(tmp_path: Path):
    """Verify complete AI-agent development lifecycle on isolated CLI app."""
    proj_dir = create_cli_app_project(tmp_path / "cli_consumer")

    # Step 1: Initialize baseline
    init_res = run_pydocsync_cli(["init"], cwd=proj_dir)
    assert init_res.returncode == 0
    assert "Initialized baseline for 2 compliant symbols" in init_res.stdout
    assert (proj_dir / ".project" / "pydocsync").exists()

    # Step 2: Check baseline (clean state)
    check_clean = run_pydocsync_cli(["check"], cwd=proj_dir)
    assert check_clean.returncode == 0
    assert "PYDOCSYNC: All symbols synchronized with baseline." in check_clean.stdout

    # Step 3: Simulate AI modification without doc update (changed default retries 3 -> 5)
    parser_file = proj_dir / "my_cli_app" / "parser.py"
    parser_file.write_text(
        '''"""CLI argument and payload parser."""

def parse_config(raw_path: str, max_retries: int = 5) -> dict:
    """Parse configuration file into structured dictionary.

    Args:
        raw_path: Path to configuration file.
        max_retries: Retry attempts on transient read error (default 3).

    Returns:
        Parsed configuration dictionary.
    """
    return {"path": raw_path, "retries": max_retries}
''',
        encoding="utf-8",
    )

    # Step 4: Check detects violation (exit code 1, PYDOCSYNC001)
    check_drift = run_pydocsync_cli(["check"], cwd=proj_dir)
    assert check_drift.returncode == 1
    assert "PYDOCSYNC001: 1 symbol(s) require documentation review" in check_drift.stderr
    assert "Symbol:     parse_config" in check_drift.stderr
    assert "Impact:     HIGH_IMPACT" in check_drift.stderr
    assert "accept --symbol parse_config --reason" in check_drift.stderr

    # Step 5: Acknowledge with audit reason
    accept_res = run_pydocsync_cli(
        ["accept", "--symbol", "parse_config", "--reason", "Increased default retry count to 5 for unstable networks"],
        cwd=proj_dir,
    )
    assert accept_res.returncode == 0
    assert "successfully acknowledged and baseline updated" in accept_res.stdout

    # Step 6: Verify synchronized again (exit code 0)
    check_after_accept = run_pydocsync_cli(["check"], cwd=proj_dir)
    assert check_after_accept.returncode == 0
    assert "PYDOCSYNC: All symbols synchronized with baseline." in check_after_accept.stdout


def test_cli_argument_error_handling(tmp_path: Path):
    """Verify standard exit code 2 when required CLI arguments are missing."""
    proj_dir = create_cli_app_project(tmp_path / "cli_err")

    # Missing --reason on accept
    res = run_pydocsync_cli(["accept", "--symbol", "foo"], cwd=proj_dir)
    assert res.returncode == 2
    assert "the following arguments are required: --reason" in res.stderr
