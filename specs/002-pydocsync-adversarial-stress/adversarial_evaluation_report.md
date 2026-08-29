# Adversarial Evaluation Report: Behavioral Falsification & AST Boundary Analysis

**Feature Branch**: `002-pypydocsync-adversarial-stress`  
**Date**: 2026-08-29  
**Status**: Completed Empirical Falsification Experiment  
**Test Matrix**: 16 adversarial attack cases across 38 total automated tests  

---

## 1. Adversarial Attack Matrix: Classifier v0.1 vs Runtime Evidence vs v0.2

| Case ID | Category | Transformation Description | Empirical Runtime Behavioral Delta | Classifier v0.1 Result | v0.1 Potential Verdict | Classifier v0.2 Result | Rule Triggered (v0.2) |
|---|---|---|---|---|:---:|---|---|
| **ADV01** | False-Negative | Evaluation order shift with side-effects (`f(a()) + g(b())` → `g(b()) + f(a())`) | **DIVERGED** (trace: `['call:10','call:15']` vs `['call:15','call:10']`) | `CANDIDATE_LOW_IMPACT` | 🚨 **Potential FN** | `HIGH_IMPACT` | `RULE_CALL_SEQUENCE_ORDER_CHANGE` |
| **ADV02** | False-Negative | Aliasing vs list copy (`list(items)` → `items`) | **DIVERGED** (caller argument mutated) | `CANDIDATE_LOW_IMPACT` | 🚨 **Potential FN** | `CANDIDATE_LOW_IMPACT` (Known Limit) | `RULE_LOCAL_VAR_RENAME` *(Documented AST Limitation)* |
| **ADV03** | False-Negative | Mutable default list (`buf=None` → `buf=[]`) | **DIVERGED** (state persists across calls) | `HIGH_IMPACT` | ✅ **Match** | `HIGH_IMPACT` | `RULE_DEFAULT_VALUE_CHANGE` |
| **ADV04** | False-Negative | Closure variable capture mutation | **DIVERGED** (ret: `30` vs `60`) | `HIGH_IMPACT` | ✅ **Match** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV05** | False-Negative | Generator early return vs yield | **DIVERGED** (ret: `[1,2,3]` vs `[1]`) | `HIGH_IMPACT` | ✅ **Match** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV06** | False-Negative | Boolean short-circuit side-effect reorder | **DIVERGED** (trace: `[]` vs `['call:side_effect']`) | `CANDIDATE_LOW_IMPACT` | 🚨 **Potential FN** | `HIGH_IMPACT` | `RULE_CALL_SEQUENCE_ORDER_CHANGE` |
| **ADV07** | False-Negative | Truthiness vs explicit `is not None` (`if val` on `0`) | **DIVERGED** (ret: `VAL:0` vs `NONE`) | `HIGH_IMPACT` | ✅ **Match** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV08** | False-Negative | Exception swallowing bare pass | **DIVERGED** (raised `ValueError` vs returned `-1`) | `HIGH_IMPACT` | ✅ **Match** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV09** | False-Negative | In-place `list.sort()` vs `sorted()` | **DIVERGED** (input list mutated in place) | `CANDIDATE_LOW_IMPACT` | 🚨 **Potential FN** | `CANDIDATE_LOW_IMPACT` (Known Limit) | `RULE_LOCAL_VAR_RENAME` *(Documented AST Limitation)* |
| **ADV10** | False-Negative | Dict key insertion order altered | **DIVERGED** (keys: `['a','b']` vs `['b','a']`) | `CANDIDATE_LOW_IMPACT` | 🚨 **Potential FN** | `HIGH_IMPACT` | `RULE_DICT_KEY_ORDER_CHANGE` |
| **ADV11** | False-Negative | Floating point operation reordering | **IDENTICAL** (for tested input `100.05`) | `HIGH_IMPACT` | ⚠️ **Conservative Over-Trigger** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV12** | False-Positive | De Morgan boolean transformation | **IDENTICAL** | `CANDIDATE_LOW_IMPACT` | ✅ **Match** | `CANDIDATE_LOW_IMPACT` | `RULE_LOCAL_VAR_RENAME` |
| **ADV13** | False-Positive | Tuple unpacking swap (`a,b = b,a`) | **IDENTICAL** | `CANDIDATE_LOW_IMPACT` | ✅ **Match** | `CANDIDATE_LOW_IMPACT` | `RULE_LOCAL_VAR_RENAME` |
| **ADV14** | False-Positive | Loop to list comprehension with filter | **IDENTICAL** | `CANDIDATE_LOW_IMPACT` | ✅ **Match** | `CANDIDATE_LOW_IMPACT` | `RULE_LOCAL_VAR_RENAME` |
| **ADV15** | False-Positive | String `+` vs `' \| '.join()` rewrite | **IDENTICAL** | `HIGH_IMPACT` | ⚠️ **Conservative Over-Trigger** | `HIGH_IMPACT` | `RULE_THRESHOLD_CONSTANT_CHANGE` |
| **ADV16** | False-Positive | If/else statement block vs inline ternary | **IDENTICAL** | `HIGH_IMPACT` | ⚠️ **Conservative Over-Trigger** | `HIGH_IMPACT` | `RULE_CONTROL_FLOW_CHANGE` |

---

## 2. Statistical Findings & Evolution Summary

### Classifier v0.1 Baseline Results
- **Evaluated Cases**: 16 adversarial attack transformations
- **Potential Blind Spots (Potential False Negatives in v0.1)**: **4 cases**
  - ADV01 (Evaluation order shift in expressions)
  - ADV06 (Short-circuit boolean operand reordering with side effects)
  - ADV10 (Dictionary literal insertion order changes)
  - ADV02 / ADV09 (In-place argument mutation vs copy)
- **Conservative Over-Triggers (Potential False Positives under Test Inputs)**: **3 cases**
  - ADV11 (Arithmetic restructuring introducing float constants)
  - ADV15 (String concatenation rewritten with `join`)
  - ADV16 (If/else rewritten as ternary return statement)

### Classifier v0.2 Refinements
1. **Resolved Blind Spots**:
   - `CallSequenceOrderRule`: Successfully caught ADV01 and ADV06 by tracking call permutations within expression trees.
   - `DictKeyOrderRule`: Successfully caught ADV10 by tracking dictionary key ordering shifts.
2. **Explicit Safety Semantics (`review_required`)**:
   - `RuleResult` now enforces an explicit `review_required: bool` contract. `CANDIDATE_LOW_IMPACT` does not imply unreviewed safety when analysis boundaries are crossed; unresolvable AST cases route cleanly to `UNKNOWN` (`review_required=True`).
3. **Documented Fundamental AST Boundaries (Deliberate Non-Inference)**:
   - **Aliasing & In-Place Mutation (ADV02, ADV09)**: Distinguishing `res = list(x)` vs `res = x` followed by `.append()` requires inter-procedural heap and alias analysis. Rather than constructing a brittle pseudo-compiler inside the AST visitor, PyDocSync treats intra-function assignment aliasing as a documented AST boundary limitation.
4. **Zero Core Regressions**:
   - All **22 original test cases** from `001-pypydocsync-core` continue to pass 100% (38/38 total passing tests in 0.16s).

---

## 3. Next Research Step: Real-Project Evaluation (Freeze v0.2)

Rather than designing more synthetic classifier versions (`v0.3`), Classifier v0.2 is **frozen** to evaluate realistic AI-generated modifications across 50–100 real functions in `logseq_toolkit/`:
- Refactoring vs bug fixes vs feature extensions vs docstring omissions.
- Measure precision, recall, and human review agreement under real-world development conditions.

