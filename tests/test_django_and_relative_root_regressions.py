"""Mandatory Regression Tests for Django Migrations, Relative Roots, and Zero-File Safety.

WHAT IS THIS?
-------------
Tests verifying the critical bug fixes reported during Django adoption:
1. Django migration files (e.g. 0001_initial.py, 0002_add_field.py) with undocumented
   `class Migration:` must not trigger `RULE_UNLINKED_DOCUMENTATION`.
2. Scanning with relative roots (e.g. `--root ..` from an inner directory) must
   accurately discover files and detect drift, never silently passing with exit 0.
3. Scanning an empty directory or directory with zero Python files must fail with
   exit code 2 and a clear error message, preventing silent false passes.
4. Traversal pruning must skip ignored directories in-place without recursing into them.
"""

import subprocess
import sys
from pathlib import Path

import pytest
from pydocsync.discovery import DEFAULT_IGNORED_DIRS, discover_python_files


def run_pydocsync_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Execute pydocsync CLI in a subprocess with the test virtualenv."""
    cmd = [sys.executable, "-m", "pydocsync.cli"] + args
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def test_django_migrations_are_ignored_by_default(tmp_path: Path):
    """Repro 1: Verify adding a new Django migration class does not trigger doc check failure."""
    proj = tmp_path / "django_proj"
    app_dir = proj / "app"
    migrations_dir = app_dir / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)

    # Valid documented business logic file
    (app_dir / "models.py").write_text(
        '''"""App models."""

def get_app_name() -> str:
    """Return application name."""
    return "demo_app"
''',
        encoding="utf-8",
    )

    # Initial migration (undocumented class)
    (migrations_dir / "0001_initial.py").write_text(
        '''class Migration:
    operations = []
''',
        encoding="utf-8",
    )

    # Step 1: Initialize baseline
    init_res = run_pydocsync_cli(["init", "--root", str(proj)], cwd=tmp_path)
    assert init_res.returncode == 0
    assert "Initialized baseline for 1 compliant symbols" in init_res.stdout

    # Step 2: Check passes initially
    check_res1 = run_pydocsync_cli(["check", "--root", str(proj)], cwd=tmp_path)
    assert check_res1.returncode == 0
    assert "All symbols synchronized with baseline" in check_res1.stdout

    # Step 3: Add second migration (undocumented class)
    (migrations_dir / "0002_add_field.py").write_text(
        '''class Migration:
    operations = ["add_field"]
''',
        encoding="utf-8",
    )

    # Step 4: Check MUST still pass cleanly without RULE_UNLINKED_DOCUMENTATION failure
    check_res2 = run_pydocsync_cli(["check", "--root", str(proj)], cwd=tmp_path)
    assert check_res2.returncode == 0, f"Migrations should be excluded but check failed: {check_res2.stderr}"
    assert "All symbols synchronized with baseline" in check_res2.stdout


def test_relative_root_parent_directory_detects_drift(tmp_path: Path):
    """Repro 2: Verify `check --root ..` from inside a subfolder accurately detects code drift."""
    proj = tmp_path / "my_project"
    app_dir = proj / "core"
    app_dir.mkdir(parents=True, exist_ok=True)

    module_file = app_dir / "service.py"
    module_file.write_text(
        '''"""Service module."""

def calculate_fee(amount: float) -> float:
    """Calculate the service fee."""
    return amount * 0.05
''',
        encoding="utf-8",
    )

    # Initialize baseline from project root
    init_res = run_pydocsync_cli(["init", "--root", "."], cwd=proj)
    assert init_res.returncode == 0

    # Mutate implementation (code drift, doc untouched)
    module_file.write_text(
        '''"""Service module."""

def calculate_fee(amount: float) -> float:
    """Calculate the service fee."""
    base_fee = 1.0
    return base_fee + (amount * 0.05)
''',
        encoding="utf-8",
    )

    # Check from INSIDE project/core using --root ..
    check_res = run_pydocsync_cli(["check", "--root", ".."], cwd=app_dir)

    # MUST NOT falsely pass with exit 0! Must catch drift and exit 1
    assert check_res.returncode == 1, (
        f"Expected exit code 1 for drift under relative root, got {check_res.returncode}. "
        f"Stdout: {check_res.stdout}, Stderr: {check_res.stderr}"
    )
    assert "PYDOCSYNC001" in check_res.stderr
    assert "calculate_fee" in check_res.stderr
    assert "RULE_BASELINE_CODE_DRIFT" in check_res.stderr


def test_zero_python_files_raises_error_and_exits_nonzero(tmp_path: Path):
    """Zero-file safety: Verify that scanning an empty tree produces error code 2."""
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()

    # Check on empty folder
    check_res = run_pydocsync_cli(["check", "--root", str(empty_dir)], cwd=tmp_path)
    assert check_res.returncode == 2
    assert "PYDOCSYNC ERROR: No Python source files found" in check_res.stderr

    # Init on empty folder
    init_res = run_pydocsync_cli(["init", "--root", str(empty_dir)], cwd=tmp_path)
    assert init_res.returncode == 2
    assert "PYDOCSYNC ERROR: No Python source files found" in init_res.stderr


def test_discovery_pruning_performance_and_defaults(tmp_path: Path):
    """Verify that in-place pruning skips large ignored directories during traversal."""
    proj = tmp_path / "fast_proj"
    proj.mkdir()

    # Create root level file
    (proj / "main.py").write_text("def run(): pass\n", encoding="utf-8")

    # Create dummy .venv with 500 subdirectories and files
    venv_dir = proj / ".venv"
    for i in range(20):
        sub = venv_dir / f"pkg_{i}"
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"mod_{i}.py").write_text("x = 1\n", encoding="utf-8")

    # Create dummy migrations and tests folders
    (proj / "migrations").mkdir()
    (proj / "migrations" / "0001.py").write_text("x = 1\n", encoding="utf-8")
    (proj / "tests").mkdir()
    (proj / "tests" / "test_foo.py").write_text("x = 1\n", encoding="utf-8")

    # Discover files
    found = discover_python_files(proj)

    # Should ONLY find main.py; .venv, migrations, tests must be completely pruned
    assert found == [Path("main.py")]
    assert "migrations" in DEFAULT_IGNORED_DIRS
    assert "Spashta_2.0" not in DEFAULT_IGNORED_DIRS
    assert "Spashta_2.1" not in DEFAULT_IGNORED_DIRS
