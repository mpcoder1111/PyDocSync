# PyDocSync Project Constitution

## Core Principles

### Principle I: Pure Standard Library Architecture
- **Zero Runtime Dependencies**: PyDocSync is built strictly using the Python 3.10+ standard library (`ast`, `json`, `hashlib`, `dataclasses`, `pathlib`, `argparse`).
- **Core Engine Isolation**: AST parsing, normalization, multi-representation fingerprinting, and impact classification logic have zero external package coupling.

### Principle II: Spec-Driven Development (SDD) & Immutability
- **Idea Maturation Pipeline**: Architecture notes and technical proposals are drafted under `ideas/` (e.g. `ideas/arch_*.md`) before formal specification.
- **SDD Lifecycle**: Features strictly follow `specify` → `clarify` → `plan` → `tasks` → `implement` → `converge`.
- **Shipped Spec Immutability**: Shipped feature specifications (`specs/###-feature-name/`) are permanent historical records. New iterations require a newly numbered spec.

### Principle III: Deterministic Representation Synchronization
- **Multi-Representation Fingerprinting**: Independent SHA-256 fingerprint planes (`CODE`, `API`, `TYPE`, `DOC`, `RAISE_TYPE`, `RAISE_DETAIL`, `EXAMPLE`).
- **AST Normalization Invariants**: Ephemeral location metadata (`lineno`, `col_offset`) is stripped while semantic AST contexts (`ast.Load`, `ast.Store`, `ast.Del`), constants, and control flow are strictly preserved.
- **Review Signals, Not Semantic Proof**: PyDocSync signals when code transformations create a documentation-review obligation (`PYDOCSYNC001`), never claiming to semantically prove natural language correctness.

### Principle IV: Gated Safety & Explicit Review Acknowledgment
- **Explicit Human/Agent Audit Boundary**: `pydocsync accept` requires a non-empty, descriptive audit reason to record intentional review decisions in the baseline lockfile (`.project/pydocsync/`).
- **Fail-Safe Review Routing**: When static analysis encounters ambiguous runtime behavior or aliasing, it routes the case to `UNKNOWN` with `review_required=True` rather than silently assuming the change is safe.

### Principle V: Automated Verification & Scoped Testing
- All code changes are verified through automated unit, integration, and security test suites.
- Full regression test suite must achieve 100% pass rate before completing any feature milestone.

---

## Technology & Platform Constraints

- **Python Support**: Python `>=3.10` (standard library only).
- **Packaging Standard**: PEP 517 build standard with Flit backend (`flit_core`).
- **Type Safety**: 100% type coverage with modern Python 3.10+ syntax and PEP 561 `py.typed` marker.
- **Test Framework**: `pytest`.

---

## Governance

- This Constitution defines the non-negotiable architectural invariants for PyDocSync.
- Amendments require documented version increments.

**Version**: 1.0.0 | **Ratified**: 2026-08-30 | **Status**: Active
