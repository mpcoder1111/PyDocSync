# Feature Specification: 007-pypydocsync-release-audit

## Pre-Release Security, Schema Versioning, AST Determinism & Policy Audit for PyDocSync 0.2.0

**Feature Branch**: `007-pypydocsync-release-audit`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: Team Review Directive & Release Audit Checklist  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Deterministic Platform, Two-Layer Architecture) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Pre-release audit domains (US1: Baseline Schema Versioning & Staleness Safety, US2: Security & Adversarial Accept Validation, US3: AST Normalization & Python Version Alignment, US4: Documentation & Boundary Precision) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-012) for the release audit |
| 4 | [Success Criteria](#success-criteria) | Release candidate validation, schema backward compatibility, zero security bypasses |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Non-feature audit milestone; frozen Classifier v0.2 logic unchanged |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Strict boundary between public API contracts and internal engines. |
| **II. Spec-Driven Development (SDD)** | **YES** | Formal specification and convergence report for the release audit milestone. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Formalizes deterministic AST normalization invariants and Python-version compatibility guarantees. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Tests malicious inputs, malformed lockfiles, empty reasons, and race conditions. |
| **VII. Graph & State Safety** | **YES** | Baseline lockfiles gain explicit `schema_version: 1` and `pypydocsync_version` envelopes. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Schema Versioning & Staleness Safety (Priority: P1)

As a developer or system integrator, I want baseline lockfiles to contain explicit `schema_version: 1`, `pypydocsync_version: "0.2.0"`, and `fingerprint_algorithm: "sha256"` metadata headers, and I want `pypypydocsync accept` to compute fingerprints against the current physical file on disk (preventing stale race acknowledgments), so that baseline format evolution is future-proof and never silently corrupted.

**Why this priority**: Foundational for schema migrations, cross-version safety, and state integrity.

**Independent Test**: Verify that generated lockfiles contain top-level schema metadata, and verify that modifying a file on disk immediately prior to `accept` records the actual current file representation.

**Acceptance Scenarios**:
1. **Given** a call to `pypypydocsync init` or `pypypydocsync accept`, **When** lockfiles are written, **Then** they contain `schema_version: 1`, `pypydocsync_version: "0.2.0"`, and `fingerprint_algorithm: "sha256"`.
2. **Given** an un-synchronized symbol, **When** `pypypydocsync accept` runs, **Then** it reads and fingerprints the actual current file on disk rather than cached or stale state.

---

### User Story 2 - Security Boundaries & Robust Input Validation (Priority: P1)

As an auditor or CI administrator, I want `pypypydocsync accept` and `pypypydocsync check` to strictly validate inputs—rejecting whitespace-only or empty reason strings, non-existent symbols, corrupted JSON lockfiles, and path traversal attempts—and clearly document that `accept` represents an intentional human/agent authorization decision rather than semantic proof of correctness.

**Why this priority**: Prevents security bypasses and silent false self-approvals in CI pipelines.

**Independent Test**: Execute adversarial accept commands (empty reason, whitespace reason, non-existent symbol, corrupted JSON lockfile) and verify clean exit code 1 or 2 with informative error messages.

**Acceptance Scenarios**:
1. **Given** `pypypydocsync accept` with an empty or whitespace-only reason (`--reason "   "`), **When** executed, **Then** it fails with exit code 2 and a clear error message.
2. **Given** a corrupted/malformed JSON baseline file, **When** `pypypydocsync check` runs, **Then** it detects the invalid baseline and cleanly reports an error without crashing.

---

### User Story 3 - AST Normalization Audit & Python 3.10+ Support Guarantee (Priority: P1)

As an open-source user across diverse Python environments, I want deterministic AST normalization (stripping location metadata while strictly preserving `ctx` Load/Store/Del semantics and literal constants) tested and documented across Python 3.10+, so that I have predictable representation hashing.

**Why this priority**: Core architectural guarantee of deterministic representation hashing.

**Independent Test**: Dedicated unit tests verifying `ctx` preservation and location stripping across AST nodes.

**Acceptance Scenarios**:
1. **Given** code with identical semantics but different variable location offsets, **When** normalized, **Then** AST hashes are identical.
2. **Given** code altering variable access context (`Load` vs `Store` vs `Del`), **When** normalized, **Then** AST hashes differ deterministically.

---

### User Story 4 - Public Boundary Documentation & Complementary Tooling Positioning (Priority: P1)

As a Python developer evaluating PyDocSync on GitHub, I want the `README.md` to clearly explain:
1. PyDocSync's complementary role (addressing **Implementation Drift** alongside Ruff/Mypy/Pydoclint which address Missing Information and Contract Drift).
2. Explicit Symbol Selection Policy (monitored vs excluded symbols).
3. Public vs Internal API stability guarantees.
4. Benchmark-scoped empirical findings ("observed on evaluated benchmarks").

**Why this priority**: Eliminates user confusion and ensures responsible, defensible public presentation.

**Independent Test**: Review `packages/pypypydocsync/README.md` against all 4 documentation criteria.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Baseline lockfile format MUST include top-level envelope metadata:
  `{"schema_version": 1, "pypydocsync_version": "0.2.0", "fingerprint_algorithm": "sha256", "symbols": { ... }}`.
- **FR-002**: `pypypydocsync accept` MUST reject empty, blank, or whitespace-only `--reason` strings with exit code 2.
- **FR-003**: `pypypydocsync accept` MUST reject requests for symbols not present in the target module.
- **FR-004**: `pypypydocsync accept` MUST always read and fingerprint the actual physical file on disk at execution time.
- **FR-005**: `pypypydocsync check` and `pypypydocsync init` MUST handle corrupted/invalid JSON lockfiles safely by reporting an actionable error.
- **FR-006**: AST normalization in `ast_extract.py` MUST be accompanied by dedicated unit tests proving `lineno`/`col_offset` stripping while preserving `ctx` (`Load`, `Store`, `Del`).
- **FR-007**: Supported Python versions MUST be explicitly aligned and verified for Python 3.10, 3.11, 3.12, and 3.13 in `pyproject.toml` and documentation.
- **FR-008**: `README.md` MUST prominently document:
  - The 3 drift categories: **A. Missing Info** (Ruff/pydoclint), **B. Contract Drift** (Mypy), **C. Implementation Drift** (PyDocSync).
  - Symbol selection policy (public top-level callables and classes; private `_` symbols ignored by default).
  - Explicit trust boundary statement (`accept` = authorization audit trail, not semantic proof).
  - Benchmark-scoped metrics wording.
  - Public API stability declaration.
- **FR-009**: All existing 81 tests MUST continue to pass 100% alongside new release audit tests.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Zero Validation Bypasses)**: 100% of malicious or invalid `accept`/`check` attempts (empty reason, malformed lockfile, non-existent symbol) rejected cleanly with exit codes 1 or 2.
- **SC-002 (Schema Versioning Integrity)**: All lockfiles adhere to `schema_version: 1`.
- **SC-003 (AST Normalization Verified)**: Location stripping and `ctx` semantic preservation covered by unit tests.
- **SC-004 (Documentation Precision)**: README updated with 3 drift layers, symbol policies, trust model, and benchmark-scoped results.
- **SC-005 (Full Test Suite Regression)**: 85+ total automated tests passing 100%.
