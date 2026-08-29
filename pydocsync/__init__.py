"""PyDocSync: Deterministic Representation Synchronization for AI-Assisted Codebases.

Public API:
- `check(root_dir=".") -> SyncResult`: Scan codebase against baseline lockfiles.
- `init(root_dir=".") -> int`: Initialize baseline lockfiles for compliant symbols.
- `accept(symbol_qualname, reason, root_dir=".") -> bool`: Acknowledge reviewed symbol change.
- `SyncResult`: Typed outcome of a synchronization scan.
- `SyncFailure`: Structured representation failure envelope.
"""

from pydocsync.api import SyncResult, accept, check, init
from pydocsync.report import SyncFailure

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "check",
    "init",
    "accept",
    "SyncResult",
    "SyncFailure",
]
