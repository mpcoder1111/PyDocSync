"""CLI Entrypoint for PyDocSync.

WHAT IS THIS?
-------------
Provides CLI commands:
- `pydocsync check`: Scans working tree against baselines and emits PYDOCSYNC001 reports.
- `pydocsync init`: Establishes baselines for new symbols; protects drifted records.
- `pydocsync accept`: Explicitly records manual review acknowledgment with mandatory audit reason.
- `pydocsync refresh`: Re-records baselines whose documentation was updated (stale records).

WHY DO WE NEED THIS?
--------------------
The `run_*` functions hold the behavior and return structured results (problems, stale records,
protected records) so the CLI and the Python API share one implementation. Nothing that cannot be
evaluated is skipped silently: unreadable files, corrupt baselines and ambiguous requests become
`Problem`s or typed `PyDocSyncError`s, which `main()` maps to exit codes through a single base class.

Exit codes: 0 = success, 1 = review required / symbol not found / init protected drifted records,
2 = a problem prevented a complete evaluation, or invalid usage. When a run has both drift and
problems, the worst class wins (2) and both are printed.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from pydocsync.ast_extract import SymbolRepresentation, load_symbols
from pydocsync.baseline import BaselineManager
from pydocsync.classifier import ASTChangeImpactClassifier
from pydocsync.discovery import discover_python_files, is_path_excluded
from pydocsync.evaluate import Outcome, evaluate_symbol
from pydocsync.fingerprint import generate_fingerprints
from pydocsync.problems import (
    AmbiguousSymbolError,
    BaselineProblemError,
    InitIncompleteError,
    InvalidArgumentError,
    Problem,
    PyDocSyncError,
    SourceProblemsError,
)
from pydocsync.report import (
    SyncFailure,
    format_ambiguity_report,
    format_problems_report,
    format_pydocsync001_report,
    format_stale_notice,
)
from pydocsync.results import AcceptResult, Candidate, InitResult, RefreshResult, StaleRecord, SymbolRef


@dataclass
class CheckReport:
    """Everything one `check` run found.

    Attributes:
        failures: Review obligations (PYDOCSYNC001).
        problems: Files or lockfiles that could not be evaluated.
        stale: Symbols whose documentation changed but whose baseline was not refreshed.
        files_checked: Number of files fully evaluated.
        symbols_checked: Number of symbols evaluated.
    """

    failures: list[SyncFailure] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)
    stale: list[StaleRecord] = field(default_factory=list)
    files_checked: int = 0
    symbols_checked: int = 0


def _require_reason(reason: str | None, command: str) -> str:
    """Return the stripped reason or raise if it is missing or blank."""
    if reason is None or not reason.strip():
        raise InvalidArgumentError(f"A non-empty, descriptive audit reason is required for '{command}'.")
    return reason.strip()


def _resolve_file_argument(root: Path, file: str) -> Path | None:
    """Resolve a `--file` argument to a scanned file path relative to root.

    Args:
        root: Resolved scan root.
        file: The user-supplied path (relative to root, or absolute).

    Returns:
        The path relative to root, or None if it does not exist, is not a `.py` file, or lies in
        a directory that discovery excludes (so it would never have been scanned).

    Raises:
        InvalidArgumentError: If the path lies outside the project root.
    """
    candidate = Path(file)
    abs_path = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        rel = abs_path.relative_to(root)
    except ValueError:
        raise InvalidArgumentError(f"--file '{file}' is outside the project root '{root}'.") from None
    if not abs_path.is_file() or abs_path.suffix != ".py" or is_path_excluded(rel):
        return None
    return rel


def run_check(root_dir: Path | str = ".") -> CheckReport:
    """Evaluate every discovered Python file against its baseline.

    Files or lockfiles that cannot be evaluated are recorded as problems and evaluation continues,
    so a single run reports all drift and all problems together.

    Args:
        root_dir: Root directory of project or package to scan (default ".").

    Returns:
        A CheckReport with failures, problems, stale records and coverage counts.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
    """
    root = Path(root_dir).resolve()
    mgr = BaselineManager(root_dir=root)
    classifier = ASTChangeImpactClassifier()
    report = CheckReport()

    for rel_path in discover_python_files(root_dir=root):
        symbols, problem = load_symbols(root / rel_path, rel_path)
        if problem is not None:
            report.problems.append(problem)
            continue
        try:
            records = mgr.read_module_baseline(rel_path)
        except BaselineProblemError as err:
            report.problems.append(err.problem)
            continue

        report.files_checked += 1
        display = rel_path.as_posix()
        for sym in symbols:
            report.symbols_checked += 1
            current_fp = generate_fingerprints(sym)
            result = evaluate_symbol(sym, display, records.get(sym.key), current_fp, classifier)
            if result.outcome == Outcome.FLAG and result.failure is not None:
                report.failures.append(result.failure)
            elif result.outcome == Outcome.STALE:
                report.stale.append(StaleRecord(display, sym.qualname, sym.key, result.changed_planes))

    report.problems.sort(key=lambda p: p.sort_key)
    return report


def scan_and_check(root_dir: Path | str = ".") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles.

    Compatibility wrapper around `run_check`. It never returns a partial "clean" list: if any file
    or lockfile could not be evaluated it raises, carrying every problem.

    Args:
        root_dir: Root directory of project or package to scan (default ".").

    Returns:
        List of SyncFailure instances representing unaligned symbols requiring review.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
        SourceProblemsError: If any file or lockfile could not be evaluated.
    """
    report = run_check(root_dir=root_dir)
    if report.problems:
        raise SourceProblemsError(report.problems)
    return report.failures


