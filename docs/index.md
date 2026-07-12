# Capability Elicitation Bench

Measuring **how much optimisation power** (prompt search → few-shot → best-of-N → verifier) is required before a model reliably follows a target constraint.

---

## Quick Start

```bash
git clone https://github.com/fahdev789/CapabilityElicitationBench.git
cd CapabilityElicitationBench
pip install -r requirements.txt
python scripts/run_eval.py --provider mock
```

---

## Example Elicitation Curve

![Elicitation curve](assets/elicitation_curve.png)

*Mock data — success-rate vs. elicitation level (L0 → L7).*

---

## Why this matters

| Reference | Idea supplied |
| --- | --- |
| [Apollo: "We Need a Science of Evals"](https://www.apolloresearch.ai/science/we-need-a-science-of-evals/) | Optimisation-power framing |
| [Apollo: "The Evals Gap"](https://www.apolloresearch.ai/science/the-evals-gap/) | Coverage gap vs. risks |
| [Anthropic RSP v3.1](https://www.anthropic.com/news/responsible-scaling-policy-v3) | "Affirmative case" thresholds |
| [MT-Bench](https://arxiv.org/abs/2306.05685) | LLM-as-judge template |
| [G-Eval](https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/generative-ai/working-with-llms/evaluation/g-eval-metric-for-summarization) | Meta-eval of LLM judges |

---

## Roadmap

| Milestone | Description | ETA |
| --- | --- | --- |
| **v0.1** | Reasoning-format constraint, 100 math tasks, 2 models | done |
| **v0.2** | Code-review tasks + verifier loop | Aug 2026 |
| **v1.0** | ≥ 10 task families, cross-model dashboard | Dec 2026 |

---

## Contributing

Issues & PRs welcome — new tasks, judge ideas, model adapters, docs.

*License:* code MIT, data CC-BY-4.0.

---

*This site is open-source. [Improve this page](https://github.com/fahdev789/CapabilityElicitationBench/tree/main/docs).*
