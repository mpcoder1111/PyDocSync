"""Regression suite for spec 010: exclusion rules, config file, safer default ignores, --require-baseline.

WHAT IS THIS?
-------------
Executable form of the spec 010 regression matrix (`specs/010-exclude-and-require-baseline/spec.md`):
1. Pattern syntax (strict gitignore-style subset): valid forms, invalid forms, and a cross-check of the
   regex matcher against an independent segment-wise reference matcher.
2. `--exclude` on check/init/accept/refresh, and visibility of what the rules did.
3. `<root>/.pydocsync.json` (exclude / default_excludes / require_baseline) and its strict validation.
4. Default ignores (`node_modules`, `site-packages`) and `--no-default-excludes`.
5. `check --require-baseline`.
6. `.pre-commit-hooks.yaml`.

WHY DO WE NEED THIS?
--------------------
Since spec 009 an unparseable file exits 2, so files that only look like Python (templates, generated
code) need an escape hatch, and every exclusion reduces what PyDocSync checks, so it must be visible and
strictly validated. Every substantive test here MUST fail on the committed spec-009 code (FR-016).
New public names are imported inside tests so each test fails individually on the older code.
"""

import fnmatch
import itertools
import json
import subprocess
import sys
from pathlib import Path

import pytest

GOOD_SRC = '''def f(t=30):
    """Uses timeout 30."""
    return t
'''

LEGACY_SRC = '''def legacy_fn(t=30):
    """Legacy timeout 30."""
    return t
'''

UNDOCUMENTED_SRC = "def public_thing(x):\n    return x\n"
BROKEN_TEMPLATE = "{% if user %}\ndef broken(:\n    pass\n"
CONFIG = ".pydocsync.json"


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
    """Return the baseline lockfile path for a module such as 'pkg/a.py'."""
    return root / ".project" / "pydocsync" / Path(rel_py).with_suffix(".json")


def combined(res: subprocess.CompletedProcess[str]) -> str:
    """Join stdout and stderr for text assertions."""
    return res.stdout + "\n" + res.stderr


def init_ok(root: Path, *extra: str) -> None:
    """Run `init` and assert it succeeded cleanly."""
    res = run_cli(["init", *extra], cwd=root)
    assert res.returncode == 0, combined(res)


# --------------------------------------------------------------------------- pattern syntax

# (pattern, path, is_dir, expected)
MATCH_TABLE = [
    ("generated", "generated", True, True),
    ("generated", "a/b/generated", False, True),
    ("generated", "a/generated.py", False, False),
    ("generated", "regenerated", True, False),
    ("templates/", "templates", True, True),
    ("templates/", "app/templates", True, True),
    ("templates/", "templates", False, False),
    ("templates/", "app/templates/x.py", False, False),
    ("pkg/legacy", "pkg/legacy", True, True),
    ("pkg/legacy", "pkg/legacy", False, True),
    ("pkg/legacy", "x/pkg/legacy", True, False),
    ("pkg/legacy", "pkg/legacy/a.py", False, False),
    ("/pkg/legacy", "pkg/legacy", True, True),
    ("/pkg/legacy", "x/pkg/legacy", True, False),
    ("pkg/legacy/", "pkg/legacy", True, True),
    ("pkg/legacy/", "pkg/legacy", False, False),
    ("*_pb2.py", "a/b/x_pb2.py", False, True),
    ("*_pb2.py", "x_pb2.pyc", False, False),
    ("mod?.py", "mod1.py", False, True),
    ("mod?.py", "mod12.py", False, False),
    ("**/tmp", "tmp", True, True),
    ("**/tmp", "a/tmp", True, True),
    ("**/tmp", "a/b/tmp", True, True),
    ("**/tmp", "tmpx", True, False),
    ("pkg/**/gen", "pkg/gen", True, True),
    ("pkg/**/gen", "pkg/a/gen", True, True),
    ("pkg/**/gen", "pkg/a/b/gen", True, True),
    ("pkg/**/gen", "other/gen", True, False),
    ("pkg/**/gen", "pkg/gen2", True, False),
    ("pkg/**", "pkg/x", True, True),
    ("pkg/**", "pkg/x/y.py", False, True),
    ("pkg/**", "pkg", True, False),
    ("**", "anything/at/all.py", False, True),
    ("a/*/c", "a/b/c", True, True),
    ("a/*/c", "a/b/d/c", True, False),
    ("a/*/c", "a/c", True, False),
    ("Build", "build", True, False),
    ("build/", "rebuild", True, False),
]

