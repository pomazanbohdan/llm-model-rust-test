from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_OUTPUT_DIR = "hf-dataset/reports/family-cascade"
TIER_SEQUENCE = ("cheap", "medium", "full")


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def run_step(repo_root: Path, command: list[str]) -> None:
    print(f"[rustforge] {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed with exit code {result.returncode}: {' '.join(command)}")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run family-first cheap/medium/full validation cascade.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cheap-per-family", type=int, default=3)
    parser.add_argument("--medium-per-family", type=int, default=3)
    parser.add_argument("--full-per-family", type=int, default=5)
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--tiers", default="core")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable
    input_dir = repo_root / args.input_dir
    output_dir = repo_root / args.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    family_to_category: dict[str, str] = {}
    for record in iter_records(input_dir / "data"):
        if str(record["tier"]) != "core":
            continue
        family_id = derive_family_id(record)
        family_to_category[family_id] = str(record["category"])

    family_ids = sorted(family_to_category)
    previous_passed = set(family_ids)
    tier_amounts = {
        "cheap": args.cheap_per_family,
        "medium": args.medium_per_family,
        "full": args.full_per_family,
    }

    cascade_rows: list[dict[str, object]] = []
    tier_summaries: list[dict[str, object]] = []

    for validation_tier in TIER_SEQUENCE:
        passed_this_tier: set[str] = set()
        amount = tier_amounts[validation_tier]
        for family_id in family_ids:
            if family_id not in previous_passed:
                continue
            safe_name = family_id.replace(".", "_")
            report_dir = output_dir / validation_tier / safe_name
            run_step(
                repo_root,
                [
                    python,
                    "scripts/validate-hf-dataset.py",
                    "--tiers",
                    "core",
                    "--validation-tier",
                    validation_tier,
                    "--family-include",
                    family_id,
                    "--max-per-category",
                    str(amount),
                    "--timeout-sec",
                    str(args.timeout_sec),
                    "--report-dir",
                    str(report_dir.relative_to(repo_root)),
                ],
            )
            summary = load_json(report_dir / "validation-summary.json")
            checked = int(summary["validated_records"])
            validated = int(summary["status_counts"].get("validated", 0))
            failed = int(summary["status_counts"].get("failed", 0))
            family_row = {
                "family_id": family_id,
                "category": family_to_category[family_id],
                "tier": validation_tier,
                "checked": checked,
                "validated": validated,
                "failed": failed,
                "pass_rate": (validated / checked) if checked else 0.0,
            }
            cascade_rows.append(family_row)
            if checked and failed == 0:
                passed_this_tier.add(family_id)

        tier_summary = {
            "tier": validation_tier,
            "families_entered": len(previous_passed),
            "families_passed": len(passed_this_tier),
            "families_failed": len(previous_passed) - len(passed_this_tier),
        }
        tier_summaries.append(tier_summary)
        previous_passed = passed_this_tier

    final_summary = {
        "family_count": len(family_ids),
        "tiers": tier_summaries,
        "fully_passed_families": sorted(previous_passed),
        "fully_passed_family_count": len(previous_passed),
        "fully_passed_category_counts": dict(Counter(family_to_category[family_id] for family_id in previous_passed)),
    }
    (output_dir / "cascade-summary.json").write_text(json.dumps(final_summary, indent=2), encoding="utf-8")
    (output_dir / "cascade-rows.json").write_text(json.dumps(cascade_rows, indent=2), encoding="utf-8")
    print(json.dumps(final_summary, indent=2))


if __name__ == "__main__":
    main()
