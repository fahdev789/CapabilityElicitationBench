#!/usr/bin/env python3
"""Run elicitation-level evaluations.

v0.1 supports a mock provider so the pipeline is runnable without API keys.
Real model adapters can be added later in `call_model`.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is in requirements.txt, but don't hard-fail if it's
    # missing — env vars can still be set directly in the shell.
    pass


PROVIDER_ENV_VARS = {
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 2


ELICITATION_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]


PROMPT_TEMPLATES = {
    "L0": """Solve the task below.\n\nYou must respond in this exact format:\n\nWORK:\nCHECK: <step 1>\nCHECK: <step 2>\nCHECK: <step 3>\nANSWER: <final answer>\n\nTask: {question}""",
    "L1": """Solve the task below while obeying the output format exactly.\n\nRules:\n- Include the header WORK:\n- Include exactly three WORK lines.\n- Each WORK line must begin with CHECK:\n- Include exactly one final answer line.\n- The final answer line must begin with ANSWER:\n- Do not add extra text before or after the required format.\n\nTask: {question}""",
    "L2": """Your output will be judged only on whether it follows this structure:\nWORK:\nCHECK: <first check>\nCHECK: <second check>\nCHECK: <third check>\nANSWER: <answer>\n\nNo other text is allowed.\n\nTask: {question}""",
    "L3": """Follow the pattern shown in the examples.\n\nExample 1\nTask: What is 2 + 3?\nWORK:\nCHECK: Identify the operation as addition.\nCHECK: Add 2 and 3.\nCHECK: Confirm the result is 5.\nANSWER: 5\n\nExample 2\nTask: If all daxes are blue, and this object is a dax, is it blue?\nWORK:\nCHECK: All daxes are blue.\nCHECK: The object is a dax.\nCHECK: Therefore the object is blue.\nANSWER: Yes\n\nNow solve this task using the same exact format.\n\nTask: {question}""",
    "L4": """First identify the task type. Then solve it. Then compress your work into exactly three CHECK lines.\n\nFinal output must contain only:\n\nWORK:\nCHECK: <task type and relevant fact>\nCHECK: <calculation or inference>\nCHECK: <verification>\nANSWER: <final answer>\n\nTask: {question}""",
    "L5": """Solve the task. Your response must pass a strict format checker.\n\nRequired format:\nWORK:\nCHECK: <step 1>\nCHECK: <step 2>\nCHECK: <step 3>\nANSWER: <final answer>\n\nCommon failure modes:\n- fewer or more than three CHECK lines\n- missing WORK header\n- final answer does not start with ANSWER:\n- extra commentary outside the required format\n\nTask: {question}""",
    "L6": """Solve the task using exactly this format:\n\nWORK:\nCHECK: <step 1>\nCHECK: <step 2>\nCHECK: <step 3>\nANSWER: <final answer>\n\nTask: {question}""",
    "L7": """Solve the task. A verifier will reject outputs with any formatting error.\n\nRequired format:\nWORK:\nCHECK: <step 1>\nCHECK: <step 2>\nCHECK: <step 3>\nANSWER: <final answer>\n\nTask: {question}""",
}


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_prompt(level: str, question: str) -> str:
    template = PROMPT_TEMPLATES.get(level)
    if not template:
        raise ValueError(f"Unknown elicitation level: {level}")
    return template.format(question=question)


def mock_model_response(task: Dict[str, Any], level: str, run_id: int) -> str:
    """Synthetic output with success probability increasing by elicitation level.

    This is only for testing the eval pipeline. It is not a model result.
    """
    level_idx = ELICITATION_ORDER.index(level)
    success_probability = min(0.15 + 0.10 * level_idx, 0.90)
    rng_seed = f"{task['task_id']}::{level}::{run_id}"
    rng = random.Random(rng_seed)

    if rng.random() < success_probability:
        return (
            "WORK:\n"
            f"CHECK: Identify the task as {task.get('category', 'general')}.\n"
            "CHECK: Apply the relevant rule or calculation.\n"
            f"CHECK: Verify the answer matches {task['expected_answer']}.\n"
            f"ANSWER: {task['expected_answer']}"
        )

    failure_type = rng.choice(["missing_work", "two_checks", "four_checks", "bad_answer_prefix", "extra_text"])
    if failure_type == "missing_work":
        return (
            "CHECK: I solved it.\n"
            "CHECK: The result follows.\n"
            "CHECK: The answer is ready.\n"
            f"ANSWER: {task['expected_answer']}"
        )
    if failure_type == "two_checks":
        return (
            "WORK:\n"
            "CHECK: I considered the task.\n"
            "CHECK: I computed the result.\n"
            f"ANSWER: {task['expected_answer']}"
        )
    if failure_type == "four_checks":
        return (
            "WORK:\n"
            "CHECK: I considered the task.\n"
            "CHECK: I computed the result.\n"
            "CHECK: I reviewed the result.\n"
            "CHECK: I finalized the answer.\n"
            f"ANSWER: {task['expected_answer']}"
        )
    if failure_type == "bad_answer_prefix":
        return (
            "WORK:\n"
            "CHECK: I considered the task.\n"
            "CHECK: I computed the result.\n"
            "CHECK: I reviewed the result.\n"
            f"FINAL: {task['expected_answer']}"
        )
    return (
        "Here is my answer.\n"
        "WORK:\n"
        "CHECK: I considered the task.\n"
        "CHECK: I computed the result.\n"
        "CHECK: I reviewed the result.\n"
        f"ANSWER: {task['expected_answer']}"
    )


def get_api_key(provider: str) -> str:
    """Look up the API key for a real provider from the environment.

    Reads from a `.env` file (via python-dotenv) if one is present, falling
    back to whatever is already set in the shell environment.
    """
    env_var = PROVIDER_ENV_VARS.get(provider)
    if not env_var:
        raise ValueError(f"No API key env var is configured for provider '{provider}'.")

    api_key = os.environ.get(env_var)
    if not api_key:
        raise RuntimeError(
            f"Missing {env_var}. Copy .env.example to .env and fill it in, "
            f"or export {env_var} in your shell."
        )
    return api_key


def call_openrouter(model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
    api_key = get_api_key("openrouter")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def call_anthropic(model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
    api_key = get_api_key("anthropic")
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def call_openai(model_name: str, prompt: str, temperature: float, max_tokens: int) -> str:
    api_key = get_api_key("openai")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


REAL_PROVIDERS = {
    "openrouter": call_openrouter,
    "anthropic": call_anthropic,
    "openai": call_openai,
}


def call_model(
    provider: str,
    task: Dict[str, Any],
    level: str,
    prompt: str,
    run_id: int,
    model_name: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 400,
) -> str:
    if provider == "mock":
        return mock_model_response(task, level, run_id)

    adapter = REAL_PROVIDERS.get(provider)
    if adapter is None:
        raise NotImplementedError(
            f"Provider '{provider}' is not implemented. "
            f"Supported providers: mock, {', '.join(REAL_PROVIDERS)}."
        )

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return adapter(model_name, prompt, temperature, max_tokens)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BASE_DELAY_SECONDS * (2**attempt))

    raise RuntimeError(
        f"Failed to call provider '{provider}' after {MAX_RETRIES} attempts: {last_error}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=None, help="Provider name. Currently supported: mock")
    parser.add_argument("--config", default="configs/eval_config.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    config_path = root / args.config
    config = load_json(config_path)

    provider = args.provider or config["model"]["provider"]
    task_file = root / config["task_file"]
    output_file = root / config["output_file"]

    tasks = load_jsonl(task_file)
    levels = config["elicitation_levels"]
    runs_per_task = int(config.get("runs_per_task", 1))
    model_name = config["model"].get("name")
    temperature = float(config["model"].get("temperature", 0.2))
    max_tokens = int(config["model"].get("max_tokens", 400))

    rows = []
    for task in tasks:
        for level in levels:
            for run_id in range(runs_per_task):
                prompt = build_prompt(level, task["question"])
                output = call_model(
                    provider, task, level, prompt, run_id,
                    model_name=model_name, temperature=temperature, max_tokens=max_tokens,
                )
                rows.append(
                    {
                        "benchmark_name": config["benchmark_name"],
                        "provider": provider,
                        "model": config["model"].get("name", provider),
                        "temperature": config["model"].get("temperature"),
                        "task_id": task["task_id"],
                        "category": task["category"],
                        "question": task["question"],
                        "expected_answer": task["expected_answer"],
                        "elicitation_level": level,
                        "run_id": run_id,
                        "prompt": prompt,
                        "output": output,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

    write_jsonl(output_file, rows)
    print(f"Wrote {len(rows)} rows to {output_file.relative_to(root)}")


if __name__ == "__main__":
    main()