INVALID_PATTERNS = ["", " x", "x ", "!x", "#x", "a\\b", "[x]", "a**b", "***", "a//b", "..", "../x", "./x", "/"]


@pytest.mark.parametrize("pattern,path,is_dir,expected", MATCH_TABLE)
def test_pattern_matching_table(pattern: str, path: str, is_dir: bool, expected: bool):
    """Every documented pattern form matches exactly what the spec says."""
    from pydocsync.patterns import compile_pattern

    assert compile_pattern(pattern, "--exclude").matches(path, is_dir) is expected


@pytest.mark.parametrize("pattern", INVALID_PATTERNS)
def test_invalid_patterns_are_rejected_with_the_pattern_quoted(pattern: str):
    """Unsupported or ambiguous syntax is an error that quotes the pattern (never silently reinterpreted)."""
    from pydocsync import InvalidArgumentError
    from pydocsync.patterns import compile_pattern

    with pytest.raises(InvalidArgumentError) as excinfo:
        compile_pattern(pattern, "--exclude")

    assert repr(pattern) in str(excinfo.value)
    assert not isinstance(excinfo.value, ValueError)


def _ref_match_segments(pattern_segs: list[str], path_segs: list[str]) -> bool:
    if not pattern_segs:
        return not path_segs
    head = pattern_segs[0]
    if head == "**":
        if len(pattern_segs) == 1:
            return len(path_segs) >= 1
        return any(_ref_match_segments(pattern_segs[1:], path_segs[i:]) for i in range(len(path_segs) + 1))
    if not path_segs:
        return False
    return fnmatch.fnmatchcase(path_segs[0], head) and _ref_match_segments(pattern_segs[1:], path_segs[1:])


def reference_match(pattern: str, path: str, is_dir: bool) -> bool:
    """Independent, regex-free, segment-wise matcher used to cross-check the real one."""
    dir_only = pattern.endswith("/")
    body = pattern[:-1] if dir_only else pattern
    if dir_only and not is_dir:
        return False
    anchored = body.startswith("/") or "/" in body
    body = body.lstrip("/")
    path_segs = path.split("/")
    if not anchored:
        return fnmatch.fnmatchcase(path_segs[-1], body)
    return _ref_match_segments(body.split("/"), path_segs)


def test_regex_matcher_agrees_with_independent_reference_matcher():
    """A generated path set catches translator mistakes the hand-written table would miss."""
    from pydocsync.patterns import compile_pattern

    patterns = sorted({row[0] for row in MATCH_TABLE} | {"pkg/**/**", "a/**/b/*.py", "**/gen/", "x*y", "?", "pkg/*"})
    names = ["a", "b", "pkg", "gen", "tmp", "x_pb2.py", "build", "Build", "c", "legacy"]
    paths = [
        "/".join(combo)
        for depth in range(1, 4)
        for combo in itertools.product(names, repeat=depth)
    ]
    checked = 0
    for pattern in patterns:
        compiled = compile_pattern(pattern, "--exclude")
        for path in paths:
            for is_dir in (True, False):
                assert compiled.matches(path, is_dir) == reference_match(pattern, path, is_dir), (
                    pattern,
                    path,
                    is_dir,
                )
                checked += 1
    assert checked > 10_000


# --------------------------------------------------------------------------- US1: --exclude


def _project_with_template(root: Path) -> None:
    write(root, "ok.py", GOOD_SRC)
    write(root, "templates/app.py", BROKEN_TEMPLATE)


