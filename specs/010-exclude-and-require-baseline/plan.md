# Implementation Plan: 010-exclude-and-require-baseline

## Technical Architecture & Design for Exclusion Rules, Config File and Strict-Baseline Mode

**Feature Code**: `010-exclude-and-require-baseline`  
**Created**: 2026-09-20  
**Status**: Implemented — see convergence_report.md for deviations  
**Spec**: [`spec.md`](spec.md) | **Governance tier**: T3 behavioral | **Target version**: `0.4.0` (unreleased; ships with spec 009)

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Summary](#summary) | Approach |
| 2 | [Technical Context](#technical-context) | Constraints |
| 3 | [Constitution Check](#constitution-check) | Gates |
| 4 | [Source Layout](#source-layout) | Files added/modified |
| 5 | [Design](#design) | D1–D8 |
| 6 | [Contracts](#contracts) | CLI, config schema, output, API |
| 7 | [Test Plan](#test-plan) | Matrix → tests; must-fail gate |
| 8 | [Risks](#risks) | Known risks and mitigations |
| 9 | [Delivery Order](#delivery-order) | Input for tasks |

---

## Summary

Discovery gets a real, configurable rule engine instead of a fixed name set:

1. A small **pattern module** compiles a strict gitignore-style subset into regexes (rejecting anything ambiguous).
2. A **settings resolver** merges `<root>/.pydocsync.json` and CLI flags into one `Settings` object (exclude patterns, default-excludes on/off, require-baseline).
3. **Discovery** applies default rules (split into *always* vs *convention* sets) plus user patterns while walking, prunes matched directories, and returns the files together with what the rules did (excluded count, unmatched patterns) and — for a single path — *why* it is excluded.
4. The four `run_*` functions take the resolved settings; `check` gains `--require-baseline` and prints exclusion visibility; the API mirrors the options.
5. A `.pre-commit-hooks.yaml` is added.

No baseline schema change; no new dependency.

---

## Technical Context

| Item | Value |
|---|---|
| Language | Python ≥ 3.10, standard library only (`re`, `json`, `os`, `pathlib`) |
| Config format | JSON (`tomllib` unavailable on 3.10) |
| Platform | Windows and POSIX: all matching on POSIX-style relative paths, case-sensitive |
| Tests | `pytest` via `.venv`; 153 passing at start |
| Compatibility pins | `DEFAULT_IGNORED_DIRS` (test asserts `migrations` in it), `discover_python_files(root) -> list[Path]`, output lines from spec 009 |

---

## Constitution Check

| Gate | Principle | Answer |
|---|---|---|
| Stdlib only | I | **YES** |
| Spec complete before plan | II | **YES** (`spec.md`, decisions D1–D10) |
| Deterministic, platform-independent output | III | **YES** — POSIX paths, sorted discovery, case-sensitive matching |
| Reduced coverage made visible; invalid input never silently ignored | IV | **YES** — excluded count, unmatched-pattern warning, strict pattern/config validation |
| Regression tests fail on pre-010 code; full suite green | V | **YES** — see Test Plan |
| Baseline schema change? | T4 trigger | **NO** |

---

## Source Layout

```text
pydocsync/
├── patterns.py        [NEW]      ExcludePattern, compile_pattern(), strict syntax validation, matching
├── config.py          [NEW]      Settings, load_settings(): .pydocsync.json + CLI merge, ConfigError checks
├── discovery.py       [MODIFIED] ALWAYS_/CONVENTION_ dir sets (DEFAULT_IGNORED_DIRS stays the union), PathFilter with user patterns,
│                                 discover() -> Discovery, exclusion_reason(), discover_python_files() wrapper
├── problems.py        [MODIFIED] ProblemKind.BASELINE_MISSING; ConfigError, FileExcludedError
├── cli.py             [MODIFIED] shared --exclude/--no-default-excludes options, --require-baseline, run_* take settings, visibility output
├── api.py             [MODIFIED] SyncResult.excluded_count/unmatched_excludes; exclude/default_excludes/require_baseline kwargs
├── report.py          [MODIFIED] excluded line + unmatched warning formatters, BASELINE_MISSING guidance
└── __init__.py        [MODIFIED] export ConfigError, FileExcludedError
.pre-commit-hooks.yaml [NEW]      hook `pydocsync-check`
tests/
└── test_exclusions_and_require_baseline.py  [NEW]
README.md, .agents/skills/pydocsync/SKILL.md, AGENTS.md (ledger), ideas/future_features.md  [MODIFIED]
```

---

## Design

### D1 — Patterns (`patterns.py`)

`compile_pattern(text: str, origin: str) -> ExcludePattern`, raising `InvalidArgumentError` for: empty; leading/trailing whitespace; leading `!` or `#`; contains `\`; contains `[` or `]`; a segment that contains `*` but is not exactly `*`-only-wildcards-within-segment… concretely: a segment may use `*` and `?` freely **except** the segment `**` must stand alone (`a**b`, `***` rejected); empty segment (`a//b`); `.` or `..` segments. The message quotes the pattern and lists the supported forms.

Semantics (spec "Pattern Syntax"):
- `dir_only` = trailing `/`; `anchored` = leading `/` or an inner `/`.
- Unanchored → regex tested against the **last path component** only.
- Anchored → regex tested against the full relative POSIX path. Segment translation: literal → `re.escape`, `*` → `[^/]*`, `?` → `[^/]`; a standalone `**` segment → zero-or-more directories (`(?:.*/)?` at start/middle) or "everything beneath" (`/.+`) at the end.
- `matches(rel_posix: str, is_dir: bool) -> bool`. `dir_only` patterns never match files.

Pure functions, no I/O; exhaustively table-tested.

### D2 — Settings (`config.py`)

`Settings(exclude: tuple[ExcludePattern, ...], default_excludes: bool, require_baseline: bool)`.

`load_settings(root, exclude=(), default_excludes=None, require_baseline=None, use_config=True)`:
1. If `<root>/.pydocsync.json` exists: read (UTF-8), parse; errors → `ConfigError` naming the file and reason (invalid JSON with line/column, non-object, unknown key listing allowed keys, wrong type, invalid pattern quoting the pattern). Missing file = defaults.
2. `exclude` = config patterns (origin `.pydocsync.json`) + given patterns (origin `--exclude`).
3. `default_excludes`: explicit argument wins; else config; else True. `require_baseline` likewise.
4. Patterns compiled once; deterministic order (config first, then flags, duplicates removed by text).

`ConfigError(PyDocSyncError)`, exit code 2.

### D3 — Discovery (`discovery.py`)

- `ALWAYS_IGNORED_DIRS = {venv, node_modules, site-packages, __pycache__}` plus the dot-directory rule; `CONVENTION_IGNORED_DIRS = {build, dist, _archive, migrations, tests, fixtures}`; `DEFAULT_IGNORED_DIRS = ALWAYS | CONVENTION | {.venv, .git}` (a superset of the 0.3.0 value; keeps the existing test valid).
- `PathFilter(ignored_dirs=..., exclude=())`; `Settings.path_filter()` builds it: `ALWAYS` always, `CONVENTION` unless `default_excludes` is off.
- `discover(root, path_filter) -> Discovery(files, excluded_count, matched_patterns)`: `os.walk` with in-place pruning. Per directory (rel POSIX path): default name rule first (silent prune, not counted), then user patterns (prune, count once, record every matching pattern). Per `.py` file: user patterns (skip, count, record). Directories/files that no user pattern touches are visited as before. Sorted result. Empty result → `NoSourceFilesError`; when user patterns exist the message adds "(all candidates were excluded by the exclusion rules)".
- `discover_python_files(root_dir, path_filter=None)` stays: wrapper returning `discover(...).files`.
- `exclusion_reason(rel_path, path_filter) -> str | None`: evaluates the same rules against each ancestor directory and the file itself (single implementation used by discovery and by `--file` validation, FR-023); returns e.g. `default directory 'tests'`, `pattern 'templates/' (from --exclude)`.
- `is_path_excluded(rel, filter)` remains, implemented via `exclusion_reason`.

### D4 — CLI and run functions (`cli.py`)

- Shared parser helper adds `--exclude` (`action="append"`, metavar `PATTERN`, help with syntax examples) and `--no-default-excludes` to `check`, `init`, `accept`, `refresh`; `check` also gets `--require-baseline`.
- `run_check/run_init/run_accept/run_refresh` gain keyword parameters `exclude: Sequence[str] = ()`, `default_excludes: bool | None = None` (and `require_baseline: bool | None = None` for `run_check`); each calls `load_settings(root, ...)` and `discover(...)` once. Config errors raise `ConfigError` before any scan or write.
- `run_check` also returns `excluded_count`, `unmatched_excludes` (patterns with no match), and applies `require_baseline`: after the scan, if enabled and no `*.json` exists under `<root>/.project/pydocsync` **and** at least one public symbol was seen → `Problem(BASELINE_MISSING, ".project/pydocsync", None, "no baseline exists ... run 'pydocsync init'")`.
- `accept --file` / `refresh --file`: validation uses `exclusion_reason`. Excluded → `accept` raises `FileExcludedError` (exit 1, message naming the rule); `refresh` raises `InvalidArgumentError` (exit 2, same explanation), consistent with spec 009's exit codes.
- `main()` maps `PyDocSyncError` generically as before; the new errors need no special handling beyond message printing.

### D5 — Visibility output

`check` success block (unchanged lines kept):
```text
PYDOCSYNC: All symbols synchronized with baseline.
PYDOCSYNC: checked 14 files, 133 symbols.
PYDOCSYNC: excluded by rules: 3 path(s).          <- only when user rules excluded something
```
The excluded line also prints when drift or problems exist (stdout, after the coverage information). Unmatched patterns: one stderr line each, `PYDOCSYNC WARNING: exclude pattern 'X' (from --exclude) matched no scanned path.`; exit code unaffected. `init`/`refresh`/`accept` print the warnings too (stderr) but not the counts.

### D6 — API (`api.py`)

`SyncResult` gains `excluded_count: int = 0`, `unmatched_excludes: list[str]`. `check(root_dir, *, exclude=(), default_excludes=None, require_baseline=None)`; `init`, `init_report`, `accept`, `refresh` gain `exclude` and `default_excludes` keyword-only parameters. All read `.pydocsync.json` from `root_dir` by default.

### D7 — Pre-commit hook

`.pre-commit-hooks.yaml`:
```yaml
- id: pydocsync-check
  name: pydocsync check
  description: Fail when Python code changed without a documentation review (PyDocSync).
  entry: pydocsync check
  language: python
  types: [python]
  pass_filenames: false
```
Users add flags through `args:`. Tests parse the file with a tiny key/value reader (no YAML library) and execute the `entry` in a temp project.

### D8 — Docs and agent guidance

README: "Excluding files" (syntax table, config schema, precedence, `--no-default-excludes`, always-skipped dirs), "`--require-baseline`", pre-commit snippet, updated "Upgrading to 0.4.0" (no 0.4.1 statement), exit-code tables. Consumer `SKILL.md`: how to react to "unparseable template file" (add an exclude, do not delete/edit), the guardrail (never exclude real source to silence `check`; exclusions are visible in output and should be reviewed by a human), and that `.pydocsync.json` is read automatically.

---

## Contracts

### Config file `<root>/.pydocsync.json`

```json
{
  "exclude": ["templates/", "**/*_pb2.py", "pkg/generated/**"],
  "default_excludes": true,
  "require_baseline": false
}
```
All keys optional. Unknown keys and wrong types are errors (exit 2).

### Exit codes (additions to spec 009)

| Situation | Exit |
|---|---|
| Invalid pattern (flag or config), invalid config file | 2 |
| `--require-baseline` and no baseline while public symbols exist | 2 (with drift printed as well if any) |
| `accept --file <excluded>` | 1 (`FileExcludedError`) |
| `refresh --file <excluded>` | 2 |
| Everything excluded (zero files) | 2 |

### Python API additions

`SyncResult.excluded_count`, `SyncResult.unmatched_excludes`; keyword arguments `exclude`, `default_excludes`, `require_baseline` (check only); exports `ConfigError`, `FileExcludedError`.

---

## Test Plan

New file `tests/test_exclusions_and_require_baseline.py`, written **first** (red), one group per matrix row of the spec:

- **Pattern unit tests** (pure, table-driven): every syntax form, files vs directories, depth, no partial-name matches, `**` at start/middle/end, case sensitivity, and every invalid form. A small independent reference matcher (segment-wise, no regex) cross-checks the regex results on a generated set of paths to catch translator mistakes.
- **CLI/API integration** (subprocess like the existing suites): US1–US6 scenarios, output-line guards from spec 009, warnings, config precedence, `--root` handling, dry-run parity, hook execution.

**Must-fail-on-pre-010 gate** (FR-016): create a temporary git worktree of commit `4f00c2a` (the committed spec-009 state), run the new file there, and record per test whether it fails; substantive behavior tests must fail; guards (*guard* rows) must pass. Evidence goes into `convergence_report.md`.

Scoped gate while developing: the new file plus `tests/test_django_and_relative_root_regressions.py`; full suite before each phase end and at completion. The existing 200 ms scan-budget test guards performance.

---

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Regex translation errors (`**` cases) silently exclude the wrong files | Strict subset, table tests, independent reference-matcher cross-check, visibility output |
| R2 | Windows vs POSIX path handling | Everything normalised to `Path.relative_to(root).as_posix()`; backslash patterns rejected; tests run on this Windows machine |
| R3 | An agent excludes real code to make `check` pass | Exclusions always visible in output, unmatched warnings, SKILL guardrail; cannot be prevented technically, only surfaced |
| R4 | Exit-1 vs exit-2 for `accept --file <excluded>` may surprise | Follows spec 009 (accept "not found" family = 1); message names the rule |
| R5 | Pre-commit hook untested under the real tool | Structural + entry-execution tests; documented as such |
| R6 | Config precedence confusion (flag vs file) | Flags only add excludes or disable defaults; documented as union; no option can *remove* a config rule |
| R7 | Public constant `DEFAULT_IGNORED_DIRS` semantics | Kept as a superset union; regression guard |
| R8 | `.project/` baselines of PyDocSync itself become stale/flagged by these code changes | Handled with the spec-009 dogfood workflow at the end (accept/refresh/init), recorded in the convergence report |

---

## Delivery Order

1. Tests first (red) and the must-fail gate against the spec-009 commit.
2. `patterns.py` (+ its unit tests green).
3. `problems.py` additions; `config.py`.
4. `discovery.py` rework (existing suite stays green).
5. `cli.py` wiring: options, settings, visibility, `--require-baseline`, `--file` exclusion reasons.
6. `api.py`, `report.py`, `__init__.py`, export test update.
7. `.pre-commit-hooks.yaml`.
8. README, SKILL.md, AGENTS.md ledger, `ideas/future_features.md`.
9. Dogfood baselines, full suite, gate evidence, convergence report.
10. Commit on `feat/0.4.0-hardening`.
