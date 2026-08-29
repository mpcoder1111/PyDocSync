# Tasks: 006-pypydocsync-consumer-integration

**Input**: Design documents from `specs/006-pypydocsync-consumer-integration/` (`spec.md`, `plan.md`)  
**Prerequisites**: `plan.md` (complete), `spec.md` (complete)  

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`US1`, `US2`, `US3`)

---

## Phase 1: Consumer Project Fixtures (Priority: P1)

**Purpose**: Build standalone project generators in isolated temporary directories

- [x] T001 Initialize package `packages/pypypydocsync/tests/consumer_integration/__init__.py`
- [x] T002 [US1] Implement `packages/pypypydocsync/tests/consumer_integration/consumer_fixtures.py` creating two isolated external project archetypes (`my_cli_app` and `data_pipeline`)

---

## Phase 2: CLI End-to-End Workflow Verification (Priority: P1)

**Purpose**: Verify CLI commands via subprocess execution

- [x] T003 [US1] Implement `test_cli_workflow.py` testing `pypypydocsync init` creating `.project/pypypydocsync/*.json` in isolated project
- [x] T004 [US2] Test `pypypydocsync check` passing on clean code (exit code 0)
- [x] T005 [US2] Simulate AI code drift (altered default parameter & new exception) and test `pypypydocsync check` failing with `PYPYDOCSYNC001` and exit code 1
- [x] T006 [US3] Test `pypypydocsync accept --symbol ... --reason ...` acknowledging the drift and subsequent `pypypydocsync check` passing with exit code 0
- [x] T007 [US2] Test CLI argument errors (missing `--reason` on accept) emitting exit code 2

---

## Phase 3: Programmatic Python API Verification (Priority: P1)

**Purpose**: Verify public Python API in consumer environment

- [x] T008 [US1] Implement `test_api_workflow.py` validating `from pypypydocsync import check, init, accept, SyncResult` in consumer workspace
- [x] T009 [US3] Verify audit reason persistence in `.project/pypypydocsync/*.json`

---

## Phase 4: Full Test Suite Regression & Hardening Convergence

**Purpose**: Verify zero regressions and compile final consumer report

- [x] T010 Re-run full test suite across the entire repository (81 tests passing 100%)
- [x] T011 Generate `specs/006-pypydocsync-consumer-integration/consumer_integration_report.md`
- [x] T012 Run `/speckit-converge` and update `AGENTS.md` implemented ledger
