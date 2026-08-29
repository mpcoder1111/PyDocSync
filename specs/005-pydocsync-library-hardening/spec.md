# Feature Specification: 005-pypydocsync-library-hardening

## Standalone Library Hardening, Public API Encapsulation & Packaging for Experimental PyDocSync 0.2.x

**Feature Branch**: `005-pypydocsync-library-hardening`  
**Created**: 2026-08-29  
**Last updated**: 2026-08-29  
**Status**: Draft  
**Input**: User description & Team review directive (Library Hardening & Public API Encapsulation)  

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with project constitution (Two-Layer Architecture, Clean Contracts) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | Developer & AI agent consumption journeys (US1: Minimal Public Python API, US2: Ergonomic CLI & CI Gate, US3: Clean Standalone Packaging for pip install) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 to FR-012) and packaging constraints |
| 4 | [Success Criteria](#success-criteria) | Public API minimalism, package build validation, backwards compatibility |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Experimental 0.2.x release scope (not v1.0), zero internal leakages |

---

## Applicable Constitution Principles

*Per project governance (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Two-Layer Pure Domain Architecture** | **YES** | Public API (`from pypypydocsync import check, init, accept`) encapsulates all internal AST, fingerprint, and classifier machinery. |
| **II. Spec-Driven Development (SDD)** | **YES** | Follows formal SDD lifecycle for Feature 005. |
| **III. Intent-First & Grounded Planning** | **YES** | Designed for external Python developers and AI coding agents to install and use without learning internal AST details. |
| **V. Deterministic Platform, AI-as-Producer** | **YES** | Emits deterministic exit codes (`0` for synced, `1` for violation) and machine-readable `PYPYDOCSYNC001` payloads. |
| **VI. Self-Enforcing Quality Gates** | **YES** | Retains 100% pass rates across the full 75-test regression suite. |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Minimal Public Python API Surface (Priority: P1)

As a Python developer or tool builder, I want to import a clean, minimal top-level API (`from pypypydocsync import check, init, accept, SyncResult, SyncFailure`) without needing to understand AST normalizers, fingerprint hashes, or classifier rule internals, so that I can programmatically integrate PyDocSync into custom scripts, IDE extensions, or test runners.

**Why this priority**: Prevents leaking internal architecture into the public contract, allowing internal evolution (`v0.2 → v0.3`) without breaking consumers.

**Independent Test**: Test importing only public symbols from the top-level `pypydocsync` package and verify that internal modules (`ast_extract`, `fingerprint`, `classifier`) are not required for standard usage.

**Acceptance Scenarios**:
1. **Given** a Python script importing `from pypypydocsync import check, init, accept`, **When** executed on a repository, **Then** it returns typed `SyncResult` dataclasses containing status, failures, and statistics.

---

### User Story 2 - Ergonomic CLI & Structured Machine-Readable Exit Codes (Priority: P1)

As an AI coding agent or CI workflow engineer, I want clean CLI commands (`pypypydocsync check`, `pypypydocsync init`, `pypypydocsync accept --symbol ... --reason ...`) with standard exit codes (`0` = clean/synchronized, `1` = violation requiring review, `2` = usage error) and structured error output, so that PyDocSync can be added to GitHub Actions, pre-commit hooks, or IDE background watchers seamlessly.

**Why this priority**: Primary interface for automated AI-agent coding workflows and CI enforcement.

**Independent Test**: Execute CLI entry point via console script and `python -m pypypydocsync` across clean, drifted, and acknowledged states, validating exit codes and stderr formatting.

**Acceptance Scenarios**:
1. **Given** clean code, **When** `pypypydocsync check` runs, **Then** it exits with `0` and outputs a clean confirmation message.
2. **Given** un-acknowledged code drift, **When** `pypypydocsync check` runs, **Then** it exits with `1` and emits formatted `PYPYDOCSYNC001` blocks to stderr.
3. **Given** a valid acknowledgment, **When** `pypypydocsync accept --symbol <sym> --reason "<audit reason>"` runs, **Then** it records the baseline and exits with `0`.

---

### User Story 3 - Standalone Packaging & Build Verification (`pip install pypydocsync`) (Priority: P1)

As an open-source maintainer, I want `packages/pypypydocsync/` configured with complete `pyproject.toml` packaging metadata (PEP 517/518 build-system, `hatchling` or `flit-core` backend, Python ≥ 3.10 requirement, MIT/Apache license, `py.typed` PEP 561 marker, entrypoints), so that it builds into a standard wheel (`.whl`) and sdist (`.tar.gz`) that installs cleanly via `pip`.

**Why this priority**: Pre-requisite for distributing PyDocSync to external developers and repositories.

**Independent Test**: Build the distribution package (`python -m build packages/pypypydocsync`) and verify wheel installation into a clean virtual environment.

**Acceptance Scenarios**:
1. **Given** `packages/pypypydocsync/pyproject.toml`, **When** `python -m build` runs, **Then** it creates valid `.whl` and `.tar.gz` artifacts.
2. **Given** the built wheel, **When** installed in a clean environment, **Then** the `pypydocsync` CLI command is globally accessible.

---

## Edge Cases & Boundary Handling

- **Experimental Versioning**: Package version is explicitly tagged as `0.2.0-experimental` (or `0.2.0`) in `pyproject.toml` and `__version__`.
- **Typing Integrity**: Includes `py.typed` marker file for strict type checker compliance.
- **Zero Runtime Dependencies**: Core package runs exclusively using Python 3.10+ standard library (`ast`, `hashlib`, `struct`, `dataclasses`, `pathlib`, `argparse`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST export a minimal top-level API in `packages/pypypydocsync/pypydocsync/__init__.py`:
  - `check(root_dir: str | Path = ".") -> SyncResult`
  - `init(root_dir: str | Path = ".") -> int`
  - `accept(symbol_qualname: str, reason: str, root_dir: str | Path = ".") -> bool`
  - `SyncResult` (dataclass holding `is_synchronized: bool`, `failures: list[SyncFailure]`, `scanned_symbols: int`)
  - `SyncFailure` (public failure envelope)
  - `__version__ = "0.2.0"`
- **FR-002**: Internal modules (`ast_extract`, `fingerprint`, `classifier`, `baseline`, `report`) MUST be private to package implementation and not required for public usage.
- **FR-003**: System MUST provide a `__main__.py` entry point enabling `python -m pypypydocsync <command>`.
- **FR-004**: System MUST configure `pyproject.toml` with:
  - PEP 517 standard build system (`flit_core` or `hatchling`)
  - `[project.scripts]` entry point: `pypydocsync = "pypydocsync.cli:main"`
  - Package description, authors, license, classifiers (Python 3.10, 3.11, 3.12, 3.13)
  - Zero external runtime dependencies
- **FR-005**: Package MUST include a `py.typed` marker file for PEP 561 compliance.
- **FR-006**: System MUST provide comprehensive, developer-friendly documentation in `packages/pypypydocsync/README.md` with:
  - Quickstart guide (`pip install`, `pypypydocsync init`, `pypypydocsync check`, `pypypydocsync accept`)
  - Python programmatic API usage example
  - Machine-readable `PYPYDOCSYNC001` envelope specification
  - Empirical research summary (Features 001–004 benchmark results)
- **FR-007**: System MUST implement packaging and public API verification tests in `packages/pypypydocsync/tests/test_public_api.py`.
- **FR-008**: All 75 previous tests MUST continue to pass 100%.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Minimal API Surface)**: Public API surface restricted to exactly 3 primary functions (`check`, `init`, `accept`) and 2 data structures (`SyncResult`, `SyncFailure`).
- **SC-002 (Package Build & Install Validation)**: Package builds cleanly via PEP 517 without warnings and installs in clean environments with working `pypydocsync` CLI.
- **SC-003 (Zero External Runtime Dependencies)**: Package imports cleanly with 0 external third-party dependencies on Python 3.10+.
- **SC-004 (Documentation Completeness)**: Comprehensive `README.md` with runnable snippets and AI-agent workflow guide.
- **SC-005 (Full Test Suite Regression)**: 100% pass rate preserved across all 75+ automated tests.
