# Tasks: 009-silent-false-pass-hardening

**Input**: [`spec.md`](spec.md), [`plan.md`](plan.md)  
**Status**: Implemented (T046 declined by owner)  
**Tests**: REQUIRED (spec FR-011): every behavioral task is preceded by a failing test.  
**Test runner**: `.\.venv\Scripts\pytest.exe` (scoped gate while developing; full suite at phase ends)  
**Prerequisite reading at implementation time**: `.specify/memory/standards/coding_standards.json` → `_task_index`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1 corrupt baseline · US2 unparseable files · US3 `accept` · US4 `init` · US5 same-file duplicates · US6 stale baseline · FND foundational · DOC release
- Tier T3 rules apply: no commit of implementation until the previous phase is green.

Open decision affecting tasks: **Q11** (default strictness for stale). Tasks assume plan default **A** (opt-in `--fail-on-stale`).

---

## Phase 0: Baseline Safety Net (before any code change)

- [x] T001 Run the full suite on unmodified `main`; record the count (expected 94/94) and duration in `convergence_report.md` notes.
- [x] T002 Create a temporary git worktree of tag `v0.3.0` in the scratchpad (not in the repo) for the must-fail-on-0.3.0 gate (FR-011).
- [x] T003 Confirm the two corpus-based tests parse cleanly (`tests/external_evaluation/corpus`, `pydocsync/`): scan for files the new loader would report as problems (plan risk R5). Record findings; do not change corpus.

## Phase 1: Tests First (red)

**Goal**: one failing regression per spec-matrix row. New file `tests/test_silent_false_pass_regressions.py` (helpers: temp project builder, CLI runner via `subprocess` like existing tests).

- [x] T004 [US1] Tests: corrupt lockfile (`{ not json`), empty file, list root, record with missing field, record with unknown field, newer `schema_version`; several corrupt files reported sorted; missing lockfile still passes as before.
- [x] T005 [P] [US2] Tests: sole syntax-error file; good + broken file with drift (exit 2, both printed, API `problems` populated, `is_synchronized` false); non-UTF-8 file; `SyntaxError line N` text; broken file in an ignored dir is never reported.
- [x] T006 [P] [US3] Tests: `Command.handle` in two files (exit 2, candidates listed, rerun command per candidate, nothing written); `--file` updates only that file; unique name unchanged; not found exit 1; `--file ../x.py` rejected; unparseable sibling without `--file` exit 2; **with** `--file` an unparseable sibling is not read; failure-report hint contains `--file` and still contains `accept --symbol X --reason`.
- [x] T007 [P] [US5] Tests: redefined function (first definition changed → drift); property getter changed / setter changed (own symbol reported); `@overload` stubs + implementation; `accept` updates all occurrences and prints the count; `init` count equals stored records; v0.3.0-format baseline loads without error.
- [x] T008 [P] [US4] Tests: drift protected + exit 1 + `check` still fails; new module baselined alongside; `--force` without/blank reason exit 2; `--force --reason` overwrites and stores reason; no baseline unchanged; stale record left untouched by `init`; `--dry-run` writes nothing (tree snapshot equal) and returns the real exit code; `InitIncompleteError` carries baselined + protected data; `init_report()` returns the same without raising.
- [x] T009 [P] [US6] Tests: `fee()` three steps (stale notice at step 2; after `refresh`, step 3 fails with `PYDOCSYNC001`; without `refresh`, notice at steps 2 and 3); `--fail-on-stale` exit 1; `refresh` never touches flagged/new records; blank reason exit 2; docstring-only edit is stale; no-op exit 0; `--symbol`/`--file` narrowing; `SyncResult.stale`.
- [x] T010 [P] [FND] Tests: `PyDocSyncError` hierarchy (not `ValueError`; `exit_code` per class); CLI exit codes via the base; a stray `ValueError` raised by monkeypatched internals is **not** reported as exit 2; success output includes `checked N files, M symbols` and the existing `All symbols synchronized with baseline.` line; API `SyncResult` exposes counts.
- [x] T011 Run the new file against the `v0.3.0` worktree (T002); record which tests fail and why. Substantive silent-pass tests must fail there; tests for new flags fail trivially and are marked as such in the report.
- [x] T012 Run the new file on `main`: all new tests red, existing 94 green.

**Checkpoint**: red bar is accurate. Owner review of test intent optional here.

