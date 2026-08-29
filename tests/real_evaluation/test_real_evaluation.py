"""Tri-Part Concordance Evaluation Runner for PyDocSync v0.2.

WHAT IS THIS?
-------------
Evaluates the 15 realistic AI development scenarios against:
1. PyDocSync v0.2 Prediction (Classifier impact & review_required)
2. Blind Human Consensus (Review required vs Update required)
3. AI Agent Action (PASS, DOC_UPDATE, CLI_ACCEPT)
4. Empirical metrics (Precision, Recall, Over-Trigger rate, Unnecessary Churn rate)
"""

import time
from pathlib import Path
import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification
from pydocsync.fingerprint import generate_fingerprints
from .human_assessments import BLIND_HUMAN_ASSESSMENTS
from .scenarios import REAL_PROJECT_SCENARIOS, RealProjectScenario


@pytest.mark.parametrize("scenario", REAL_PROJECT_SCENARIOS, ids=lambda s: s.scenario_id)
def test_real_project_scenario_evaluation(scenario: RealProjectScenario):
    """Evaluate scenario against frozen PyDocSync v0.2 and compare with blind human consensus."""
    # 1. Extract representations
    syms_old = extract_symbols_from_source(scenario.initial_code)
    syms_new = extract_symbols_from_source(scenario.modified_code)

    assert syms_old, f"Failed to parse initial code for {scenario.scenario_id}"
    assert syms_new, f"Failed to parse modified code for {scenario.scenario_id}"

    old_sym = syms_old[0]
    new_sym = syms_new[0]

    fp_old = generate_fingerprints(old_sym)
    fp_new = generate_fingerprints(new_sym)

    # 2. Frozen PyDocSync v0.2 Classification
    classifier = ASTChangeImpactClassifier()
    result = classifier.classify_change(old_sym, new_sym, fp_old, fp_new)

    # 3. Retrieve Blind Human Consensus
    human_assessment = BLIND_HUMAN_ASSESSMENTS.get(scenario.scenario_id)
    assert human_assessment is not None, f"Missing human assessment for {scenario.scenario_id}"

    # 4. Determine Concordance Label
    pydocsync_review_req = result.review_required
    human_review_req = human_assessment.consensus_review_required
    human_update_req = human_assessment.consensus_update_required

    # Check for Unnecessary Churn
    unnecessary_churn = False
    if scenario.ai_intended_action == "DOC_UPDATE" and not human_update_req:
        unnecessary_churn = True

    concordance = "UNKNOWN"
    if pydocsync_review_req == human_review_req:
        concordance = "CONCORDANT_REVIEW" if pydocsync_review_req else "CONCORDANT_PASS"
    elif pydocsync_review_req and not human_review_req:
        concordance = "CONSERVATIVE_OVER_TRIGGER"
    elif not pydocsync_review_req and human_review_req:
        concordance = "UNRESOLVED_ESCAPE"

    print(
        f"\n[{scenario.scenario_id}] Category: {scenario.category}\n"
        f"PyDocSync v0.2: {result.classification.value} (review_req={pydocsync_review_req}, rule={result.rule_id})\n"
        f"Blind Human Consensus: ReviewReq={human_review_req}, UpdateReq={human_update_req}\n"
        f"AI Action: {scenario.ai_intended_action} (Unnecessary Churn={unnecessary_churn})\n"
        f"Concordance: {concordance}\n"
        f"Evidence: {result.evidence}"
    )

    # Verify no unresolved escapes on behavioral changes
    assert concordance != "UNRESOLVED_ESCAPE", (
        f"Escaped modification detected: {scenario.scenario_id} required review by human consensus!"
    )


def test_full_project_scan_performance():
    """Verify that full production package scan executes well under 200 ms."""
    from pydocsync.cli import scan_and_check

    start_time = time.perf_counter()
    failures = scan_and_check(root_dir="packages/pydocsync/pydocsync")
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    print(f"\n[PERFORMANCE] Scanned 6 production modules in {duration_ms:.2f} ms (Failures: {len(failures)})")
    assert duration_ms < 200.0, f"Full package scan took too long: {duration_ms:.2f} ms (budget 200 ms)"