def _candidate(mgr: BaselineManager, rel: Path, occurrences: list[SymbolRepresentation]) -> Candidate:
    """Describe one file defining an ambiguous name, including whether it currently drifts."""
    drifting: bool | None
    try:
        records = mgr.read_module_baseline(rel)
        classifier = ASTChangeImpactClassifier()
        drifting = any(
            evaluate_symbol(
                sym, rel.as_posix(), records.get(sym.key), generate_fingerprints(sym), classifier
            ).outcome
            == Outcome.FLAG
            for sym in occurrences
        )
    except BaselineProblemError:
        drifting = None
    return Candidate(path=rel.as_posix(), lines=tuple(s.lineno for s in occurrences), drifting=drifting)


def run_accept(symbol_qualname: str, reason: str, root_dir: Path | str = ".", file: str | None = None) -> AcceptResult | None:
    """Record review acknowledgment for every definition of a symbol in exactly one file.

    Args:
        symbol_qualname: Qualified symbol name (e.g. 'Command.handle').
        reason: Human or AI agent audit rationale explaining why the documentation remains accurate.
        root_dir: Root directory of project (default ".").
        file: Optional file (relative to root) that selects among same-named symbols. When given,
            only that file is read.

    Returns:
        AcceptResult, or None if the symbol was not found.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If no file is given and zero Python source files are found.
        InvalidArgumentError: If `file` lies outside the project root.
        SourceProblemsError: If any file that had to be read could not be evaluated.
        AmbiguousSymbolError: If the name is defined in more than one file and no `file` is given.
        BaselineProblemError: If the chosen file's baseline lockfile is corrupt.
    """
    root = Path(root_dir).resolve()
    mgr = BaselineManager(root_dir=root)

    if file is not None:
        if not root.is_dir():
            raise FileNotFoundError(f"Directory not found: '{root_dir}'")
        selected = _resolve_file_argument(root, file)
        if selected is None:
            return None
        targets = [selected]
    else:
        targets = discover_python_files(root_dir=root)

    problems: list[Problem] = []
    hits: dict[Path, list[SymbolRepresentation]] = {}
    for rel_path in targets:
        symbols, problem = load_symbols(root / rel_path, rel_path)
        if problem is not None:
            problems.append(problem)
            continue
        occurrences = [sym for sym in symbols if sym.qualname == symbol_qualname]
        if occurrences:
            hits[rel_path] = occurrences

    # An unreadable file might define the same name, so a unique answer cannot be trusted.
    if problems:
        raise SourceProblemsError(problems)
    if not hits:
        return None
    if len(hits) > 1:
        raise AmbiguousSymbolError(
            symbol_qualname, [_candidate(mgr, rel, occ) for rel, occ in sorted(hits.items())]
        )

    ((rel_path, occurrences),) = hits.items()
    records = mgr.read_module_baseline(rel_path)
    for sym in occurrences:
        records[sym.key] = mgr.make_record(generate_fingerprints(sym), reason)
    mgr.save_module_baseline(rel_path, records)
    return AcceptResult(path=rel_path.as_posix(), updated_count=len(occurrences))