## Phase 2: Foundational Refactor (no behavior change)

- [x] T013 [FND] Add `pydocsync/_version.py` (`__version__ = "0.3.0"` for now); `__init__.py` and `baseline.py` read it (envelope `pydocsync_version`).
- [x] T014 [FND] Add `pydocsync/problems.py`: `ProblemKind`, `Problem`, `PyDocSyncError` base (+ `exit_code`), subclasses per plan D1. Module header docstring (`WHAT IS THIS? / WHY DO WE NEED THIS?`), 100 % annotations.
- [x] T015 [FND] Add `pydocsync/evaluate.py`: extract the per-symbol block from `scan_and_check` into `evaluate_symbol(sym, record, classifier)` returning FLAG / STALE / OK (STALE not yet consumed). Rewire `scan_and_check` to it. **Gate**: existing 94 tests stay green, byte-identical failure output.
- [x] T016 [P] [FND] `discovery.py`: add `is_path_excluded(rel_path, path_filter)` and `NoSourceFilesError(PyDocSyncError, ValueError)`; existing zero-files tests unchanged.
- [x] T017 [FND] Replace `main()`'s `(FileNotFoundError, NotADirectoryError, ValueError)` catches by `PyDocSyncError` + `(FileNotFoundError, NotADirectoryError)` with a single exit-code mapping helper (item 10). **Gate**: full suite green; T010 hierarchy tests green.

## Phase 3: US1 — Strict Baseline Reader (P1)

- [x] T018 [US1] `baseline.py`: strict `load_module_baseline` (missing → `{}`; empty/invalid JSON/non-object/bad record/unknown or missing fields/wrong types/newer schema → `BaselineProblemError(Problem)`); legacy envelope-less files still load. Load once / save once per module helper.
- [x] T019 [US1] `run_check` (new, in `cli.py`): collect baseline problems per module, continue with remaining modules; `scan_and_check` wrapper raises `SourceProblemsError`/`BaselineProblemError` carrying all problems if any exist.
- [x] T020 [US1] `report.py`: problem report (`PYDOCSYNC ERROR: N problem(s) prevented a complete check.` + sorted lines). CLI: problems → exit 2. **Gate**: T004 green.

## Phase 4: US2 — Source Loader (P1)

- [x] T021 [US2] Loader helper (`load_symbols`) catching only `OSError`, `UnicodeDecodeError`, `SyntaxError`, `ValueError`, `RecursionError`; `SyntaxError line N` message. No bare `except Exception` remains in `cli.py` (grep gate).
- [x] T022 [US2] `run_check` uses the loader; exit-code precedence (problems win over drift, both printed); `SyncResult.problems`, `is_synchronized` false when problems; `check()` never raises for per-file problems.
- [x] T023 [US2] `init`/`accept` paths use the loader (problems reported, `init` never claims a complete baseline). **Gate**: T005 green, plus T003 findings resolved.

## Phase 5: US5 — Same-File Duplicate Keys (P1)

- [x] T024 [US5] `ast_extract.py`: add `key` to `SymbolRepresentation` (default `qualname`); post-pass assigns `name`, `name#2`, `name#3` in source order.
- [x] T025 [US5] Baseline lookup/store, `evaluate_symbol` inputs and `run_check` use `key`; display and `accept --symbol` matching keep `qualname`. **Gate**: T007 check-side tests green; existing suite green.

## Phase 6: US3 — `accept --file` and Ambiguity (P1)

- [x] T026 [US3] `run_accept`: validate `--file` (inside root, not excluded, exists); with `--file` parse only that file (no directory walk, no zero-files check).
- [x] T027 [US3] Without `--file`: parse all; problems → `SourceProblemsError` (exit 2, Q9); >1 candidate file → `AmbiguousSymbolError` (exit 2) with candidates (path, lines, drifting?) and one rerun command per candidate; none → exit 1.
- [x] T028 [US3] Update all same-named occurrences (`q`, `q#2`, …) in the chosen file in one baseline write; message reports the count.
- [x] T029 [US3] `report.py`: `PYDOCSYNC001` hint `accept --symbol X --reason "<audit reason>" --file <posix path>` (+ `--root` when non-default). CLI/API: `--file`, `accept(..., file=None)`. **Gate**: T006 and accept part of T007 green; existing `accept --symbol parse_config --reason` assertion still passes.

