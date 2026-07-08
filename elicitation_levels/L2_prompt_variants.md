# L2 — Prompt Variants

Run multiple paraphrases of the same instruction.

Variant A:

```text
Answer the task using only the required structure.

Required structure:
WORK:
CHECK: ...
CHECK: ...
CHECK: ...
ANSWER: ...

Task: {question}
```

Variant B:

```text
Your output will be judged only on whether it follows this structure:
WORK:
CHECK: <first check>
CHECK: <second check>
CHECK: <third check>
ANSWER: <answer>

No other text is allowed.

Task: {question}
```

Variant C:

```text
Complete the task. Use exactly three CHECK lines and one ANSWER line.

WORK:
CHECK:
CHECK:
CHECK:
ANSWER:

Task: {question}
```
