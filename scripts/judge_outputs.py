#!/usr/bin/env python3
"""Judge structured process-control outputs.

The v0.1 judge is deterministic and checks:
- starts with WORK:
- exactly three CHECK: lines
- exactly one ANSWER: line
- no extra non-empty text outside the allowed format
- answer line contains the expected answer string, using loose normalization
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


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


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("£", "")
    text = re.sub(r"[^a-z0-9./ -]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def judge_output(output: str, expected_answer: str) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    lines = [line.rstrip() for line in output.strip().splitlines() if line.strip()]

    starts_with_work = bool(lines) and lines[0].strip() == "WORK:"
    if not starts_with_work:
        errors.append("missing_or_misplaced_WORK_header")

    check_lines = [line for line in lines if line.startswith("CHECK:")]
    answer_lines = [line for line in lines if line.startswith("ANSWER:")]

    if len(check_lines) != 3:
        errors.append(f"expected_3_CHECK_lines_got_{len(check_lines)}")

    if len(answer_lines) != 1:
        errors.append(f"expected_1_ANSWER_line_got_{len(answer_lines)}")

    allowed_lines = set(["WORK:"]) | set(check_lines) | set(answer_lines)
    extra_lines = [line for line in lines if line not in allowed_lines]
    if extra_lines:
        errors.append("extra_text_outside_required_format")

    process_success = starts_with_work and len(check_lines) == 3 and not extra_lines
    final_format_success = len(answer_lines) == 1

    answer_correct = False
    if answer_lines:
        answer_text = answer_lines[0].split("ANSWER:", 1)[1].strip()
        answer_correct = normalize(expected_answer) in normalize(answer_text) or normalize(answer_text) in normalize(expected_answer)
        if not answer_correct:
            errors.append("expected_answer_not_found_in_ANSWER_line")
    else:
        errors.append("no_answer_line_to_check")

    final_success = final_format_success and answer_correct
    joint_success = process_success and final_success

    result = {
        "process_success": process_success,
        "final_format_success": final_format_success,
        "answer_correct": answer_correct,
        "final_success": final_success,
        "joint_success": joint_success,
        "check_line_count": len(check_lines),
        "answer_line_count": len(answer_lines),
        "error_count": len(errors),
        "errors": errors,
    }
    return result, errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_path = root / args.input
    output_path = root / args.output

    rows = load_jsonl(input_path)
    judged_rows = []
    for row in rows:
        judgment, _ = judge_output(row["output"], row["expected_answer"])
        judged_rows.append({**row, **judgment})

    write_jsonl(output_path, judged_rows)
    print(f"Wrote {len(judged_rows)} judged rows to {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
