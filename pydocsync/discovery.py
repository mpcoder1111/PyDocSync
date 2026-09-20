"""File Discovery and Directory Traversal Engine for PyDocSync.

WHAT IS THIS?
-------------
Provides high-performance, pruned directory discovery for Python source files
under a project root. Normalizes relative paths, prunes ignored directories
in-place during filesystem traversal (skipping heavy vendor and artifact
directories like .venv, node_modules, and git), applies user exclusion patterns
(`--exclude`, `.pydocsync.json`), reports what those patterns did, and protects
against zero-file false passes.

WHY DO WE NEED THIS?
--------------------
Previously, directory exclusions were hardcoded and duplicated across multiple
CLI routines, and exclusion logic evaluated absolute path parts, which caused
relative root references (like `--root ..`) to treat `..` as a hidden folder
and silently skip all files. Centralizing traversal with an in-place pruned
`os.walk` guarantees sub-second scans and single-point-of-truth exclusions.

Default ignores come in two groups. Vendor/cache directories (`venv`, `node_modules`,
`site-packages`, `__pycache__`, and every dot-directory) are never scanned. Convention
directories (`build`, `dist`, `_archive`, `migrations`, `tests`, `fixtures`) are skipped by
default but can be scanned (`--no-default-excludes`), for projects with real code in `pkg/build/`.
User patterns are counted and tracked so the CLI can show what they excluded and warn about
patterns that matched nothing: an exclusion must never be invisible.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path, PurePosixPath

from pydocsync.patterns import ExcludePattern
from pydocsync.problems import PyDocSyncError

ALWAYS_IGNORED_DIRS: frozenset[str] = frozenset({"venv", "node_modules", "site-packages", "__pycache__"})
CONVENTION_IGNORED_DIRS: frozenset[str] = frozenset({"build", "dist", "_archive", "migrations", "tests", "fixtures"})

DEFAULT_IGNORED_DIRS: frozenset[str] = ALWAYS_IGNORED_DIRS | CONVENTION_IGNORED_DIRS | frozenset({".venv", ".git"})


class NoSourceFilesError(PyDocSyncError, ValueError):
    """No Python source files were found to scan (exit 2).

    Also a `ValueError` so callers written against the spec 008 contract (which documented
    `ValueError` for the zero-files case) keep working.
    """


@dataclass(frozen=True)
class PathFilter:
    """Configurable directory and path filter for file discovery.

    Attributes:
        ignored_dirs: Directory names skipped at any depth (besides dot-directories).
        exclude: User exclusion patterns (from `--exclude` or `.pydocsync.json`).
    """

    ignored_dirs: frozenset[str] = DEFAULT_IGNORED_DIRS
    exclude: tuple[ExcludePattern, ...] = ()

    def should_ignore_dir(self, dir_name: str) -> bool:
        """Determine if a directory should be pruned and skipped during traversal.

        Args:
            dir_name: Bare name of the directory (e.g. '.venv', 'migrations').

        Returns:
            True if directory matches default or configured ignore conventions.
        """
        if dir_name.startswith(".") and dir_name not in (".", ".."):
            return True
        return dir_name in self.ignored_dirs


@dataclass
class Discovery:
    """Result of one discovery walk.

    Attributes:
        files: Python files relative to the root, sorted.
        excluded_count: Paths removed by user patterns (a pruned directory counts once).
        matched_patterns: Text of every user pattern that matched at least one visited path.
    """

    files: list[Path] = field(default_factory=list)
    excluded_count: int = 0
    matched_patterns: set[str] = field(default_factory=set)


def exclusion_reason(rel_path: Path | str, path_filter: PathFilter | None = None) -> str | None:
    """Explain why a single file would not be scanned, using the same rules as discovery.

    Args:
        rel_path: File path relative to the scan root.
        path_filter: The filter in effect; default conventions if None.

    Returns:
        A short reason (e.g. "default directory 'tests'" or "pattern 'templates/' (from --exclude)"),
        or None if the file would be scanned.
    """
    flt = path_filter or PathFilter()
    parts = PurePosixPath(Path(rel_path).as_posix()).parts
    for index, name in enumerate(parts[:-1]):
        if flt.should_ignore_dir(name):
            kind = "default directory" if name in flt.ignored_dirs else "hidden directory"
            return f"{kind} '{name}'"
        rel_dir = "/".join(parts[: index + 1])
        for pattern in flt.exclude:
            if pattern.matches(rel_dir, True):
                return f"pattern '{pattern.text}' (from {pattern.origin})"
    rel_file = "/".join(parts)
    for pattern in flt.exclude:
        if pattern.matches(rel_file, False):
            return f"pattern '{pattern.text}' (from {pattern.origin})"
    return None


def is_path_excluded(rel_path: Path | str, path_filter: PathFilter | None = None) -> bool:
    """Report whether a file path would be excluded from scanning.

    Lets callers validate a single explicit file (e.g. `accept --file`) against the same
    exclusion rules as discovery without walking the tree.

    Args:
        rel_path: File path relative to the scan root.
        path_filter: Optional PathFilter; uses default filter conventions if None.

    Returns:
        True if a parent directory is ignored or a pattern excludes the path.
    """
    return exclusion_reason(rel_path, path_filter) is not None


def discover(root_dir: Path | str = ".", path_filter: PathFilter | None = None) -> Discovery:
    """Discover Python source files under root_dir, recording what user patterns excluded.

    Traverses the directory tree using `os.walk` and mutates `dirnames` in-place
    to prevent recursing into ignored subdirectories. Normalizes all returned
    paths to be relative to `root_dir`.

    Args:
        root_dir: Base directory to search (defaults to current directory).
        path_filter: Optional PathFilter; uses default filter conventions if None.

    Returns:
        Discovery with sorted files, the number of paths excluded by user patterns, and the
        patterns that matched something.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan (also a ValueError).
    """
    root = Path(root_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: '{root_dir}'")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: '{root_dir}'")

    flt = path_filter or PathFilter()
    result = Discovery()

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root)
        kept: list[str] = []
        for name in sorted(dirnames):
            # Default rules first (silent, not counted); user patterns are counted and tracked.
            if flt.should_ignore_dir(name):
                continue
            rel = (rel_dir / name).as_posix()
            hits = [pattern for pattern in flt.exclude if pattern.matches(rel, True)]
            if hits:
                result.excluded_count += 1
                result.matched_patterns.update(pattern.text for pattern in hits)
                continue
            kept.append(name)
        # In-place directory pruning: os.walk will not descend into pruned directories
        dirnames[:] = kept

        for fname in sorted(filenames):
            if not fname.endswith(".py"):
                continue
            rel = (rel_dir / fname).as_posix()
            hits = [pattern for pattern in flt.exclude if pattern.matches(rel, False)]
            if hits:
                result.excluded_count += 1
                result.matched_patterns.update(pattern.text for pattern in hits)
                continue
            result.files.append(rel_dir / fname)

    result.files.sort()
    if not result.files:
        message = f"No Python source files found under '{root_dir}'."
        if flt.exclude:
            message += " All candidate files were removed by the exclusion rules (--exclude / .pydocsync.json)."
        raise NoSourceFilesError(message)
    return result


def discover_python_files(
    root_dir: Path | str = ".",
    path_filter: PathFilter | None = None,
) -> list[Path]:
    """Discover Python source files under root_dir with in-place pruned traversal.

    Compatibility wrapper around `discover` returning only the file list.

    Args:
        root_dir: Base directory to search (defaults to current directory).
        path_filter: Optional PathFilter; uses default filter conventions if None.

    Returns:
        List of Path objects relative to root_dir, sorted deterministically.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan (also a ValueError).
    """
    return discover(root_dir, path_filter).files
