# Feature Specification: 008-django-migrations-traversal-hardening

## Django Migrations Exclusion, Relative-Root Normalization, Zero-File Safety & Traversal Optimization

**Feature Code**: `008-django-migrations-traversal-hardening`  
**Created**: 2026-09-19  
**Status**: Implemented  
**Input**: Adopting Team Feedback & Django 600-file Integration Evaluation

---

## Index

| # | Section | Summary |
|---|---|---|
| 1 | [Applicable Constitution Principles](#applicable-constitution-principles) | Alignment with Constitution (Zero Runtime Dependencies, Gated Safety, Deterministic Invariants) |
| 2 | [User Scenarios & Testing](#user-scenarios--testing) | User Story 1 (Django Migrations Exclusion), User Story 2 (Relative Root Traversal Drift), User Story 3 (Zero-File Error Guard), User Story 4 (Pruned Traversal Performance) |
| 3 | [Requirements](#requirements) | Functional requirements (FR-001 through FR-008) |
| 4 | [Success Criteria](#success-criteria) | Both reported failure modes resolved with mandatory automated regression tests |
| 5 | [Assumptions & Boundaries](#assumptions--boundaries) | Phase 1 scope; Phase 2 configurable glob system foundation |

---

## Applicable Constitution Principles

*Per project constitution (`.specify/memory/constitution.md`):*

| Principle | Applies? | Notes |
|---|---|---|
| **I. Pure Standard Library Architecture** | **YES** | Zero external dependencies; uses strictly standard library `os`, `pathlib`, `dataclasses`. |
| **II. Spec-Driven Development (SDD)** | **YES** | Formal specification, implementation plan, and convergence ledger record. |
| **III. Deterministic Representation Synchronization** | **YES** | Normalizes relative paths and excludes non-source directories deterministically. |
| **IV. Gated Safety & Explicit Review Acknowledgment** | **YES** | Replaces silent false-passes with explicit non-zero exit codes (exit 2) when 0 files are scanned. |
| **V. Automated Verification & Scoped Testing** | **YES** | 100% test pass rate across 94 unit, integration, and security tests. |

---

## User Scenarios & Testing

### User Story 1 - Django Migrations Exclusion (Priority: P1)

As a Django developer or CI administrator, I want auto-generated database migration files (e.g. `app/migrations/0002_add_field.py`) containing undocumented `class Migration:` to be excluded by default from documentation review obligations, so that valid schema migrations do not block `pydocsync check` with `RULE_UNLINKED_DOCUMENTATION`.

**Acceptance Scenarios**:
1. **Given** a Django project with `app/migrations/0001_initial.py` initialized in the baseline, **When** a developer or migration command adds `app/migrations/0002_add_field.py` containing undocumented `class Migration:`, **Then** `pydocsync check` exits 0 and reports all symbols synchronized with baseline.

---

### User Story 2 - Relative Root Normalization & False-Pass Elimination (Priority: P1)

As a developer running PyDocSync from an inner module or application folder using relative root arguments (e.g. `pydocsync check --root ..`), I want the tool to resolve the root path and test exclusions against relative path components rather than the full path parts, so that `..` is not mistaken for a hidden directory and code drift is reliably caught with `PYDOCSYNC001` (exit 1) instead of falsely passing with exit 0.

**Acceptance Scenarios**:
1. **Given** a codebase with modified function code and an unmaintained docstring, **When** invoking `pydocsync check --root ..` from within a subfolder, **Then** PyDocSync detects the code drift, emits a `PYDOCSYNC001` report with `RULE_BASELINE_CODE_DRIFT`, and exits with return code 1.

---

### User Story 3 - Zero-File Error Guard (Priority: P1)

As a CI/CD pipeline author, I want PyDocSync to fail with exit code 2 and a clear diagnostic error message if zero Python files were discovered to scan, so that a misconfigured path or empty directory never silently reports "All symbols synchronized".

**Acceptance Scenarios**:
1. **Given** an empty directory or a path containing no Python source files, **When** invoking `pydocsync check --root <empty_dir>` or `pydocsync init --root <empty_dir>`, **Then** the process outputs `PYDOCSYNC ERROR: No Python source files found under '<empty_dir>'.` to `sys.stderr` and exits with code 2.

---

### User Story 4 - High-Speed Pruned Traversal (Priority: P2)

As an engineer using PyDocSync in local pre-commit hooks, I want directory traversal to prune ignored directory subtrees in-place during `os.walk` without descending into heavy vendor, test, or artifact folders (`.venv`, `node_modules`, `build`, `dist`), so that scans complete in milliseconds even on large enterprise codebases.

**Acceptance Scenarios**:
1. **Given** a repository with a `.venv` directory containing thousands of files, **When** file discovery executes, **Then** `.venv` is pruned in-place and discovery completes in under 50 ms.

---

## Requirements

- **FR-001**: Implement `pydocsync.discovery` providing `DEFAULT_IGNORED_DIRS` containing `migrations`, `.venv`, `venv`, `.git`, `__pycache__`, `build`, `dist`, `_archive`, `tests`, and `fixtures`.
- **FR-002**: Remove legacy author-specific exclusions (`Spashta_2.0`, `Spashta_2.1`).
- **FR-003**: Implement `PathFilter` abstraction structured to allow future Phase 2 glob-based configuration.
- **FR-004**: Replace `root.rglob("*.py")` in `cli.py` across `scan_and_check`, `initialize_baseline`, and `accept_symbol_review` with unified `discover_python_files(root_dir)`.
- **FR-005**: In-place prune `dirnames` in `os.walk` so ignored directories are never descended into.
- **FR-006**: Normalize `root` using `Path(root_dir).resolve()` in `cli.py` and `BaselineManager`.
- **FR-007**: Raise `ValueError` and exit with code 2 when 0 Python files are found.
- **FR-008**: Provide automated regression tests verifying both Django migration exclusion and `--root ..` drift detection.
