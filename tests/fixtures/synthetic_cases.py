"""Synthetic test cases covering 15 controlled Python edge cases for PyDocSync testing.

WHAT IS THIS?
-------------
Contains versioned Python code snippets before and after controlled transformations
used to validate the AST extractor and the Change Impact Classifier.
"""

from dataclasses import dataclass

@dataclass
class SyntheticCase:
    case_id: str
    description: str
    initial_code: str
    transformed_code: str
    expected_classification: str  # "HIGH_IMPACT", "CANDIDATE_LOW_IMPACT", "UNKNOWN"
    expected_changed_fp: list[str]
    expected_rule_id: str


SYNTHETIC_CASES: list[SyntheticCase] = [
    # TC01: Variable rename (Candidate Low Impact)
    SyntheticCase(
        case_id="TC01_VAR_RENAME",
        description="Local variable rename inside function body",
        initial_code='''def calc_total(price: float, tax: float) -> float:
    """Calculate total price."""
    total = price + tax
    return total
''',
        transformed_code='''def calc_total(price: float, tax: float) -> float:
    """Calculate total price."""
    sum_val = price + tax
    return sum_val
''',
        expected_classification="CANDIDATE_LOW_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_LOCAL_VAR_RENAME",
    ),

    # TC02: Default argument change (High Impact)
    SyntheticCase(
        case_id="TC02_DEFAULT_ARG_CHANGE",
        description="Default timeout changed from 30 to 60",
        initial_code='''def fetch_data(url: str, timeout: int = 30) -> str:
    """Fetch data from remote URL."""
    return f"Fetching {url}"
''',
        transformed_code='''def fetch_data(url: str, timeout: int = 60) -> str:
    """Fetch data from remote URL."""
    return f"Fetching {url}"
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["api"],
        expected_rule_id="RULE_DEFAULT_VALUE_CHANGE",
    ),

    # TC03: Threshold Constant Changed (High Impact)
    SyntheticCase(
        case_id="TC03_THRESHOLD_CONSTANT_CHANGE",
        description="Internal MAX_RETRIES threshold changed from 3 to 5",
        initial_code='''def run_job(job_id: str) -> bool:
    """Execute job with retries."""
    max_retries = 3
    return len(job_id) <= max_retries
''',
        transformed_code='''def run_job(job_id: str) -> bool:
    """Execute job with retries."""
    max_retries = 5
    return len(job_id) <= max_retries
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_THRESHOLD_CONSTANT_CHANGE",
    ),

    # TC04: Exception Type Added (High Impact)
    SyntheticCase(
        case_id="TC04_NEW_EXCEPTION_TYPE",
        description="Added a new ValueError raise statement",
        initial_code='''def parse_int(val: str) -> int:
    """Parse string integer."""
    return int(val)
''',
        transformed_code='''def parse_int(val: str) -> int:
    """Parse string integer."""
    if not val:
        raise ValueError("val cannot be empty")
    return int(val)
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code", "raise_type", "raise_detail"],
        expected_rule_id="RULE_EXCEPTION_BEHAVIOR_CHANGE",
    ),

    # TC05: Exception Detail Message Changed (High Impact)
    SyntheticCase(
        case_id="TC05_EXCEPTION_DETAIL_CHANGE",
        description="Changed exception constraint message from 3 to 5 blocks",
        initial_code='''def validate_blocks(count: int) -> None:
    """Validate block count."""
    if count < 3:
        raise ValueError("minimum 3 blocks required")
''',
        transformed_code='''def validate_blocks(count: int) -> None:
    """Validate block count."""
    if count < 5:
        raise ValueError("minimum 5 blocks required")
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code", "raise_detail"],
        expected_rule_id="RULE_EXCEPTION_BEHAVIOR_CHANGE",
    ),

    # TC06: Loop to list comprehension (Candidate Low Impact)
    SyntheticCase(
        case_id="TC06_LOOP_TO_COMPREHENSION",
        description="Rewrote procedural loop as a list comprehension",
        initial_code='''def get_squares(nums: list[int]) -> list[int]:
    """Return squares of input numbers."""
    res = []
    for x in nums:
        res.append(x * x)
    return res
''',
        transformed_code='''def get_squares(nums: list[int]) -> list[int]:
    """Return squares of input numbers."""
    return [x * x for x in nums]
''',
        expected_classification="CANDIDATE_LOW_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_COMPREHENSION_REWRITE",
    ),

    # TC07: Async function await logic added (High Impact)
    SyntheticCase(
        case_id="TC07_ASYNC_AWAIT_CHANGE",
        description="Added an async retry call",
        initial_code='''async def fetch_async(url: str) -> str:
    """Fetch asynchronous data."""
    return url
''',
        transformed_code='''async def fetch_async(url: str) -> str:
    """Fetch asynchronous data."""
    await some_async_helper(url)
    return url
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_CONTROL_FLOW_CHANGE",
    ),

    # TC08: Generator yield logic added (High Impact)
    SyntheticCase(
        case_id="TC08_GENERATOR_YIELD",
        description="Changed standard return to generator yield",
        initial_code='''def items():
    """Get items."""
    return [1, 2]
''',
        transformed_code='''def items():
    """Get items."""
    yield 1
    yield 2
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_CONTROL_FLOW_CHANGE",
    ),

    # TC09: Property getter method modified (Candidate Low Impact)
    SyntheticCase(
        case_id="TC09_PROPERTY_GETTER",
        description="Refactored property getter internal calculation",
        initial_code='''class Box:
    @property
    def area(self) -> float:
        """Return box area."""
        return self.w * self.h
''',
        transformed_code='''class Box:
    @property
    def area(self) -> float:
        """Return box area."""
        val = self.w * self.h
        return float(val)
''',
        expected_classification="CANDIDATE_LOW_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_LOCAL_VAR_RENAME",
    ),

    # TC10: Type annotation refined (TYPE change)
    SyntheticCase(
        case_id="TC10_TYPE_ANNOTATION_REFINED",
        description="Refined return type from int to int | None",
        initial_code='''def find_index(tag: str) -> int:
    """Find index of tag."""
    return 0
''',
        transformed_code='''def find_index(tag: str) -> int | None:
    """Find index of tag."""
    return 0
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["types"],
        expected_rule_id="RULE_TYPE_CONTRACT_CHANGE",
    ),

    # TC11: Dynamic decorator added (Unknown / Unclassified)
    SyntheticCase(
        case_id="TC11_DYNAMIC_DECORATOR",
        description="Wrapped with a custom dynamic decorator",
        initial_code='''def process(data: str) -> str:
    """Process data."""
    return data
''',
        transformed_code='''@custom_runtime_magic(level="deep")
def process(data: str) -> str:
    """Process data."""
    return data
''',
        expected_classification="UNKNOWN",
        expected_changed_fp=["api"],
        expected_rule_id="RULE_UNKNOWN_METAPROGRAMMING",
    ),

    # TC12: Non-semantic comment and whitespace tweak (Zero Change)
    SyntheticCase(
        case_id="TC12_COMMENT_WHITESPACE",
        description="Added inline comments and reformatted whitespace",
        initial_code='''def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''',
        transformed_code='''def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    # Add a and b together
    return a + b
''',
        expected_classification="CANDIDATE_LOW_IMPACT",
        expected_changed_fp=[],
        expected_rule_id="RULE_NO_SEMANTIC_CHANGE",
    ),

    # TC13: Branching return condition added (High Impact)
    SyntheticCase(
        case_id="TC13_NEW_BRANCH_RETURN",
        description="Added an early return for None values",
        initial_code='''def clean_str(s: str) -> str:
    """Clean string."""
    return s.strip()
''',
        transformed_code='''def clean_str(s: str) -> str:
    """Clean string."""
    if s == "":
        return "DEFAULT"
    return s.strip()
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["code"],
        expected_rule_id="RULE_CONTROL_FLOW_CHANGE",
    ),

    # TC14: Positional to keyword-only parameter conversion (High Impact)
    SyntheticCase(
        case_id="TC14_KEYWORD_ONLY_PARAM",
        description="Converted parameter to keyword-only with *",
        initial_code='''def format_name(first: str, last: str) -> str:
    """Format full name."""
    return f"{first} {last}"
''',
        transformed_code='''def format_name(first: str, *, last: str) -> str:
    """Format full name."""
    return f"{first} {last}"
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["api"],
        expected_rule_id="RULE_API_SIGNATURE_CHANGE",
    ),

    # TC15: Dataclass default field altered (High Impact)
    SyntheticCase(
        case_id="TC15_DATACLASS_DEFAULT",
        description="Changed default field value in dataclass",
        initial_code='''from dataclasses import dataclass

@dataclass
class Config:
    """Configuration options."""
    retries: int = 3
''',
        transformed_code='''from dataclasses import dataclass

@dataclass
class Config:
    """Configuration options."""
    retries: int = 10
''',
        expected_classification="HIGH_IMPACT",
        expected_changed_fp=["api", "code"],
        expected_rule_id="RULE_DEFAULT_VALUE_CHANGE",
    ),
]
