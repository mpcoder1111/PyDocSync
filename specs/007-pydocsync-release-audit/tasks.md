# Tasks: 007-pypydocsync-release-audit

**Input**: Design documents from `specs/007-pypydocsync-release-audit/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`, `US4`)

---

## Phase 1: Baseline Schema Versioning & Lockfile Upgrade (Priority: P1)

- [x] T001 [US1] Update `packages/pypypydocsync/pypydocsync/baseline.py` with `schema_version: 1` envelope structure and backward compatibility reader
- [x] T002 [US1] Re-initialize project baseline lockfiles in `.project/pypypydocsync/` with schema version 1

---

## Phase 2: Security Boundaries & Input Validation (Priority: P1)

- [x] T003 [US2] Update `packages/pypypydocsync/pypydocsync/cli.py` to enforce non-empty `reason.strip()`, valid symbol lookup, and return code 2 on empty reason
- [x] T004 [US2] Author `packages/pypypydocsync/tests/test_security_boundaries.py` testing blank reason rejection, non-existent symbol rejection, and corrupted lockfile resilience

---

## Phase 3: AST Normalization Invariants & Determinism (Priority: P1)

- [x] T005 [US3] Author `packages/pypypydocsync/tests/test_ast_invariants.py` verifying location metadata stripping and `ctx` semantic preservation
- [x] T006 [US3] Align Python 3.10+ support statements across `pyproject.toml` and documentation

---

## Phase 4: Documentation, Trust Model & Policy Polish (Priority: P1)

- [x] T007 [US4] Update `packages/pypypydocsync/README.md` documenting:
  1. The 3 Drift Layers (Ruff/pydoclint vs Mypy vs PyDocSync)
  2. Symbol Selection & Exclusion Policy
  3. Trust & Authorization Boundary of `pypypydocsync accept`
  4. Public vs Internal API stability declarations
  5. Scoped empirical metrics wording

---

## Phase 5: Regression Verification & Release Candidate Build

- [x] T008 Re-run full test suite across the repository (88 tests passing 100%)
- [x] T009 Compile clean wheel `pypypydocsync-0.2.0-py3-none-any.whl` via `flit`
- [x] T010 Generate `specs/007-pypydocsync-release-audit/release_audit_report.md`
- [x] T011 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
