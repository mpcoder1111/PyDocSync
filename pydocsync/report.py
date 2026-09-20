"""PYDOCSYNC001 Structured Error Report Formatter.

WHAT IS THIS?
-------------
Formats machine-readable, actionable failure envelopes for AI coding agents
and developers when symbol synchronization drift is detected, plus the reports for
problems (files or baselines that could not be evaluated), stale baseline records and
ambiguous `accept` requests.
"""

from dataclasses import dataclass

from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.classifier import RuleResult
from pydocsync.problems import Problem
from pydocsync.results import Candidate, StaleRecord


@dataclass
class SyncFailure:
    """Represents a single symbol synchronization review obligation."""

    symbol: SymbolRepresentation
    file_path: str
    rule_result: RuleResult
    changed_fingerprints: list[str]


def _root_suffix(root_arg: str | None) -> str:
    """Return ` --root <root>` when the run used a non-default root, so hints stay runnable."""
    if root_arg and root_arg != ".":
        return f' --root "{root_arg}"' if " " in root_arg else f" --root {root_arg}"
    return ""


def _accept_command(qualname: str, file_path: str, root_arg: str | None) -> str:
    return f'pydocsync accept --symbol {qualname} --reason "<audit reason>" --file {file_path}{_root_suffix(root_arg)}'


def format_pydocsync001_report(failures: list[SyncFailure], root_arg: str | None = None) -> str:
    """Format failures into machine-readable PYDOCSYNC001 report.

    Args:
        failures: Review obligations to report.
        root_arg: The `--root` value used for the run, echoed in the suggested commands
            when it is not the default.

    Returns:
        The report text.
    """
    if not failures:
        return "PYDOCSYNC: All symbols synchronized with baseline."

    blocks: list[str] = [
        f"PYDOCSYNC001: {len(failures)} symbol(s) require documentation review.",
        "=" * 70,
    ]

    for fail in failures:
        sym = fail.symbol
        occurrence = f" (definition {sym.key.rsplit('#', 1)[1]})" if "#" in sym.key else ""
        block = [
            f"Symbol:     {sym.qualname}{occurrence}",
            f"File:       {fail.file_path}:{sym.lineno}",
            f"Impact:     {fail.rule_result.classification.value}",
            f"Rule ID:    {fail.rule_result.rule_id}",
            f"Changed:    {', '.join(fail.changed_fingerprints)}",
            f"Evidence:   {fail.rule_result.evidence}",
            f"Reason:     {fail.rule_result.reason}",
            f"Action:     Update docstring for '{sym.qualname}', or if documentation",
            "            remains 100% accurate, acknowledge via:",
            f"            {_accept_command(sym.qualname, fail.file_path, root_arg)}",
            "-" * 70,
        ]
        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def format_problems_report(problems: list[Problem], action: str = "check") -> str:
    """Format problems (unreadable/unparseable files, corrupt baselines) into an error report.

    Args:
        problems: Everything that prevented a complete evaluation.
        action: What was being attempted ("check", "baseline", "refresh"), for the header.

    Returns:
        The report text, one sorted line per problem.
    """
    ordered = sorted(problems, key=lambda p: p.sort_key)
    lines = [
        f"PYDOCSYNC ERROR: {len(ordered)} problem(s) prevented a complete {action}.",
        "=" * 70,
    ]
    for prob in ordered:
        location = f"{prob.path}:{prob.line}" if prob.line else prob.path
        lines.append(f"  {prob.kind.value}  {location}  {prob.reason}")
    return "\n".join(lines)


def format_stale_notice(stale: list[StaleRecord], root_arg: str | None = None) -> str:
    """Format the notice for symbols whose documentation changed but whose baseline was not refreshed.

    Args:
        stale: Stale records, reported sorted by file and key.
        root_arg: The `--root` value used for the run.

    Returns:
        The notice text.
    """
    ordered = sorted(stale, key=lambda s: (s.file, s.key))
    lines = [
        f"PYDOCSYNC: {len(ordered)} symbol(s) have updated documentation not yet recorded in the baseline.",
    ]
    for rec in ordered:
        label = rec.qualname if rec.key == rec.qualname else f"{rec.qualname} (definition {rec.key.rsplit('#', 1)[1]})"
        lines.append(f"  {rec.file}: {label} (changed: {', '.join(rec.changed_planes)})")
    lines.append(
        f'  Record them with: pydocsync refresh --reason "<why the docs match the code>"{_root_suffix(root_arg)}'
    )
    return "\n".join(lines)


def format_ambiguity_report(qualname: str, candidates: list[Candidate], root_arg: str | None = None) -> str:
    """Format the error for an `accept` request whose symbol name exists in several files.

    Args:
        qualname: The requested qualified symbol name.
        candidates: Every file that defines it.
        root_arg: The `--root` value used for the run.

    Returns:
        The report text, ending with one ready-to-run command per candidate file.
    """
    ordered = sorted(candidates, key=lambda c: c.path)
    lines = [
        f"PYDOCSYNC ERROR: Symbol '{qualname}' is defined in {len(ordered)} files; refusing to guess which to accept.",
        "=" * 70,
    ]
    for cand in ordered:
        state = {True: "currently drifting", False: "unchanged", None: "state unknown"}[cand.drifting]
        line_list = ", ".join(str(n) for n in cand.lines)
        lines.append(f"  {cand.path}:{line_list}  ({state})")
    lines.append("Re-run with the file you mean:")
    for cand in ordered:
        lines.append(f"  {_accept_command(qualname, cand.path, root_arg)}")
    return "\n".join(lines)
