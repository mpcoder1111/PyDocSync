"""Structured problems and typed errors for PyDocSync.

WHAT IS THIS?
-------------
Defines `Problem` (a file or baseline that could not be evaluated), `ProblemKind`, and the
`PyDocSyncError` exception hierarchy. Every error carries an `exit_code` so the CLI can map
failures to process exit codes generically.

WHY DO WE NEED THIS?
--------------------
Before spec 009, anything PyDocSync could not evaluate (a corrupt lockfile, a file with a syntax
error, an ambiguous symbol) was silently skipped and reported as "All symbols synchronized".
Modelling these situations as data (`Problem`) and as typed errors makes them impossible to
ignore. `PyDocSyncError` deliberately does NOT inherit from `ValueError`, so a broad
`except ValueError` handler can never swallow a PyDocSync failure (or mislabel a genuine bug
as a tidy "exit 2").
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocsync.results import Candidate, InitResult


class ProblemKind(str, Enum):
    """Category of a condition that prevented a complete evaluation."""

    BASELINE_CORRUPT = "BASELINE_CORRUPT"
    BASELINE_UNSUPPORTED_VERSION = "BASELINE_UNSUPPORTED_VERSION"
    BASELINE_UNREADABLE = "BASELINE_UNREADABLE"
    BASELINE_MISSING = "BASELINE_MISSING"
    SOURCE_UNPARSEABLE = "SOURCE_UNPARSEABLE"
    SOURCE_UNREADABLE = "SOURCE_UNREADABLE"


@dataclass(frozen=True)
class Problem:
    """A file or lockfile that PyDocSync could not evaluate.

    Attributes:
        kind: Category of the problem.
        path: POSIX-style path relative to the scan root.
        line: 1-based line number when known, else None.
        reason: Human-readable explanation including the error kind.
    """

    kind: ProblemKind
    path: str
    line: int | None
    reason: str

    @property
    def sort_key(self) -> tuple[str, int, str]:
        """Deterministic ordering key (path, line, kind) for stable reports."""
        return (self.path, self.line or 0, self.kind.value)


class PyDocSyncError(Exception):
    """Base class for all PyDocSync failures that map to a CLI exit code.

    Attributes:
        exit_code: Process exit code the CLI uses for this error (default 2).
    """

    exit_code: int = 2


class InvalidArgumentError(PyDocSyncError):
    """A command was invoked with arguments PyDocSync cannot act on (exit 2)."""


class ConfigError(PyDocSyncError):
    """The `.pydocsync.json` config file cannot be used (exit 2).

    A config that cannot be read must never be treated as "no exclusions": that would silently
    change what is checked. The message names the file and the reason.
    """


class FileExcludedError(PyDocSyncError):
    """A `--file` argument names a file that the exclusion rules remove from scanning (exit 1).

    Attributes:
        path: The file as given by the caller.
        reason: The rule that excludes it (default directory or pattern with its origin).
    """

    exit_code = 1

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"--file '{path}' is excluded by {reason}.")
        self.path = path
        self.reason = reason


class BaselineProblemError(PyDocSyncError):
    """A baseline lockfile is missing required structure or is unreadable (exit 2).

    Attributes:
        problem: The structured description of the offending lockfile.
    """

    def __init__(self, problem: Problem) -> None:
        super().__init__(f"{problem.path}: {problem.reason}")
        self.problem = problem


class SourceProblemsError(PyDocSyncError):
    """One or more files or lockfiles prevented a complete evaluation (exit 2).

    Attributes:
        problems: Every problem found, so callers can report all of them at once.
    """

    def __init__(self, problems: list[Problem]) -> None:
        ordered = sorted(problems, key=lambda p: p.sort_key)
        super().__init__(f"{len(ordered)} problem(s) prevented a complete evaluation")
        self.problems = ordered


class AmbiguousSymbolError(PyDocSyncError):
    """A symbol name resolves to more than one file; PyDocSync refuses to guess (exit 2).

    Attributes:
        qualname: The requested qualified symbol name.
        candidates: Every file that defines it, sorted by path.
    """

    def __init__(self, qualname: str, candidates: "list[Candidate]") -> None:
        super().__init__(f"Symbol '{qualname}' is defined in {len(candidates)} files; use --file to choose one")
        self.qualname = qualname
        self.candidates = candidates


class InitIncompleteError(PyDocSyncError):
    """`init` completed its writes but could not baseline everything.

    Raised after new symbols were written, when drifted records were protected (exit 1) or
    problems were found (exit 2). The attached result keeps what was baselined and what was
    protected, so no information is lost.

    Attributes:
        result: The full outcome of the init run.
    """

    exit_code = 1

    def __init__(self, result: "InitResult") -> None:
        super().__init__(
            f"init incomplete: {len(result.protected)} record(s) protected, {len(result.problems)} problem(s)"
        )
        self.result = result
        if result.problems:
            self.exit_code = 2
