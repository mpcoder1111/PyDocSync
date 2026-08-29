"""Dual-Execution Runtime Evidence Harness for PyDocSync.

WHAT IS THIS?
-------------
Executes pairs of Python callable snippets against identical controlled inputs
in isolated in-memory namespaces, capturing return values, exception traces,
and call-order logs to measure empirical behavioral equivalence.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class RuntimeExecutionResult:
    """Captured runtime execution state for a single snippet execution."""

    return_value: Any = None
    exception_type: str | None = None
    exception_message: str | None = None
    side_effects: list[str] = field(default_factory=list)
    state_mutations: dict[str, Any] = field(default_factory=dict)


def execute_callable_snippet(
    code_str: str, func_name: str, args: tuple = (), kwargs: dict | None = None
) -> RuntimeExecutionResult:
    """Execute a function snippet in an isolated namespace and capture outputs and traces."""
    kwargs = kwargs or {}
    trace_log: list[str] = []

    # Mock helper tracer available in snippet scope
    def trace(event_name: str) -> None:
        trace_log.append(str(event_name))

    # Helper dummy objects for order tracking
    def log_call(val: Any) -> Any:
        trace_log.append(f"call:{val}")
        return val

    namespace: dict[str, Any] = {
        "trace": trace,
        "log_call": log_call,
        "__builtins__": __builtins__,
    }

    try:
        exec(code_str, namespace)
        target_func = namespace.get(func_name)
        if not callable(target_func):
            return RuntimeExecutionResult(
                exception_type="NameError",
                exception_message=f"Function '{func_name}' not found in executed snippet",
            )

        ret = target_func(*args, **kwargs)
        return RuntimeExecutionResult(
            return_value=ret,
            side_effects=list(trace_log),
        )
    except Exception as exc:
        return RuntimeExecutionResult(
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            side_effects=list(trace_log),
        )


def compare_runtime_behavior(
    initial_code: str,
    transformed_code: str,
    func_name: str,
    test_inputs: list[tuple[tuple, dict]],
) -> tuple[bool, str]:
    """Execute both snippets across all test inputs; return (is_behavior_identical, evidence_diff)."""
    for i, (args, kwargs) in enumerate(test_inputs):
        res1 = execute_callable_snippet(initial_code, func_name, args, kwargs)
        res2 = execute_callable_snippet(transformed_code, func_name, args, kwargs)

        if (
            res1.return_value != res2.return_value
            or res1.exception_type != res2.exception_type
            or res1.exception_message != res2.exception_message
            or res1.side_effects != res2.side_effects
        ):
            diff = (
                f"Input[{i}] args={args}: "
                f"Initial(ret={res1.return_value}, exc={res1.exception_type}, trace={res1.side_effects}) != "
                f"Transformed(ret={res2.return_value}, exc={res2.exception_type}, trace={res2.side_effects})"
            )
            return False, diff

    return True, "All test inputs produced identical outputs, exceptions, and side-effect traces."
