#!/usr/bin/env python3
"""Plot elicitation curves from judged outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd
import io # <--- Added this import

ELICITATION_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"]


# This function is no longer load_jsonl but reads the specific tabular output
def load_analysis_summary(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    # The header is the first line, data is the second line
    if len(lines) < 2:
        raise ValueError("Analysis summary file is empty or malformed.")

    # Use pandas to read the space-separated data
    # We are skipping the first line, as it's just 'Wrote summary to ...'
    # The actual header is the second line, and the data is the third line.
    data_io = io.StringIO(''.join(lines[1:]))
    df = pd.read_csv(data_io, sep=r'\s+', engine='python')
    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    input_path = root / args.input
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_analysis_summary(input_path)
    if df.empty:
        raise SystemExit("No rows found after parsing analysis summary.")

    # Extract provider and model from the DataFrame (assuming only one row for overall summary)
    provider = df['provider'].iloc[0] if not df.empty else 'Unknown Provider'
    model = df['model'].iloc[0] if not df.empty else 'Unknown Model'

    # The current analysis summary only provides one row (overall metrics), not per-elicitation level
    # To plot an elicitation curve, we need data per level. If the current summary only has overall, then we cannot plot a curve.
    # Let's assume for now the user expects to plot the 'joint_success_rate' if it exists directly.
    # However, the previous `analyze_results.py` produced only *one* row for `overall`.
    # If the user wants a curve, the `analyze_results.py` needs to be changed to output data per elicitation level.
    # For now, let's assume `df` contains the summary which should include `l0_joint_success_rate` and `best_joint_success_rate`

    # Re-reading the context, the original `plot_results.py` was expecting a JSONL with `elicitation_level` for groupby.
    # The current `analyze_results.py` output a single row summary. This means the plotting logic for a curve won't work.
    # The user's request was to display model name, not to change the plotting logic for a curve.
    # I will adapt the `plot_results.py` to read the single summary line and potentially plot the L0 and Best rates.
    # To create an elicitation curve, the `analyze_results.py` script needs to be modified to output data per elicitation level.

    # Given the single-row output from analyze_results.py, we can't create a curve directly from 'elicitation_level'.
    # Instead, we'll plot the two success rates available from the summary.

    l0_success_rate = df['l0_joint_success_rate'].iloc[0]
    best_success_rate = df['best_joint_success_rate'].iloc[0]

    metrics = pd.DataFrame({
        'metric': ['L0 Joint Success Rate', 'Best Joint Success Rate'],
        'value': [l0_success_rate, best_success_rate]
    })

    plt.figure(figsize=(9, 5))
    plt.bar(metrics['metric'], metrics['value'], color=['skyblue', 'lightcoral'])
    plt.ylim(0, 1)
    plt.ylabel('Success Rate')
    plt.title(f"Joint Success Rates for {provider}/{model}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    print(f"Wrote plot to {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
