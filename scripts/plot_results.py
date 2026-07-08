#!/usr/bin/env python3
"""Plot elicitation curves from judged outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_path = root / args.input
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(load_jsonl(input_path))
    if df.empty:
        raise SystemExit("No rows found.")

    summary = (
        df.groupby("elicitation_level", as_index=False)
        .agg(
            process_success_rate=("process_success", "mean"),
            final_success_rate=("final_success", "mean"),
            joint_success_rate=("joint_success", "mean"),
        )
    )
    summary["elicitation_level"] = pd.Categorical(summary["elicitation_level"], categories=ELICITATION_ORDER, ordered=True)
    summary = summary.sort_values("elicitation_level")

    x = [str(v) for v in summary["elicitation_level"]]

    plt.figure(figsize=(9, 5))
    plt.plot(x, summary["process_success_rate"], marker="o", label="Process success")
    plt.plot(x, summary["final_success_rate"], marker="o", label="Final answer success")
    plt.plot(x, summary["joint_success_rate"], marker="o", label="Joint success")
    plt.xlabel("Elicitation level")
    plt.ylabel("Success rate")
    plt.ylim(0, 1)
    plt.title("Elicitation curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    print(f"Wrote plot to {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
