"""Regression suite for spec 009: silent "All symbols synchronized" false passes.

WHAT IS THIS?
-------------
Executable form of the spec 009 regression matrix (`specs/009-silent-false-pass-hardening/spec.md`):
1. Corrupt / unreadable / unsupported baseline lockfiles fail `check` (exit 2), never pass.
2. Unparseable source files are reported instead of skipped (exit 2, all problems in one run).
3. `pydocsync accept` refuses ambiguous symbol names and supports `--file`.
4. `pydocsync init` protects records that `check` flags, supports `--force --reason` and `--dry-run`.
5. Same qualified name defined more than once in one file is tracked per definition.
6. Stale baselines (documentation updated, baseline not refreshed) are reported and refreshable.
7. Exception hierarchy, exit-code mapping and coverage output.

WHY DO WE NEED THIS?
--------------------
Each test reproduces a scenario a real user hit on v0.3.0, where PyDocSync printed
"All symbols synchronized" (exit 0) although it could not, or did not, evaluate the code.
Every substantive test here MUST fail on v0.3.0 and pass on 0.4.0 (spec FR-011).
New public names are imported inside the tests so that each test fails individually on v0.3.0
instead of the whole module failing at collection.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GOOD_SRC = '''def f(t=30):
    """Uses timeout 30."""
    return t
'''

DRIFTED_SRC = '''def f(t=60):
    """Uses timeout 30."""
    return t
'''

STALE_NOTICE = "have updated documentation not yet recorded in the baseline"


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run `python -m pydocsync <args>` in cwd, capturing text output."""
    return subprocess.run([sys.executable, "-m", "pydocsync", *args], capture_output=True, text=True, cwd=cwd)


def write(root: Path, rel: str, text: str) -> Path:
    """Write a UTF-8 file under root, creating parent directories."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def lockfile(root: Path, rel_py: str) -> Path:
    """Return the baseline lockfile path for a module path such as 'pkg/a.py'."""
    return root / ".project" / "pydocsync" / Path(rel_py).with_suffix(".json")


def init_ok(root: Path) -> None:
    """Run `init` and assert it succeeded cleanly."""
    res = run_cli(["init"], cwd=root)
    assert res.returncode == 0, res.stderr + res.stdout


def combined(res: subprocess.CompletedProcess[str]) -> str:
    """Join stdout and stderr for text assertions."""
    return res.stdout + "\n" + res.stderr


# --------------------------------------------------------------------------- US1: corrupt baselines


def _valid_lockfile_json(root: Path) -> dict:
    return json.loads(lockfile(root, "m.py").read_text(encoding="utf-8"))


def _mutations() -> dict[str, object]:
    return {
        "invalid_json": "{ not json",
        "empty_file": "",
        "list_root": "[]",
        "record_missing_field": {"schema_version": 1, "symbols": {"f": {"code": "x"}}},
        "newer_schema": {"schema_version": 99, "symbols": {}},
    }


@pytest.mark.parametrize("kind", list(_mutations()))
def test_corrupt_baseline_makes_check_fail(tmp_path: Path, kind: str):
    """A damaged lockfile must not be treated as 'no baseline' (exit 2, file named)."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    payload = _mutations()[kind]
    lockfile(tmp_path, "m.py").write_text(
        payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8"
    )

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "All symbols synchronized" not in res.stdout
    assert "PYDOCSYNC ERROR" in res.stderr
    assert "m.json" in res.stderr
    assert "Traceback" not in res.stderr


