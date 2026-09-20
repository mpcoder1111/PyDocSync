"""PyDocSync: Deterministic Representation Synchronization for AI-Assisted Codebases.

Public API:
- `check(root_dir=".") -> SyncResult`: Scan codebase against baseline lockfiles. Problems (unreadable
  files, corrupt baselines) and stale records are returned as data in the result.
- `init(root_dir=".", *, force=False, reason=None) -> int`: Baseline new symbols; protects drifted records
  (raises `InitIncompleteError` carrying the details). `init_report(...)` returns the details without raising.
- `accept(symbol_qualname, reason, root_dir=".", *, file=None) -> bool`: Acknowledge reviewed symbol change.
- `refresh(root_dir=".", *, reason, symbol=None, file=None) -> int`: Record baselines whose documentation was updated.
- `SyncResult`: Typed outcome of a synchronization scan.
- `SyncFailure`: Structured representation failure envelope.
- `Problem`, `ProblemKind`, `StaleRecord`, `InitResult`: Structured results.
- `PyDocSyncError` and subclasses (`AmbiguousSymbolError`, `InitIncompleteError`, `SourceProblemsError`):
  typed failures carrying an `exit_code`; none is a `ValueError`.
"""

from pydocsync._version import __version__
from pydocsync.api import SyncResult, accept, check, init, init_report, refresh
from pydocsync.problems import (
    AmbiguousSymbolError,
    InitIncompleteError,
    InvalidArgumentError,
    Problem,
    ProblemKind,
    PyDocSyncError,
    SourceProblemsError,
)
from pydocsync.report import SyncFailure
from pydocsync.results import InitResult, StaleRecord, SymbolRef

__all__ = [
    "__version__",
    "check",
    "init",
    "init_report",
    "accept",
    "refresh",
    "SyncResult",
    "SyncFailure",
    "Problem",
    "ProblemKind",
    "StaleRecord",
    "InitResult",
    "SymbolRef",
    "PyDocSyncError",
    "AmbiguousSymbolError",
    "InitIncompleteError",
    "InvalidArgumentError",
    "SourceProblemsError",
]
