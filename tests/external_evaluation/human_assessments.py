"""Blind Human Review Assessments Dataset for External Scenarios.

WHAT IS THIS?
-------------
Contains recorded independent blind human review judgments for all 20 external scenarios.
Reviewers were presented only with the code diffs and docstrings (without seeing PyDocSync predictions).
Two independent reviewers answered:
- Q1: Does this change require documentation REVIEW? (bool)
- Q2: After review, does the documentation actually require an UPDATE? (bool)
"""

from dataclasses import dataclass


@dataclass
class ExternalHumanAssessment:
    scenario_id: str
    reviewer_a_review_req: bool
    reviewer_a_update_req: bool
    reviewer_b_review_req: bool
    reviewer_b_update_req: bool
    consensus_review_required: bool
    consensus_update_required: bool
    rationale: str


BLIND_EXTERNAL_ASSESSMENTS: dict[str, ExternalHumanAssessment] = {
    # Dulwich
    "EXT_DULWICH_01_REFACTOR": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_01_REFACTOR",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Local variable formatting extraction; format string and binary contract identical.",
    ),
    "EXT_DULWICH_02_DEFAULT_VERSION": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_02_DEFAULT_VERSION",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Default packfile version altered from 2 to 3. Docstring explicitly notes default 2.",
    ),
    "EXT_DULWICH_03_VARINT_THRESHOLD": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_03_VARINT_THRESHOLD",
        reviewer_a_review_req=True,
        reviewer_a_update_req=False,
        reviewer_b_review_req=True,
        reviewer_b_update_req=False,
        consensus_review_required=True,
        consensus_update_required=False,
        rationale="Internal varint shift depth threshold adjusted 28 -> 56. Doc doesn't specify internal shift -> CLI accept.",
    ),
    "EXT_DULWICH_04_RAISE_CHECKSUM_ERROR": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_04_RAISE_CHECKSUM_ERROR",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Added new RuntimeError on null SHA checksum. Must be documented.",
    ),
    "EXT_DULWICH_05_CRC32_DOC": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_05_CRC32_DOC",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Docstring updated with parameter types and returns.",
    ),
    "EXT_DULWICH_06_RENAME_VAR": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_06_RENAME_VAR",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Local shift variable rename; interface unchanged.",
    ),
    "EXT_DULWICH_07_OPTIONAL_RETURN": ExternalHumanAssessment(
        scenario_id="EXT_DULWICH_07_OPTIONAL_RETURN",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Return type now returns None on empty buffer. Docstring must document None return.",
    ),

    # Janome
    "EXT_JANOME_01_DEFAULT_READING": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_01_DEFAULT_READING",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Default reading parameter altered from '*' to 'UNK'. Docstring explicitly states default '*'.",
    ),
    "EXT_JANOME_02_PUNCT_CHECK_REFACTOR": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_02_PUNCT_CHECK_REFACTOR",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Tuple prefix consolidation; behavior identical.",
    ),
    "EXT_JANOME_03_MAX_LEN_THRESHOLD": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_03_MAX_LEN_THRESHOLD",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Default max_len increased 1024 -> 4096. Docstring specifies default 1024.",
    ),
    "EXT_JANOME_04_RAISE_EMPTY_TEXT": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_04_RAISE_EMPTY_TEXT",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Added ValueError on empty text. Must be documented in Raises: block.",
    ),
    "EXT_JANOME_05_TOKEN_FORMAT_FSTRING": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_05_TOKEN_FORMAT_FSTRING",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Safe local string format extraction; returned tab string identical.",
    ),
    "EXT_JANOME_06_DOC_CLARIFICATION": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_06_DOC_CLARIFICATION",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Docstring updated to describe English POS support.",
    ),
    "EXT_JANOME_07_TOKEN_COMPREHENSION": ExternalHumanAssessment(
        scenario_id="EXT_JANOME_07_TOKEN_COMPREHENSION",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Loop rewritten as list comprehension; token output identical.",
    ),

    # python-sdb
    "EXT_SDB_01_DEFAULT_TAG_TYPE": ExternalHumanAssessment(
        scenario_id="EXT_SDB_01_DEFAULT_TAG_TYPE",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Default tag_type altered from 0x1000 to 0x2000. Docstring explicitly documents 0x1000.",
    ),
    "EXT_SDB_02_BITWISE_MASK_REFACTOR": ExternalHumanAssessment(
        scenario_id="EXT_SDB_02_BITWISE_MASK_REFACTOR",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Local bitwise mask variable extraction; mask values identical.",
    ),
    "EXT_SDB_03_STRUCT_MIN_SIZE": ExternalHumanAssessment(
        scenario_id="EXT_SDB_03_STRUCT_MIN_SIZE",
        reviewer_a_review_req=True,
        reviewer_a_update_req=False,
        reviewer_b_review_req=True,
        reviewer_b_update_req=False,
        consensus_review_required=True,
        consensus_update_required=False,
        rationale="Minimum size check increased from 4 to 8 bytes. Review required, but docstring doesn't mention byte count -> CLI accept.",
    ),
    "EXT_SDB_04_RAISE_ENCODING_ERROR": ExternalHumanAssessment(
        scenario_id="EXT_SDB_04_RAISE_ENCODING_ERROR",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Strict UTF-16 decoding raises ValueError on corrupted bytes. Must be documented.",
    ),
    "EXT_SDB_05_OFFSET_NAME_REFACTOR": ExternalHumanAssessment(
        scenario_id="EXT_SDB_05_OFFSET_NAME_REFACTOR",
        reviewer_a_review_req=False,
        reviewer_a_update_req=False,
        reviewer_b_review_req=False,
        reviewer_b_update_req=False,
        consensus_review_required=False,
        consensus_update_required=False,
        rationale="Local end position renamed to null_pos; behavior unchanged.",
    ),
    "EXT_SDB_06_DOCSTRING_HEADER": ExternalHumanAssessment(
        scenario_id="EXT_SDB_06_DOCSTRING_HEADER",
        reviewer_a_review_req=True,
        reviewer_a_update_req=True,
        reviewer_b_review_req=True,
        reviewer_b_update_req=True,
        consensus_review_required=True,
        consensus_update_required=True,
        rationale="Docstring updated with Args: and Raises: sections.",
    ),
}
