#!/usr/bin/env python3
"""Analyze judged outputs and produce summary tables."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


ELICITATION_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def minimum_elicitation_level(summary: pd.DataFrame, metric: str, threshold: float) -> str:
    for level in ELICITATION_ORDER:
        rows = summary[summary["elicitation_level"] == level]
        if not rows.empty and float(rows.iloc[0][metric]) >= threshold:
            return level
    return "not_reached"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_path = root / args.input
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(input_path)
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("No rows found.")

    summary = (
        df.groupby(["provider", "model", "elicitation_level", "category"], as_index=False)
        .agg(
            n=("joint_success", "size"),
            process_success_rate=("process_success", "mean"),
            final_success_rate=("final_success", "mean"),
            joint_success_rate=("joint_success", "mean"),
            avg_error_count=("error_count", "mean"),
        )
        .sort_values(["provider", "model", "category", "elicitation_level"])
    )

    overall = (
        df.groupby(["provider", "model", "elicitation_level"], as_index=False)
        .agg(
            n=("joint_success", "size"),
            process_success_rate=("process_success", "mean"),
            final_success_rate=("final_success", "mean"),
            joint_success_rate=("joint_success", "mean"),
            avg_error_count=("error_count", "mean"),
        )
    )

    lines = []
    for (provider, model), group in overall.groupby(["provider", "model"]):
        l0 = group[group["elicitation_level"] == "L0"]
        best_joint = float(group["joint_success_rate"].max())
        l0_joint = float(l0.iloc[0]["joint_success_rate"]) if not l0.empty else 0.0
        gap = best_joint - l0_joint
        min_level = minimum_elicitation_level(group, "joint_success_rate", args.threshold)
        lines.append(
            {
                "provider": provider,
                "model": model,
                "metric": "overall",
                "l0_joint_success_rate": l0_joint,
                "best_joint_success_rate": best_joint,
                "capability_propensity_gap": gap,
                "minimum_elicitation_level": min_level,
                "reliability_threshold": args.threshold,
            }
        )

    meta = pd.DataFrame(lines)

    with output_path.open("w", encoding="utf-8") as f:
        f.write("# overall_by_level\n")
        overall.sort_values(["provider", "model", "elicitation_level"]).to_csv(f, index=False)
        f.write("\n# by_category\n")
        summary.to_csv(f, index=False)
        f.write("\n# threshold_metrics\n")
        meta.to_csv(f, index=False)

    print(f"Wrote summary to {output_path.relative_to(root)}")
    print(meta.to_string(index=False))


if __name__ == "__main__":
    main()
