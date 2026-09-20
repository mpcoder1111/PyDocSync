"""Result data structures returned by PyDocSync operations.

WHAT IS THIS?
-------------
Plain dataclasses describing the outcome of `init`, `accept` and `refresh`, plus small value
objects shared by reports (`SymbolRef`, `StaleRecord`, `Candidate`).

WHY DO WE NEED THIS?
--------------------
Callers (the CLI, wrappers, editor integrations) need structured data, not parsed text.
Keeping these types in one leaf module lets `problems.py` and `report.py` refer to them
without circular imports.
"""

from dataclasses import dataclass, field

from pydocsync.patterns import ExcludePattern
from pydocsync.problems import Problem


@dataclass(frozen=True)
class SymbolRef:
    """Reference to one symbol definition in one file.

    Attributes:
        file: POSIX-style path relative to the scan root.
        qualname: Qualified symbol name as written in source (e.g. `Command.handle`).
        key: Per-file unique baseline key (`qualname`, `qualname#2`, ...).
    """

    file: str
    qualname: str
    key: str


@dataclass(frozen=True)
class StaleRecord:
    """A symbol whose baseline record differs from the code but is not flagged by check.

    Typically documentation was updated together with the code, but the baseline was not
    refreshed, so it can no longer guard later code-only changes.

    Attributes:
        file: POSIX-style path relative to the scan root.
        qualname: Qualified symbol name.
        key: Per-file unique baseline key.
        changed_planes: Fingerprint planes that differ from the baseline record.
    """

    file: str
    qualname: str
    key: str
    changed_planes: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    """One file that defines an ambiguous symbol name.

    Attributes:
        path: POSIX-style path relative to the scan root.
        lines: Line numbers of every definition of the name in this file.
        drifting: True/False if check currently flags it, None if that could not be determined.
    """

    path: str
    lines: tuple[int, ...]
    drifting: bool | None


@dataclass
class InitResult:
    """Outcome of an `init` run (real or dry run).

    Attributes:
        baselined: Symbols newly written to the baseline.
        protected: Drifted records that were left untouched (check still flags them).
        stale: Records left untouched because their documentation was updated (see `refresh`).
        overwritten: Records replaced under `--force`.
        unchanged: Number of symbols whose record already matched.
        problems: Files or lockfiles that could not be evaluated.
        files_checked: Number of files evaluated.
        symbols_checked: Number of symbols evaluated.
        dry_run: True when nothing was written.
        unmatched: Exclusion patterns that matched no scanned path (a likely typo).
    """

    baselined: list[SymbolRef] = field(default_factory=list)
    protected: list[SymbolRef] = field(default_factory=list)
    stale: list[SymbolRef] = field(default_factory=list)
    overwritten: list[SymbolRef] = field(default_factory=list)
    unchanged: int = 0
    problems: list[Problem] = field(default_factory=list)
    files_checked: int = 0
    symbols_checked: int = 0
    dry_run: bool = False
    unmatched: list[ExcludePattern] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of symbols now covered by a baseline record that matches the code."""
        return len(self.baselined) + len(self.overwritten) + self.unchanged

    @property
    def exit_code(self) -> int:
        """Exit code the CLI uses: 2 for problems, 1 when records were protected, else 0."""
        if self.problems:
            return 2
        return 1 if self.protected else 0


@dataclass(frozen=True)
class AcceptResult:
    """Outcome of a successful `accept`.

    Attributes:
        path: File whose baseline was updated.
        updated_count: Number of same-named definitions updated in that file.
    """

    path: str
    updated_count: int


@dataclass
class RefreshResult:
    """Outcome of a `refresh` run.

    Attributes:
        refreshed: Stale symbols that were re-recorded.
        problems: Files or lockfiles that could not be evaluated.
        unmatched: Exclusion patterns that matched no scanned path (a likely typo).
    """

    refreshed: list[SymbolRef] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)
    unmatched: list[ExcludePattern] = field(default_factory=list)
