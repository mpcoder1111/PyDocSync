# Convergence Report: 009-silent-false-pass-hardening

**Date**: 2026-09-20  
**Status**: Implemented; **awaiting owner review**. Nothing committed, tagged or released.  
**Spec**: [`spec.md`](spec.md) | **Plan**: [`plan.md`](plan.md) | **Tasks**: [`tasks.md`](tasks.md)

---

## 1. Test evidence

| Check | Result |
|---|---|
| Baseline before any change (`main`, v0.3.0 code) | 94 passed |
| New regression file against the **real v0.3.0 source** (git tag `v0.3.0` worktree, import path and `__version__ == 0.3.0` verified) | **52 failed, 7 passed** of 59 |
| Same file on the new code | **59 passed** |
| Full suite on the new code | **153 passed** (94 existing + 59 new) |

The 7 tests that pass on v0.3.0 are intentional compatibility guards (behavior that must NOT change): missing lockfile is not a problem; legacy envelope-less lockfile loads; broken file in an ignored directory is not reported; `accept` of a unique name needs no `--file`; property setter change is detected; a v0.3.0-style baseline for duplicated names loads without error; `init` without an existing baseline is unchanged.

Weak tests found and fixed during red-bar validation: four tests initially passed on v0.3.0 only because argparse rejected the unknown flag with exit 2 (or echoed a filename containing the asserted word). They now assert the actual message (`non-empty`, `outside the project root`).

## 2. Requirement traceability

| Requirement | Status | Evidence |
|---|---|---|
| FR-001…003 corrupt/unsupported baseline → exit 2, missing ≠ corrupt | Done | `test_corrupt_baseline_makes_check_fail[5 kinds]`, unknown field, sorted multi-report, missing lockfile, API problems |
| FR-004…006 unparseable/unreadable source reported, run continues | Done | syntax error, `SyntaxError line N`, good+broken with drift, non-UTF-8, ignored dir, `init` |
| FR-007…009 `accept` ambiguity, `--file`, unique name unchanged | Done | 9 tests incl. traversal, unparseable sibling with/without `--file`, API `AmbiguousSymbolError` |
| FR-010, 010a init protection, `--force --reason`, precedence | Done | 8 tests; drift+problem exit 2 with both printed |
| FR-010b hint includes `--file` | Done | `test_failure_report_hint_includes_file` |
| FR-010c same-file duplicates (`name`, `name#2`…) | Done | redefinition, getter/setter, `@overload`, count, `accept` covers all + count |
| FR-011 regression tests fail on v0.3.0 | Done | Section 1 |
| FR-012 `problems` as data, typed errors, `PyDocSyncError` not a `ValueError` | Done | hierarchy test; stray `ValueError` not reported as exit 2; `InitIncompleteError` data |
| FR-013 README / `--help` / upgrade notes | Done (README, CLI help, and the consumer SKILL.md after owner permission) | README sections "After a Documented Change", "Nothing Is Skipped Silently", "Upgrading to 0.4.0" |
| FR-014, 015 coverage line, `init --dry-run` | Done | coverage test, dry-run test |
| FR-016…019 stale detection, `--fail-on-stale`, `refresh`, `init` leaves stale untouched | Done | `fee()` three-step test, 8 further US6 tests |
| FR-020 residual limit documented | Done | README warning block; `test_without_refresh_the_stale_notice_is_visible_on_every_check` documents the limit |
| FR-021 valid file with docstring-only class evaluated | Done | `test_file_with_docstring_only_class_is_evaluated_not_skipped` |
| SC-011 evaluation results (specs 002–004) unchanged | Done | those suites are part of the 153 passing tests |
| SC-012 no CLI-wide `ValueError` catch | Done | the one remaining `except ValueError` in `cli.py` is the narrow guard around `Path.relative_to` (outside-root detection) |

## 3. Findings during implementation (beyond the field report)

1. **Docstring-only class silently skipped the whole file** (FR-021). Verified on the real v0.3.0 source: `class AppError(Exception): """Doc."""` plus a drifted function in the same file gave `init` = 0 symbols and `check` = exit 0. Fixed in `ast_extract.py`. Likely the most widespread silent pass of all.
2. **Sticky doc baseline** (US6). This repository's own baseline had 16 stale symbols when the new check first ran on it, some dating back to 0.3.0.
3. `accept()` (Python API) does not validate a blank reason; only the CLI does. Left unchanged (out of scope); worth a follow-up.
4. The consumer `SKILL.md` refers to "the mandatory PyDocSync procedure in `AGENTS.md`", but `AGENTS.md` contains no such procedure text.
5. `init` output still says "compliant symbols" although it also counts undocumented symbols (field-report item 5, deferred; tests pin the wording).

## 4. Dogfooding (this repository's own baseline)

`pydocsync check` on the repository, run after the implementation: 7 review obligations (my own code changes) and 16 stale records. Handled with the new workflow: 4 `accept --file` (reviewed, docstrings still accurate; specific reasons stored), 1 `refresh` (16 stale symbols; reason records that two of them predate this work), then `init` for the three new modules. Final state: `check` and `check --fail-on-stale` both exit 0 (`checked 14 files, 133 symbols`). The updated files under `.project/pydocsync/` are uncommitted changes, as is everything else.

## 5. Follow-ups completed after owner sign-off (2026-09-20)

| Item | Result |
|---|---|
| `ideas/future_features.md` | Created (deferred items 5-9 and 11, findings from this spec; spec 010 reserved for `--exclude`/`--require-baseline`; MCP server considered and deferred by the owner, see the backlog) |
| `AGENTS.md` Implemented-ledger entry | Added for 009 (newest first) |
| Consumer `SKILL.md` | Updated: version, `init` protection, exit codes/problems, `accept --file`, new `refresh`, API and exceptions |
| Reply to the reporter | Not required (owner) |

Still not done, by design: commit, tag `v0.4.0`, wheel, README install instructions and status badge (still 0.3.0 text until release), spec 010.

## 6. Cleanup

The temporary `v0.3.0` git worktree used for the must-fail gate lived in the scratchpad and was removed after the evidence run.
