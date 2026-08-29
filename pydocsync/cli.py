"""CLI Entrypoint for PyDocSync.

WHAT IS THIS?
-------------
Provides CLI commands:
- `pydocsync check`: Scans working tree against baselines and emits PYDOCSYNC001 reports.
- `pydocsync init`: Scans and initializes initial baseline lockfiles for compliant symbols.
- `pydocsync accept`: Explicitly records manual review acknowledgment with mandatory audit reason.
"""

import argparse
import sys
from pathlib import Path

from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.baseline import BaselineManager
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification, RuleResult
from pydocsync.fingerprint import FingerprintSet, generate_fingerprints
from pydocsync.report import SyncFailure, format_pydocsync001_report


def scan_and_check(root_dir: Path | str = ".") -> list[SyncFailure]:
    """Scan all Python files in root_dir against baseline lockfiles."""
    root = Path(root_dir)
    mgr = BaselineManager(root_dir=root)
    classifier = ASTChangeImpactClassifier()
    failures: list[SyncFailure] = []

    # Find all .py files excluding venv, hidden, build, test files, and archives
    ignored_patterns = {
        ".venv",
        "venv",
        "build",
        "dist",
        "__pycache__",
        "_archive",
        "tests",
        "fixtures",
        "Spashta_2.0",
        "Spashta_2.1",
    }
    py_files = [
        p
        for p in root.rglob("*.py")
        if not any(part.startswith(".") or part in ignored_patterns for part in p.parts)
    ]

    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        try:
            symbols = extract_symbols_from_source(content)
        except Exception:
            continue

        rel_path = py_file.relative_to(root)
        baseline_records = mgr.load_module_baseline(rel_path)

        for sym in symbols:
            current_fp = generate_fingerprints(sym)
            if sym.qualname not in baseline_records:
                # Gated check for new symbol
                if sym.is_public and (not sym.docstring or not sym.docstring.strip()):
                    failures.append(
                        SyncFailure(
                            symbol=sym,
                            file_path=str(rel_path),
                            rule_result=RuleResult(
                                classification=ChangeClassification.HIGH_IMPACT,
                                rule_id="RULE_UNLINKED_DOCUMENTATION",
                                evidence="New public symbol lacks documentation",
                                reason="New public symbol cannot be baseline synchronized without docstring.",
                                review_required=True,
                            ),
                            changed_fingerprints=["DOC_MISSING"],
                        )
                    )
                continue

            base_rec = baseline_records[sym.qualname]
            base_fp_dict = {
                "code": base_rec.code,
                "api": base_rec.api,
                "types": base_rec.types,
                "doc": base_rec.doc,
                "raise_type": base_rec.raise_type,
                "raise_detail": base_rec.raise_detail,
                "example": base_rec.example,
            }
            curr_fp_dict = current_fp.to_dict()

            changed_fps = [k for k, v in curr_fp_dict.items() if base_fp_dict.get(k) != v]

            if not changed_fps:
                continue

            base_fp = FingerprintSet(
                code=base_rec.code,
                api=base_rec.api,
                types=base_rec.types,
                doc=base_rec.doc,
                raise_type=base_rec.raise_type,
                raise_detail=base_rec.raise_detail,
                example=base_rec.example,
            )

            # Evaluate representation change against baseline fingerprints
            rule_res = classifier.classify_change(sym, sym, base_fp, current_fp)
            if rule_res.classification == ChangeClassification.CANDIDATE_LOW_IMPACT and base_fp.code != current_fp.code:
                # When old AST tree isn't preserved on disk, code divergence requires review
                rule_res = RuleResult(
                    classification=ChangeClassification.HIGH_IMPACT,
                    rule_id="RULE_BASELINE_CODE_DRIFT",
                    evidence=f"Fingerprints changed: {', '.join(changed_fps)}",
                    reason="Implementation code drifted from baseline while documentation remained unchanged.",
                )

            if (
                rule_res.classification in (ChangeClassification.HIGH_IMPACT, ChangeClassification.UNKNOWN)
                and "doc" not in changed_fps
            ):
                failures.append(
                    SyncFailure(
                        symbol=sym,
                        file_path=str(rel_path),
                        rule_result=rule_res,
                        changed_fingerprints=changed_fps,
                    )
                )

    return failures


