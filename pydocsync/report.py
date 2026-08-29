"""PYDOCSYNC001 Structured Error Report Formatter.

WHAT IS THIS?
-------------
Formats machine-readable, actionable failure envelopes for AI coding agents
and developers when symbol synchronization drift is detected.
"""

from dataclasses import dataclass

from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.classifier import RuleResult


@dataclass
class SyncFailure:
    """Represents a single symbol synchronization review obligation."""

    symbol: SymbolRepresentation
    file_path: str
    rule_result: RuleResult
    changed_fingerprints: list[str]


def format_pydocsync001_report(failures: list[SyncFailure]) -> str:
    """Format failures into machine-readable PYDOCSYNC001 report."""
    if not failures:
        return "PYDOCSYNC: All symbols synchronized with baseline."

    blocks: list[str] = [
        f"PYDOCSYNC001: {len(failures)} symbol(s) require documentation review.",
        "=" * 70,
    ]

    for fail in failures:
        block = [
            f"Symbol:     {fail.symbol.qualname}",
            f"File:       {fail.file_path}:{fail.symbol.lineno}",
            f"Impact:     {fail.rule_result.classification.value}",
            f"Rule ID:    {fail.rule_result.rule_id}",
            f"Changed:    {', '.join(fail.changed_fingerprints)}",
            f"Evidence:   {fail.rule_result.evidence}",
            f"Reason:     {fail.rule_result.reason}",
            f"Action:     Update docstring for '{fail.symbol.qualname}', or if documentation",
            f"            remains 100% accurate, acknowledge via:",
            f'            python packages/pydocsync/pydocsync/cli.py accept --symbol {fail.symbol.qualname} --reason "<audit reason>"',
            "-" * 70,
        ]
        blocks.append("\n".join(block))

    return "\n\n".join(blocks)
