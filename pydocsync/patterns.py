"""Exclusion pattern compiler for PyDocSync.

WHAT IS THIS?
-------------
Compiles the strict, documented gitignore-style subset used by `--exclude` and by the `exclude`
list of `.pydocsync.json` into deterministic matchers. Patterns are matched against the
POSIX-style path of a directory or file relative to the scan root.

Supported forms: `name` (any file or directory called `name`, at any depth), `name/` (directories
only), `a/b` or `/a/b` (anchored to the root), `*` and `?` inside a segment, and `**` as a whole
segment (zero or more directories; `pkg/**` = everything beneath `pkg`). Matching is
case-sensitive on every platform.

WHY DO WE NEED THIS?
--------------------
Excluding files reduces what PyDocSync checks, which is the same risk as a silent skip. A pattern
that means something different from what its author wrote would hide code without anyone
noticing, so anything ambiguous or unsupported (negation `!`, backslashes, `[..]` classes, `a**b`,
empty segments, `.`/`..`) is rejected with an error that quotes the pattern, instead of being
reinterpreted. The matcher uses only `re`, keeping the core standard-library only.
"""

import re
from dataclasses import dataclass, field

from pydocsync.problems import InvalidArgumentError

SYNTAX_HELP = (
    "Supported forms: 'name' (any depth), 'dir/' (directories only), 'a/b' or '/a/b' (anchored to the root), "
    "'*' and '?' within a segment, '**' as a whole segment (e.g. 'pkg/**/gen', '**/tmp'); "
    "not supported: '!' negation, backslash, '[..]', '#', 'a**b', empty segments, '.' and '..'"
)


@dataclass(frozen=True)
class ExcludePattern:
    """A validated, compiled exclusion pattern.

    Attributes:
        text: The pattern exactly as the user wrote it.
        origin: Where it came from (`--exclude` or `.pydocsync.json`), used in messages.
        dir_only: True if the pattern ended with `/` (matches directories only).
        anchored: True if the pattern is matched against the full relative path rather than the name.
        regex: Compiled matcher (implementation detail).
    """

    text: str
    origin: str
    dir_only: bool
    anchored: bool
    regex: "re.Pattern[str]" = field(repr=False, compare=False)

    def matches(self, rel_posix: str, is_dir: bool) -> bool:
        """Report whether this pattern matches a path.

        Args:
            rel_posix: Path relative to the scan root, using `/` separators.
            is_dir: True if the path is a directory.

        Returns:
            True if the path itself matches. (A matched directory excludes its whole subtree
            because discovery prunes it.)
        """
        if self.dir_only and not is_dir:
            return False
        target = rel_posix if self.anchored else rel_posix.rsplit("/", 1)[-1]
        return self.regex.match(target) is not None


def _error(text: str, origin: str, reason: str) -> InvalidArgumentError:
    return InvalidArgumentError(f"Invalid exclude pattern {text!r} (from {origin}): {reason}. {SYNTAX_HELP}.")


def _translate_segment(segment: str) -> str:
    """Translate one path segment (containing only literals, `*` and `?`) into a regex fragment."""
    out: list[str] = []
    for char in segment:
        if char == "*":
            out.append("[^/]*")
        elif char == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(char))
    return "".join(out)


def compile_pattern(text: str, origin: str = "--exclude") -> ExcludePattern:
    """Validate and compile one exclusion pattern.

    Args:
        text: The pattern as written by the user.
        origin: Where the pattern came from, quoted in error and warning messages.

    Returns:
        The compiled pattern.

    Raises:
        InvalidArgumentError: If the pattern is empty, padded with whitespace, or uses syntax outside
            the supported subset. The message quotes the pattern.
    """
    if not text:
        raise _error(text, origin, "the pattern is empty")
    if text != text.strip():
        raise _error(text, origin, "leading or trailing whitespace is not allowed")
    if text.startswith("!"):
        raise _error(text, origin, "negation ('!') is not supported")
    if text.startswith("#"):
        raise _error(text, origin, "patterns starting with '#' are not supported")
    if "\\" in text:
        raise _error(text, origin, "backslashes are not supported; use '/' as the separator")
    if "[" in text or "]" in text:
        raise _error(text, origin, "character classes '[..]' are not supported")

    body = text
    dir_only = body.endswith("/")
    if dir_only:
        body = body[:-1]
    leading_slash = body.startswith("/")
    if leading_slash:
        body = body[1:]
    if not body:
        raise _error(text, origin, "the pattern names no path")

    segments = body.split("/")
    for segment in segments:
        if segment == "":
            raise _error(text, origin, "empty path segment ('//')")
        if segment in (".", ".."):
            raise _error(text, origin, f"'{segment}' segments are not supported; patterns are relative to the root")
        if "**" in segment and segment != "**":
            raise _error(text, origin, "'**' must be a whole path segment")

    anchored = leading_slash or len(segments) > 1
    if not anchored:
        segment = segments[0]
        regex_body = ".+" if segment == "**" else _translate_segment(segment)
    else:
        parts: list[str] = []
        last_index = len(segments) - 1
        for index, segment in enumerate(segments):
            if segment == "**":
                # Non-final: zero or more directories (absorbs its own slash). Final: everything beneath.
                parts.append(".+" if index == last_index else "(?:.*/)?")
            else:
                parts.append(_translate_segment(segment) + ("" if index == last_index else "/"))
        regex_body = "".join(parts)

    return ExcludePattern(
        text=text,
        origin=origin,
        dir_only=dir_only,
        anchored=anchored,
        regex=re.compile(f"^{regex_body}$"),
    )
