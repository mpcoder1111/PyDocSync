# Implementation Plan: 008-django-migrations-traversal-hardening

## Technical Architecture & Design for Core Traversal Hardening

**Feature Code**: `008-django-migrations-traversal-hardening`  
**Created**: 2026-09-19  
**Status**: Implemented  

---

## Technical Design & Component Changes

```text
pydocsync/
├── discovery.py              [NEW] Centralized PathFilter and in-place pruned os.walk crawler
├── baseline.py               [MODIFIED] Resolved root path handling in BaselineManager
├── cli.py                    [MODIFIED] Unified discover_python_files and zero-file error exit
tests/
├── test_django_and_relative_root_regressions.py  [NEW] Mandatory repro tests for US1, US2, US3, US4
```

### 1. Discovery Engine (`pydocsync/discovery.py`)
- `DEFAULT_IGNORED_DIRS`: Frozenset of standard directory names to exclude by default.
- `PathFilter`: Immutable dataclass checking `dir_name.startswith(".") and dir_name not in (".", "..")` and `dir_name in self.ignored_dirs`.
- `discover_python_files(root_dir, path_filter)`:
  - Resolves `root = Path(root_dir).resolve()`.
  - Prunes `dirnames[:] = [d for d in dirnames if not flt.should_ignore_dir(d)]`.
  - Converts every found file to a relative path: `full_path.relative_to(root)`.
  - Guards against empty results: `if not py_files: raise ValueError(...)`.

### 2. Baseline Manager Path Resolving (`pydocsync/baseline.py`)
- `self.root_dir = Path(root_dir).resolve()`.
- Baseline lockfile path derivation relies on consistent resolved root directory.

### 3. CLI Command Integration (`pydocsync/cli.py`)
- Standardized all file searches across `scan_and_check`, `initialize_baseline`, and `accept_symbol_review` to use `discover_python_files(root_dir=root)`.
- Standardized error exit in `main()`: catches `(FileNotFoundError, NotADirectoryError, ValueError)` and exits with return code 2.

### 4. Verification Suite
- `tests/test_django_and_relative_root_regressions.py`:
  - `test_django_migrations_are_ignored_by_default`: Tests unbaselined `0002_add_field.py` migration passing check.
  - `test_relative_root_parent_directory_detects_drift`: Tests `--root ..` catching implementation drift with exit code 1.
  - `test_zero_python_files_raises_error_and_exits_nonzero`: Tests exit code 2 on empty directory.
  - `test_discovery_pruning_performance_and_defaults`: Tests `.venv` subtree pruning.
