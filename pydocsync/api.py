"""Public Programmatic API for PyDocSync.

WHAT IS THIS?
-------------
Provides high-level, stable Python API functions for integrating PyDocSync into
custom tools, IDE extensions, or test runners without exposing internal AST normalizers
or classifier rule implementations.
"""

from dataclasses import dataclass, field
from pathlib import Path

from pydocsync.cli import accept_symbol_review, initialize_baseline, scan_and_check
from pydocsync.report import SyncFailure


@dataclass
class SyncResult:
    """Outcome of running PyDocSync check across a project root."""

    is_synchronized: bool
    failures: list[SyncFailure] = field(default_factory=list)
    failure_count: int = 0

    def __post_init__(self) -> None:
        self.failure_count = len(self.failures)
        self.is_synchronized = (self.failure_count == 0)


def check(root_dir: Path | str = ".") -> SyncResult:
    """Scan working tree against baseline lockfiles and return structured SyncResult.

    Args:
        root_dir: Root directory of project or package to scan (default ".").

    Returns:
        SyncResult dataclass with is_synchronized status and list of SyncFailures.
    """
    failures = scan_and_check(root_dir=root_dir)
    return SyncResult(is_synchronized=(len(failures) == 0), failures=failures)


def init(root_dir: Path | str = ".") -> int:
    """Scan working tree and initialize baseline lockfiles for all compliant symbols.

    Args:
        root_dir: Root directory of project or package to initialize (default ".").

    Returns:
        Integer count of symbols successfully baselined.
    """
    return initialize_baseline(root_dir=root_dir)


def accept(symbol_qualname: str, reason: str, root_dir: Path | str = ".") -> bool:
    """Explicitly record review acknowledgment for a symbol change.

    Args:
        symbol_qualname: Qualified symbol name (e.g. 'mypkg.mymod.my_func').
        reason: Mandatory human or AI agent audit rationale explaining why doc remains accurate.
        root_dir: Root directory of project (default ".").

    Returns:
        True if symbol was found and baseline updated, False otherwise.
    """
    return accept_symbol_review(symbol_qualname=symbol_qualname, reason=reason, root_dir=root_dir)
