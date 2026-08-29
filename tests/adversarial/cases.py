"""Adversarial stress test cases for PyDocSync behavioral falsification.

WHAT IS THIS?
-------------
Contains 16 adversarial attack cases across two primary matrices:
- False-Negative Attacks (11 cases: evaluation order, mutable defaults, closure mutations,
  generator early return, boolean short-circuits, aliasing/identity, exception swallowing, etc.)
- False-Positive Attacks (5 cases: De Morgan boolean equivalents, tuple swaps, etc.)
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdversarialCase:
    case_id: str
    category: str  # "FALSE_NEGATIVE_ATTACK" or "FALSE_POSITIVE_ATTACK"
    description: str
    func_name: str
    initial_code: str
    transformed_code: str
    test_inputs: list[tuple[tuple, dict]] = field(default_factory=list)
    expected_runtime_identical: bool = False


ADVERSARIAL_CASES: list[AdversarialCase] = [
    # -------------------------------------------------------------
    # False-Negative Attacks (Dangerous transformations that look safe to naive AST)
    # -------------------------------------------------------------
    # ADV01: Evaluation Order Shift with Side Effects
    AdversarialCase(
        case_id="ADV01_EVAL_ORDER_SHIFT",
        category="FALSE_NEGATIVE_ATTACK",
        description="Reordered function argument calls when sub-calls have side-effects",
        func_name="compute_order",
        initial_code='''def compute_order(x: int) -> int:
    """Compute combined order."""
    return log_call(x * 2) + log_call(x * 3)
''',
        transformed_code='''def compute_order(x: int) -> int:
    """Compute combined order."""
    return log_call(x * 3) + log_call(x * 2)
''',
        test_inputs=[((5,), {})],
        expected_runtime_identical=False,
    ),

    # ADV02: Aliasing vs In-Place Mutation
    AdversarialCase(
        case_id="ADV02_ALIASING_MUTATION",
        category="FALSE_NEGATIVE_ATTACK",
        description="Changed list copy to reference aliasing before mutating input",
        func_name="append_tag",
        initial_code='''def append_tag(items: list) -> list:
    """Append tag to copy of list."""
    res = list(items)
    res.append("TAG")
    return res
''',
        transformed_code='''def append_tag(items: list) -> list:
    """Append tag to copy of list."""
    res = items
    res.append("TAG")
    return res
''',
        test_inputs=[(([1, 2],), {})],
        expected_runtime_identical=False,
    ),

    # ADV03: Mutable Default Parameter Trap
    AdversarialCase(
        case_id="ADV03_MUTABLE_DEFAULT_TRAP",
        category="FALSE_NEGATIVE_ATTACK",
        description="Changed None default to persistent mutable list default []",
        func_name="collect_items",
        initial_code='''def collect_items(val: int, buf: list = None) -> list:
    """Collect items into buffer."""
    if buf is None:
        buf = []
    buf.append(val)
    return buf
''',
        transformed_code='''def collect_items(val: int, buf: list = []) -> list:
    """Collect items into buffer."""
    buf.append(val)
    return buf
''',
        test_inputs=[((1,), {}), ((2,), {})],
        expected_runtime_identical=False,
    ),

    # ADV04: Closure Variable Capture Mutation
    AdversarialCase(
        case_id="ADV04_CLOSURE_CAPTURE_MUTATION",
        category="FALSE_NEGATIVE_ATTACK",
        description="Closure variable modified after inner function creation",
        func_name="make_multiplier",
        initial_code='''def make_multiplier(base: int):
    """Return multiplier function."""
    mult = base
    def fn(x: int) -> int:
        return x * mult
    return fn(10)
''',
        transformed_code='''def make_multiplier(base: int):
    """Return multiplier function."""
    mult = base
    def fn(x: int) -> int:
        return x * mult
    mult = base * 2
    return fn(10)
''',
        test_inputs=[((3,), {})],
        expected_runtime_identical=False,
    ),

    # ADV05: Generator Early Return vs Yield Exhaustion
    AdversarialCase(
        case_id="ADV05_GENERATOR_EARLY_RETURN",
        category="FALSE_NEGATIVE_ATTACK",
        description="Added an early return in generator body terminating yield sequence",
        func_name="gen_nums",
        initial_code='''def gen_nums(limit: int) -> list:
    """Generate numbers up to limit."""
    def _gen():
        yield 1
        yield 2
        yield 3
    return list(_gen())
''',
        transformed_code='''def gen_nums(limit: int) -> list:
    """Generate numbers up to limit."""
    def _gen():
        yield 1
        if limit < 5:
            return
        yield 2
        yield 3
    return list(_gen())
''',
        test_inputs=[((2,), {})],
        expected_runtime_identical=False,
    ),

    # ADV06: Short-Circuit Boolean Side Effect
    AdversarialCase(
        case_id="ADV06_SHORT_CIRCUIT_SIDE_EFFECT",
        category="FALSE_NEGATIVE_ATTACK",
        description="Reordered boolean operands where right operand has side effect",
        func_name="check_flag",
        initial_code='''def check_flag(flag: bool) -> bool:
    """Check flag with logging."""
    return flag or (log_call("side_effect") == "side_effect")
''',
        transformed_code='''def check_flag(flag: bool) -> bool:
    """Check flag with logging."""
    return (log_call("side_effect") == "side_effect") or flag
''',
        test_inputs=[((True,), {})],
        expected_runtime_identical=False,
    ),

    # ADV07: Truthiness vs Explicit None Check
    AdversarialCase(
        case_id="ADV07_TRUTHINESS_VS_NONE",
        category="FALSE_NEGATIVE_ATTACK",
        description="Replaced 'is not None' with 'if val' breaking on 0/empty values",
        func_name="format_val",
        initial_code='''def format_val(val: int | None) -> str:
    """Format value."""
    if val is not None:
        return f"VAL:{val}"
    return "NONE"
''',
        transformed_code='''def format_val(val: int | None) -> str:
    """Format value."""
    if val:
        return f"VAL:{val}"
    return "NONE"
''',
        test_inputs=[((0,), {})],
        expected_runtime_identical=False,
    ),

    # ADV08: Exception Swallowing via Bare Pass
    AdversarialCase(
        case_id="ADV08_EXCEPTION_SWALLOWING",
        category="FALSE_NEGATIVE_ATTACK",
        description="Swallowed ValueError silently instead of propagating",
        func_name="parse_or_fail",
        initial_code='''def parse_or_fail(raw: str) -> int:
    """Parse integer or fail."""
    return int(raw)
''',
        transformed_code='''def parse_or_fail(raw: str) -> int:
    """Parse integer or fail."""
    try:
        return int(raw)
    except ValueError:
        return -1
''',
        test_inputs=[(("invalid",), {})],
        expected_runtime_identical=False,
    ),

    # ADV09: In-place sort vs sorted() copy
    AdversarialCase(
        case_id="ADV09_INPLACE_SORT_MUTATION",
        category="FALSE_NEGATIVE_ATTACK",
        description="Replaced sorted() with in-place list.sort() mutating argument",
        func_name="sort_helper",
        initial_code='''def sort_helper(nums: list) -> list:
    """Sort list non-destructively."""
    return sorted(nums)
''',
        transformed_code='''def sort_helper(nums: list) -> list:
    """Sort list non-destructively."""
    nums.sort()
    return nums
''',
        test_inputs=[(([3, 1, 2],), {})],
        expected_runtime_identical=True,  # Return value is identical, but caller object identity is mutated!
    ),

    # ADV10: Dict Key Iteration Order Dependency
    AdversarialCase(
        case_id="ADV10_DICT_KEY_ORDER",
        category="FALSE_NEGATIVE_ATTACK",
        description="Changed dictionary insertion order affecting iteration output",
        func_name="combine_keys",
        initial_code='''def combine_keys() -> list:
    """Get key order."""
    d = {"a": 1, "b": 2}
    return list(d.keys())
''',
        transformed_code='''def combine_keys() -> list:
    """Get key order."""
    d = {"b": 2, "a": 1}
    return list(d.keys())
''',
        test_inputs=[((), {})],
        expected_runtime_identical=False,
    ),

    # ADV11: Floating point rounding semantics
    AdversarialCase(
        case_id="ADV11_FLOAT_ROUNDING",
        category="FALSE_NEGATIVE_ATTACK",
        description="Reordered arithmetic operations causing float precision drift",
        func_name="calc_discount",
        initial_code='''def calc_discount(price: float, rate: float) -> float:
    """Calculate discounted price."""
    return price - (price * rate)
''',
        transformed_code='''def calc_discount(price: float, rate: float) -> float:
    """Calculate discounted price."""
    return price * (1.0 - rate)
''',
        test_inputs=[((100.05, 0.1), {})],
        expected_runtime_identical=True,
    ),

    # -------------------------------------------------------------
    # False-Positive Attacks (Complex refactorings that are strictly safe)
    # -------------------------------------------------------------
    # ADV12: De Morgan's Boolean Law Transformation
    AdversarialCase(
        case_id="ADV12_DE_MORGAN_EQUIVALENCE",
        category="FALSE_POSITIVE_ATTACK",
        description="Rewrote not (a and b) as (not a) or (not b)",
        func_name="is_valid_pair",
        initial_code='''def is_valid_pair(a: bool, b: bool) -> bool:
    """Check pair validity."""
    return not (a and b)
''',
        transformed_code='''def is_valid_pair(a: bool, b: bool) -> bool:
    """Check pair validity."""
    return (not a) or (not b)
''',
        test_inputs=[((True, True), {}), ((True, False), {}), ((False, False), {})],
        expected_runtime_identical=True,
    ),

    # ADV13: Tuple Unpacking Swap
    AdversarialCase(
        case_id="ADV13_TUPLE_SWAP",
        category="FALSE_POSITIVE_ATTACK",
        description="Rewrote temporary variable swap with Python tuple unpacking",
        func_name="swap_elements",
        initial_code='''def swap_elements(a: int, b: int) -> tuple[int, int]:
    """Swap two integers."""
    temp = a
    a = b
    b = temp
    return a, b
''',
        transformed_code='''def swap_elements(a: int, b: int) -> tuple[int, int]:
    """Swap two integers."""
    a, b = b, a
    return a, b
''',
        test_inputs=[((10, 20), {})],
        expected_runtime_identical=True,
    ),

    # ADV14: Equivalent List Comprehension with Filter
    AdversarialCase(
        case_id="ADV14_EQUIVALENT_COMPREHENSION",
        category="FALSE_POSITIVE_ATTACK",
        description="Rewrote loop with conditional append to list comprehension",
        func_name="get_evens",
        initial_code='''def get_evens(nums: list[int]) -> list[int]:
    """Filter even numbers."""
    out = []
    for n in nums:
        if n % 2 == 0:
            out.append(n)
    return out
''',
        transformed_code='''def get_evens(nums: list[int]) -> list[int]:
    """Filter even numbers."""
    return [n for n in nums if n % 2 == 0]
''',
        test_inputs=[(([1, 2, 3, 4, 5, 6],), {})],
        expected_runtime_identical=True,
    ),

    # ADV15: Multi-line String Concatenation Equivalence
    AdversarialCase(
        case_id="ADV15_STRING_CONCAT_EQUIVALENCE",
        category="FALSE_POSITIVE_ATTACK",
        description="Rewrote + string concatenation to join() list",
        func_name="build_msg",
        initial_code='''def build_msg(user: str, act: str) -> str:
    """Build message string."""
    return "User: " + user + " | Action: " + act
''',
        transformed_code='''def build_msg(user: str, act: str) -> str:
    """Build message string."""
    return " | ".join(["User: " + user, "Action: " + act])
''',
        test_inputs=[(("alice", "login"), {})],
        expected_runtime_identical=True,
    ),

    # ADV16: Ternary Conditional Expression Equivalence
    AdversarialCase(
        case_id="ADV16_TERNARY_EQUIVALENCE",
        category="FALSE_POSITIVE_ATTACK",
        description="Rewrote if/else statement block as inline ternary expression",
        func_name="clamp_max",
        initial_code='''def clamp_max(val: int, cap: int) -> int:
    """Clamp value to cap."""
    if val > cap:
        return cap
    else:
        return val
''',
        transformed_code='''def clamp_max(val: int, cap: int) -> int:
    """Clamp value to cap."""
    return cap if val > cap else val
''',
        test_inputs=[((10, 5), {}), ((3, 5), {})],
        expected_runtime_identical=True,
    ),
]
