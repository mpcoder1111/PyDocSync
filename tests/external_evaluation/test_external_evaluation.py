"""External Multi-Repository Generalization Test Runner for PyDocSync v0.2.

WHAT IS THIS?
-------------
Evaluates frozen PyDocSync v0.2 across 20 realistic scenarios from 3 external Apache-2.0
Python projects (Dulwich, Janome, python-sdb) against independent blind human consensus.
Measures:
- Recall, Precision, Over-Trigger rate, Unnecessary Churn rate, and UNKNOWN/Escalation rate.
"""

import time
import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification
from pydocsync.fingerprint import generate_fingerprints
from .human_assessments import BLIND_EXTERNAL_ASSESSMENTS
from .scenarios import EXTERNAL_SCENARIOS, ExternalScenario


@pytest.mark.parametrize("scenario", EXTERNAL_SCENARIOS, ids=lambda s: s.scenario_id)
def test_external_scenario_evaluation(scenario: ExternalScenario):
    """Evaluate external scenario against frozen PyDocSync v0.2 and compare with blind human consensus."""
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
    human_assessment = BLIND_EXTERNAL_ASSESSMENTS.get(scenario.scenario_id)
    assert human_assessment is not None, f"Missing human assessment for {scenario.scenario_id}"

    # 4. Determine Concordance Label
    pydocsync_review_req = result.review_required
    human_review_req = human_assessment.consensus_review_required
    human_update_req = human_assessment.consensus_update_required

    # Check for Unnecessary Churn & Escalation
    unnecessary_churn = False
    if scenario.ai_intended_action == "DOC_UPDATE" and not human_update_req:
        unnecessary_churn = True

    is_escalated = (result.classification == ChangeClassification.UNKNOWN)

    concordance = "UNKNOWN"
    if pydocsync_review_req == human_review_req:
        concordance = "CONCORDANT_REVIEW" if pydocsync_review_req else "CONCORDANT_PASS"
    elif pydocsync_review_req and not human_review_req:
        concordance = "CONSERVATIVE_OVER_TRIGGER"
    elif not pydocsync_review_req and human_review_req:
        concordance = "UNRESOLVED_ESCAPE"

    print(
        f"\n[{scenario.scenario_id}] Repo: {scenario.repository} | Category: {scenario.category}\n"
        f"PyDocSync v0.2: {result.classification.value} (review_req={pydocsync_review_req}, rule={result.rule_id})\n"
        f"Blind Human Consensus: ReviewReq={human_review_req}, UpdateReq={human_update_req}\n"
        f"AI Action: {scenario.ai_intended_action} (Churn={unnecessary_churn}, Escalated={is_escalated})\n"
        f"Concordance: {concordance}\n"
        f"Evidence: {result.evidence}"
    )

    # Verify zero escapes on external codebase modifications
    assert concordance != "UNRESOLVED_ESCAPE", (
        f"Escaped modification detected on external repo: {scenario.scenario_id}!"
    )


def test_external_corpus_scan_performance():
    """Verify that scanning all external representative modules executes well under 200 ms."""
    from pydocsync.cli import scan_and_check

    start_time = time.perf_counter()
    failures = scan_and_check(root_dir="packages/pydocsync/tests/external_evaluation/corpus")
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    print(f"\n[PERFORMANCE] Scanned external corpus in {duration_ms:.2f} ms (Failures: {len(failures)})")
    assert duration_ms < 200.0, f"External corpus scan took too long: {duration_ms:.2f} ms (budget 200 ms)"