def test_record_with_unknown_field_is_a_problem(tmp_path: Path):
    """A record carrying an unexpected field is structurally invalid."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    data = _valid_lockfile_json(tmp_path)
    data["symbols"]["f"]["bogus"] = 1
    lockfile(tmp_path, "m.py").write_text(json.dumps(data), encoding="utf-8")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "m.json" in res.stderr


def test_all_corrupt_lockfiles_reported_sorted(tmp_path: Path):
    """Several corrupt lockfiles are all reported in one run, sorted by path."""
    write(tmp_path, "b.py", GOOD_SRC)
    write(tmp_path, "a.py", GOOD_SRC)
    init_ok(tmp_path)
    lockfile(tmp_path, "a.py").write_text("{ not json", encoding="utf-8")
    lockfile(tmp_path, "b.py").write_text("{ not json", encoding="utf-8")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2
    assert "a.json" in res.stderr and "b.json" in res.stderr
    assert res.stderr.index("a.json") < res.stderr.index("b.json")


def test_missing_lockfile_is_not_a_problem(tmp_path: Path):
    """Absent is not corrupt: a never-baselined documented module still passes."""
    write(tmp_path, "m.py", GOOD_SRC)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)


def test_api_reports_baseline_problem_as_data(tmp_path: Path):
    """check() returns the problem in SyncResult.problems and is not synchronized."""
    from pydocsync import ProblemKind, check

    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    lockfile(tmp_path, "m.py").write_text("{ not json", encoding="utf-8")

    result = check(root_dir=tmp_path)

    assert result.is_synchronized is False
    assert len(result.problems) == 1
    assert result.problems[0].kind == ProblemKind.BASELINE_CORRUPT
    assert result.problems[0].path.endswith("m.json")


def test_legacy_lockfile_without_envelope_still_loads(tmp_path: Path):
    """Pre-envelope (legacy flat) lockfiles stay valid (spec 007 compatibility)."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    data = _valid_lockfile_json(tmp_path)
    lockfile(tmp_path, "m.py").write_text(json.dumps(data["symbols"]), encoding="utf-8")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)


# --------------------------------------------------------------------------- US2: unparseable sources


def test_only_file_with_syntax_error_fails(tmp_path: Path):
    """A project whose sole file cannot be parsed must not report success."""
    write(tmp_path, "bad.py", "def broken(:\n    pass\n")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "All symbols synchronized" not in res.stdout
    assert "bad.py" in res.stderr
    assert "SyntaxError" in res.stderr


def test_syntax_error_report_names_kind_and_line(tmp_path: Path):
    """The report says 'SyntaxError line N' so interpreter-version mismatches are obvious."""
    write(tmp_path, "bad.py", "x = 1\ndef broken(:\n    pass\n")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2
    assert "SyntaxError line 2" in res.stderr


