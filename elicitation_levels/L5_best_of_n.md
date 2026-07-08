# L5 — Best-of-N Sampling

At this level, generate N independent outputs for the same task and accept the best valid output according to the judge.

Prompt template:

```text
Solve the task. Your response must pass a strict format checker.

Required format:
WORK:
CHECK: <step 1>
CHECK: <step 2>
CHECK: <step 3>
ANSWER: <final answer>

Common failure modes:
- fewer or more than three CHECK lines
- missing WORK header
- final answer does not start with ANSWER:
- extra commentary outside the required format

Task: {question}
```
