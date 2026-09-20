"""Effective settings for a PyDocSync run: `.pydocsync.json` merged with CLI options.

WHAT IS THIS?
-------------
Loads `<root>/.pydocsync.json` (keys `exclude`, `default_excludes`, `require_baseline`) and merges it
with command-line options into one immutable `Settings` object. Flags only ever add exclusion
patterns or turn default exclusions off; nothing on the command line can remove a rule from the
config file.

WHY DO WE NEED THIS?
--------------------
An AI agent typing a bare `pydocsync check` must get the same scan set as CI, without having to
remember flags; a forgotten flag would look like a mysterious failure. The config file is JSON
because `tomllib` does not exist on Python 3.10. A config that cannot be used (bad JSON, unknown
key, wrong type, invalid pattern) raises `ConfigError` instead of falling back to "no exclusions",
since silently changing what is checked is the bug class this project exists to remove.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pydocsync.discovery import ALWAYS_IGNORED_DIRS, CONVENTION_IGNORED_DIRS, PathFilter
from pydocsync.patterns import ExcludePattern, compile_pattern
from pydocsync.problems import ConfigError, InvalidArgumentError

CONFIG_FILENAME = ".pydocsync.json"
ALLOWED_KEYS = ("exclude", "default_excludes", "require_baseline")


@dataclass(frozen=True)
class Settings:
    """Effective scan settings.

    Attributes:
        exclude: Compiled exclusion patterns (config first, then flags, duplicates removed).
        default_excludes: Whether the convention directories (`build`, `tests`, ...) are skipped.
        require_baseline: Whether `check` fails when no baseline exists.
    """

    exclude: tuple[ExcludePattern, ...] = ()
    default_excludes: bool = True
    require_baseline: bool = False

    def path_filter(self) -> PathFilter:
        """Build the discovery filter for these settings."""
        ignored = set(ALWAYS_IGNORED_DIRS) | {".venv", ".git"}
        if self.default_excludes:
            ignored |= CONVENTION_IGNORED_DIRS
        return PathFilter(ignored_dirs=frozenset(ignored), exclude=self.exclude)


def _config_error(reason: str) -> ConfigError:
    return ConfigError(f"{CONFIG_FILENAME}: {reason}")


def _read_config(root: Path) -> dict[str, object]:
    """Read and structurally validate the config file; `{}` if it does not exist."""
    path = root / CONFIG_FILENAME
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        raise _config_error(f"cannot read the file: {err}") from err
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as err:
        raise _config_error(f"invalid JSON at line {err.lineno} column {err.colno}: {err.msg}") from err
    if not isinstance(raw, dict):
        raise _config_error("the top-level JSON value must be an object")
    unknown = sorted(set(raw) - set(ALLOWED_KEYS))
    if unknown:
        raise _config_error(f"unknown key(s): {', '.join(unknown)} (allowed: {', '.join(ALLOWED_KEYS)})")
    patterns = raw.get("exclude", [])
    if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
        raise _config_error("'exclude' must be a list of strings")
    for key in ("default_excludes", "require_baseline"):
        if key in raw and not isinstance(raw[key], bool):
            raise _config_error(f"'{key}' must be true or false")
    return raw


def load_settings(
    root: Path,
    exclude: Sequence[str] = (),
    default_excludes: bool | None = None,
    require_baseline: bool | None = None,
    use_config: bool = True,
) -> Settings:
    """Resolve the effective settings for a run.

    Args:
        root: Resolved scan root; `.pydocsync.json` is read from here (not from the cwd).
        exclude: Extra patterns from `--exclude` / API arguments; added to the config's patterns.
        default_excludes: Explicit override; None means "use the config, else True".
        require_baseline: Explicit override; None means "use the config, else False".
        use_config: Read `.pydocsync.json` (True by default).

    Returns:
        The merged, validated Settings.

    Raises:
        ConfigError: If the config file exists but cannot be used (including invalid patterns in it).
        InvalidArgumentError: If a pattern given by the caller is invalid.
    """
    raw = _read_config(root) if use_config else {}

    compiled: list[ExcludePattern] = []
    seen: set[str] = set()
    for text in raw.get("exclude", []):  # type: ignore[attr-defined]
        try:
            pattern = compile_pattern(text, CONFIG_FILENAME)
        except InvalidArgumentError as err:
            raise _config_error(str(err)) from err
        if pattern.text not in seen:
            seen.add(pattern.text)
            compiled.append(pattern)
    for text in exclude:
        pattern = compile_pattern(text, "--exclude")
        if pattern.text not in seen:
            seen.add(pattern.text)
            compiled.append(pattern)

    if default_excludes is None:
        default_excludes = bool(raw.get("default_excludes", True))
    if require_baseline is None:
        require_baseline = bool(raw.get("require_baseline", False))
    return Settings(exclude=tuple(compiled), default_excludes=default_excludes, require_baseline=require_baseline)
