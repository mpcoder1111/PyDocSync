"""Layer 2: Unit tests for AST Change Impact Classifier against 15 synthetic cases."""

from pathlib import Path
import sys
import pytest
from pydocsync.ast_extract import extract_symbols_from_source
from pydocsync.classifier import ASTChangeImpactClassifier, ChangeClassification
from pydocsync.fingerprint import generate_fingerprints

# Ensure tests root is in path for fixture loading
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

from fixtures.synthetic_cases import SYNTHETIC_CASES


@pytest.mark.parametrize("case", SYNTHETIC_CASES, ids=lambda c: c.case_id)
def test_classifier_synthetic_cases(case):
    """Verify that each synthetic transformation is correctly categorized with evidence."""
    syms_old = extract_symbols_from_source(case.initial_code)
    syms_new = extract_symbols_from_source(case.transformed_code)

    assert syms_old, f"Failed to parse initial code for {case.case_id}"
    assert syms_new, f"Failed to parse transformed code for {case.case_id}"

    old_sym = syms_old[0]
    new_sym = syms_new[0]

    fp_old = generate_fingerprints(old_sym)
    fp_new = generate_fingerprints(new_sym)

    classifier = ASTChangeImpactClassifier()
    result = classifier.classify_change(old_sym, new_sym, fp_old, fp_new)

    assert result.classification.value == case.expected_classification, (
        f"Case {case.case_id} failed: Expected {case.expected_classification}, "
        f"got {result.classification.value} (Evidence: {result.evidence})"
    )
    assert result.evidence, "RuleResult MUST contain non-empty evidence string"
    assert result.reason, "RuleResult MUST contain human-readable reason"
