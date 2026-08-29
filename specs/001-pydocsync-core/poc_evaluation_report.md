# Empirical Evidence & PoC Evaluation Report: PyDocSync Core

**Feature Branch**: `001-pypydocsync-core`  
**Date**: 2026-08-29  
**Status**: Completed PoC  
**Test Suite**: 22 unit, integration, and AI-agent workflow tests  

---

## 1. Stage-by-Stage Performance Profiling

| Stage | Operations | Total Duration (ms) | Avg per Symbol (ms) | Target Budget |
|---|---|---|---|---|
| **AST Parsing** | 30 snippets parsed | 3.29 ms | 0.11 ms | < 200 ms |
| **Fingerprint Generation** | 30 symbols (7 representations each) | 1.57 ms | 0.05 ms | < 150 ms |
| **AST Change Classification** | 15 code transformation deltas | 0.36 ms | 0.02 ms | < 100 ms |
| **Modular Baseline Lockfile I/O** | Save + Load JSON | 1.84 ms | 0.09 ms | < 50 ms |
| **Total Pipeline** | **50 functions simulated** | **7.06 ms** | **0.14 ms** | **< 500 ms (Passed: 7.06ms vs 500ms budget)** |

---

## 2. Empirical Transformation Case Results (Hypotheses vs Findings)

| Case ID | Transformation Type | Expected Classification | Actual Classification | Rule Triggered | Evidence Captured | Correct? |
|---|---|---|---|---|---|:---:|
| **TC01** | Local variable rename | CANDIDATE_LOW_IMPACT | CANDIDATE_LOW_IMPACT | `RULE_LOCAL_VAR_RENAME` | Local variable modified; API/TYPE/RAISE identical | ✅ |
| **TC02** | Default parameter value changed (`30 -> 60`) | HIGH_IMPACT | HIGH_IMPACT | `RULE_DEFAULT_VALUE_CHANGE` | defaults changed: `['30'] -> ['60']` | ✅ |
| **TC03** | Internal threshold changed (`3 -> 5`) | HIGH_IMPACT | HIGH_IMPACT | `RULE_THRESHOLD_CONSTANT_CHANGE` | Constants altered: `[3] -> [5]` | ✅ |
| **TC04** | New exception type added (`ValueError`) | HIGH_IMPACT | HIGH_IMPACT | `RULE_EXCEPTION_BEHAVIOR_CHANGE` | exception types altered | ✅ |
| **TC05** | Exception constraint text altered | HIGH_IMPACT | HIGH_IMPACT | `RULE_EXCEPTION_BEHAVIOR_CHANGE` | exception details/constraints altered | ✅ |
| **TC06** | Loop to list comprehension | CANDIDATE_LOW_IMPACT | CANDIDATE_LOW_IMPACT | `RULE_LOCAL_VAR_RENAME` | Local structure modified; interface identical | ✅ |
| **TC07** | Async function await logic added | HIGH_IMPACT | HIGH_IMPACT | `RULE_CONTROL_FLOW_CHANGE` | Awaits: `0 -> 1` | ✅ |
| **TC08** | Generator `yield` paths added | HIGH_IMPACT | HIGH_IMPACT | `RULE_CONTROL_FLOW_CHANGE` | Yields: `0 -> 2` | ✅ |
| **TC09** | Property getter internal calculation | CANDIDATE_LOW_IMPACT | CANDIDATE_LOW_IMPACT | `RULE_LOCAL_VAR_RENAME` | Local structure modified; interface identical | ✅ |
| **TC10** | Type annotation refined (`int -> int \| None`) | HIGH_IMPACT | HIGH_IMPACT | `RULE_TYPE_CONTRACT_CHANGE` | Type annotations changed on arguments/return | ✅ |
| **TC11** | Dynamic custom decorator added | UNKNOWN | UNKNOWN | `RULE_UNKNOWN_METAPROGRAMMING` | Custom/dynamic decorator altered | ✅ |
| **TC12** | Non-semantic comments & whitespace | CANDIDATE_LOW_IMPACT | CANDIDATE_LOW_IMPACT | `RULE_NO_SEMANTIC_CHANGE` | All representation fingerprints identical | ✅ |
| **TC13** | Branching return path added | HIGH_IMPACT | HIGH_IMPACT | `RULE_CONTROL_FLOW_CHANGE` | Returns: `1 -> 2` | ✅ |
| **TC14** | Positional to keyword-only (`*`) | HIGH_IMPACT | HIGH_IMPACT | `RULE_API_SIGNATURE_CHANGE` | Callable parameter kind/structure modified | ✅ |
| **TC15** | Dataclass default field altered | HIGH_IMPACT | HIGH_IMPACT | `RULE_DEFAULT_VALUE_CHANGE` | defaults changed: `['3'] -> ['10']` | ✅ |

---

## 3. Metrics Summary

- **Total Test Cases**: 15 synthetic cases + 7 integration/workflow tests = **22 automated tests**
- **Test Pass Rate**: **100% (22/22 passed)**
- **Observed False-Positive Rate on Predefined Safe-Refactor Fixtures**: **0.0%** (Observed across the 4 specific safe refactor fixture cases: TC01, TC06, TC09, TC12)
- **Observed False-Negative Rate on Predefined Behavior-Impact Fixtures**: **0.0%** (Observed across the 11 specific behavioral transformation fixture cases)
- **AI Agent Self-Correction Loop**: Verified end-to-end in `test_agent_workflow.py`.

---

## 4. Key PoC Learnings & Evolutions

1. **Decorator Metaprogramming (Discovery from TC11)**:
   - *Finding*: Generic API signature hashing initially treated custom dynamic decorators as high-impact signature modifications.
   - *Refinement*: Differentiated standard built-ins (`@property`, `@staticmethod`, `@classmethod`, `@lru_cache`) from unknown decorators, ensuring dynamic wrappers fail-safe to `UNKNOWN` (`Review Trigger`).
2. **Actionable Evidence Payload for AI Agents**:
   - Rather than binary pass/fail hashes, every `PYPYDOCSYNC001` envelope delivers the exact difference (e.g. `defaults changed: ['30'] -> ['60']`) and the exact CLI remediation command.

---

## 5. Next Research Steps: Adversarial Suite & CKG Transitive Impact

1. **Adversarial Benchmark Expansion ("Try to break PyDocSync")**:
   - *Safe-looking but dangerous*: Evaluation order shifts, mutable default side-effects, closure mutation, generator early termination.
   - *Dangerous-looking but safe*: Advanced equivalent comprehension rewrites, multi-line formatting equivalents.
2. **CKG Transitive Impact Analysis (Phase 2)**:
   - Integrating with Spashta CKG to track callee modifications (`C()` changes) up the call graph to detect whether caller documentation (`A()` or `B()`) requires a review trigger even when their individual AST fingerprints remain untouched.
3. **Empirical Calibration on 20–50 Real Project Functions**:
   - Run against active code in `logseq_toolkit/` and document every classifier boundary failure.