def test_good_file_beside_broken_file_still_reports_drift_and_problem(tmp_path: Path):
    """Evaluation continues past a broken file: drift AND the problem are both printed, exit 2."""
    write(tmp_path, "good.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "good.py", DRIFTED_SRC)
    write(tmp_path, "broken.py", "def broken(:\n    pass\n")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "PYDOCSYNC001" in res.stderr
    assert "broken.py" in res.stderr


def test_api_good_plus_broken_file_reports_both(tmp_path: Path):
    """check() exposes failures and problems together; never synchronized."""
    from pydocsync import ProblemKind, check

    write(tmp_path, "good.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "good.py", DRIFTED_SRC)
    write(tmp_path, "broken.py", "x = 1\ndef broken(:\n    pass\n")

    result = check(root_dir=tmp_path)

    assert result.is_synchronized is False
    assert result.failure_count >= 1
    assert [p.kind for p in result.problems] == [ProblemKind.SOURCE_UNPARSEABLE]
    assert result.problems[0].path == "broken.py"
    assert result.problems[0].line == 2


def test_undecodable_file_is_reported(tmp_path: Path):
    """A file that is not valid UTF-8 is reported, not skipped."""
    (tmp_path / "bin.py").write_bytes(b"\xff\xfe def x(): pass\n")
    write(tmp_path, "ok.py", GOOD_SRC)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "bin.py" in res.stderr


def test_broken_file_in_ignored_directory_is_never_reported(tmp_path: Path):
    """Excluded directories are never scanned, so their broken files never count."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "tests/bad.py", "def broken(:\n")
    write(tmp_path, "app/migrations/0001_initial.py", "def broken(:\n")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)


DOCSTRING_ONLY_CLASS_SRC = '''class AppError(Exception):
    """Application error."""


def f(t={default}):
    """Uses timeout 30."""
    return t
'''


def test_file_with_docstring_only_class_is_evaluated_not_skipped(tmp_path: Path):
    """A valid file with a docstring-only class (e.g. an exception) must not be skipped or flagged as broken.

    On v0.3.0 the extractor crashed on such a class and the whole file was silently skipped:
    init baselined 0 symbols and drift in the same file was never reported.
    """
    write(tmp_path, "m.py", DOCSTRING_ONLY_CLASS_SRC.format(default=30))

    init = run_cli(["init"], cwd=tmp_path)
    assert init.returncode == 0, combined(init)
    assert "Initialized baseline for 2 compliant symbols" in init.stdout

    write(tmp_path, "m.py", DOCSTRING_ONLY_CLASS_SRC.format(default=99))
    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "Symbol:     f" in res.stderr


def test_init_reports_unparseable_file_and_is_not_complete(tmp_path: Path):
    """init must not claim a complete baseline when a file was skipped."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "broken.py", "def broken(:\n")

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "broken.py" in res.stderr


# --------------------------------------------------------------------------- US3: accept


COMMAND_SRC = '''class Command:
    """Command."""

    def handle(self, x={default}):
        """Handle."""
        return x
'''


def _two_command_files(root: Path) -> None:
    write(root, "pkg/a.py", COMMAND_SRC.format(default=1))
    write(root, "pkg/b.py", COMMAND_SRC.format(default=1))
    init_ok(root)
    write(root, "pkg/a.py", COMMAND_SRC.format(default=2))  # only a.py drifts


def test_accept_ambiguous_name_is_an_error_and_changes_nothing(tmp_path: Path):
    """The same qualified name in two files: exit 2, candidates listed, nothing written."""
    _two_command_files(tmp_path)
    before_a = lockfile(tmp_path, "pkg/a.py").read_bytes()
    before_b = lockfile(tmp_path, "pkg/b.py").read_bytes()

    res = run_cli(["accept", "--symbol", "Command.handle", "--reason", "reviewed"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "pkg/a.py" in res.stderr and "pkg/b.py" in res.stderr
    assert "--file pkg/a.py" in res.stderr and "--file pkg/b.py" in res.stderr
    assert lockfile(tmp_path, "pkg/a.py").read_bytes() == before_a
    assert lockfile(tmp_path, "pkg/b.py").read_bytes() == before_b


def test_accept_with_file_updates_only_that_file(tmp_path: Path):
    """--file selects exactly one candidate; the other baseline is untouched."""
    _two_command_files(tmp_path)
    before_b = lockfile(tmp_path, "pkg/b.py").read_bytes()
    before_a = lockfile(tmp_path, "pkg/a.py").read_bytes()

    res = run_cli(
        ["accept", "--symbol", "Command.handle", "--reason", "default changed on purpose", "--file", "pkg/a.py"],
        cwd=tmp_path,
    )

    assert res.returncode == 0, combined(res)
    assert lockfile(tmp_path, "pkg/a.py").read_bytes() != before_a
    assert lockfile(tmp_path, "pkg/b.py").read_bytes() == before_b


def test_accept_unique_name_without_file_still_works(tmp_path: Path):
    """Backward compatible: a name that exists in exactly one file needs no --file."""
    write(tmp_path, "solo.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "solo.py", DRIFTED_SRC)

    res = run_cli(["accept", "--symbol", "f", "--reason", "reviewed"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert run_cli(["check"], cwd=tmp_path).returncode == 0


def test_accept_not_found_keeps_exit_1(tmp_path: Path):
    """'Not found' is exit 1 (unchanged) — distinct from ambiguity/usage errors (exit 2)."""
    _two_command_files(tmp_path)

    missing = run_cli(["accept", "--symbol", "Nope.nothing", "--reason", "r"], cwd=tmp_path)
    wrong_file = run_cli(
        ["accept", "--symbol", "Command.missing", "--reason", "r", "--file", "pkg/b.py"], cwd=tmp_path
    )

    assert missing.returncode == 1, combined(missing)
    assert wrong_file.returncode == 1, combined(wrong_file)


def test_accept_file_outside_root_is_rejected(tmp_path: Path):
    """A --file path that escapes the project root is rejected (exit 2)."""
    root = tmp_path / "proj"
    write(root, "m.py", GOOD_SRC)
    write(tmp_path, "outside.py", GOOD_SRC)
    init_ok(root)

    res = run_cli(["accept", "--symbol", "f", "--reason", "r", "--file", "../outside.py"], cwd=root)

    assert res.returncode == 2, combined(res)
    assert "outside the project root" in res.stderr.lower()


def test_accept_refuses_when_unparseable_file_and_no_file_given(tmp_path: Path):
    """The broken file might define the same name, so uniqueness is unknown: exit 2."""
    write(tmp_path, "good.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "good.py", DRIFTED_SRC)
    write(tmp_path, "broken.py", "def broken(:\n")
    before = lockfile(tmp_path, "good.py").read_bytes()

    res = run_cli(["accept", "--symbol", "f", "--reason", "r"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "broken.py" in res.stderr
    assert lockfile(tmp_path, "good.py").read_bytes() == before


def test_accept_with_file_does_not_read_other_files(tmp_path: Path):
    """With --file only that file is resolved: an unparseable sibling has no effect."""
    write(tmp_path, "good.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "good.py", DRIFTED_SRC)
    write(tmp_path, "broken.py", "def broken(:\n")

    res = run_cli(["accept", "--symbol", "f", "--reason", "r", "--file", "good.py"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)


def test_failure_report_hint_includes_file(tmp_path: Path):
    """The PYDOCSYNC001 hint always names the file, so it is correct for duplicated names."""
    _two_command_files(tmp_path)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert 'accept --symbol Command.handle --reason "<audit reason>" --file pkg/a.py' in res.stderr


def test_api_accept_ambiguity_raises_typed_error_with_data(tmp_path: Path):
    """API: ambiguity raises AmbiguousSymbolError (a PyDocSyncError, not a ValueError)."""
    from pydocsync import AmbiguousSymbolError, PyDocSyncError, accept

    _two_command_files(tmp_path)

    with pytest.raises(AmbiguousSymbolError) as excinfo:
        accept("Command.handle", "reviewed", root_dir=tmp_path)

    assert isinstance(excinfo.value, PyDocSyncError)
    assert not isinstance(excinfo.value, ValueError)
    assert excinfo.value.exit_code == 2
    assert {c.path for c in excinfo.value.candidates} == {"pkg/a.py", "pkg/b.py"}


# --------------------------------------------------------------------------- US5: duplicates in one file


REDEFINED_SRC = '''def f():
    """First."""
    return {first}


def f():
    """Second."""
    return {second}
'''

BOX_SRC = '''class Box:
    """Box."""

    @property
    def size(self):
        """Get size."""
        return {getter}

    @size.setter
    def size(self, value):
        """Set size."""
        self._size = {setter}
'''

OVERLOAD_SRC = '''from typing import overload


@overload
def g(x: int) -> int: {stub1}
@overload
def g(x: str) -> str: ...
def g(x):
    """Implementation."""
    return x
'''


def test_redefined_function_first_definition_change_is_detected(tmp_path: Path):
    """Changing the FIRST of two same-named definitions must not be a silent pass."""
    write(tmp_path, "m.py", REDEFINED_SRC.format(first=1, second=2))
    init_ok(tmp_path)
    write(tmp_path, "m.py", REDEFINED_SRC.format(first=10, second=2))

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "Symbol:     f" in res.stderr


def test_redefined_function_second_definition_change_is_detected(tmp_path: Path):
    """The later definition is tracked separately and identified as 'definition 2'."""
    write(tmp_path, "m.py", REDEFINED_SRC.format(first=1, second=2))
    init_ok(tmp_path)
    write(tmp_path, "m.py", REDEFINED_SRC.format(first=1, second=20))

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "definition 2" in res.stderr


def test_property_getter_change_reports_the_property_symbol(tmp_path: Path):
    """A getter change is reported for Box.size itself, not only the enclosing class."""
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value"))
    init_ok(tmp_path)
    write(tmp_path, "box.py", BOX_SRC.format(getter=99, setter="value"))

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "Symbol:     Box.size" in res.stderr


def test_property_setter_change_is_detected(tmp_path: Path):
    """A setter change is reported for Box.size (definition 2)."""
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value"))
    init_ok(tmp_path)
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value + 1"))

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "Symbol:     Box.size" in res.stderr


def test_overload_stub_change_is_detected(tmp_path: Path):
    """Changing one @overload stub is detected (each definition has its own record)."""
    write(tmp_path, "ov.py", OVERLOAD_SRC.format(stub1="..."))
    init_ok(tmp_path)
    write(tmp_path, "ov.py", OVERLOAD_SRC.format(stub1="pass"))

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "Symbol:     g" in res.stderr


def test_init_count_matches_stored_records_for_duplicates(tmp_path: Path):
    """init reports 3 symbols for class + getter + setter and stores 3 records (not 2)."""
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value"))

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "Initialized baseline for 3 compliant symbols" in res.stdout
    stored = json.loads(lockfile(tmp_path, "box.py").read_text(encoding="utf-8"))["symbols"]
    assert sorted(stored) == ["Box", "Box.size", "Box.size#2"]


def test_accept_updates_all_definitions_of_a_name_and_reports_count(tmp_path: Path):
    """accept works per name per file, covers every definition, and prints how many."""
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value"))
    init_ok(tmp_path)
    write(tmp_path, "box.py", BOX_SRC.format(getter=99, setter="value + 1"))

    res = run_cli(
        ["accept", "--symbol", "Box.size", "--reason", "reviewed both accessors", "--file", "box.py"],
        cwd=tmp_path,
    )

    assert res.returncode == 0, combined(res)
    assert "2 definitions updated" in res.stdout
    after = run_cli(["check"], cwd=tmp_path)
    assert "Symbol:     Box.size" not in after.stderr


def test_v030_style_baseline_for_duplicates_loads_without_error(tmp_path: Path):
    """A v0.3.0 lockfile (one record per name) is loadable; at most a one-time review is requested."""
    write(tmp_path, "box.py", BOX_SRC.format(getter=1, setter="value"))
    init_ok(tmp_path)
    data = json.loads(lockfile(tmp_path, "box.py").read_text(encoding="utf-8"))
    data["symbols"] = {k: v for k, v in data["symbols"].items() if "#" not in k}
    lockfile(tmp_path, "box.py").write_text(json.dumps(data), encoding="utf-8")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode in (0, 1), combined(res)
    assert "Traceback" not in res.stderr


# --------------------------------------------------------------------------- US4: init protection


def test_init_after_drift_protects_the_record(tmp_path: Path):
    """init must not erase drift: record protected, exit 1, check still fails."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)
    assert run_cli(["check"], cwd=tmp_path).returncode == 1
    before = lockfile(tmp_path, "m.py").read_bytes()

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "protected" in combined(res)
    assert "accept --symbol" in combined(res) and "--force" in combined(res)
    assert lockfile(tmp_path, "m.py").read_bytes() == before
    assert run_cli(["check"], cwd=tmp_path).returncode == 1


def test_init_still_baselines_new_modules_next_to_protected_drift(tmp_path: Path):
    """Onboarding a new module works even while another record is protected."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)
    write(tmp_path, "new.py", '''def added():\n    """Added."""\n    return 1\n''')

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert lockfile(tmp_path, "new.py").exists()


@pytest.mark.parametrize("extra", [[], ["--reason", ""], ["--reason", "   "]])
def test_init_force_requires_a_non_blank_reason(tmp_path: Path, extra: list[str]):
    """--force without a real reason changes nothing and exits 2."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)
    before = lockfile(tmp_path, "m.py").read_bytes()

    res = run_cli(["init", "--force", *extra], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "non-empty" in res.stderr.lower()
    assert lockfile(tmp_path, "m.py").read_bytes() == before


def test_init_force_with_reason_overwrites_and_stores_reason(tmp_path: Path):
    """--force --reason overwrites protected records and stores the reason per record."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)

    res = run_cli(["init", "--force", "--reason", "Deliberate baseline reset after review"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    record = json.loads(lockfile(tmp_path, "m.py").read_text(encoding="utf-8"))["symbols"]["f"]
    assert record["review_reason"] == "Deliberate baseline reset after review"
    assert record["status"] == "acknowledged"
    assert run_cli(["check"], cwd=tmp_path).returncode == 0


def test_init_without_existing_baseline_is_unchanged(tmp_path: Path):
    """No baseline yet: init behaves as before (exit 0, existing message)."""
    write(tmp_path, "m.py", GOOD_SRC)

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "Initialized baseline for 1 compliant symbols" in res.stdout


def test_init_dry_run_writes_nothing_and_returns_real_exit_code(tmp_path: Path):
    """--dry-run previews without touching the tree and reports the exit code the real run would."""
    write(tmp_path, "m.py", GOOD_SRC)

    fresh = run_cli(["init", "--dry-run"], cwd=tmp_path)
    assert fresh.returncode == 0, combined(fresh)
    assert not (tmp_path / ".project").exists()

    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)
    before = lockfile(tmp_path, "m.py").read_bytes()
    drift = run_cli(["init", "--dry-run"], cwd=tmp_path)
    assert drift.returncode == 1, combined(drift)
    assert lockfile(tmp_path, "m.py").read_bytes() == before


def test_api_init_raises_with_data_and_init_report_returns_it(tmp_path: Path):
    """init() raises InitIncompleteError carrying baselined + protected; init_report() returns the same."""
    from pydocsync import InitIncompleteError, PyDocSyncError, init, init_report

    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)
    write(tmp_path, "new.py", '''def added():\n    """Added."""\n    return 1\n''')

    report = init_report(root_dir=tmp_path, dry_run=True)
    assert [s.qualname for s in report.protected] == ["f"]
    assert [s.qualname for s in report.baselined] == ["added"]

    with pytest.raises(InitIncompleteError) as excinfo:
        init(root_dir=tmp_path)

    err = excinfo.value
    assert isinstance(err, PyDocSyncError) and not isinstance(err, ValueError)
    assert err.exit_code == 1
    assert [s.qualname for s in err.result.protected] == ["f"]
    assert [s.qualname for s in err.result.baselined] == ["added"]
    assert lockfile(tmp_path, "new.py").exists()  # new symbols are written before raising


def test_init_leaves_stale_records_untouched(tmp_path: Path):
    """A stale record may hide an unreviewed later change; init must not silently rewrite it."""
    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)
    write(tmp_path, "m.py", '''def f(t=60):\n    """Uses timeout 60."""\n    return t\n''')
    assert run_cli(["check"], cwd=tmp_path).returncode == 0
    before = lockfile(tmp_path, "m.py").read_bytes()

    res = run_cli(["init"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "refresh" in combined(res)
    assert lockfile(tmp_path, "m.py").read_bytes() == before


# --------------------------------------------------------------------------- US6: stale baselines


FEE_V1 = '''def fee(amount):
    """Charge a 5 percent fee."""
    return amount * 0.05
'''
FEE_V2 = '''def fee(amount):
    """Charge an 8 percent fee."""
    return amount * 0.08
'''
FEE_V3 = '''def fee(amount):
    """Charge an 8 percent fee."""
    return amount * 0.50
'''


def test_fee_three_step_reproduction_with_refresh(tmp_path: Path):
    """Step 3 (code-only change) fails once the documented step-2 change was refreshed."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)

    write(tmp_path, "fee.py", FEE_V2)  # step 2: code and doc change together
    step2 = run_cli(["check"], cwd=tmp_path)
    assert step2.returncode == 0, combined(step2)
    assert STALE_NOTICE in step2.stdout

    refresh = run_cli(["refresh", "--reason", "Fee raised to 8 percent, docs updated"], cwd=tmp_path)
    assert refresh.returncode == 0, combined(refresh)
    assert STALE_NOTICE not in run_cli(["check"], cwd=tmp_path).stdout

    write(tmp_path, "fee.py", FEE_V3)  # step 3: code only
    step3 = run_cli(["check"], cwd=tmp_path)
    assert step3.returncode == 1, combined(step3)
    assert "PYDOCSYNC001" in step3.stderr


def test_without_refresh_the_stale_notice_is_visible_on_every_check(tmp_path: Path):
    """The residual window is made visible: notice at step 2 and again at step 3."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "fee.py", FEE_V2)
    assert STALE_NOTICE in run_cli(["check"], cwd=tmp_path).stdout

    write(tmp_path, "fee.py", FEE_V3)
    step3 = run_cli(["check"], cwd=tmp_path)

    assert step3.returncode == 0, combined(step3)  # documented limit: not distinguishable without refresh
    assert STALE_NOTICE in step3.stdout


def test_fail_on_stale_exits_1(tmp_path: Path):
    """--fail-on-stale lets CI enforce a refreshed baseline."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "fee.py", FEE_V2)

    res = run_cli(["check", "--fail-on-stale"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    assert "PYDOCSYNC003" in combined(res)
    assert "refresh" in combined(res)


def test_docstring_only_edit_is_stale_and_refreshable(tmp_path: Path):
    """A doc-only edit is also reported as stale and can be refreshed."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "fee.py", FEE_V1.replace("5 percent", "five percent"))

    assert STALE_NOTICE in run_cli(["check"], cwd=tmp_path).stdout
    assert run_cli(["refresh", "--reason", "Wording only"], cwd=tmp_path).returncode == 0
    assert STALE_NOTICE not in run_cli(["check"], cwd=tmp_path).stdout


def test_refresh_never_touches_flagged_or_new_records(tmp_path: Path):
    """refresh re-records only stale symbols; flagged drift and unbaselined symbols are left alone."""
    write(tmp_path, "m.py", GOOD_SRC)
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "m.py", DRIFTED_SRC)  # flagged (code drift, doc unchanged)
    write(tmp_path, "fee.py", FEE_V2)  # stale
    write(tmp_path, "new.py", '''def added():\n    """Added."""\n    return 1\n''')
    flagged_before = lockfile(tmp_path, "m.py").read_bytes()

    res = run_cli(["refresh", "--reason", "docs updated"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert lockfile(tmp_path, "m.py").read_bytes() == flagged_before
    assert not lockfile(tmp_path, "new.py").exists()
    check = run_cli(["check"], cwd=tmp_path)
    assert check.returncode == 1
    assert "Symbol:     f" in check.stderr
    assert STALE_NOTICE not in check.stdout


@pytest.mark.parametrize("args", [["refresh"], ["refresh", "--reason", ""], ["refresh", "--reason", "  "]])
def test_refresh_requires_a_non_blank_reason(tmp_path: Path, args: list[str]):
    """Missing or blank reason: nothing changes, exit 2."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "fee.py", FEE_V2)
    before = lockfile(tmp_path, "fee.py").read_bytes()

    res = run_cli(args, cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "non-empty" in res.stderr.lower()
    assert lockfile(tmp_path, "fee.py").read_bytes() == before


def test_refresh_with_nothing_stale_is_a_noop(tmp_path: Path):
    """Nothing stale: exit 0 and no rewrite."""
    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    before = lockfile(tmp_path, "fee.py").read_bytes()

    res = run_cli(["refresh", "--reason", "nothing to do"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert lockfile(tmp_path, "fee.py").read_bytes() == before


def test_refresh_can_be_narrowed_by_file_and_symbol(tmp_path: Path):
    """--file and --symbol restrict which stale records are refreshed."""
    write(tmp_path, "a.py", FEE_V1)
    write(tmp_path, "b.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "a.py", FEE_V2)
    write(tmp_path, "b.py", FEE_V2)

    assert run_cli(["refresh", "--reason", "a only", "--file", "a.py"], cwd=tmp_path).returncode == 0
    check = run_cli(["check"], cwd=tmp_path)
    assert "b.py" in check.stdout and "a.py" not in check.stdout

    assert run_cli(["refresh", "--reason", "b by symbol", "--symbol", "fee", "--file", "b.py"], cwd=tmp_path).returncode == 0
    assert STALE_NOTICE not in run_cli(["check"], cwd=tmp_path).stdout


def test_api_stale_and_refresh(tmp_path: Path):
    """SyncResult.stale lists stale symbols; refresh() returns the number re-recorded."""
    from pydocsync import check, refresh

    write(tmp_path, "fee.py", FEE_V1)
    init_ok(tmp_path)
    write(tmp_path, "fee.py", FEE_V2)

    result = check(root_dir=tmp_path)
    assert result.is_synchronized is True
    assert [(s.file, s.qualname) for s in result.stale] == [("fee.py", "fee")]

    assert refresh(root_dir=tmp_path, reason="docs updated") == 1
    assert check(root_dir=tmp_path).stale == []


# --------------------------------------------------------------------------- foundations


def test_exception_hierarchy_is_not_a_value_error():
    """One base with an exit code; new errors must not be swallowed by a ValueError handler."""
    from pydocsync import AmbiguousSymbolError, InitIncompleteError, PyDocSyncError, SourceProblemsError
    from pydocsync.discovery import NoSourceFilesError

    assert issubclass(PyDocSyncError, Exception) and not issubclass(PyDocSyncError, ValueError)
    for cls in (AmbiguousSymbolError, InitIncompleteError, SourceProblemsError):
        assert issubclass(cls, PyDocSyncError)
        assert not issubclass(cls, ValueError)
    assert AmbiguousSymbolError.exit_code == 2
    assert SourceProblemsError.exit_code == 2
    # Zero-files keeps the ValueError contract documented by spec 008.
    assert issubclass(NoSourceFilesError, PyDocSyncError) and issubclass(NoSourceFilesError, ValueError)


def test_stray_value_error_is_not_reported_as_exit_2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A ValueError from a bug must surface, not masquerade as a tidy 'exit 2' (item 10)."""
    import pydocsync.cli as cli

    write(tmp_path, "m.py", GOOD_SRC)

    def boom(*_args: object, **_kwargs: object) -> None:
        raise ValueError("internal bug")

    monkeypatch.setattr(cli, "run_check", boom)
    monkeypatch.setattr(sys, "argv", ["pydocsync", "check", "--root", str(tmp_path)])

    with pytest.raises(ValueError, match="internal bug"):
        cli.main()


def test_successful_check_states_coverage(tmp_path: Path):
    """A clean check says what it covered, so scanning nothing is visible at a glance."""
    from pydocsync import check

    write(tmp_path, "m.py", GOOD_SRC)
    init_ok(tmp_path)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "All symbols synchronized with baseline." in res.stdout
    assert "checked 1 files, 1 symbols" in res.stdout
    result = check(root_dir=tmp_path)
    assert (result.files_checked, result.symbols_checked) == (1, 1)