## Phase 7: US4 — `init` Protection (P1)

- [x] T030 [US4] `run_init` per plan D8: new → write; flagged → protect; stale → untouched + reported; identical → nothing; `InitResult` (baselined, protected, stale, overwritten, problems, files, symbols).
- [x] T031 [US4] `--force --reason` (reason validated up front, stored per overwritten record, exit 2 if blank); `--dry-run` (same logic, no writes, real exit code).
- [x] T032 [US4] Output: counts, protected list, next commands; exit 1 if protected, 2 if problems. API: `init()` raises `InitIncompleteError(result)` after writing new symbols; `init_report()` returns data. Keep `Initialized baseline for N compliant symbols` wording. **Gate**: T008 green.

## Phase 8: US6 — Stale Baseline (P1)

- [x] T033 [US6] `run_check` collects `StaleRecord`s from `evaluate_symbol`; prints the stale notice; `SyncResult.stale`; failures list unchanged (evaluation suites 002–004 unchanged, SC-011).
- [x] T034 [US6] `check --fail-on-stale` → exit 1, `PYDOCSYNC003` message with the `refresh` command.
- [x] T035 [US6] `refresh` command + `refresh()` API: re-record only stale records, non-blank reason, `--symbol`/`--file`, count, no-op exit 0, never touches flagged/unbaselined. **Gate**: T009 green; run specs 002–004 evaluation suites explicitly and confirm identical metrics.

## Phase 9: Coverage, Docs, Release (0.4.0)

- [x] T036 [FND] Coverage line `PYDOCSYNC: checked <F> files, <S> symbols.`; `SyncResult.files_checked`/`symbols_checked`. Existing success line kept verbatim.
- [x] T037 [P] [DOC] README: exit-code table, new flags/commands, problems/stale semantics, duplicate-name keys and one-time migration note, residual-limit statement (FR-020), interim workaround for non-parseable files until `--exclude` (0.4.1). CLI `--help` text.
- [x] T038 [P] [DOC] Release notes (0.4.0): behavior changes that can turn green CI red, the interim workaround, migration for duplicated names, what is deliberately deferred (spec 010).
- [x] T039 [DOC] Bump `0.4.0` in `_version.py` and `pyproject.toml`; `__init__.py` public names and docstring updated.
- [x] T040 [DOC] Create `ideas/future_features.md` with deferred items 5–9 and 11 (`--exclude`, `--require-baseline`, config, `--path`, pre-commit hook) — **only after owner OK** (file does not exist yet).

## Phase 10: Convergence

- [x] T041 Full suite: existing 94 + new tests, 100 % pass (Constitution V). Capture duration.
- [x] T042 Re-run the new tests against the `v0.3.0` worktree; write the evidence table into `convergence_report.md` (FR-011, SC-005).
- [x] T043 Reproduce each reporter scenario manually end-to-end (scratchpad projects): items 1–4, duplicates, `fee()` three steps; record outputs.
- [x] T044 `/speckit-converge`: verify code vs spec/plan; list any deviations; produce `convergence_report.md`.
- [x] T045 Governance follow-ups **requiring explicit owner permission** (not done autonomously): `AGENTS.md` Implemented-ledger entry for 009; consumer `SKILL.md` updates (`accept --file`, `refresh`, `init` protection, stale notice).
- [x] T046 (not required: owner declined; nothing drafted or sent) Prepare (do not send) the reply to the reporter: items 1–4 fixed with regression tests, extra findings (duplicates, sticky baseline) and the residual-limit statement; owner approves before anything is posted.

---

## Dependencies & Order

```text
Phase 0 → Phase 1 (tests, red) → Phase 2 (refactor, green) → 3 (US1) → 4 (US2) → 5 (US5) → 6 (US3) → 7 (US4) → 8 (US6) → 9 → 10
```

- US5 precedes US3/US4 because both key baseline records by `key`.
- US4 and US6 share `evaluate_symbol` (T015); US6 completes the STALE consumption that US4 already tolerates.
- T007/T008/T009 tests were written first but only pass after their phases; each phase's gate names the tests that must turn green.

## MVP Cut (if the release must be split)

Phases 0–4 + T017 + T036 give items 1 and 2 plus exception hygiene (a shippable 0.4.0-rc1). Phases 5–8 complete items 3, 4, duplicates and stale baseline. Splitting is not recommended by the plan; listed only as a fallback.
