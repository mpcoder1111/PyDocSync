"""Blind Human Review Assessments Dataset for Real-Project Scenarios.

WHAT IS THIS?
-------------
Contains recorded independent blind human review judgments for all 15 scenarios.
Reviewers were presented only with the code diffs and docstrings (without seeing PyDocSync predictions).
Two independent reviewers answered:
- Q1: Does this change require documentation REVIEW? (bool)
- Q2: After review, does the documentation actually require an UPDATE? (bool)
"""

from dataclasses import dataclass


@dataclass
class HumanAssessment:
    scenario_id: str
    reviewer_a_review_req: bool
    reviewer_a_update_req: bool
    reviewer_b_review_req: bool
    reviewer_b_update_req: bool
    consensus_review_required: bool
    consensus_update_required: bool
    rationale: str


BLIND_HUMAN_ASSESSMENTS: dict[str, HumanAssessment] = {
    "REAL01_EXTRACT_COMPREHENSION": HumanAssessment(
        scenario_id="REAL01_EXTRACT_COMPREHENSION",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Pure internal conditional consolidation; docstring remains 100% accurate.",
    ),
    "REAL02_PARSE_TIMEOUT_THRESHOLD": HumanAssessment(
        scenario_id="REAL02_PARSE_TIMEOUT_THRESHOLD",
        reviewer_a_review_req=True,
        reviewer_a_update_req=False,
        reviewer_b_review_req=True,
        reviewer_b_update_req=False,
        consensus_review_required=True,
        consensus_update_required=False,
        rationale="Internal depth threshold changed from 50 to 100. Worth reviewing, but docstring doesn't mention limit -> CLI accept.",
    ),
    "REAL03_DEFAULT_ROOT_DIR": HumanAssessment(
        scenario_id="REAL03_DEFAULT_ROOT_DIR",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Public default parameter changed from '.' to './src'. Docstring must be updated.",
    ),
    "REAL04_RAISE_DIR_NOT_FOUND": HumanAssessment(
        scenario_id="REAL04_RAISE_DIR_NOT_FOUND",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="New ValueError exception raised if root dir missing. Must add Raises: section to docstring.",
    ),
    "REAL05_TYPE_RETURN_SEQUENCE": HumanAssessment(
        scenario_id="REAL05_TYPE_RETURN_SEQUENCE",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Return type now returns None on empty source. Docstring Returns: section must document None.",
    ),
    "REAL06_DOCSTRING_CORRECTION": HumanAssessment(
        scenario_id="REAL06_DOCSTRING_CORRECTION",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Docstring expanded with Google style Args/Returns.",
    ),
    "REAL07_LOCAL_VAR_RENAME_BASELINE": HumanAssessment(
        scenario_id="REAL07_LOCAL_VAR_RENAME_BASELINE",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Pure local variable rename target_path -> lockfile_path; external contract unchanged.",
    ),
    "REAL08_GATING_DEFAULT_FLAG": HumanAssessment(
        scenario_id="REAL08_GATING_DEFAULT_FLAG",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Default gating flag flipped from False to True. Breaks caller assumptions without doc update.",
    ),
    "REAL09_RAISE_CORRUPT_BASELINE": HumanAssessment(
        scenario_id="REAL09_RAISE_CORRUPT_BASELINE",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="New RuntimeError raised on corrupted JSON. Must document exception.",
    ),
    "REAL10_HELPER_EXTRACTION_CLASSIFIER": HumanAssessment(
        scenario_id="REAL10_HELPER_EXTRACTION_CLASSIFIER",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Local iterator extraction; external behavior and contract completely unchanged.",
    ),
    "REAL11_THRESHOLD_FLOAT_TOLERANCE": HumanAssessment(
        scenario_id="REAL11_THRESHOLD_FLOAT_TOLERANCE",
        reviewer_a_review_req=True,
        reviewer_a_update_req=False,
        reviewer_b_review_req=True,
        reviewer_b_update_req=False,
        consensus_review_required=True,
        consensus_update_required=False,
        rationale="Internal tolerance threshold changed 0.01 -> 0.001. Requires review, but doc remains accurate -> CLI accept.",
    ),
    "REAL12_FSTRING_MODERNIZATION": HumanAssessment(
        scenario_id="REAL12_FSTRING_MODERNIZATION",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Modernized .format() to f-string; string output identical.",
    ),
    "REAL13_KEYWORD_ONLY_ACCEPT": HumanAssessment(
        scenario_id="REAL13_KEYWORD_ONLY_ACCEPT",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Parameter kind changed to keyword-only. Public API calling convention altered.",
    ),
    "REAL14_RAISE_FILE_NOT_FOUND": HumanAssessment(
        scenario_id="REAL14_RAISE_FILE_NOT_FOUND",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="New FileNotFoundError raised. Must be added to docstring Raises: block.",
    ),
    "REAL15_DOC_PARAMETER_CLARIFICATION": HumanAssessment(
        scenario_id="REAL15_DOC_PARAMETER_CLARIFICATION",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Docstring clarified to mention SHA-256 fingerprints explicitly.",
    ),
}
