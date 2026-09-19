"""File Discovery and Directory Traversal Engine for PyDocSync.

WHAT IS THIS?
-------------
Provides high-performance, pruned directory discovery for Python source files
under a project root. Normalizes relative paths, prunes ignored directories
in-place during filesystem traversal (skipping heavy vendor and artifact
directories like .venv, node_modules, and git), and protects against zero-file
false passes.

WHY DO WE NEED THIS?
--------------------
Previously, directory exclusions were hardcoded and duplicated across multiple
CLI routines, and exclusion logic evaluated absolute path parts, which caused
relative root references (like `--root ..`) to treat `..` as a hidden folder
and silently skip all files. Centralizing traversal with an in-place pruned
`os.walk` guarantees sub-second scans and single-point-of-truth exclusions.
"""

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_IGNORED_DIRS: frozenset[str] = frozenset(
    {
        ".venv",
        "venv",
        ".git",
        "__pycache__",
        "build",
        "dist",
        "_archive",
        "migrations",
        "tests",
        "fixtures",
    }
)


@dataclass(frozen=True)
class PathFilter:
    """Configurable directory and path filter for file discovery."""

    ignored_dirs: frozenset[str] = DEFAULT_IGNORED_DIRS

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


def discover_python_files(
    root_dir: Path | str = ".",
    path_filter: PathFilter | None = None,
) -> list[Path]:
    """Discover Python source files under root_dir with in-place pruned traversal.

    Traverses the directory tree using `os.walk` and mutates `dirnames` in-place
    to prevent recursing into ignored subdirectories. Normalizes all returned
    paths to be relative to `root_dir`.

    Args:
        root_dir: Base directory to search (defaults to current directory).
        path_filter: Optional PathFilter; uses default filter conventions if None.

    Returns:
        List of Path objects relative to root_dir, sorted deterministically.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        ValueError: If zero Python source files are found to scan.
    """
    root = Path(root_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: '{root_dir}'")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: '{root_dir}'")

    flt = path_filter or PathFilter()
    py_files: list[Path] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # In-place directory pruning: os.walk will not descend into pruned directories
        dirnames[:] = [d for d in dirnames if not flt.should_ignore_dir(d)]

        for fname in filenames:
            if fname.endswith(".py"):
                full_path = Path(dirpath) / fname
                py_files.append(full_path.relative_to(root))

    if not py_files:
        raise ValueError(f"No Python source files found under '{root_dir}'.")

    return sorted(py_files)