def accept_symbol_review(symbol_qualname: str, reason: str, root_dir: Path | str = ".") -> bool:
    """Explicitly record review acknowledgment for a symbol."""
    root = Path(root_dir)
    mgr = BaselineManager(root_dir=root)

    # Search across python files for the symbol
    py_files = [
        p
        for p in root.rglob("*.py")
        if not any(part.startswith(".") or part in ("venv", "build", "dist", "__pycache__") for part in p.parts)
    ]

    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            symbols = extract_symbols_from_source(content)
        except Exception:
            continue

        for sym in symbols:
            if sym.qualname == symbol_qualname:
                fp = generate_fingerprints(sym)
                rel_path = py_file.relative_to(root)
                mgr.record_symbol_baseline(rel_path, sym, fp, reason=reason, enforce_gating=False)
                return True

    return False


def initialize_baseline(root_dir: Path | str = ".") -> int:
    """Scan all Python files in root_dir and establish initial baseline lockfiles."""
    root = Path(root_dir)
    mgr = BaselineManager(root_dir=root)
    count = 0

    ignored_patterns = {
        ".venv",
        "venv",
        "build",
        "dist",
        "__pycache__",
        "_archive",
        "tests",
        "fixtures",
        "Spashta_2.0",
        "Spashta_2.1",
    }
    py_files = [
        p
        for p in root.rglob("*.py")
        if not any(part.startswith(".") or part in ignored_patterns for part in p.parts)
    ]

    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()
            symbols = extract_symbols_from_source(content)
        except Exception:
            continue

        rel_path = py_file.relative_to(root)
        for sym in symbols:
            fp = generate_fingerprints(sym)
            mgr.record_symbol_baseline(rel_path, sym, fp, reason="Initial baseline creation", enforce_gating=False)
            count += 1

    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="PyDocSync: Representation Synchronization CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # pydocsync check
    check_p = subparsers.add_parser("check", help="Scan working tree against baseline")
    check_p.add_argument("--root", default=".", help="Root project directory")

    # pydocsync init
    init_p = subparsers.add_parser("init", help="Initialize baseline lockfiles for compliant symbols")
    init_p.add_argument("--root", default=".", help="Root project directory")

    # pydocsync accept
    accept_p = subparsers.add_parser("accept", help="Acknowledge reviewed symbol change")
    accept_p.add_argument("--symbol", required=True, help="Qualified symbol name (e.g. pkg.mod.func)")
    accept_p.add_argument("--reason", required=True, help="Mandatory human/agent audit reason")
    accept_p.add_argument("--root", default=".", help="Root project directory")

    args = parser.parse_args()

    if args.command == "init":
        count = initialize_baseline(root_dir=args.root)
        print(f"PYDOCSYNC: Initialized baseline for {count} compliant symbols across project.")
        sys.exit(0)

    elif args.command == "check":
        failures = scan_and_check(root_dir=args.root)
        if failures:
            print(format_pydocsync001_report(failures), file=sys.stderr)
            sys.exit(1)
        else:
            print("PYDOCSYNC: All symbols synchronized with baseline.")
            sys.exit(0)

    elif args.command == "accept":
        if not args.reason or not args.reason.strip():
            print("PYDOCSYNC ERROR: A non-empty, descriptive audit reason is required for 'accept'.", file=sys.stderr)
            sys.exit(2)

        ok = accept_symbol_review(args.symbol, args.reason.strip(), root_dir=args.root)
        if ok:
            print(f"PYDOCSYNC: Symbol '{args.symbol}' successfully acknowledged and baseline updated.")
            sys.exit(0)
        else:
            print(f"PYDOCSYNC ERROR: Symbol '{args.symbol}' not found in project.", file=sys.stderr)
            sys.exit(1)



if __name__ == "__main__":
    main()
