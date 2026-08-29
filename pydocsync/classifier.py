"""AST Change Impact Classifier Engine for PyDocSync.

WHAT IS THIS?
-------------
An extensible, rule-based classifier that inspects AST deltas and categorizes
transformations into HIGH_IMPACT, CANDIDATE_LOW_IMPACT, or UNKNOWN with structured
evidence and human-readable reasoning.
"""

import ast
from dataclasses import dataclass
from enum import Enum

from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.fingerprint import FingerprintSet


class ChangeClassification(str, Enum):
    """Change impact classification categories."""

    HIGH_IMPACT = "HIGH_IMPACT"
    CANDIDATE_LOW_IMPACT = "CANDIDATE_LOW_IMPACT"
    UNKNOWN = "UNKNOWN"


@dataclass
class RuleResult:
    """Outcome of evaluating a single classification rule against an AST delta."""

    classification: ChangeClassification
    rule_id: str
    evidence: str
    reason: str
    review_required: bool = False

    def __post_init__(self) -> None:
        if self.classification in (ChangeClassification.HIGH_IMPACT, ChangeClassification.UNKNOWN):
            self.review_required = True



class BaseClassificationRule:
    """Base interface for an AST change classification rule."""

    rule_id: str = "BASE_RULE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        """Inspect symbol delta and return RuleResult if matched, else None."""
        raise NotImplementedError


class DefaultValueChangeRule(BaseClassificationRule):
    """Detects changes in default parameter values in callable signatures."""

    rule_id = "RULE_DEFAULT_VALUE_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.api != new_fp.api:
            # Check if parameter count/names match but defaults differed
            old_node = old_sym.raw_node
            new_node = new_sym.raw_node
            if isinstance(old_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and isinstance(
                new_node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                old_defaults = [ast.unparse(d) for d in old_node.args.defaults]
                new_defaults = [ast.unparse(d) for d in new_node.args.defaults]
                if old_defaults != new_defaults:
                    return RuleResult(
                        classification=ChangeClassification.HIGH_IMPACT,
                        rule_id=self.rule_id,
                        evidence=f"defaults changed: {old_defaults} -> {new_defaults}",
                        reason="Callable default parameter value was altered, affecting caller behavior.",
                    )
        return None


class ExceptionBehaviorChangeRule(BaseClassificationRule):
    """Detects alterations in exception types or constraint string literals."""

    rule_id = "RULE_EXCEPTION_BEHAVIOR_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.raise_type != new_fp.raise_type or old_fp.raise_detail != new_fp.raise_detail:
            evidence_parts: list[str] = []
            if old_fp.raise_type != new_fp.raise_type:
                evidence_parts.append(f"exception types altered")
            if old_fp.raise_detail != new_fp.raise_detail:
                evidence_parts.append(f"exception details/constraints altered")

            return RuleResult(
                classification=ChangeClassification.HIGH_IMPACT,
                rule_id=self.rule_id,
                evidence=", ".join(evidence_parts),
                reason="Observable exception types or constraint message literals were added or modified.",
            )
        return None


class TypeContractChangeRule(BaseClassificationRule):
    """Detects modifications in parameter or return type annotations."""

    rule_id = "RULE_TYPE_CONTRACT_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.types != new_fp.types:
            return RuleResult(
                classification=ChangeClassification.HIGH_IMPACT,
                rule_id=self.rule_id,
                evidence="Type annotations changed on arguments or return value",
                reason="Type contract altered, potentially invalidating documented argument/return expectations.",
            )
        return None


class APISignatureChangeRule(BaseClassificationRule):
    """Detects structural signature alterations: positional vs kw-only, parameter order/names, decorators."""

    rule_id = "RULE_API_SIGNATURE_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.api != new_fp.api:
            # Check if change is due to custom/dynamic decorators
            old_decs = [ast.unparse(d) for d in getattr(old_sym.raw_node, "decorator_list", [])]
            new_decs = [ast.unparse(d) for d in getattr(new_sym.raw_node, "decorator_list", [])]
            if old_decs != new_decs:
                # Standard builtin decorators
                standard_decs = {"property", "staticmethod", "classmethod", "lru_cache", "override"}
                has_custom = any(d.split("(")[0].replace("@", "") not in standard_decs for d in (old_decs + new_decs))
                if has_custom:
                    return RuleResult(
                        classification=ChangeClassification.UNKNOWN,
                        rule_id="RULE_UNKNOWN_METAPROGRAMMING",
                        evidence=f"Custom/dynamic decorator altered: {old_decs} -> {new_decs}",
                        reason="Dynamic decorator or metaprogramming layer added/modified; requires human/agent review.",
                    )

            return RuleResult(
                classification=ChangeClassification.HIGH_IMPACT,
                rule_id=self.rule_id,
                evidence="Callable parameter order, kind (positional/keyword-only), or structure modified",
                reason="Public calling signature modified, potentially breaking existing caller arguments.",
            )
        return None





class ThresholdConstantRule(BaseClassificationRule):
    """Detects modifications to internal literal constants and numeric thresholds."""

    rule_id = "RULE_THRESHOLD_CONSTANT_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.code != new_fp.code:
            # Check for constant value shifts
            old_consts = [n.value for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, ast.Constant)]
            new_consts = [n.value for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, ast.Constant)]
            if sorted(str(c) for c in old_consts) != sorted(str(c) for c in new_consts):
                return RuleResult(
                    classification=ChangeClassification.HIGH_IMPACT,
                    rule_id=self.rule_id,
                    evidence=f"Constants altered: {old_consts} -> {new_consts}",
                    reason="Numeric threshold, retry limit, or string constant modified in implementation.",
                )
        return None


class ControlFlowChangeRule(BaseClassificationRule):
    """Detects changes in branching return paths, async/await, or generator yields."""

    rule_id = "RULE_CONTROL_FLOW_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.code != new_fp.code:
            old_returns = len([n for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, ast.Return)])
            new_returns = len([n for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, ast.Return)])
            old_awaits = len([n for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, ast.Await)])
            new_awaits = len([n for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, ast.Await)])
            old_yields = len([n for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, (ast.Yield, ast.YieldFrom))])
            new_yields = len([n for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, (ast.Yield, ast.YieldFrom))])

            if (old_returns != new_returns) or (old_awaits != new_awaits) or (old_yields != new_yields):
                return RuleResult(
                    classification=ChangeClassification.HIGH_IMPACT,
                    rule_id=self.rule_id,
                    evidence=f"Returns: {old_returns}->{new_returns}, Awaits: {old_awaits}->{new_awaits}, Yields: {old_yields}->{new_yields}",
                    reason="Control flow structure, asynchronous execution, or generator yield paths altered.",
                )
        return None


class CallSequenceOrderRule(BaseClassificationRule):
    """Detects permutation/reordering of identical sub-function calls (evaluation order shifts)."""

    rule_id = "RULE_CALL_SEQUENCE_ORDER_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.code != new_fp.code:
            old_calls = [ast.unparse(n) for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, ast.Call)]
            new_calls = [ast.unparse(n) for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, ast.Call)]
            # If the same set of calls exists in different order (permutation)
            if len(old_calls) > 1 and len(old_calls) == len(new_calls) and sorted(old_calls) == sorted(new_calls) and old_calls != new_calls:
                return RuleResult(
                    classification=ChangeClassification.HIGH_IMPACT,
                    rule_id=self.rule_id,
                    evidence=f"Call invocation sequence shifted: {old_calls} -> {new_calls}",
                    reason="Sub-function call order altered; potential side-effect order divergence.",
                )
        return None



class DictKeyOrderRule(BaseClassificationRule):
    """Detects dictionary literal key insertion order changes."""

    rule_id = "RULE_DICT_KEY_ORDER_CHANGE"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.code != new_fp.code:
            old_dicts = [[ast.unparse(k) for k in n.keys if k is not None] for n in ast.walk(old_sym.canonical_body_ast) if isinstance(n, ast.Dict)]
            new_dicts = [[ast.unparse(k) for k in n.keys if k is not None] for n in ast.walk(new_sym.canonical_body_ast) if isinstance(n, ast.Dict)]
            if old_dicts != new_dicts:
                return RuleResult(
                    classification=ChangeClassification.HIGH_IMPACT,
                    rule_id=self.rule_id,
                    evidence=f"Dict key order altered: {old_dicts} -> {new_dicts}",
                    reason="Dictionary insertion order altered; changes iteration sequence.",
                )
        return None


class LocalRefactorRule(BaseClassificationRule):
    """Detects candidate safe refactors: variable renames, simple comprehensions."""

    rule_id = "RULE_LOCAL_VAR_RENAME"

    def evaluate(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult | None:
        if old_fp.code != new_fp.code and old_fp.api == new_fp.api and old_fp.types == new_fp.types and old_fp.raise_type == new_fp.raise_type:
            return RuleResult(
                classification=ChangeClassification.CANDIDATE_LOW_IMPACT,
                rule_id=self.rule_id,
                evidence="Local variable or structure modified with identical signature and error contract",
                reason="Candidate safe internal refactoring without observable interface or exception change.",
            )
        return None


class ASTChangeImpactClassifier:
    """Evaluates symbol changes across an ordered collection of classification rules (v0.2)."""

    def __init__(self, rules: list[BaseClassificationRule] | None = None) -> None:
        self.rules: list[BaseClassificationRule] = rules or [
            DefaultValueChangeRule(),
            ExceptionBehaviorChangeRule(),
            TypeContractChangeRule(),
            APISignatureChangeRule(),
            ThresholdConstantRule(),
            ControlFlowChangeRule(),
            CallSequenceOrderRule(),
            DictKeyOrderRule(),
            LocalRefactorRule(),
        ]

    def classify_change(
        self,
        old_sym: SymbolRepresentation,
        new_sym: SymbolRepresentation,
        old_fp: FingerprintSet,
        new_fp: FingerprintSet,
    ) -> RuleResult:
        """Classify AST delta against rules; fallback to UNKNOWN if unclassified."""
        # If all fingerprints are identical, zero semantic change
        if old_fp == new_fp:
            return RuleResult(
                classification=ChangeClassification.CANDIDATE_LOW_IMPACT,
                rule_id="RULE_NO_SEMANTIC_CHANGE",
                evidence="All representation fingerprints identical",
                reason="Whitespace, comments, or non-semantic formatting changes only.",
            )

        for rule in self.rules:
            result = rule.evaluate(old_sym, new_sym, old_fp, new_fp)
            if result is not None:
                return result

        # Fallback to UNKNOWN
        return RuleResult(
            classification=ChangeClassification.UNKNOWN,
            rule_id="RULE_UNKNOWN_METAPROGRAMMING",
            evidence="Complex or unclassified AST delta",
            reason="Unrecognized AST transformation; fail-safe to documentation review obligation.",
        )