def accept_symbol_review(
    symbol_qualname: str, reason: str, root_dir: Path | str = ".", file: str | None = None
) -> bool:
    """Explicitly record review acknowledgment for a symbol.

    Args:
        symbol_qualname: Qualified symbol name (e.g. 'mypkg.mymod.my_func').
        reason: Mandatory human or AI agent audit rationale explaining why doc remains accurate.
        root_dir: Root directory of project (default ".").
        file: Optional file that selects among same-named symbols.

    Returns:
        True if symbol was found and baseline updated, False otherwise.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
        AmbiguousSymbolError: If the name is defined in more than one file and no `file` is given.
        SourceProblemsError: If a file that had to be read could not be evaluated.
    """
    return run_accept(symbol_qualname, reason, root_dir=root_dir, file=file) is not None


def run_init(
    root_dir: Path | str = ".",
    force: bool = False,
    reason: str | None = None,
    dry_run: bool = False,
) -> InitResult:
    """Establish baselines for new symbols without erasing drift.

    New symbols are written. A record that `check` currently flags is protected (left untouched).
    A record whose documentation was updated (stale) is also left untouched and reported, because
    it may hide an unreviewed later change; `refresh` records those deliberately. `force` with a
    reason overwrites protected and stale records and stores the reason in each.

    Args:
        root_dir: Root directory of project or package to scan (default ".").
        force: Overwrite protected and stale records (requires `reason`).
        reason: Audit reason stored in each overwritten record.
        dry_run: Compute and return the outcome without writing anything.

    Returns:
        InitResult describing what was (or would be) baselined, protected, left stale or overwritten.

    Raises:
        InvalidArgumentError: If `force` is set without a non-blank reason.
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
    """
    force_reason = _require_reason(reason, "init --force") if force else None
    root = Path(root_dir).resolve()
    mgr = BaselineManager(root_dir=root)
    classifier = ASTChangeImpactClassifier()
    result = InitResult(dry_run=dry_run)

    for rel_path in discover_python_files(root_dir=root):
        symbols, problem = load_symbols(root / rel_path, rel_path)
        if problem is not None:
            result.problems.append(problem)
            continue
        try:
            records = mgr.read_module_baseline(rel_path)
        except BaselineProblemError as err:
            # Never overwrite a lockfile we cannot read; the user must restore or delete it.
            result.problems.append(err.problem)
            continue

        result.files_checked += 1
        display = rel_path.as_posix()
        changed = False
        for sym in symbols:
            result.symbols_checked += 1
            fp = generate_fingerprints(sym)
            ref = SymbolRef(display, sym.qualname, sym.key)
            record = records.get(sym.key)
            if record is None:
                records[sym.key] = mgr.make_record(fp, "Initial baseline creation")
                result.baselined.append(ref)
                changed = True
                continue

            outcome = evaluate_symbol(sym, display, record, fp, classifier).outcome
            if outcome == Outcome.OK:
                result.unchanged += 1
            elif force_reason is not None:
                records[sym.key] = mgr.make_record(fp, force_reason)
                result.overwritten.append(ref)
                changed = True
            elif outcome == Outcome.FLAG:
                result.protected.append(ref)
            else:
                result.stale.append(ref)

        if changed and not dry_run:
            mgr.save_module_baseline(rel_path, records)

    result.problems.sort(key=lambda p: p.sort_key)
    return result


def initialize_baseline(root_dir: Path | str = ".") -> int:
    """Scan all Python files in root_dir and establish baseline lockfiles.

    Compatibility wrapper around `run_init`.

    Args:
        root_dir: Root directory of project or package to scan (default ".").

    Returns:
        Integer count of symbols covered by a matching baseline record.

    Raises:
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
        InitIncompleteError: If records were protected or problems were found.
    """
    result = run_init(root_dir=root_dir)
    if result.protected or result.problems:
        raise InitIncompleteError(result)
    return result.count