def test_exclude_flag_removes_unparseable_template_and_says_so(tmp_path: Path):
    """The reporter's template scenario: one flag turns a permanent exit 2 into exit 0, visibly."""
    _project_with_template(tmp_path)
    init_ok(tmp_path, "--exclude", "templates/")

    res = run_cli(["check", "--exclude", "templates/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "checked 1 files, 1 symbols." in res.stdout
    assert "excluded by rules: 1 path(s)." in res.stdout
    assert "templates" not in res.stderr


def test_same_template_without_the_flag_still_fails(tmp_path: Path):
    """Guard (spec 009 behavior): without the rule the unparseable file is still a problem."""
    _project_with_template(tmp_path)
    init_ok(tmp_path, "--exclude", "templates/")

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "templates/app.py" in res.stderr


def test_repeated_exclude_flags_are_a_union(tmp_path: Path):
    """Several --exclude flags all apply."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "templates/a.py", BROKEN_TEMPLATE)
    write(tmp_path, "gen/b.py", BROKEN_TEMPLATE)
    init_ok(tmp_path, "--exclude", "templates/", "--exclude", "gen/")

    res = run_cli(["check", "--exclude", "templates/", "--exclude", "gen/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "excluded by rules: 2 path(s)." in res.stdout


def test_excluded_modules_are_ignored_by_every_command_and_lockfiles_untouched(tmp_path: Path):
    """Exclusion affects discovery only: excluded modules are never read, baselined, refreshed or accepted."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "legacy/old.py", LEGACY_SRC)
    init_ok(tmp_path)
    write(tmp_path, "legacy/old.py", LEGACY_SRC.replace("t=30", "t=99"))  # drift inside the excluded module
    before = lockfile(tmp_path, "legacy/old.py").read_bytes()

    check = run_cli(["check", "--exclude", "legacy/"], cwd=tmp_path)
    init = run_cli(["init", "--exclude", "legacy/"], cwd=tmp_path)
    refresh = run_cli(["refresh", "--reason", "nothing to do", "--exclude", "legacy/"], cwd=tmp_path)
    accept = run_cli(["accept", "--symbol", "legacy_fn", "--reason", "r", "--exclude", "legacy/"], cwd=tmp_path)

    assert check.returncode == 0, combined(check)  # drift in the excluded module is not reported
    assert init.returncode == 0, combined(init)
    assert refresh.returncode == 0, combined(refresh)
    assert accept.returncode == 1, combined(accept)  # symbol only exists in the excluded module
    assert lockfile(tmp_path, "legacy/old.py").read_bytes() == before


def test_accept_of_excluded_file_exits_1_and_names_the_rule(tmp_path: Path):
    """accept --file on an excluded path says why (not the generic 'not found')."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "templates/app.py", GOOD_SRC)
    write(tmp_path, "tests/test_x.py", GOOD_SRC)
    init_ok(tmp_path, "--exclude", "templates/")

    by_pattern = run_cli(
        ["accept", "--symbol", "f", "--reason", "r", "--file", "templates/app.py", "--exclude", "templates/"],
        cwd=tmp_path,
    )
    by_default = run_cli(["accept", "--symbol", "f", "--reason", "r", "--file", "tests/test_x.py"], cwd=tmp_path)

    assert by_pattern.returncode == 1, combined(by_pattern)
    assert "excluded" in by_pattern.stderr and "templates/" in by_pattern.stderr
    assert by_default.returncode == 1, combined(by_default)
    assert "default directory 'tests'" in by_default.stderr


def test_refresh_of_excluded_file_is_a_usage_error(tmp_path: Path):
    """refresh --file on an excluded path exits 2 and explains the rule."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "templates/app.py", GOOD_SRC)
    init_ok(tmp_path, "--exclude", "templates/")

    res = run_cli(
        ["refresh", "--reason", "r", "--file", "templates/app.py", "--exclude", "templates/"], cwd=tmp_path
    )

    assert res.returncode == 2, combined(res)
    assert "excluded" in res.stderr


def test_everything_excluded_is_the_zero_files_error(tmp_path: Path):
    """If the rules remove every Python file the run fails (exit 2) and says exclusions were applied."""
    write(tmp_path, "ok.py", GOOD_SRC)

    res = run_cli(["check", "--exclude", "ok.py"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "No Python source files found" in res.stderr
    assert "exclusion" in res.stderr.lower()


def test_init_dry_run_honours_exclusions(tmp_path: Path):
    """The dry-run preview equals what the real run would do with the same rules."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "legacy/old.py", GOOD_SRC)

    res = run_cli(["init", "--dry-run", "--exclude", "legacy/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "Would initialize baseline for 1 compliant symbols" in res.stdout
    assert not (tmp_path / ".project").exists()


@pytest.mark.parametrize("pattern", INVALID_PATTERNS)
def test_invalid_flag_pattern_exits_2_before_any_scan(tmp_path: Path, pattern: str):
    """An invalid pattern never results in a scan or a write (exit 2, pattern quoted)."""
    write(tmp_path, "ok.py", GOOD_SRC)

    res = run_cli(["init", "--exclude", pattern], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert repr(pattern) in res.stderr
    assert "Traceback" not in res.stderr
    assert not (tmp_path / ".project").exists()


def test_api_accept_of_excluded_file_raises_typed_error(tmp_path: Path):
    """API: FileExcludedError is a PyDocSyncError (exit 1), not a ValueError."""
    from pydocsync import FileExcludedError, PyDocSyncError, accept

    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "templates/app.py", GOOD_SRC)
    init_ok(tmp_path, "--exclude", "templates/")

    with pytest.raises(FileExcludedError) as excinfo:
        accept("f", "reason", root_dir=tmp_path, file="templates/app.py", exclude=["templates/"])

    assert isinstance(excinfo.value, PyDocSyncError) and not isinstance(excinfo.value, ValueError)
    assert excinfo.value.exit_code == 1


# --------------------------------------------------------------------------- US2: config file


def test_config_file_drives_a_bare_check_identically_to_flags(tmp_path: Path):
    """A bare `pydocsync check` gets the project's exclusions; output equals the flag form."""
    with_config = tmp_path / "with_config"
    with_flags = tmp_path / "with_flags"
    for proj in (with_config, with_flags):
        _project_with_template(proj)
    write(with_config, CONFIG, json.dumps({"exclude": ["templates/"]}))
    init_ok(with_config)
    init_ok(with_flags, "--exclude", "templates/")

    via_config = run_cli(["check"], cwd=with_config)
    via_flags = run_cli(["check", "--exclude", "templates/"], cwd=with_flags)

    assert via_config.returncode == via_flags.returncode == 0, combined(via_config)
    assert via_config.stdout == via_flags.stdout
    assert "excluded by rules: 1 path(s)." in via_config.stdout


def test_config_is_read_from_the_root_not_the_cwd(tmp_path: Path):
    """--root selects the config file (also with a relative --root .. from a subdirectory)."""
    proj = tmp_path / "proj"
    _project_with_template(proj)
    (proj / "sub").mkdir()
    write(proj, CONFIG, json.dumps({"exclude": ["templates/"]}))
    init_ok(proj)

    from_parent = run_cli(["check", "--root", "proj"], cwd=tmp_path)
    from_sub = run_cli(["check", "--root", ".."], cwd=proj / "sub")

    assert from_parent.returncode == 0, combined(from_parent)
    assert from_sub.returncode == 0, combined(from_sub)


def test_config_and_flags_are_a_union(tmp_path: Path):
    """Flags add to config patterns; nothing removes a config rule."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "templates/a.py", BROKEN_TEMPLATE)
    write(tmp_path, "gen/b.py", BROKEN_TEMPLATE)
    write(tmp_path, CONFIG, json.dumps({"exclude": ["templates/"]}))
    init_ok(tmp_path, "--exclude", "gen/")

    res = run_cli(["check", "--exclude", "gen/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "excluded by rules: 2 path(s)." in res.stdout


CONFIG_ERRORS = {
    "invalid_json": "{ not json",
    "not_an_object": "[]",
    "unknown_key": json.dumps({"excludes": []}),
    "exclude_not_a_list": json.dumps({"exclude": "templates/"}),
    "exclude_item_not_a_string": json.dumps({"exclude": [1]}),
    "invalid_pattern": json.dumps({"exclude": ["!x"]}),
    "default_excludes_not_bool": json.dumps({"default_excludes": "no"}),
    "require_baseline_not_bool": json.dumps({"require_baseline": 1}),
}


@pytest.mark.parametrize("kind", list(CONFIG_ERRORS))
@pytest.mark.parametrize("command", ["check", "init"])
def test_invalid_config_fails_every_command_before_scanning(tmp_path: Path, kind: str, command: str):
    """A config that cannot be read never means 'no exclusions' (that would be a silent skip)."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, CONFIG, CONFIG_ERRORS[kind])

    res = run_cli([command], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert CONFIG in res.stderr
    assert "Traceback" not in res.stderr
    assert not (tmp_path / ".project").exists()


def test_missing_config_is_not_an_error(tmp_path: Path):
    """Guard: no config file means defaults."""
    write(tmp_path, "ok.py", GOOD_SRC)

    assert run_cli(["check"], cwd=tmp_path).returncode == 0


def test_config_error_is_a_typed_error(tmp_path: Path):
    """API: ConfigError is a PyDocSyncError (exit 2), not a ValueError."""
    from pydocsync import ConfigError, PyDocSyncError, check

    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, CONFIG, "{ not json")

    with pytest.raises(ConfigError) as excinfo:
        check(root_dir=tmp_path)

    assert isinstance(excinfo.value, PyDocSyncError) and not isinstance(excinfo.value, ValueError)
    assert excinfo.value.exit_code == 2


# --------------------------------------------------------------------------- US3: default ignores


def test_node_modules_and_site_packages_are_never_scanned(tmp_path: Path):
    """Vendored code is skipped by default and even when default excludes are switched off."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "node_modules/pkg/a.py", UNDOCUMENTED_SRC)
    write(tmp_path, "lib/site-packages/b.py", UNDOCUMENTED_SRC)

    default = run_cli(["check"], cwd=tmp_path)
    everything = run_cli(["check", "--no-default-excludes"], cwd=tmp_path)

    assert default.returncode == 0, combined(default)
    assert everything.returncode == 0, combined(everything)


def test_convention_directories_are_scanned_only_with_no_default_excludes(tmp_path: Path):
    """Real code in pkg/build/ can be checked with --no-default-excludes (field-report item 6)."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "pkg/build/core.py", UNDOCUMENTED_SRC)

    default = run_cli(["check"], cwd=tmp_path)
    opted_in = run_cli(["check", "--no-default-excludes"], cwd=tmp_path)

    assert default.returncode == 0, combined(default)
    assert opted_in.returncode == 1, combined(opted_in)
    assert "pkg/build/core.py" in opted_in.stderr


def test_hints_keep_no_default_excludes_so_they_are_runnable(tmp_path: Path):
    """The suggested accept/refresh commands carry --no-default-excludes, otherwise they would be rejected."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "pkg/build/core.py", UNDOCUMENTED_SRC)

    res = run_cli(["check", "--no-default-excludes"], cwd=tmp_path)

    assert res.returncode == 1, combined(res)
    hint = 'pydocsync accept --symbol public_thing --reason "<audit reason>" --file pkg/build/core.py'
    assert hint + " --no-default-excludes" in res.stderr
    # the hinted command really works (with a concrete reason)
    accept = run_cli(
        ["accept", "--symbol", "public_thing", "--reason", "reviewed", "--file", "pkg/build/core.py",
         "--no-default-excludes"],
        cwd=tmp_path,
    )
    assert accept.returncode == 0, combined(accept)


def test_config_can_disable_default_excludes(tmp_path: Path):
    """default_excludes: false in config behaves like --no-default-excludes."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, "pkg/build/core.py", UNDOCUMENTED_SRC)
    write(tmp_path, CONFIG, json.dumps({"default_excludes": False}))

    assert run_cli(["check"], cwd=tmp_path).returncode == 1


def test_hidden_dirs_pycache_and_venv_stay_skipped_without_default_excludes(tmp_path: Path):
    """Vendor/cache directories are not part of the switchable defaults."""
    write(tmp_path, "ok.py", GOOD_SRC)
    for rel in (".hidden/x.py", "__pycache__/x.py", "venv/x.py"):
        write(tmp_path, rel, UNDOCUMENTED_SRC)

    assert run_cli(["check", "--no-default-excludes"], cwd=tmp_path).returncode == 0


def test_default_ignored_dirs_constant_is_a_superset():
    """DEFAULT_IGNORED_DIRS keeps every 0.3.0 name and adds the new vendor directories."""
    from pydocsync.discovery import DEFAULT_IGNORED_DIRS

    v030 = {".venv", "venv", ".git", "__pycache__", "build", "dist", "_archive", "migrations", "tests", "fixtures"}
    assert v030 <= set(DEFAULT_IGNORED_DIRS)
    assert {"node_modules", "site-packages"} <= set(DEFAULT_IGNORED_DIRS)


# --------------------------------------------------------------------------- US4: --require-baseline


def test_require_baseline_fails_when_nothing_was_ever_baselined(tmp_path: Path):
    """No baseline folder while public symbols exist: exit 2, BASELINE_MISSING, next step named."""
    write(tmp_path, "ok.py", GOOD_SRC)

    plain = run_cli(["check"], cwd=tmp_path)
    strict = run_cli(["check", "--require-baseline"], cwd=tmp_path)

    assert plain.returncode == 0, combined(plain)  # guard: default behavior unchanged
    assert strict.returncode == 2, combined(strict)
    assert "BASELINE_MISSING" in strict.stderr
    assert "pydocsync init" in strict.stderr


def test_require_baseline_fails_for_an_empty_baseline_folder(tmp_path: Path):
    """An existing but empty baseline folder is the same situation."""
    write(tmp_path, "ok.py", GOOD_SRC)
    (tmp_path / ".project" / "pydocsync").mkdir(parents=True)

    res = run_cli(["check", "--require-baseline"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "BASELINE_MISSING" in res.stderr


def test_require_baseline_passes_once_a_baseline_exists(tmp_path: Path):
    """With at least one lockfile the flag adds nothing."""
    write(tmp_path, "ok.py", GOOD_SRC)
    init_ok(tmp_path)

    assert run_cli(["check", "--require-baseline"], cwd=tmp_path).returncode == 0


def test_require_baseline_passes_without_public_symbols(tmp_path: Path):
    """No public symbols means there is nothing to baseline."""
    write(tmp_path, "priv.py", "def _helper():\n    return 1\n")

    assert run_cli(["check", "--require-baseline"], cwd=tmp_path).returncode == 0


def test_require_baseline_from_config(tmp_path: Path):
    """require_baseline: true in config behaves like the flag."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, CONFIG, json.dumps({"require_baseline": True}))

    assert run_cli(["check"], cwd=tmp_path).returncode == 2


def test_require_baseline_with_drift_prints_both_and_exits_2(tmp_path: Path):
    """Exit 2 wins and nothing is hidden (spec 009 precedence)."""
    write(tmp_path, "undoc.py", UNDOCUMENTED_SRC)

    res = run_cli(["check", "--require-baseline"], cwd=tmp_path)

    assert res.returncode == 2, combined(res)
    assert "PYDOCSYNC001" in res.stderr
    assert "BASELINE_MISSING" in res.stderr


def test_api_require_baseline_reports_problem_as_data(tmp_path: Path):
    """check(require_baseline=True) returns a BASELINE_MISSING problem and is not synchronized."""
    from pydocsync import ProblemKind, check

    write(tmp_path, "ok.py", GOOD_SRC)

    result = check(root_dir=tmp_path, require_baseline=True)

    assert result.is_synchronized is False
    assert [p.kind for p in result.problems] == [ProblemKind.BASELINE_MISSING]


# --------------------------------------------------------------------------- US5: visibility


def test_unmatched_pattern_warns_on_stderr_without_changing_the_exit_code(tmp_path: Path):
    """A typo'd pattern that matches nothing cannot pass silently."""
    write(tmp_path, "ok.py", GOOD_SRC)
    init_ok(tmp_path)

    res = run_cli(["check", "--exclude", "nothing_here/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "WARNING" in res.stderr
    assert "nothing_here/" in res.stderr
    assert "--exclude" in res.stderr
    assert "excluded by rules" not in res.stdout


def test_unmatched_config_pattern_names_its_source(tmp_path: Path):
    """The warning says which file the pattern came from."""
    write(tmp_path, "ok.py", GOOD_SRC)
    write(tmp_path, CONFIG, json.dumps({"exclude": ["typo_dir/"]}))
    init_ok(tmp_path)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "typo_dir/" in res.stderr and CONFIG in res.stderr


def test_other_commands_warn_about_unmatched_patterns_too(tmp_path: Path):
    """init warns as well (stderr), so the agent sees it whichever command it runs."""
    write(tmp_path, "ok.py", GOOD_SRC)

    res = run_cli(["init", "--exclude", "nope/"], cwd=tmp_path)

    assert res.returncode == 0, combined(res)
    assert "WARNING" in res.stderr and "nope/" in res.stderr


def test_output_is_unchanged_when_no_rule_applies(tmp_path: Path):
    """Guard: without rules the output is exactly the spec-009 output."""
    write(tmp_path, "ok.py", GOOD_SRC)
    init_ok(tmp_path)

    res = run_cli(["check"], cwd=tmp_path)

    assert res.stdout == (
        "PYDOCSYNC: All symbols synchronized with baseline.\nPYDOCSYNC: checked 1 files, 1 symbols.\n"
    )
    assert res.stderr == ""


def test_api_exposes_exclusion_data_and_reads_config_by_default(tmp_path: Path):
    """SyncResult.excluded_count / unmatched_excludes; keyword arguments; config read automatically."""
    from pydocsync import check

    _project_with_template(tmp_path)
    init_ok(tmp_path, "--exclude", "templates/")

    explicit = check(root_dir=tmp_path, exclude=["templates/", "nope/"])
    assert explicit.excluded_count == 1
    assert explicit.unmatched_excludes == ["nope/"]
    assert explicit.is_synchronized is True

    write(tmp_path, CONFIG, json.dumps({"exclude": ["templates/"]}))
    from_config = check(root_dir=tmp_path)
    assert from_config.excluded_count == 1
    assert from_config.is_synchronized is True


# --------------------------------------------------------------------------- US6: pre-commit hook


HOOK_FILE = Path(__file__).resolve().parents[1] / ".pre-commit-hooks.yaml"


def _hook_fields() -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in HOOK_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().lstrip("- ").strip()
        if ":" in stripped and not line.lstrip().startswith("#"):
            key, _, value = stripped.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def test_pre_commit_manifest_defines_the_hook():
    """The manifest exposes hook `pydocsync-check` with the documented settings."""
    fields = _hook_fields()

    assert fields["id"] == "pydocsync-check"
    assert fields["entry"] == "pydocsync check"
    assert fields["language"] == "python"
    assert fields["types"] == "[python]"
    assert fields["pass_filenames"] == "false"


def test_pre_commit_entry_behaves_like_check_and_accepts_extra_args(tmp_path: Path):
    """Running the manifest's entry (plus args:) gives check's exit codes."""
    write(tmp_path, "ok.py", GOOD_SRC)
    init_ok(tmp_path)
    entry = _hook_fields()["entry"].split()
    assert entry[0] == "pydocsync"
    argv = [sys.executable, "-m", "pydocsync", *entry[1:]]

    clean = subprocess.run(argv + ["--fail-on-stale"], capture_output=True, text=True, cwd=tmp_path)
    write(tmp_path, "ok.py", GOOD_SRC.replace("t=30", "t=99"))
    drift = subprocess.run(argv, capture_output=True, text=True, cwd=tmp_path)

    assert clean.returncode == 0, combined(clean)
    assert drift.returncode == 1, combined(drift)


def test_discovery_and_single_file_validation_apply_the_same_rules(tmp_path: Path):
    """accept/refresh --file validation (exclusion_reason) must agree with what discovery scans (FR-023)."""
    from pydocsync.config import load_settings
    from pydocsync.discovery import discover, exclusion_reason

    rels = [
        "a.py",
        "pkg/b.py",
        "pkg/build/c.py",
        "pkg/legacy/d.py",
        "templates/e.py",
        "x/tests/f.py",
        "node_modules/g.py",
        "deep/er/gen/h.py",
        "keep/mod1.py",
        "keep/mod12.py",
        "keep/x_pb2.py",
    ]
    for rel in rels:
        write(tmp_path, rel, GOOD_SRC)
    settings = load_settings(tmp_path, exclude=["templates/", "pkg/legacy", "**/gen", "*_pb2.py", "mod?.py"])
    flt = settings.path_filter()

    scanned = {path.as_posix() for path in discover(tmp_path, flt).files}
    validated = {rel for rel in rels if exclusion_reason(rel, flt) is None}

    assert scanned == validated
    assert scanned == {"a.py", "pkg/b.py", "keep/mod12.py"}
