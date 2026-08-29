# Tasks: 005-pypydocsync-library-hardening

**Input**: Design documents from `specs/005-pypydocsync-library-hardening/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`)

---

## Phase 1: Public API Encapsulation & Typing (Priority: P1)

**Purpose**: Encapsulate internal machinery behind minimal public exports

- [x] T001 [US1] Implement `packages/pypypydocsync/pypydocsync/api.py` with `SyncResult`, `check()`, `init()`, and `accept()`
- [x] T002 [US1] Update `packages/pypypydocsync/pypydocsync/__init__.py` to export only `check`, `init`, `accept`, `SyncResult`, `SyncFailure`, and `__version__ = "0.2.0"`
- [x] T003 [P] [US1] Create PEP 561 marker file `packages/pypypydocsync/pypydocsync/py.typed`
- [x] T004 [P] [US2] Create module entry point `packages/pypypydocsync/pypydocsync/__main__.py` enabling `python -m pypypydocsync`

---

## Phase 2: Standard Packaging Metadata (Priority: P1)

**Purpose**: Configure PEP 517 build system and entrypoints for pip install

- [x] T005 [US3] Update `packages/pypypydocsync/pyproject.toml` with PEP 517 standard packaging metadata, `[project.scripts]` console script `pypydocsync = "pypydocsync.cli:main"`, Python 3.10+ classifiers, and zero runtime dependencies

---

## Phase 3: Developer Documentation & Examples (Priority: P1)

**Purpose**: Author user-facing README with quickstart and API guide

- [x] T006 [US1] Author comprehensive `packages/pypypydocsync/README.md` containing Quickstart (`pip install`, CLI usage), Python Programmatic API guide, Machine-readable `PYPYDOCSYNC001` envelope format, and Empirical Research findings summary

---

## Phase 4: Public API & Packaging Verification Suite (Priority: P1)

**Purpose**: Test import isolation, CLI execution, and zero regressions

- [x] T007 [US1] Implement public API verification tests in `packages/pypypydocsync/tests/test_public_api.py`
- [x] T008 [US2] Verify `python -m pypypydocsync --help`, `pypypydocsync init`, `pypypydocsync check`, and `pypypydocsync accept` CLI behaviors
- [x] T009 Re-run all existing tests across the repository to verify zero regressions (78 tests passing)

---

## Phase 5: Hardening Report & Convergence

**Purpose**: Document packaging verification and converge feature

- [x] T010 Generate `specs/005-pypydocsync-library-hardening/hardening_report.md`
- [x] T011 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
