from __future__ import annotations

import argparse
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_SCORE_DIR = "hf-dataset/reports/family-scores-all"
DEFAULT_REPORT_ROOT = "hf-dataset/reports/coverage-uplift"
TARGET_THRESHOLD = 0.50
FULL_TAIL_ROWS = 12
TIMEOUT_SEC = 90


def load_family_scores(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def build_category_state(families: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    by_category: dict[str, dict[str, object]] = defaultdict(lambda: {
        "families": [],
        "validated": 0,
        "total": 0,
    })
    for row in families:
        category = str(row["category"])
        entry = by_category[category]
        entry["families"].append(row)
        entry["validated"] += int(row["validated_rows"])
        entry["total"] += int(row["total_rows"])
    return by_category


def main() -> None:
    parser = argparse.ArgumentParser(description="Raise RustForge category coverage to a minimum threshold.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--score-dir", default=DEFAULT_SCORE_DIR)
    parser.add_argument("--report-root", default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--threshold", type=float, default=TARGET_THRESHOLD)
    parser.add_argument("--full-tail-rows", type=int, default=FULL_TAIL_ROWS)
    parser.add_argument("--timeout-sec", type=int, default=TIMEOUT_SEC)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / args.input_dir
    score_path = repo_root / args.score_dir / "family-scores.json"
    report_root = repo_root / args.report_root
    report_root.mkdir(parents=True, exist_ok=True)

    data = load_family_scores(score_path)
    categories = build_category_state(data["families"])

    auxiliary_categories = {"review_preference", "rust_qa"}
    execution_categories = []
    auxiliary_plan = []
    plan_rows = []

    for category, info in sorted(categories.items()):
        total_rows = int(info["total"])
        validated_rows = int(info["validated"])
        coverage = (validated_rows / total_rows) if total_rows else 0.0
        families = sorted(info["families"], key=lambda row: row["family_id"])
        family_ids = [str(row["family_id"]) for row in families]
        family_count = len(families)
        current_min = min(int(row["validated_rows"]) for row in families) if families else 0
        target_validated = math.ceil(total_rows * args.threshold)
        target_per_family = math.ceil(target_validated / family_count) if family_count else 0
        additional_per_family = max(0, target_per_family - current_min)

        plan_rows.append({
            "category": category,
            "current_coverage": round(coverage * 100.0, 2),
            "target_coverage": round(args.threshold * 100.0, 2),
            "current_min_family": current_min,
            "target_min_family": target_per_family,
            "additional_per_family": additional_per_family,
            "families": family_ids,
        })

        if coverage >= args.threshold:
            continue
        if category in auxiliary_categories:
            auxiliary_plan.append((category, family_ids, current_min, additional_per_family))
        else:
            execution_categories.append((category, family_ids, current_min, additional_per_family))

    (report_root / "plan.json").write_text(json.dumps(plan_rows, indent=2), encoding="utf-8")

    for category, family_ids, current_min, additional_per_family in execution_categories:
        if additional_per_family <= 0:
            continue
        family_arg = ",".join(family_ids)
        if additional_per_family <= args.full_tail_rows:
            run_command([
                "python",
                "scripts/validate-hf-dataset.py",
                "--input-dir",
                args.input_dir,
                "--report-dir",
                str(Path(args.report_root) / f"{category}-full"),
                "--tiers",
                "core",
                "--validation-tier",
                "full",
                "--family-include",
                family_arg,
                "--start-per-family",
                str(current_min),
                "--max-per-family",
                str(additional_per_family),
                "--timeout-sec",
                str(args.timeout_sec),
            ], repo_root)
            continue

        cheap_count = additional_per_family - args.full_tail_rows
        full_count = args.full_tail_rows
        run_command([
            "python",
            "scripts/validate-hf-dataset.py",
            "--input-dir",
            args.input_dir,
            "--report-dir",
            str(Path(args.report_root) / f"{category}-cheap"),
            "--tiers",
            "core",
            "--validation-tier",
            "cheap",
            "--family-include",
            family_arg,
            "--start-per-family",
            str(current_min),
            "--max-per-family",
            str(cheap_count),
            "--timeout-sec",
            str(args.timeout_sec),
        ], repo_root)
        run_command([
            "python",
            "scripts/validate-hf-dataset.py",
            "--input-dir",
            args.input_dir,
            "--report-dir",
            str(Path(args.report_root) / f"{category}-full"),
            "--tiers",
            "core",
            "--validation-tier",
            "full",
            "--family-include",
            family_arg,
            "--start-per-family",
            str(current_min + cheap_count),
            "--max-per-family",
            str(full_count),
            "--timeout-sec",
            str(args.timeout_sec),
        ], repo_root)

    for category, family_ids, current_min, additional_per_family in auxiliary_plan:
        if additional_per_family <= 0:
            continue
        run_command([
            "python",
            "scripts/validate-hf-auxiliary.py",
            "--input-dir",
            args.input_dir,
            "--report-dir",
            str(Path(args.report_root) / f"{category}-aux"),
            "--category-include",
            category,
            "--start-per-family",
            str(current_min),
            "--max-per-family",
            str(additional_per_family),
        ], repo_root)

    print(json.dumps({
        "execution_categories_processed": [item[0] for item in execution_categories],
        "auxiliary_categories_processed": [item[0] for item in auxiliary_plan],
        "plan_path": str(report_root / "plan.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
