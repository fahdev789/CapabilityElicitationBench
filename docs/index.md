# Capability Elicitation Bench

**Goal**  
Measure how much optimisation power (prompt search → few-shot → best-of-N → verifier) is required before a model reliably follows a target constraint.

**Why now?**  
– Apollo: “Science of Evals” needs optimisation-power metrics.  
– Anthropic RSP: distance-from-threshold arguments need evidence curves.  
Open benchmarks for this don’t exist.

**Quick start**
```bash
git clone https://github.com/fahdev789/CapabilityElicitationBench
pip install -r requirements.txt
python scripts/run_eval.py --provider mock
