# Limitations

## 1. Visible process is not private chain-of-thought

This repo measures compliance with a visible process field requested from the model. It does not claim access to a model's private internal reasoning.

For modern reasoning systems, visible explanations may be summaries, compressed reasoning, or policy-constrained outputs rather than faithful internal cognition.

## 2. Structured constraint-following is a proxy behavior

The first benchmark studies controllability through formatting and process constraints. This is not equivalent to measuring dangerous capabilities.

The goal is to build the measurement machinery first on safer behavior.

## 3. Judge limitations

The initial judge is deterministic and checks surface structure. It does not fully verify semantic correctness. Later versions should add:

```text
- exact-answer checks for simple tasks
- LLM-as-judge comparison
- human audit sample
- inter-judge agreement
```

## 4. Elicitation ladder is incomplete

The ladder captures several forms of elicitation pressure, but it does not exhaust all possible optimization power. Missing factors include:

```text
- fine-tuning
- expert red-teaming
- long-horizon agents
- external tools
- automated prompt search
- model-specific jailbreak strategies
```

## 5. No universal threshold

An 80% reliability threshold is a configurable convention, not a scientific law. Different behaviors and risk contexts may require different thresholds.

## 6. Results are model- and setup-dependent

Results can change with:

```text
- model version
- decoding settings
- system prompt
- API behavior
- hidden provider policies
- prompt formatting
- task distribution
- judge strictness
```

Therefore, claims should include the full experimental configuration.
