"""Adversarial stress test runner and empirical evidence logger for PyDocSync.

WHAT IS THIS?
-------------
Runs all 16 adversarial attack cases through the dual-execution harness,
evaluates them against frozen Classifier v0.1, and records potential false negatives
(blind spots) and potential false positives (over-triggers).
"""

from pathlib import Path
import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification
from pydocsync.fingerprint import generate_fingerprints
from .cases import ADVERSARIAL_CASES, AdversarialCase
from .harness import compare_runtime_behavior


@pytest.mark.parametrize("case", ADVERSARIAL_CASES, ids=lambda c: c.case_id)
def test_adversarial_case_execution(case: AdversarialCase):
    """Execute dual-execution comparison and evaluate classifier prediction."""
    # 1. Measure empirical runtime behavioral difference under test inputs
    runtime_identical, diff_evidence = compare_runtime_behavior(
        case.initial_code,
        case.transformed_code,
        case.func_name,
        case.test_inputs,
    )

    # 2. Extract AST and compute representation fingerprints
    syms_old = extract_symbols_from_source(case.initial_code)
    syms_new = extract_symbols_from_source(case.transformed_code)

    assert syms_old, f"Failed to parse initial AST for {case.case_id}"
    assert syms_new, f"Failed to parse transformed AST for {case.case_id}"

    old_sym = syms_old[0]
    new_sym = syms_new[0]

    fp_old = generate_fingerprints(old_sym)
    fp_new = generate_fingerprints(new_sym)

    # 3. Classify with frozen Classifier v0.1
    classifier = ASTChangeImpactClassifier()
    result = classifier.classify_change(old_sym, new_sym, fp_old, fp_new)

    # 4. Print empirical record for logging
    status_label = "MATCH"
    if not runtime_identical and result.classification == ChangeClassification.CANDIDATE_LOW_IMPACT:
        status_label = "POTENTIAL_FALSE_NEGATIVE"
    elif runtime_identical and result.classification == ChangeClassification.HIGH_IMPACT:
        status_label = "POTENTIAL_FALSE_POSITIVE"

    print(
        f"\n[{case.case_id}] "
        f"Runtime Identical: {runtime_identical} | "
        f"Classifier v0.1: {result.classification.value} ({result.rule_id}) | "
        f"Verdict: {status_label}\n"
        f"Evidence: {result.evidence}\n"
        f"Runtime Diff: {diff_evidence}"
    )

    # Basic invariant: Execution must complete without unhandled test crash
    assert result.rule_id is not None
