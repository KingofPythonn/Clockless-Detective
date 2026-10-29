"""Solve every sample input without using any supplied expected outputs.

Usage (PowerShell / Windows):
    python run_samples.py
    python run_samples.py samples_without_outputs.json

Put this script next to solution.py and samples.json.
"""

import json
import sys
from pathlib import Path

from solution import analyze


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("samples.json")

    try:
        with path.open("r", encoding="utf-8-sig") as file:
            samples = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read sample file '{path}': {exc}", file=sys.stderr)
        return 1

    if not isinstance(samples, list):
        print("The samples file must contain a JSON list of examples.", file=sys.stderr)
        return 1

    for index, sample in enumerate(samples, start=1):
        if not isinstance(sample, dict):
            print(f"Sample {index} must be a JSON object.", file=sys.stderr)
            return 1

        # Each example can be {"name": ..., "input": ..., "output": ...},
        # {"name": ..., "input": ...}, or just the input model itself.
        model = sample.get("input", sample)
        name = sample.get("name", f"Sample {index}")

        try:
            result = analyze(model)
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            print(f"Cannot solve sample {index} ({name}): {exc}", file=sys.stderr)
            return 1

        print(f"\n=== Sample {index}: {name} ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\nSolved {len(samples)} sample(s). All outputs were computed from inputs only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
