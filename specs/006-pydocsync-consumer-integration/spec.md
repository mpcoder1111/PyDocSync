# Feature Specification: 006-pypydocsync-consumer-integration

## External Consumer Integration & End-to-End Workflow Verification for PyDocSync 0.2.0

**Feature Branch**: `006-pypydocsync-consumer-integration`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Team review directive (External Consumer Integration)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Deterministic Platform, Quality Gates) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Realistic external consumer workflows (US1: Clean Project Baselining, US2: AI Code Change Detection & PYPYDOCSYNC001, US3: Clean Acknowledgment via CLI & Programmatic API) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-010) for external consumption |
| 4 | [Success Criteria](#success-criteria) | Measurable consumer ergonomics, exit codes, and zero source coupling |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Isolated consumer workspace, wheel-installed execution only |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Consumer projects interact strictly through the installed package and public CLI/API with zero knowledge of internal engines. |
| **II. Spec-Driven Development (SDD)** | **YES** | Follows formal SDD lifecycle for Feature 006. |
| **III. Intent-First & Grounded Planning** | **YES** | Validates how external developers and AI coding agents experience PyDocSync in real development cycles. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Evaluates deterministic exit codes (`0` vs `1`) and `PYPYDOCSYNC001` machine-readable payloads. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Verifies end-to-end AI agent remediation loop (`init` → `check` → drift → `accept` → `check` pass). |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Isolated External Consumer Baselining (`pypypydocsync init`) (Priority: P1)

As an external Python project maintainer who just ran `pip install pypydocsync`, I want to run `pypypydocsync init` in my standalone repository root, so that PyDocSync scans my Python modules and generates local modular `.project/pypypydocsync/*.json` lockfiles without modifying my source code or requiring custom configuration.

**Why this priority**: First touchpoint for external adoption.

**Independent Test**: Create an isolated external consumer project fixture outside PyDocSync's tree, run `pypypydocsync init`, and verify that baseline lockfiles are generated cleanly.

**Acceptance Scenarios**:
1. **Given** an isolated external repository with multiple Python files, **When** `pypypydocsync init` is executed, **Then** it creates `.project/pypypydocsync/` lockfiles and reports the exact symbol count.
2. **Given** the freshly initialized external project, **When** `pypypydocsync check` runs, **Then** it exits with `0` and reports all symbols synchronized.

---

### User Story 2 - AI Code Modification & `PYPYDOCSYNC001` Detection Gate (Priority: P1)

As an AI coding agent pair-programming on the external repository, I want `pypypydocsync check` to catch when I modify an API signature default or add a new exception without updating docstrings, emitting a structured `PYPYDOCSYNC001` failure block and exit code `1`, so that I receive immediate, machine-readable feedback in CI or pre-commit.

**Why this priority**: Core value proposition: preventing silent documentation rot during autonomous AI development.

**Independent Test**: Apply a behavioral modification (e.g. altered default parameter) in the consumer project without updating docstrings, run `pypypydocsync check`, and verify `exit code 1` and `PYPYDOCSYNC001` payload.

**Acceptance Scenarios**:
1. **Given** an un-synchronized code modification in the consumer project, **When** `pypypydocsync check` is executed, **Then** it exits with `1` and emits the exact symbol, file, line number, changed fingerprints, and remediation command to stderr.

---

### User Story 3 - Clean Remediation Loop via CLI & Programmatic API (Priority: P1)

As an external developer or AI agent, I want to resolve review obligations either by (a) updating the docstring to match code, or (b) running `pypypydocsync accept --symbol <sym> --reason "<audit reason>"`, so that `pypypydocsync check` returns to exit code `0` cleanly with an audit trail and zero documentation churn.

**Why this priority**: Proves the complete governance lifecycle works end-to-end for external consumers.

**Independent Test**: Execute `pypypydocsync accept` with an audit reason in the consumer project and verify that `pypypydocsync check` returns to `0`.

**Acceptance Scenarios**:
1. **Given** a `PYPYDOCSYNC001` violation on an intentional refactor, **When** `pypypydocsync accept` is run with a reason, **Then** the baseline is updated and subsequent `pypypydocsync check` passes with exit code `0`.

---

## Edge Cases & Boundary Handling

- **Zero PyDocSync Source Coupling**: The consumer project MUST NOT import anything from `packages/pypypydocsync/` source tree; it executes solely via the installed `pypydocsync` package (`pip install`).
- **Standard Exit Codes**: `0` for clean sync, `1` for violation, `2` for CLI syntax error.
- **Auditable Audit Trail**: Acknowledged records preserve the reason string in the JSON lockfile for git history audits.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create an automated consumer integration test suite under `packages/pypypydocsync/tests/consumer_integration/`.
- **FR-002**: Consumer test harness MUST execute in an isolated workspace simulating 2 distinct external project archetypes:
  1. A multi-module CLI/utility tool with docstrings.
  2. A data processing / algorithmic package with class methods.
- **FR-003**: System MUST execute the full lifecycle via CLI:
  `init` → `check (pass)` → simulate AI code edit → `check (fail, exit 1, PYPYDOCSYNC001)` → `accept` → `check (pass, exit 0)`.
- **FR-004**: System MUST execute the programmatic Python API lifecycle:
  `from pypypydocsync import check, init, accept, SyncResult` in the consumer environment.
- **FR-005**: System MUST verify that `PYPYDOCSYNC001` error output contains the exact CLI remediation command.
- **FR-006**: System MUST verify that invalid CLI invocations (e.g. `pypypydocsync accept` without `--reason`) emit exit code `2` with helpful usage instructions.
- **FR-007**: System MUST generate an integration verification report under `specs/006-pypydocsync-consumer-integration/consumer_integration_report.md`.
- **FR-008**: All 78 previous automated tests MUST continue to pass 100%.

### Key Domain Entities

- **ConsumerProjectFixture**: Temporary isolated directory tree with standalone Python source files.
- **ConsumerWorkflowStep**: Lifecycle stage (`INIT`, `CLEAN_CHECK`, `AI_MODIFICATION`, `VIOLATION_CHECK`, `AUDIT_ACCEPT`, `FINAL_CHECK`).
- **ConsumerExecutionResult**: Captured return code, stdout, stderr, and baseline lockfile state.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (End-to-End Consumer Lifecycle)**: 100% of consumer lifecycle steps (`init` → `check` → drift → `accept` → `check`) pass with expected exit codes (`0` and `1`).
- **SC-002 (Zero Source Coupling)**: Consumer tests run using only `pypydocsync` installed entrypoint and public imports.
- **SC-003 (Audit Integrity)**: Audit reasons recorded by `accept` are verified present in `.project/pypypydocsync/*.json`.
- **SC-004 (Full Regression Suite Pass)**: All 78+ existing tests pass 100%.
