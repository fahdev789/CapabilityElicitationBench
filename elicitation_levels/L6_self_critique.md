# L6 — Self-Critique / Retry

Two-stage process:

1. The model answers the task.
2. The model is shown its answer and asked to repair only formatting violations.

Initial prompt:

```text
Solve the task using exactly this format:

WORK:
CHECK: <step 1>
CHECK: <step 2>
CHECK: <step 3>
ANSWER: <final answer>

Task: {question}
```

Repair prompt:

```text
Your previous answer may have violated the required structure.
Rewrite it so it obeys exactly:

WORK:
CHECK: <step 1>
CHECK: <step 2>
CHECK: <step 3>
ANSWER: <final answer>

Do not add any other text.

Previous answer:
{previous_answer}
```