def run_refresh(
    root_dir: Path | str = ".",
    reason: str | None = None,
    symbol: str | None = None,
    file: str | None = None,
) -> RefreshResult:
    """Re-record baseline records whose documentation was updated (stale records).

    Only stale records are touched: records that `check` flags and symbols that were never
    baselined are left alone, so `refresh` can never hide drift.

    Args:
        root_dir: Root directory of project or package to scan (default ".").
        reason: Mandatory audit reason stored in each refreshed record.
        symbol: Optional qualified symbol name to restrict the refresh to.
        file: Optional file (relative to root) to restrict the refresh to.

    Returns:
        RefreshResult listing refreshed symbols and any problems encountered.

    Raises:
        InvalidArgumentError: If the reason is blank or `file` lies outside the project root.
        FileNotFoundError: If root_dir does not exist.
        NotADirectoryError: If root_dir is not a directory.
        NoSourceFilesError: If zero Python source files are found to scan.
    """
    audit_reason = _require_reason(reason, "refresh")
    root = Path(root_dir).resolve()
    mgr = BaselineManager(root_dir=root)
    classifier = ASTChangeImpactClassifier()
    result = RefreshResult()

    if file is not None:
        if not root.is_dir():
            raise FileNotFoundError(f"Directory not found: '{root_dir}'")
        selected = _resolve_file_argument(root, file)
        if selected is None:
            raise InvalidArgumentError(f"--file '{file}' was not found among the scanned Python files.")
        targets = [selected]
    else:
        targets = discover_python_files(root_dir=root)

    for rel_path in targets:
        symbols, problem = load_symbols(root / rel_path, rel_path)
        if problem is not None:
            result.problems.append(problem)
            continue
        try:
            records = mgr.read_module_baseline(rel_path)
        except BaselineProblemError as err:
            result.problems.append(err.problem)
            continue

        display = rel_path.as_posix()
        changed = False
        for sym in symbols:
            if symbol is not None and sym.qualname != symbol:
                continue
            record = records.get(sym.key)
            fp = generate_fingerprints(sym)
            if record is None or evaluate_symbol(sym, display, record, fp, classifier).outcome != Outcome.STALE:
                continue
            records[sym.key] = mgr.make_record(fp, audit_reason)
            result.refreshed.append(SymbolRef(display, sym.qualname, sym.key))
            changed = True
        if changed:
            mgr.save_module_baseline(rel_path, records)

    result.problems.sort(key=lambda p: p.sort_key)
    return result


def _print_problems(problems: list[Problem], action: str) -> None:
    print(format_problems_report(problems, action=action), file=sys.stderr)


def _run_check_command(args: argparse.Namespace) -> int:
    report = run_check(root_dir=args.root)
    if report.problems:
        _print_problems(report.problems, "check")
    if report.failures:
        print(format_pydocsync001_report(report.failures, root_arg=args.root), file=sys.stderr)

    if not report.problems and not report.failures:
        if report.stale:
            print("PYDOCSYNC: No symbol requires documentation review.")
        else:
            print("PYDOCSYNC: All symbols synchronized with baseline.")
        print(f"PYDOCSYNC: checked {report.files_checked} files, {report.symbols_checked} symbols.")
    if report.stale:
        print(format_stale_notice(report.stale, root_arg=args.root))

    if report.problems:
        return 2
    if report.failures:
        return 1
    if report.stale and args.fail_on_stale:
        print(
            f"PYDOCSYNC003: {len(report.stale)} symbol(s) have a stale baseline "
            "(run 'pydocsync refresh --reason ...' and commit the updated baseline).",
            file=sys.stderr,
        )
        return 1
    return 0


def _run_init_command(args: argparse.Namespace) -> int:
    result = run_init(root_dir=args.root, force=args.force, reason=args.reason, dry_run=args.dry_run)
    verb = "Would initialize" if result.dry_run else "Initialized"
    print(f"PYDOCSYNC: {verb} baseline for {result.count} compliant symbols across project.")
    if result.overwritten:
        print(f"PYDOCSYNC: {len(result.overwritten)} record(s) overwritten under --force (reason stored in each).")
    if result.stale:
        print(
            f"PYDOCSYNC: {len(result.stale)} record(s) have updated documentation not yet recorded; "
            'left untouched. Record them with: pydocsync refresh --reason "<why the docs match the code>"'
        )
    if result.protected:
        lines = [
            f"PYDOCSYNC: {len(result.protected)} drifted record(s) protected; init will not erase drift that check flags:",
            *(f"  {ref.file}: {ref.qualname}" for ref in result.protected),
            "Next: update the docstring, or after review run:",
            f'  pydocsync accept --symbol <name> --reason "<audit reason>" --file <path>',
            "or, to deliberately reset the baseline:",
            '  pydocsync init --force --reason "<why>"',
        ]
        print("\n".join(lines), file=sys.stderr)
    if result.problems:
        _print_problems(result.problems, "baseline")
    return result.exit_code


