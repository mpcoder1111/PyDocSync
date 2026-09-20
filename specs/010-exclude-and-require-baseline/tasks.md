# Tasks: 010-exclude-and-require-baseline

**Input**: [`spec.md`](spec.md), [`plan.md`](plan.md)  
**Status**: Implemented  
**Tests**: REQUIRED (FR-016): every behavioral task is preceded by a failing test.  
**Runner**: `.\.venv\Scripts\python.exe -m pytest` (scoped while developing; full suite at phase ends)  
**Before coding**: re-read `.specify/memory/standards/coding_standards.json` → `writing_new_python_module` (header docstring `WHAT IS THIS? / WHY DO WE NEED THIS?`, Google-style docstrings, full type annotations, no `Optional`/`Union`).

## Format: `[ID] [P?] [Story] Description`

- **[P]** parallelizable · **[Story]**: US1 `--exclude` · US2 config file · US3 default ignores · US4 `--require-baseline` · US5 visibility · US6 pre-commit · FND foundation · DOC docs/release

---

## Phase 0: Safety Net

- [x] T001 Confirm branch `feat/0.4.0-hardening`, clean tree, 153 tests green (baseline for FR-015).
- [x] T002 Create a temporary git worktree of commit `4f00c2a` in the scratchpad for the must-fail gate (FR-016); remove it at the end.

## Phase 1: Tests First (red)

New file `tests/test_exclusions_and_require_baseline.py` (helpers like the 009 suite: `run_cli`, `write`, lockfile path).

- [x] T003 [FND] Pattern unit tests (table-driven): all valid forms × files/dirs × depths; `**` start/middle/end; no partial-name match; case sensitivity; every invalid form (empty, whitespace-padded, `!x`, `#x`, `a\b`, `[x]`, `a**b`, `***`, `a//b`, `..`) raises `InvalidArgumentError` quoting the pattern. Add an independent segment-wise reference matcher and cross-check it against the regex matcher on a generated path set.
- [x] T004 [P] [US1] CLI tests: template file excluded (exit 0, `excluded by rules: 1 path(s).`); same file without flag exit 2 (*guard*); repeated `--exclude`; `init`/`refresh`/`accept` ignore excluded files and leave their lockfiles byte-identical; `accept --file <excluded>` exit 1 naming the rule; `refresh --file <excluded>` exit 2; all files excluded → exit 2 zero-files message mentioning exclusions; `init --dry-run` honours exclusions.
- [x] T005 [P] [US2] Config tests: bare `check` driven by `.pydocsync.json` (same output as flags); read from `--root` not cwd (`--root ..` case); union with flags; `default_excludes: false`; `require_baseline: true`; errors → exit 2 naming `.pydocsync.json` (invalid JSON, non-object, unknown key, wrong type, invalid pattern); missing file = no config (*guard*); errors raised before any write.
- [x] T006 [P] [US3] Default-ignore tests: `node_modules/` and `site-packages/` skipped (also with `--no-default-excludes`); `pkg/build/core.py` flagged only with `--no-default-excludes`; dot-dirs, `__pycache__`, `venv` still skipped; `DEFAULT_IGNORED_DIRS` superset of the 0.3.0 set and contains the new names.
- [x] T007 [P] [US4] `--require-baseline` tests: no folder + public symbols → exit 2, `BASELINE_MISSING` in API problems, message names `pydocsync init`; empty folder same; one lockfile → pass; no public symbols → pass; config `require_baseline`; combined with drift → exit 2 with both printed; no flag → unchanged (*guard*).
- [x] T008 [P] [US5] Visibility tests: unmatched pattern warning on stderr naming pattern and source, exit unchanged; no extra lines when no rule applied (*guard*); `SyncResult.excluded_count` / `unmatched_excludes`; API keyword arguments and default config reading.
- [x] T009 [P] [US6] Hook tests: `.pre-commit-hooks.yaml` has the required keys (`id: pydocsync-check`, `entry: pydocsync check`, `language: python`, `types: [python]`, `pass_filenames: false`); executing the `entry` in a temp project gives `check`'s exit codes; extra args (`--fail-on-stale`) pass through.
- [x] T010 Run the new file against the `4f00c2a` worktree; record which tests fail and why (substantive ones must fail; *guard* rows pass).
- [x] T011 Run the new file on the working tree: all new behavioral tests red, the 153 existing tests green.

## Phase 2: Patterns (FND)

- [x] T012 [FND] `pydocsync/patterns.py`: `ExcludePattern`, `compile_pattern`, matching per plan D1. **Gate**: T003 green.

## Phase 3: Errors and Config (US2)

