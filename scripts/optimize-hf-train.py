from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(repo_root: Path, command: list[str]) -> None:
    print(f"[rustforge] {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed with exit code {result.returncode}: {' '.join(command)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an optimized RustForge priority train set with minimal extra validation cost.")
    parser.add_argument("--target-rows", type=int, default=15000)
    parser.add_argument("--min-family-validated", type=int, default=20)
    parser.add_argument("--min-family-pass-rate", type=float, default=1.0)
    parser.add_argument("--aux-share", type=float, default=0.05)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable

    run_step(repo_root, [python, "scripts/score-hf-families.py"])
    run_step(
        repo_root,
        [
            python,
            "scripts/build-priority-train.py",
            "--target-rows",
            str(args.target_rows),
            "--min-family-validated",
            str(args.min_family_validated),
            "--min-family-pass-rate",
            str(args.min_family_pass_rate),
            "--aux-share",
            str(args.aux_share),
        ],
    )


if __name__ == "__main__":
    main()
