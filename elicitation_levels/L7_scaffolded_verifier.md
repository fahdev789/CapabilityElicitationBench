# L7 — Scaffolded Verifier Loop

At this level, a deterministic verifier checks the output. If the output fails, the model receives structured feedback and retries.

Loop:

```text
Generate answer → verify structure → if failed, return exact errors → retry → verify again
```

Repair prompt:

```text
Your answer failed the verifier for these reasons:
{verifier_errors}

Rewrite your answer so it passes all checks.

Required format:
WORK:
CHECK: <step 1>
CHECK: <step 2>
CHECK: <step 3>
ANSWER: <final answer>

Original task:
{question}
```
