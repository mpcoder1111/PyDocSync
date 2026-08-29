# Implementation Plan: 005-pypydocsync-library-hardening

**Branch**: `005-pypydocsync-library-hardening` | **Date**: 2026-08-29 | **Spec**: [`specs/005-pypydocsync-library-hardening/spec.md`](spec.md)  
**Input**: Feature specification from `specs/005-pypydocsync-library-hardening/spec.md`  

---

## Summary

Harden `packages/pypypydocsync/` into a clean, standalone, experimental Python library (`0.2.0`). Encapsulate all internal AST and fingerprint engines behind a minimal top-level public API (`from pypypydocsync import check, init, accept, SyncResult`), configure standard PEP 517 packaging in `pyproject.toml` with console script entry points and `__main__.py`, add the PEP 561 `py.typed` marker, author developer documentation, and implement build verification tests.

---

## Technical Context

- **Build System**: PEP 517 standard packaging via `flit_core` (or `setuptools`/`hatchling`).
- **Dependencies**: Zero external runtime dependencies (pure Python 3.10+ stdlib).
- **Public API Contract**:
  - `pypydocsync.check(root_dir=".") -> SyncResult`
  - `pypydocsync.init(root_dir=".") -> int`
  - `pypydocsync.accept(symbol_qualname, reason, root_dir=".") -> bool`
  - `pypydocsync.SyncResult(is_synchronized: bool, failures: list[SyncFailure], scanned_symbols: int)`
  - `pypydocsync.SyncFailure`
- **CLI Commands**: `pypypydocsync check`, `pypypydocsync init`, `pypypydocsync accept --symbol ... --reason ...`, and `python -m pypypydocsync ...`.

---

## Constitution Check

*Constitution: `.specify/memory/constitution.md` | Standards: `.specify/memory/standards/`*

| Gate | Principle | Status | Notes |
|---|---|---|---|
| Does this feature keep business logic pure Python with zero framework coupling? | I. Two-Layer Architecture | **YES** | Standalone packaging with zero external dependencies. |
| Is a `spec.md` present and complete before this plan was written? | II. Spec-Driven Development | **YES** | `specs/005-pypydocsync-library-hardening/spec.md` created. |
| Is the public API minimal and decoupled from internal AST representations? | III. Intent-First & Clean Contracts | **YES** | Top-level exports restricted to `check`, `init`, `accept`, `SyncResult`. |
| Does the design maintain all historical tests? | VI. Self-Enforcing Quality Gates | **YES** | All 75 existing tests preserved. |

---

## Project Structure & File Layout

```text
packages/pypypydocsync/
├── pyproject.toml                     # PEP 517 metadata, build backend, scripts
├── README.md                          # Comprehensive developer guide & quickstart
├── pypydocsync/
│   ├── __init__.py                    # Public API exports (check, init, accept, SyncResult)
│   ├── __main__.py                    # python -m pypypydocsync entry point
│   ├── py.typed                       # PEP 561 type marker
│   ├── cli.py                         # CLI implementation & console script handler
│   ├── ast_extract.py                 # Internal
│   ├── fingerprint.py                 # Internal
│   ├── classifier.py                  # Internal (Frozen v0.2)
│   ├── baseline.py                    # Internal
│   └── report.py                      # Internal
└── tests/
    ├── test_public_api.py             # Packaging & public API verification tests
    ├── test_fingerprint.py            # Feature 001 tests
    ├── test_classifier.py             # Feature 001 tests
    ├── test_integration.py            # Feature 001 tests
    ├── test_agent_workflow.py         # Feature 001 tests
    ├── adversarial/                   # Feature 002 tests
    ├── real_evaluation/               # Feature 003 tests
    └── external_evaluation/           # Feature 004 tests

specs/005-pypydocsync-library-hardening/
├── spec.md                            # Specification
├── plan.md                            # This file
├── tasks.md                           # Dependency-ordered tasks
└── hardening_report.md                # Packaging & API verification report
```

---

## Execution Workflow & Roadmap

1. **Phase 1 (Public API Encapsulation & Typing)**:
   - Implement `pypydocsync/api.py` and export clean top-level functions in `pypydocsync/__init__.py`.
   - Add `py.typed` marker file and `pypydocsync/__main__.py`.
2. **Phase 2 (Packaging & CLI Metadata)**:
   - Update `pyproject.toml` with complete PEP 517 metadata, `[project.scripts]`, classifiers, and entry points.
3. **Phase 3 (Documentation & Developer Experience)**:
   - Author comprehensive `packages/pypypydocsync/README.md` with installation instructions, CLI usage, Python API examples, and whitepaper findings.
4. **Phase 4 (Public API & Packaging Test Suite)**:
   - Create `packages/pypypydocsync/tests/test_public_api.py` validating import isolation, `python -m pypypydocsync` invocation, and typed dataclass outputs.
   - Run full regression suite across all 75+ tests.
5. **Phase 5 (Convergence & Ledger Update)**:
   - Run `/speckit-converge` and update `AGENTS.md`.
