# Convergence Report: 010-exclude-and-require-baseline

**Date**: 2026-09-20  
**Status**: Implemented and committed on branch `feat/0.4.0-hardening` (not pushed, not tagged).  
**Spec**: [`spec.md`](spec.md) | **Plan**: [`plan.md`](plan.md) | **Tasks**: [`tasks.md`](tasks.md)

---

## 1. Test evidence

| Check | Result |
|---|---|
| Before starting (spec-009 commit `4f00c2a`) | 153 passed |
| New file `tests/test_exclusions_and_require_baseline.py` against the **spec-009 commit** (git worktree, import path verified) | **115 failed, 2 passed** of the 117 tests present at the gate run; the 118th (added afterwards, imports the new `pydocsync.config`) fails there by construction |
| Same file on the new code | **118 passed** |
| Full suite on the new code | **271 passed** (153 existing + 118 new), including the 200 ms package-scan budget test |

The 2 tests that pass on the spec-009 commit are the intended guards (behavior that must not change): a missing `.pydocsync.json` is not an error, and the output is byte-identical when no rule applies.

Weak test caught during red-bar validation: `test_require_baseline_fails_for_an_empty_baseline_folder` initially passed on the old code only because argparse rejected the unknown `--require-baseline` flag with exit 2. It now asserts `BASELINE_MISSING`. During the gate run the hook manifest had been copied into the old worktree by mistake, which made two hook tests pass there; the copy was removed and the honest count recorded above.

The pattern translator is cross-checked against an independent regex-free segment-wise matcher over ~100 000 pattern/path/kind combinations (`test_regex_matcher_agrees_with_independent_reference_matcher`).

## 2. Requirement traceability

| Requirement | Status | Evidence |
|---|---|---|
| FR-001…004 `--exclude` on all commands, pruning, excluded files untouched | Done | US1 tests (template scenario, repeated flags, lockfiles byte-identical, dry-run parity) |
| FR-002 strict pattern syntax with quoted errors | Done | 14 invalid forms × unit test and × CLI (exit 2, no scan, no `.project`) |
| FR-005 `accept --file <excluded>` exit 1 naming the rule | Done | pattern and default-directory cases; API `FileExcludedError` |
| FR-006 everything excluded → zero-files error mentioning exclusions | Done | test |
| FR-007, 008 config file: validation, union with flags, `--root` resolution | Done | 8 invalid-config kinds × `check`/`init`; union; `--root ..` |
| FR-009 default ignores; `DEFAULT_IGNORED_DIRS` superset | Done | node_modules/site-packages always skipped; `pkg/build` only with `--no-default-excludes`; dot-dirs/venv/`__pycache__` stay skipped |
| FR-010, 021 `--require-baseline` | Done | absent/empty folder, with lockfile, no public symbols, config key, with drift (both printed), API problem kind, message names `pydocsync init` |
| FR-011, 012, 024 visibility: excluded line, unmatched warning naming the source | Done | tests incl. config-sourced pattern; `init` warns too |
| FR-013 API keyword arguments and `SyncResult` fields | Done | `excluded_count`, `unmatched_excludes`, config read by default |
| FR-014 pre-commit manifest | Done, validated structurally and by executing its entry | manifest keys test; entry run with `--fail-on-stale` |
| FR-015 no change without new flags | Done | the 153 existing tests; byte-identical output guard |
| FR-016 regression tests fail on the spec-009 code | Done | Section 1 |
| FR-017, 022 docs | Done | README (Excluding Files, Strict Baseline Mode, pre-commit, exit codes, upgrade notes), `--help` texts, consumer SKILL.md with the agent guardrail |
| FR-018 no dependency, performance | Done | stdlib only; budget test green |
| FR-019 `init --dry-run` honours exclusions | Done | test |
| FR-020 version/upgrade notes: everything in 0.4.0 | Done | README "Upgrading to 0.4.0" |
| FR-023 same exclusion rules for discovery and single-file validation | Done | Two code paths (the walk in `discover`, and `exclusion_reason` for `accept/refresh --file`) built on the same primitives (`should_ignore_dir`, `ExcludePattern.matches`); `test_discovery_and_single_file_validation_apply_the_same_rules` cross-checks them on a real tree |

## 3. Deviations from the plan and additions

| # | Item |
|---|---|
| 1 | **New requirement found by manual testing (FR-025)**: the suggested `accept` / `refresh` command in `PYDOCSYNC001`, stale and ambiguity reports must carry `--no-default-excludes` when the run used it, otherwise the hint is rejected (a file in `pkg/build/` is excluded by default). Implemented via an `extra_args` parameter of the report formatters and covered by `test_hints_keep_no_default_excludes_so_they_are_runnable` (which also executes the hinted command). |
| 2 | Unmatched-pattern warnings are also emitted by `accept` (through an out-parameter), but only when discovery runs (i.e. without `--file`). |
| 3 | Error text refined: "Supported forms: ..." with `backslash` spelled out (readability for agents). |
| 4 | `--require-baseline` counts any `*.json` under `<root>/.project/pydocsync` as a lockfile; the check runs after the scan so that it can be combined with drift/problems (exit 2, everything printed). |

## 4. Dogfooding

`pydocsync check --fail-on-stale` on this repository after implementation: 8 flagged symbols (private helpers and two classes whose docstrings remained accurate: reviewed and recorded with `accept --file` and specific reasons) and 21 stale records (docstrings updated with the code: `refresh`), then `init` for the two new modules. Final: exit 0, `checked 16 files, 154 symbols`.

## 5. Not done, by design

| Item | Note |
|---|---|
| Tag `v0.4.0`, wheel, README install instructions and status badge | Owner's release step; code, `pyproject.toml` and baseline envelope say 0.4.0, install text still says 0.3.0 |
| Push | Not requested |
| Execution under the real `pre-commit` tool | Not installed here; manifest and entry command are tested |
| `--path`, `--include`/negation, TOML config | Recorded in `ideas/future_features.md` with reasons |

The temporary spec-009 git worktree used for the must-fail gate lived in the scratchpad and was removed after the final evidence run.