def _run_accept_command(args: argparse.Namespace) -> int:
    reason = _require_reason(args.reason, "accept")
    outcome = run_accept(args.symbol, reason, root_dir=args.root, file=args.file)
    if outcome is None:
        print(f"PYDOCSYNC ERROR: Symbol '{args.symbol}' not found in project.", file=sys.stderr)
        return 1
    noun = "definition" if outcome.updated_count == 1 else "definitions"
    print(
        f"PYDOCSYNC: Symbol '{args.symbol}' successfully acknowledged and baseline updated "
        f"({outcome.updated_count} {noun} updated in {outcome.path})."
    )
    return 0


def _run_refresh_command(args: argparse.Namespace) -> int:
    result = run_refresh(root_dir=args.root, reason=args.reason, symbol=args.symbol, file=args.file)
    print(f"PYDOCSYNC: Refreshed baseline for {len(result.refreshed)} stale symbol(s).")
    for ref in result.refreshed:
        print(f"  {ref.file}: {ref.qualname}")
    if result.problems:
        _print_problems(result.problems, "refresh")
        return 2
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyDocSync: Representation Synchronization CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_p = subparsers.add_parser("check", help="Scan working tree against baseline")
    check_p.add_argument("--root", default=".", help="Root project directory")
    check_p.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="Exit 1 when documentation was updated but the baseline was not refreshed",
    )

    init_p = subparsers.add_parser("init", help="Baseline new symbols; protect drifted records")
    init_p.add_argument("--root", default=".", help="Root project directory")
    init_p.add_argument("--force", action="store_true", help="Overwrite protected/stale records (requires --reason)")
    init_p.add_argument("--reason", default=None, help="Audit reason stored in each record overwritten by --force")
    init_p.add_argument("--dry-run", action="store_true", help="Show what would happen without writing anything")

    accept_p = subparsers.add_parser("accept", help="Acknowledge reviewed symbol change")
    accept_p.add_argument("--symbol", required=True, help="Qualified symbol name (e.g. pkg.mod.func)")
    accept_p.add_argument("--reason", required=True, help="Mandatory human/agent audit reason")
    accept_p.add_argument("--file", default=None, help="File defining the symbol (required if the name is ambiguous)")
    accept_p.add_argument("--root", default=".", help="Root project directory")

    refresh_p = subparsers.add_parser("refresh", help="Record baselines whose documentation was updated")
    refresh_p.add_argument("--reason", default=None, help="Mandatory audit reason")
    refresh_p.add_argument("--symbol", default=None, help="Only refresh this qualified symbol name")
    refresh_p.add_argument("--file", default=None, help="Only refresh symbols in this file")
    refresh_p.add_argument("--root", default=".", help="Root project directory")
    return parser


def _report_error(err: PyDocSyncError, args: argparse.Namespace) -> None:
    """Print a PyDocSyncError in the form appropriate to its type."""
    if isinstance(err, SourceProblemsError):
        _print_problems(err.problems, "check")
    elif isinstance(err, BaselineProblemError):
        _print_problems([err.problem], "check")
    elif isinstance(err, AmbiguousSymbolError):
        print(format_ambiguity_report(err.qualname, err.candidates, root_arg=getattr(args, "root", None)), file=sys.stderr)
    else:
        print(f"PYDOCSYNC ERROR: {err}", file=sys.stderr)


def main() -> None:
    """CLI entrypoint for PyDocSync commands (init, check, accept, refresh)."""
    args = _build_parser().parse_args()
    handlers = {
        "check": _run_check_command,
        "init": _run_init_command,
        "accept": _run_accept_command,
        "refresh": _run_refresh_command,
    }
    try:
        code = handlers[args.command](args)
    except PyDocSyncError as err:
        _report_error(err, args)
        sys.exit(err.exit_code)
    except (FileNotFoundError, NotADirectoryError) as err:
        print(f"PYDOCSYNC ERROR: {err}", file=sys.stderr)
        sys.exit(2)
    sys.exit(code)


if __name__ == "__main__":
    main()
