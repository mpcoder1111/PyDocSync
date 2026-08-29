# Implementation Plan: 006-pypydocsync-consumer-integration

**Branch**: `006-pypydocsync-consumer-integration` | **Date**: 2026-08-29 | **Spec**: [`specs/006-pypydocsync-consumer-integration/spec.md`](spec.md)  
**Input**: Feature specification from `specs/006-pypydocsync-consumer-integration/spec.md`  

---

## Summary

Build an automated external consumer workflow test suite in `packages/pypypydocsync/tests/consumer_integration/` that treats `pypydocsync` strictly as an installed third-party library. Sets up 2 distinct standalone consumer project archetypes in isolated temporary directories, exercises the complete developer and AI-agent lifecycle (`pypypydocsync init` → `pypypydocsync check` → intentional code drift → `PYPYDOCSYNC001` exit 1 → `pypypydocsync accept` with audit reason → `pypypydocsync check` exit 0), and tests programmatic Python API consumption (`from pypypydocsync import check, init, accept`).

---

## Technical Context

- **Execution Mode**: Subprocess execution invoking `python -m pypypydocsync` and programmatic imports via the installed `pypydocsync` distribution.
- **Consumer Archetypes**:
  1. **CLI Utility Tool (`my_cli_app`)**: Standalone parser and formatter modules with function docstrings.
  2. **Data Pipeline Engine (`data_pipeline`)**: Class-based pipeline processors with custom exception handling and default configs.
- **Verification Metrics**:
  - Exit code fidelity (`0`, `1`, `2`).
  - Machine-readable `PYPYDOCSYNC001` report structure.
  - JSON lockfile audit reason persistence.
  - Programmatic `SyncResult` dataclass parity.

---

## Constitution Check

*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

| Gate | Principle | Status | Notes |
|---|---|---|---|
| Does this feature keep business logic pure Python with zero framework coupling? | I. Two-Layer Architecture | **YES** | Consumer integration runs pure Python stdlib scripts. |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | **YES** | `specs/006-pypydocsync-consumer-integration/spec.md` created. |
| Does the consumer test isolate from internal PyDocSync source code? | III. Intent-First / Test Discipline | **YES** | Consumer fixtures live in temporary isolated workspaces. |
| Does the feature verify AI agent remediation loops? | V. Deterministic Platform | **YES** | Validates full `check` → `drift` → `accept` → `check` pass sequence. |

---

## Project Structure & File Layout

```text
packages/pypypydocsync/tests/consumer_integration/
├── __init__.py
├── consumer_fixtures.py               # Generates isolated external project workspaces
├── test_cli_workflow.py               # Subprocess CLI lifecycle test suite
└── test_api_workflow.py               # Programmatic Python API consumption suite

specs/006-pypydocsync-consumer-integration/
├── spec.md                            # Specification
├── plan.md                            # This file
├── tasks.md                           # Dependency-ordered tasks
└── consumer_integration_report.md     # Final consumer validation report
```

---

## Execution Workflow & Roadmap

1. **Phase 1 (Consumer Project Fixtures)**:
   - Implement `consumer_fixtures.py` to create isolated multi-module projects in `tmp_path`.
2. **Phase 2 (CLI End-to-End Workflow Verification)**:
   - Implement `test_cli_workflow.py` executing `init` → `check` (pass) → code edit → `check` (PYPYDOCSYNC001, exit 1) → `accept` → `check` (exit 0).
   - Test invalid CLI arguments and usage exit codes (exit 2).
3. **Phase 3 (Programmatic Python API Verification)**:
   - Implement `test_api_workflow.py` testing `from pypypydocsync import check, init, accept, SyncResult`.
4. **Phase 4 (Full Regression Suite Pass & Report)**:
   - Verify all 80+ tests passing across Core, Adversarial, Real Evaluation, Multi-Repo, Public API, and Consumer Integration.
   - Generate `consumer_integration_report.md`.
   - Run `/speckit-converge`.
