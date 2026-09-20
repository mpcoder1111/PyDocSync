"""Single evaluation of one symbol against its baseline record.

WHAT IS THIS?
-------------
`evaluate_symbol` decides, for one symbol, whether PyDocSync flags it (a documentation-review
obligation), considers it in sync (`OK`), or finds that its baseline record is out of date even
though nothing needs review (`STALE`, e.g. code and docstring were updated together).

WHY DO WE NEED THIS?
--------------------
`check`, `init` and `refresh` must agree on what "drifted" means. Before spec 009 the decision
lived inline in `scan_and_check`; `init` had no way to ask it, so it overwrote drifted records.
One function, used by all three commands, gives one definition of drift and makes the
"stale" state (baseline out of date but passing) explicit instead of silently ignored.
"""

from dataclasses import dataclass
from enum import Enum

from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.baseline import BaselineRecord
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification, RuleResult
from pydocsync.fingerprint import FingerprintSet
from pydocsync.report import SyncFailure


class Outcome(str, Enum):
    """Result category for one evaluated symbol."""

    OK = "OK"
    STALE = "STALE"
    FLAG = "FLAG"


@dataclass(frozen=True)
class Evaluation:
    """Outcome of evaluating one symbol.

    Attributes:
        outcome: OK (matches or nothing to do), STALE (record differs but not flagged), or FLAG.
        failure: The review obligation when outcome is FLAG, else None.
        changed_planes: Fingerprint planes that differ from the baseline record.
    """

    outcome: Outcome
    failure: SyncFailure | None = None
    changed_planes: tuple[str, ...] = ()


def record_to_fingerprints(record: BaselineRecord) -> FingerprintSet:
    """Rebuild the fingerprint set stored in a baseline record."""
    return FingerprintSet(
        code=record.code,
        api=record.api,
        types=record.types,
        doc=record.doc,
        raise_type=record.raise_type,
        raise_detail=record.raise_detail,
        example=record.example,
    )


def evaluate_symbol(
    sym: SymbolRepresentation,
    file_path: str,
    record: BaselineRecord | None,
    current_fp: FingerprintSet,
    classifier: ASTChangeImpactClassifier,
) -> Evaluation:
    """Decide whether a symbol is flagged, stale, or fine relative to its baseline record.

    Args:
        sym: Current symbol representation.
        file_path: POSIX-style path of the file, relative to the scan root.
        record: The symbol's baseline record, or None if it was never baselined.
        current_fp: Fingerprints of the current symbol.
        classifier: Impact classifier used for changed symbols.

    Returns:
        An Evaluation. FLAG carries the `SyncFailure`; STALE means the record differs from the
        code without needing review (documentation changed with the code) and should be refreshed.
    """
    if record is None:
        # A brand-new public symbol cannot be baseline-synchronized without documentation.
        if sym.is_public and (not sym.docstring or not sym.docstring.strip()):
            return Evaluation(
                outcome=Outcome.FLAG,
                failure=SyncFailure(
                    symbol=sym,
                    file_path=file_path,
                    rule_result=RuleResult(
                        classification=ChangeClassification.HIGH_IMPACT,
                        rule_id="RULE_UNLINKED_DOCUMENTATION",
                        evidence="New public symbol lacks documentation",
                        reason="New public symbol cannot be baseline synchronized without docstring.",
                        review_required=True,
                    ),
                    changed_fingerprints=["DOC_MISSING"],
                ),
                changed_planes=("DOC_MISSING",),
            )
        return Evaluation(outcome=Outcome.OK)

    base_fp = record_to_fingerprints(record)
    base_planes = base_fp.to_dict()
    changed = [plane for plane, value in current_fp.to_dict().items() if base_planes.get(plane) != value]
    if not changed:
        return Evaluation(outcome=Outcome.OK)

    rule_res = classifier.classify_change(sym, sym, base_fp, current_fp)
    if rule_res.classification == ChangeClassification.CANDIDATE_LOW_IMPACT and base_fp.code != current_fp.code:
        # The old AST is not preserved on disk, so any code divergence requires review.
        rule_res = RuleResult(
            classification=ChangeClassification.HIGH_IMPACT,
            rule_id="RULE_BASELINE_CODE_DRIFT",
            evidence=f"Fingerprints changed: {', '.join(changed)}",
            reason="Implementation code drifted from baseline while documentation remained unchanged.",
        )

    # A changed docstring means the documentation was touched, so no further review is demanded;
    # the record is then out of date (STALE) rather than drifted.
    if rule_res.classification in (ChangeClassification.HIGH_IMPACT, ChangeClassification.UNKNOWN) and (
        "doc" not in changed
    ):
        return Evaluation(
            outcome=Outcome.FLAG,
            failure=SyncFailure(
                symbol=sym,
                file_path=file_path,
                rule_result=rule_res,
                changed_fingerprints=changed,
            ),
            changed_planes=tuple(changed),
        )
    return Evaluation(outcome=Outcome.STALE, changed_planes=tuple(changed))
