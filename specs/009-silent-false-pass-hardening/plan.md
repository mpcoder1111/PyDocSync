# Implementation Plan: 009-silent-false-pass-hardening

## Technical Architecture & Design for Eliminating Silent "All Synchronized" Results

**Feature Code**: `009-silent-false-pass-hardening`  
**Created**: 2026-09-19  
**Status**: Implemented — see "Deviations from this plan" (Q1–Q11 resolved)  
**Spec**: [`spec.md`](spec.md) | **Governance tier**: T3 behavioral  
**Target version**: `0.4.0`

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Summary](#summary) | Approach in one paragraph |
| 2 | [Technical Context](#technical-context) | Language, constraints, test setup |
| 3 | [Constitution Check](#constitution-check) | Gates against `.specify/memory/constitution.md` |
| 4 | [Decisions](#decisions) | Q7–Q10 resolved; Q11 open |
| 5 | [Source Layout](#source-layout) | Files added/modified |
| 6 | [Design](#design) | Per-module design (D1–D9) |
| 7 | [Contracts](#contracts) | CLI, exit codes, output, Python API |
| 8 | [Data Model](#data-model) | Baseline compatibility, key scheme |
| 9 | [Test Plan](#test-plan) | Mapping spec matrix → tests; must-fail-on-0.3.0 gate |
| 10 | [Risks & Migration](#risks--migration) | Known friction and mitigations |
| 11 | [Delivery Order](#delivery-order) | Input for `/speckit-tasks` |

---

## Summary

Every reported gap has one root cause: code that cannot evaluate something (a lockfile, a source file, an ambiguous name, an existing record) quietly falls back to a "safe" default. The plan replaces those fallbacks with an explicit, structured **problem** channel and makes each of the four commands stop treating "unknown" as "fine":

1. A shared **loader** returns either symbols or a structured `Problem`; no `except Exception: continue` remains.
2. A **strict baseline reader** distinguishes *missing* (fine) from *corrupt/unsupported* (problem).
3. A single **evaluation function** decides "does `check` flag this symbol?", used by both `check` and `init`, so `init` protects exactly what `check` would report.
4. Symbols get a **per-file unique key** (`name`, `name#2`, …) so same-named definitions in one file stop overwriting each other, without changing existing baseline keys.
5. `accept` gains `--file` and refuses ambiguity; `init` gains protection, `--force --reason` and `--dry-run`; `check` prints coverage.
6. `check` reports **stale** records (documentation updated but baseline not refreshed); a new `refresh` command records them non-destructively; `--fail-on-stale` lets CI enforce it.
7. One exception base class (`PyDocSyncError`, not a `ValueError`) maps to exit codes, replacing the broad `ValueError` catch.

No new dependencies, no baseline schema change (`schema_version` stays `1`).

---

## Technical Context

| Item | Value |
|---|---|
| Language | Python ≥ 3.10, standard library only |
| Packaging | Flit (`pyproject.toml`), version `0.3.0` → `0.4.0` |
| Storage | Per-module JSON lockfiles under `.project/pydocsync/`, `schema_version: 1` (unchanged) |
| Tests | `pytest` via `.\.venv\Scripts\pytest.exe tests/`; baseline 94/94 passing at spec start |
| Constraints | Deterministic, sorted output; Windows paths; no new runtime deps; 100 % type annotations; Google-style docstrings with `WHAT IS THIS? / WHY DO WE NEED THIS?` headers in new modules |
| Standards read before implementing | `coding_standards.json` → `_task_index` (not yet read; done at task time) |

---

## Constitution Check

| Gate | Principle | Answer |
|---|---|---|
| Stdlib only, core engine isolated? | I | **YES** — only `json`, `ast`, `os`, `pathlib`, `dataclasses`, `enum`. |
| Spec present and complete before plan? | II | **YES** — spec Clarified (Q1–Q10; Q11 open, plan default applied). |
| Shipped spec 008 left untouched? | II | **YES** — new spec 009. |
| Deterministic output/ordering? | III | **YES** — problems and candidates sorted by path/line; no timestamps in reports. |
| Ambiguity routed to review, not assumed safe? | IV | **YES** — this feature exists to satisfy it. |
| Regression tests and full-suite pass required? | V | **YES** — see Test Plan. |
| Baseline schema change? | T4 trigger | **NO** — key scheme extends keys but not the envelope; legacy files load. |

No violations; Complexity Tracking not needed.

---

## Decisions

### Resolved

| Q | Decision | Consequence in this plan |
|---|---|---|
| Q7 | Keep `init() -> int`, `accept() -> bool`; typed exceptions carry data; add `init_report()` | One base class `PyDocSyncError(Exception)` with `exit_code`; **not** a `ValueError` subclass. CLI maps through the base. `InitIncompleteError` carries an `InitResult` (baselined, protected, stale, problems); new symbols are written before it is raised. |
| Q8 | `init` protects only records `check` would flag | `init` calls the shared `evaluate_symbol()` (D5). Refinement (FR-019): *stale* records (differ, not flagged) are left untouched and reported, not silently overwritten, because a stale record may hide an unreviewed later change (Q10). |
| Q9 | Refuse (exit 2) when a file is unparseable and no `--file` | With `--file`, only that file is resolved and read. |
| Q10 | Fix the sticky baseline inside 009 | New D9, `refresh` command, `--fail-on-stale`, US6. |

### Open

**Q11 — default strictness for stale records** (spec Q11). Plan default: **A** — `check` passes with a stale notice; `--fail-on-stale` is opt-in; default-strict is a candidate for 0.5.0. Rationale: `check` alone cannot separate "code+doc changed together" from a later "code-only change" (both differ from the old baseline in code and docs), so a default failure would turn the prescribed workflow into a failure and change the evaluation results of specs 002–004.

---

## Source Layout

```text
pydocsync/
├── _version.py           [NEW]      Single source of the version string (avoids import cycle baseline ↔ package)
├── problems.py           [NEW]      Problem / ProblemKind, PyDocSyncError hierarchy carrying data
├── discovery.py          [MODIFIED] is_path_excluded() for --file; NoSourceFilesError (PyDocSyncError + ValueError for 008 compatibility)
├── ast_extract.py        [MODIFIED] Per-file unique symbol key (name, name#2, …); strict source loader helper
├── baseline.py           [MODIFIED] Strict reader (missing vs corrupt), single-load/single-save per module, envelope version from _version
├── evaluate.py           [NEW]      evaluate_symbol(): the one place deciding "would check flag this?"
├── cli.py                [MODIFIED] run_check / run_init / run_accept / run_refresh, new flags, exit-code mapping via PyDocSyncError
├── api.py                [MODIFIED] SyncResult.problems + coverage, init_report, exception contract
├── report.py             [MODIFIED] Problem report, hint with --file, coverage line
└── __init__.py           [MODIFIED] Version, new public names
tests/
└── test_silent_false_pass_regressions.py   [NEW] Spec 009 matrix
README.md, pyproject.toml                   [MODIFIED] Docs, version, exit-code table, release notes
```

Discovery's exclusion rules are unchanged (exclusion changes belong to spec 010); only a path-check helper and the zero-files exception type are added.

---

## Design

### D1 — Structured problems (`problems.py`)

- `ProblemKind` enum: `BASELINE_CORRUPT`, `BASELINE_UNSUPPORTED_VERSION`, `BASELINE_UNREADABLE`, `SOURCE_UNPARSEABLE`, `SOURCE_UNREADABLE`.
- `Problem` frozen dataclass: `kind`, `path: str` (POSIX-style, relative to root), `line: int | None`, `reason: str`. Sortable by `(path, line, kind)` for deterministic output.
- `PyDocSyncError(Exception)` base with class attribute `exit_code` (instances may override). Subclasses: `AmbiguousSymbolError(qualname, candidates)` (2), `SourceProblemsError(problems)` (2), `BaselineProblemError(problem)` (2, internal), `InitIncompleteError(result)` (2 if problems else 1), `InvalidArgumentError` (2). None inherits from `ValueError`. Exception: `NoSourceFilesError(PyDocSyncError, ValueError)` keeps the 008-documented `ValueError` contract for the zero-files case.
- `main()` catches `PyDocSyncError` (use `exc.exit_code`) and `FileNotFoundError`/`NotADirectoryError` (bad root); the bare `ValueError` catch is removed (item 10).

### D2 — Source loader (`ast_extract.py` or `evaluate.py` helper)

`load_symbols(abs_path, rel_path) -> tuple[list[SymbolRepresentation], None] | tuple[None, Problem]`. Catches only `OSError`, `UnicodeDecodeError`, `SyntaxError`, `ValueError` (NUL bytes on older interpreters) and `RecursionError` (deeply nested source). Never a bare `Exception`. `SyntaxError` becomes `SyntaxError line N: <msg>`, so an interpreter-version mismatch (e.g. `match` on 3.9/3.10) is self-explanatory. Used by all three commands (fixes item 2 everywhere).

### D3 — Strict baseline reader (`baseline.py`)

- Missing file → `{}` (unchanged; absent ≠ corrupt).
- Empty file, invalid JSON, non-object root, non-dict record, missing/unknown record fields, wrong field types, `schema_version` greater than supported → `BaselineProblemError` with a `Problem`.
- Legacy pre-envelope files (no `schema_version`) with valid records still load (spec 007 compatibility).
- `check` converts the error to a `Problem` and moves on to the next module (the module's symbols are not evaluated; the problem forces exit 2). `init` never overwrites a corrupt lockfile; it reports it (restore from VCS or delete deliberately).
- Writes: load once and save once per module (init currently reloads/saves per symbol). Envelope `pydocsync_version` reads `_version.__version__`.

### D4 — Per-file unique keys (`ast_extract.py`)

`SymbolRepresentation` gains `key: str` (defaults to `qualname`). A post-pass in `extract_symbols_from_source` assigns keys in source order: first occurrence of a qualname keeps `qualname`; later ones get `qualname#2`, `qualname#3`. `#` cannot appear in an identifier, so no collision. Baseline lookup/storage, `init` protection and the classification cache use `key`; the display name and `accept --symbol` matching use `qualname`. Covers redefinitions, `@overload`, property getter/setter, `if/else` conditional definitions, and `try/except ImportError` fallbacks.

### D5 — Shared evaluation (`evaluate.py`)

Extract the per-symbol block now inside `scan_and_check` (fingerprint diff, classifier call, `RULE_BASELINE_CODE_DRIFT` escalation, "doc changed suppresses", new-public-undocumented gate) into `evaluate_symbol(sym, baseline_record | None, classifier) -> SyncFailure | None`. `check` calls it for every symbol; `init` calls it to decide "protect vs. write". Behavior of `check` is unchanged except through D3/D4 (guarded by the existing 94 tests). This is a pure refactor step performed first, under the existing tests.

### D6 — `check` (`run_check`)

Returns `CheckReport(failures, problems, files_checked, symbols_checked)`:
- Loop discovered files → loader; on problem record and `continue` (never abort).
- Load baseline strictly per module; on problem record and `continue`.
- Evaluate with D5.
- CLI: problems present → exit **2**, print the problem report and (if any) the `PYDOCSYNC001` report, both to stderr; drift only → exit 1; neither → exit 0 with the coverage line.
- `scan_and_check()` remains a compatibility wrapper returning `list[SyncFailure]`; if problems exist it raises `SourceProblemsError`/`BaselineProblemError` with all problems attached rather than silently returning a partial list (three existing tests call it on clean trees; the two corpus tests are verified at implementation time — a parse failure there is a real finding).

### D7 — `accept` (`run_accept`)

1. Validate reason (existing), validate and normalize `--file` (resolved against root; must stay inside root; must be a discovered file).
2. With `--file`: apply the exclusion helper to the path (no directory walk, no zero-files check) and parse **only that file**; other files are never opened; find all definitions of the qualname (keys `q`, `q#2`, …); none → exit 1 (not found).
3. Without `--file`: parse all discovered files. Any problems → exit 2 (Q9-A). Candidate files > 1 → `AmbiguousSymbolError`, exit 2, output lists each candidate (path, lines, drifting yes/no) and the exact rerun command per candidate. Exactly one → proceed. None → exit 1.
4. Update every occurrence in the chosen file with the reason; message reports the count ("2 definitions updated"). Baseline is written once.
5. Path traversal protection preserved: `--file ../x.py` → rejected with exit 2.

### D8 — `init` (`run_init`)

Per module: strict-load the baseline → for each symbol by key: no record → write (new); record exists and `evaluate_symbol` flags it → **protect**; record differs but is not flagged → **stale**, leave untouched and report (FR-019); identical → nothing to do. With `--force --reason`: protected and stale records are overwritten and marked `acknowledged` with the reason. `--force` requires a non-blank reason, validated before any work (exit 2). `--dry-run` runs the same logic without writing and exits with the code the real run would. New symbols are always written first; if any record was protected, `InitIncompleteError(result)` is raised (API) / exit 1 (CLI) with the data intact. Output: counts of baselined / protected / stale / overwritten, protected symbols with file, and the next commands (`accept --symbol … --file …`, `refresh --reason …`, or `init --force --reason …`). Exit: 2 if any problem, else 1 if any protected, else 0. The sentence `Initialized baseline for N compliant symbols` is kept unchanged (item 5 wording fix is deferred; existing tests assert it).

### D9 — Stale baseline detection and `refresh` (US6)

`evaluate_symbol` returns a small result with three outcomes: `FLAG(SyncFailure)`, `STALE`, `OK`. `STALE` = some fingerprint plane differs from the record but the existing suppression rule (doc changed) applies, i.e. today's silent pass. `check`:
- keeps failures exactly as today (spec 002–004 evaluation results unchanged; SC-011);
- collects `stale: list[StaleRecord(file, qualname, key, changed_planes)]` and prints `PYDOCSYNC: N symbol(s) have updated documentation not yet recorded in the baseline` with file:symbol lines and the `refresh` command; exit unchanged (0) unless `--fail-on-stale` (exit 1, message `PYDOCSYNC003`).

`refresh --reason "<why>" [--symbol S] [--file F]` (`run_refresh`): strict-load baselines, evaluate, and re-record **only** `STALE` records (reason stored, status `acknowledged`); never touches `FLAG` records or unbaselined symbols; requires a non-blank reason (exit 2); no-op exit 0 when nothing is stale; API `refresh(root_dir, reason, *, symbol=None, file=None) -> int` (count). Combines with the unique-key scheme (D4) so duplicated names refresh per occurrence.

Residual limit (documented, FR-020): between step 2 and `refresh` the state is indistinguishable from a later code-only change; the notice and `--fail-on-stale` are how that window is made visible/enforceable.

---

## Contracts

### Exit codes (documented in README and `--help`)

| Command | 0 | 1 | 2 |
|---|---|---|---|
| `check` | synchronized (stale notice may print) | review required (`PYDOCSYNC001`), or stale with `--fail-on-stale` (`PYDOCSYNC003`) | any problem (corrupt baseline, unparseable/unreadable file) or usage error; wins over 1, both printed |
| `init` | baseline written, nothing protected | ≥1 record protected | problem, `--force` without reason, usage error |
| `refresh` | stale records re-recorded / nothing stale | — | blank reason, problem, bad `--file`/`--symbol` usage |
| `accept` | updated | symbol not found | ambiguity, unparseable file blocking uniqueness, bad `--file`, blank reason |

### Output shapes

- Success: existing line `PYDOCSYNC: All symbols synchronized with baseline.` (kept verbatim for existing tests) followed by `PYDOCSYNC: checked <F> files, <S> symbols.` and, when applicable, the stale notice.
- Problems: `PYDOCSYNC ERROR: <N> problem(s) prevented a complete check.` then one line per problem: `<kind>  <path>[:<line>]  <reason>`, sorted.
- `PYDOCSYNC001` hint: `pydocsync accept --symbol <qualname> --reason "<audit reason>" --file <path>` — `--file` placed after `--reason` so the existing test substring `accept --symbol parse_config --reason` still matches; `--root <root>` appended when the run used a non-default root.
- Ambiguity: candidate table plus one ready-to-run command per candidate.

### Python API (Q7-A)

```python
@dataclass
class SyncResult:            # existing fields kept
    is_synchronized: bool    # False if failures OR problems
    failures: list[SyncFailure]
    failure_count: int
    problems: list[Problem]  # new
    stale: list[StaleRecord] # new (passing but baseline out of date)
    files_checked: int       # new
    symbols_checked: int     # new

def check(root_dir=".") -> SyncResult                      # never raises for per-file/per-baseline problems
def init(root_dir=".", *, force=False, reason=None) -> int # raises InitIncompleteError if CLI would not exit 0
def init_report(root_dir=".", *, force=False, reason=None, dry_run=False) -> InitResult
def accept(symbol_qualname, reason, root_dir=".", *, file=None) -> bool  # raises AmbiguousSymbolError / SourceProblemsError
def refresh(root_dir=".", *, reason, symbol=None, file=None) -> int     # count of stale records re-recorded
```

New public names exported: `PyDocSyncError`, `Problem`, `ProblemKind`, `StaleRecord`, `InitResult`, `AmbiguousSymbolError`, `InitIncompleteError`, `SourceProblemsError`, `refresh`.

---

## Data Model

- **Baseline envelope**: unchanged (`schema_version: 1`). Only `pydocsync_version` now reads `0.4.0`.
- **Keys**: `name` (first definition, identical to v0.3.0) and `name#N` (later definitions). Records are otherwise unchanged; `review_reason` holds the `--force`/`accept` reason.
- **In-memory**: `Problem`, `CheckReport`, `InitResult(baselined, protected, overwritten, unchanged, problems, files, symbols)`, `AcceptResult(path, updated_count)`.

---

## Test Plan

New file `tests/test_silent_false_pass_regressions.py`, written **first** (red), one test per row of the spec's regression matrix; assertions cover stdout/stderr, exit code and API result:

| Spec case | Test focus |
|---|---|
| 1 corrupt baseline | `{ not json` → exit 2, path named; also empty file, list root, missing field, newer `schema_version`; several corrupt files all reported sorted |
| 2 sole syntax-error file | exit 2, `SyntaxError line N`; unreadable/non-UTF-8 |
| 3 good + broken file | drift and problem both printed, exit 2; `SyncResult.problems` populated, `is_synchronized` false |
| 4 `Command.handle` in two files | exit 2 with candidates and rerun commands; `--file` updates only that file; unique name unchanged; not-found exit 1; `--file ../x` rejected; unparseable-elsewhere without `--file` → exit 2 |
| 5a–5d duplicates | redefinition (first def changed → drift), getter changed / setter changed, `@overload`, `accept` updates all occurrences and prints the count, legacy baseline loads |
| 6 `init` | drift protected + exit 1 + `check` still fails; new module baselined alongside; `--force` without reason exit 2; with reason overwritten and reason stored; no-baseline unchanged; docstring-updated record refreshed silently (Q8-A) |
| 7 guards | existing 008 tests (migrations, `--root ..`, zero files) stay green |
| 8 | `--dry-run` writes nothing (file tree identical); coverage line and API counts |
| 9 | `fee()` three steps (spec matrix 9): stale notice at step 2, `refresh`, step 3 fails; without refresh notice at 2 and 3; `--fail-on-stale` exit 1 |
| 10 | `refresh` scope (flagged/new untouched, blank reason, docstring-only edit, no-op); `init` leaves stale untouched |
| 11 | Exception hierarchy: not `ValueError`, exit-code mapping, stray `ValueError` not reported as exit 2, `InitIncompleteError` data (baselined + protected) |
| 12 | `accept --file` never opens sibling files (unparseable sibling ignored) |

**Must-fail-on-0.3.0 gate** (FR-011): before implementation completes, check out tag `v0.3.0` into a temporary worktree, run the new test file against it, and record that every new behavioral test fails there (tests that only exercise new flags are expected to fail trivially; the substantive ones are the silent-pass cases). The result goes into `convergence_report.md`.

Scoped gate while developing: `pytest tests/test_silent_false_pass_regressions.py` plus the module test touched; full suite before completion (94 existing + new, 100 % required).

---

## Risks & Migration

| # | Risk | Mitigation |
|---|---|---|
| R1 | Stale (sticky) baseline: after a legitimate code+doc update the record differs forever and can mask later code-only changes (US6). `init` overwriting such records would erase that evidence. | D9 (notice, `--fail-on-stale`, `refresh`), D8 leaves stale records untouched, FR-020 documents the residual window. Evaluation results (specs 002–004) protected by keeping `check` failures unchanged (SC-011). |
| R2 | v0.3.0 stored the **last** definition of a duplicated name under the plain key. After upgrade, the first definition is compared against that record, and later definitions (`name#2`) have no record. | One-time review for files with duplicated names (possibly a `RULE_BASELINE_CODE_DRIFT` on `name`, or "new public symbol lacks documentation" on undocumented overload stubs). Cleared by one `accept --symbol name --file f --reason …` per name (updates all occurrences). Documented in release notes. **Spec amendment**: US5 scenario 5 / SC-008 must say "legacy baselines load without error; duplicated names may need one-time acknowledgment" instead of "passes on unchanged code". |
| R3 | Positional keys shift if a definition of a duplicated name is inserted/removed. | Shows up as drift/new symbol → review required anyway. Documented. |
| R4 | Behavior change: previously green CI can now go red (corrupt lockfile, broken file). | Intentional; release notes list the interim workaround (move non-parseable files under a default-ignored directory) until `--exclude` ships in 0.4.1 (spec 010). |
| R5 | Corpus tests call `scan_and_check` on real code (`pydocsync`, `tests/external_evaluation/corpus`). | If any file there is unparseable the test now fails loudly; treated as a finding at implementation, not papered over. |
| R6 | `AGENTS.md` (governance) and the consumer `SKILL.md` describe `accept`/`init` usage. | Not edited without explicit human permission; proposed text is listed in the convergence report. The reporter's own `CLAUDE.md` rule (use `--file` when a name repeats) matches the new contract. |
| R7 | Baselines for deleted symbols/files remain undetected (a different meaning of "stale"). | Out of scope (spec Boundaries). Naming: this plan uses "stale" only for records whose *documentation was updated but not recorded*. |
| R8 | Adding `refresh` and `--fail-on-stale` widens the CLI surface in a T3 release. | Both are small, covered by tests, and required to make US6 honest; default behavior of `check` is unchanged (Q11-A). |

---

## Delivery Order

Input for `/speckit-tasks` (TDD, each step under the scoped gate):

1. **Tests first**: write the regression file (red); run it against `v0.3.0` tag worktree to confirm failures.
2. **Refactor under green**: `_version.py`, `problems.py`, `evaluate.py` (D5) with no behavior change; existing 94 tests stay green.
3. **US1** strict baseline reader (D3), `PyDocSyncError` hierarchy and CLI exit mapping (item 10) → check reports baseline problems.
4. **US2** source loader (D2) → check/init/accept stop swallowing; exit-code precedence and problem report; `SyncResult.problems`.
5. **US5** unique keys (D4) in extract, baseline, evaluate.
6. **US3** `accept --file`, ambiguity, hint format (D7).
7. **US4** `init` protection, `--force --reason`, `--dry-run`, stale handling (D8).
7b. **US6** stale detection in `check`, `--fail-on-stale`, `refresh` command and API (D9).
8. Coverage line + API fields; README, `--help`, release notes, version bump (`0.4.0`).
9. Full suite, must-fail-on-0.3.0 evidence, `convergence_report.md`.

---

## Deviations from this plan (recorded during implementation)

| # | Plan said | What was built | Why |
|---|---|---|---|
| 1 | `BaselineManager.load_module_baseline` becomes strict (D3) | Added a separate strict `read_module_baseline`; the lenient `load_module_baseline` is unchanged and documented as legacy | A shipped test (`test_corrupted_baseline_lockfile_resilience`) asserts the lenient contract (`{}` for a corrupt file). Every evaluation and write path uses the strict reader; only that legacy method remains lenient. Candidate for removal in a later major version. |
| 2 | Result types in `problems.py` | New `pydocsync/results.py` (`SymbolRef`, `StaleRecord`, `Candidate`, `InitResult`, `AcceptResult`, `RefreshResult`); `CheckReport` lives in `cli.py` | Avoids a circular import (`report` ↔ results) and keeps `problems.py` about problems and errors. |
| 3 | `SourceProblemsError` / `BaselineProblemError` split | `SourceProblemsError` carries any list of problems (source or baseline); `BaselineProblemError` is raised by the strict reader and converted by callers | One exception for "problems prevented a complete evaluation". |
| 4 | Not planned | **Extractor fix**: a class whose body is only a docstring is fingerprinted using a `pass` placeholder body (spec FR-021) | Found when the new loader reported valid files of this repo as unparseable; verified on the v0.3.0 source that such files were silently skipped entirely. |
| 5 | Not planned | `refresh --file <missing>` exits 2 (usage error); `accept --file <missing/excluded>` keeps exit 1 (not found) | `accept`'s exit-1 contract was fixed by the spec; a nonexistent `--file` for `refresh` has no "symbol not found" meaning. |
| 6 | Not planned | When only stale symbols exist, the first success line reads `PYDOCSYNC: No symbol requires documentation review.` instead of "All symbols synchronized with baseline." | The old sentence would be untrue while records are out of date. The clean-run line and coverage line are unchanged. |
| 7 | Not planned | `accept`'s blank-reason validation stays in the CLI layer (as in v0.3.0); the Python `accept()` does not validate the reason | Not in scope; noted in the convergence report as an observation. |
| 8 | `tests/test_public_api.py` unchanged | Updated: approved export set extended by the spec-009 names; version assertion `0.4.0` | The test pins the public surface, which this feature deliberately extends. |
