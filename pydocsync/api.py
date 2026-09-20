"""Public Programmatic API for PyDocSync.

WHAT IS THIS?
-------------
Provides high-level, stable Python API functions for integrating PyDocSync into
custom tools, IDE extensions, or test runners without exposing internal AST normalizers
or classifier rule implementations.

WHY DO WE NEED THIS?
--------------------
Wrappers and editor integrations need the same guarantees as the CLI: nothing that could not be
evaluated may look like success. `check` returns problems and stale records as data, so one bad
file never stops the run. `init` and `accept` keep their simple return types and raise a typed
`PyDocSyncError` (carrying structured data) whenever the CLI would not exit 0.
"""

from dataclasses import dataclass, field
from pathlib import Path

from pydocsync.cli import accept_symbol_review, run_check, run_init, run_refresh
from pydocsync.problems import InitIncompleteError, Problem, SourceProblemsError
from pydocsync.report import SyncFailure
from pydocsync.results import InitResult, StaleRecord


@dataclass
class SyncResult:
    """Outcome of running PyDocSync check across a project root.

    Attributes:
        is_synchronized: False if there are review failures or problems (computed on creation).
        failures: Review obligations (PYDOCSYNC001).
        failure_count: Number of failures (computed on creation).
        problems: Files or lockfiles that could not be evaluated; never silently dropped.
        stale: Symbols passing `check` whose baseline record is out of date (see `refresh`).
        files_checked: Number of files fully evaluated.
        symbols_checked: Number of symbols evaluated.
    """

    is_synchronized: bool
    failures: list[SyncFailure] = field(default_factory=list)
    failure_count: int = 0
    problems: list[Problem] = field(default_factory=list)
    stale: list[StaleRecord] = field(default_factory=list)
    files_checked: int = 0
    symbols_checked: int = 0

    def __post_init__(self) -> None:
        """Derive `failure_count` and `is_synchronized` so they can never disagree with the data.

        `is_synchronized` is False when there are review failures OR problems: a run that could
        not evaluate part of the project is never reported as synchronized.
        """
        self.failure_count = len(self.failures)
        self.is_synchronized = self.failure_count == 0 and not self.problems


def check(root_dir: Path | str = ".") -> SyncResult:
    """Scan working tree against baseline lockfiles and return structured SyncResult.

    Files or lockfiles that cannot be evaluated are returned in `problems`; the run is never
    stopped by them and never reported as synchronized.

    Args:
        root_dir: Root directory of project or package to scan (default ".").

    Returns:
        SyncResult with failures, problems, stale records and coverage counts.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
    """
    report = run_check(root_dir=root_dir)
    return SyncResult(
        is_synchronized=False,
        failures=report.failures,
        problems=report.problems,
        stale=report.stale,
        files_checked=report.files_checked,
        symbols_checked=report.symbols_checked,
    )


def init_report(
    root_dir: Path | str = ".",
    *,
    force: bool = False,
    reason: str | None = None,
    dry_run: bool = False,
) -> InitResult:
    """Baseline new symbols and return exactly what happened, without raising for protection.

    Args:
        root_dir: Root directory of project or package to initialize (default ".").
        force: Overwrite protected and stale records (requires `reason`).
        reason: Audit reason stored in each record overwritten by `force`.
        dry_run: Compute the outcome without writing anything.

    Returns:
        InitResult listing baselined, protected, stale and overwritten symbols and any problems.

    Raises:
        InvalidArgumentError: If `force` is set without a non-blank reason.
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
    """
    return run_init(root_dir=root_dir, force=force, reason=reason, dry_run=dry_run)


def init(root_dir: Path | str = ".", *, force: bool = False, reason: str | None = None) -> int:
    """Baseline new symbols; protect drifted records.

    New symbols are always written first. If any drifted record was protected or any problem
    was found, `InitIncompleteError` is raised carrying the full `InitResult`.

    Args:
        root_dir: Root directory of project or package to initialize (default ".").
        force: Overwrite protected and stale records (requires `reason`).
        reason: Audit reason stored in each record overwritten by `force`.

    Returns:
        Integer count of symbols covered by a matching baseline record.

    Raises:
        InitIncompleteError: If records were protected or problems were found.
        InvalidArgumentError: If `force` is set without a non-blank reason.
    """
    result = run_init(root_dir=root_dir, force=force, reason=reason)
    if result.protected or result.problems:
        raise InitIncompleteError(result)
    return result.count


def accept(symbol_qualname: str, reason: str, root_dir: Path | str = ".", *, file: str | None = None) -> bool:
    """Explicitly record review acknowledgment for a symbol change.

    Args:
        symbol_qualname: Qualified symbol name (e.g. 'mypkg.module.my_function').
        reason: Mandatory human or AI agent audit rationale explaining why doc remains accurate.
        root_dir: Root directory of project (default ".").
        file: File defining the symbol; required when the name exists in several files. When
            given, only that file is read.

    Returns:
        True if symbol was found and baseline updated, False otherwise.

    Raises:
        AmbiguousSymbolError: If the name is defined in more than one file and no `file` is given.
        SourceProblemsError: If a file that had to be read could not be evaluated.
    """
    return accept_symbol_review(symbol_qualname=symbol_qualname, reason=reason, root_dir=root_dir, file=file)


def refresh(
    root_dir: Path | str = ".",
    *,
    reason: str,
    symbol: str | None = None,
    file: str | None = None,
) -> int:
    """Re-record baselines whose documentation was updated (stale records).

    Records that `check` flags and symbols that were never baselined are never touched.

    Args:
        root_dir: Root directory of project or package (default ".").
        reason: Mandatory audit reason stored in each refreshed record.
        symbol: Optional qualified symbol name to restrict the refresh to.
        file: Optional file (relative to root) to restrict the refresh to.

    Returns:
        Number of stale records re-recorded.

    Raises:
        InvalidArgumentError: If the reason is blank or `file` is outside the project root.
        SourceProblemsError: If a file or lockfile could not be evaluated (after refreshing the rest).
    """
    result = run_refresh(root_dir=root_dir, reason=reason, symbol=symbol, file=file)
    if result.problems:
        raise SourceProblemsError(result.problems)
    return len(result.refreshed)