- [x] T013 [FND] `problems.py`: `ProblemKind.BASELINE_MISSING`, `ConfigError` (exit 2), `FileExcludedError` (exit 1); export from `__init__` (update `tests/test_public_api.py` export set deliberately).
- [x] T014 [US2] `pydocsync/config.py`: `Settings`, `load_settings` with all validation and precedence per plan D2. **Gate**: config-error and precedence tests green.

## Phase 4: Discovery (US1, US3)

- [x] T015 [US3] `discovery.py`: split ALWAYS/CONVENTION sets, keep `DEFAULT_IGNORED_DIRS` as the superset (adds `node_modules`, `site-packages`), extend `PathFilter`, implement `discover()` with pruning/counting/matched-pattern tracking, `exclusion_reason()`, wrapper `discover_python_files`, zero-files message. **Gate**: T006 green, all 153 existing tests still green, package-scan budget test green.

## Phase 5: CLI wiring (US1, US2, US4, US5)

- [x] T016 [US1] Shared `--exclude` / `--no-default-excludes` options on the four commands (help text with syntax examples); `run_*` take `exclude`/`default_excludes`, load settings once, call `discover`.
- [x] T017 [US1] `accept --file` / `refresh --file` use `exclusion_reason`; `FileExcludedError` (accept, exit 1) and `InvalidArgumentError` (refresh, exit 2) with rule-naming messages.
- [x] T018 [US4] `check --require-baseline` (and config): `BASELINE_MISSING` problem after the scan per plan D4; guidance text names `pydocsync init`.
- [x] T019 [US5] Visibility: `run_check` returns `excluded_count`/`unmatched_excludes`; output line and stderr warnings per plan D5 (existing lines unchanged); warnings also on `init`/`refresh`/`accept`. **Gate**: T004, T005, T007, T008 green.

## Phase 6: API and Hook (US6)

- [x] T020 [FND] `api.py`: `SyncResult` new fields, keyword arguments on `check/init/init_report/accept/refresh`, default config reading; `report.py` formatters.
- [x] T021 [US6] `.pre-commit-hooks.yaml`. **Gate**: T009 green.

## Phase 7: Docs and Governance (DOC)

- [x] T022 [P] [DOC] README: Excluding files, config schema, `--require-baseline`, pre-commit snippet, exit-code tables; rewrite "Upgrading to 0.4.0" (remove the 0.4.1 statements); `--help` review.
- [x] T023 [P] [DOC] Consumer `SKILL.md`: exclusion workflow and the agent guardrail (exclusions only for non-Python/generated/vendored files; never to silence real drift; output shows what was excluded; `.pydocsync.json` is read automatically).
- [x] T024 [P] [DOC] `AGENTS.md` ledger entry for 010; `ideas/future_features.md`: remove delivered items, add `--path`, `--include`/negation, TOML/`--config`.
- [x] T025 [DOC] Update spec 009 documents where they promise a 0.4.1 `--exclude` (convergence report, plan R4, spec Q5 text): add a short pointer "delivered in 0.4.0 by spec 010" (history stays intact).

## Phase 8: Convergence

- [x] T026 Full suite green (153 + new); scan-budget test green.
- [x] T027 Re-run the new file on the `4f00c2a` worktree; write the evidence table into `convergence_report.md` (FR-016, SC-005); remove the worktree.
- [x] T028 Manual end-to-end runs (scratchpad projects): template file with flag and with config; bare `check` with config; invalid pattern and invalid config messages; `--require-baseline`; unmatched-pattern warning; record outputs.
- [x] T029 Dogfood: `pydocsync check --fail-on-stale` on this repository; resolve flagged symbols with `accept --file` (reviewed reasons), stale with `refresh`, new modules with `init`; end at exit 0.
- [x] T030 `convergence_report.md` for 010 (traceability FR-001…FR-024, deviations from plan, findings).
- [x] T031 Commit on `feat/0.4.0-hardening` (message with the required co-author trailer); no push, no tag.

---

## Dependencies

```text
0 → 1 (red) → 2 (patterns) → 3 (errors/config) → 4 (discovery) → 5 (cli) → 6 (api/hook) → 7 (docs) → 8
```

- `discovery.py` depends on `patterns.py` and `config.py` (via `Settings.path_filter()`).
- `run_*` wiring (phase 5) depends on the reworked discovery.
- Docs (phase 7) only after behavior is final so the documented output equals the real output.

## Cut lines if the release must be trimmed

Phases 0–5 deliver `--exclude`, config, default ignores, `--require-baseline` and visibility (the reporter's needs). Phase 6's hook is small and independent; phase 7 is mandatory before the commit.
