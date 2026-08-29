---
name: "s"
description: "Answer with detail — concise but complete, structured only when structure genuinely helps."
argument-hint: "The question or topic to answer"
user-invocable: true
disable-model-invocation: false
---

## Instruction

Answer the user's question (from `$ARGUMENTS`) with enough detail to be genuinely useful, but no fluff.

Rules:
- Keep it under ~4 paragraphs or ~10 bullet points
- Use headers ONLY if the answer has 3+ distinct sections
- Use bullet lists only when a list is actually the right shape (steps, comparisons, enumerations)
- No preamble ("Great question", "Sure", "Of course", etc.)
- No trailing summary or "let me know if you need more"
- If code is needed, show the relevant snippet only — no surrounding boilerplate
- Include "why" when it's non-obvious; skip it when the answer is self-evident

## User Question

```text
$ARGUMENTS
```

Answer now, following the rules above.
