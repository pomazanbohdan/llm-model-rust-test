from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_SCORE_DIR = "hf-dataset/reports/family-scores-all"
DEFAULT_REPORT_ROOT = "hf-dataset/reports/family-depth-x2"
DEFAULT_FACTOR = 2.0
DEFAULT_FULL_TAIL_ROWS = 12
DEFAULT_TIMEOUT_SEC = 90
DEFAULT_BASELINE_CATEGORY_DEPTHS = {
    "api_refactor": 289,
    "async_concurrency_fix": 375,
    "cargo_workspace_fix": 300,
    "clippy_fmt_cleanup": 417,
    "compile_repair": 800,
    "doctest_doc_fix": 289,
    "edition2024_migration": 417,
    "macro_fix": 417,
    "review_preference": 500,
    "rust_qa": 167,
    "semantic_impl": 500,
    "test_driven_bugfix": 813,
    "unsafe_ffi_fix": 450,
}


def run_command(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def load_families(path: Path) -> list[dict[str, object]]:
    return json.loads(path.read_text(encoding="utf-8"))["families"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Raise RustForge family depth by a factor with caps at total rows.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--score-dir", default=DEFAULT_SCORE_DIR)
    parser.add_argument("--report-root", default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--factor", type=float, default=DEFAULT_FACTOR)
    parser.add_argument("--full-tail-rows", type=int, default=DEFAULT_FULL_TAIL_ROWS)
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--baseline-category-depths", default="", help="JSON file with category -> baseline depth. When set, targets are computed from that baseline instead of the current validated depth.")
    parser.add_argument("--use-current-baseline", action="store_true", help="Use each family's current validated depth as the baseline before applying the factor.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    score_path = repo_root / args.score_dir / "family-scores.json"
    report_root = repo_root / args.report_root
    report_root.mkdir(parents=True, exist_ok=True)
    if args.use_current_baseline:
        baseline_depths = None
    elif args.baseline_category_depths:
        baseline_depths = json.loads((repo_root / args.baseline_category_depths).read_text(encoding="utf-8"))
    else:
        baseline_depths = DEFAULT_BASELINE_CATEGORY_DEPTHS

    families = load_families(score_path)
    plan_rows: list[dict[str, object]] = []

    for row in sorted(families, key=lambda item: (str(item["category"]), str(item["family_id"]))):
        family_id = str(row["family_id"])
        category = str(row["category"])
        current = int(row["validated_rows"])
        total = int(row["total_rows"])
        baseline = current if baseline_depths is None else int(baseline_depths.get(category, current))
        target = min(total, max(current, int(round(baseline * args.factor))))
        additional = max(0, target - current)
        plan_rows.append({
            "family_id": family_id,
            "category": category,
            "baseline_validated": baseline,
            "current_validated": current,
            "total_rows": total,
            "target_validated": target,
            "additional_needed": additional,
        })

        if additional <= 0:
            continue

        if category in {"review_preference", "rust_qa"}:
            run_command([
                "python",
                "scripts/validate-hf-auxiliary.py",
                "--input-dir",
                args.input_dir,
                "--report-dir",
                str(Path(args.report_root) / family_id.replace(".", "-")),
                "--family-include",
                family_id,
                "--start-per-family",
                str(current),
                "--max-per-family",
                str(additional),
            ], repo_root)
            continue

        if additional <= args.full_tail_rows:
            run_command([
                "python",
                "scripts/validate-hf-dataset.py",
                "--input-dir",
                args.input_dir,
                "--report-dir",
                str(Path(args.report_root) / f"{family_id.replace('.', '-')}-full"),
                "--tiers",
                "core",
                "--validation-tier",
                "full",
                "--family-include",
                family_id,
                "--start-per-family",
                str(current),
                "--max-per-family",
                str(additional),
                "--timeout-sec",
                str(args.timeout_sec),
            ], repo_root)
            continue

        cheap_count = additional - args.full_tail_rows
        full_count = args.full_tail_rows
        run_command([
            "python",
            "scripts/validate-hf-dataset.py",
            "--input-dir",
            args.input_dir,
            "--report-dir",
            str(Path(args.report_root) / f"{family_id.replace('.', '-')}-cheap"),
            "--tiers",
            "core",
            "--validation-tier",
            "cheap",
            "--family-include",
            family_id,
            "--start-per-family",
            str(current),
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
            str(Path(args.report_root) / f"{family_id.replace('.', '-')}-full"),
            "--tiers",
            "core",
            "--validation-tier",
            "full",
            "--family-include",
            family_id,
            "--start-per-family",
            str(current + cheap_count),
            "--max-per-family",
            str(full_count),
            "--timeout-sec",
            str(args.timeout_sec),
        ], repo_root)

    (report_root / "plan.json").write_text(json.dumps(plan_rows, indent=2), encoding="utf-8")
    print(json.dumps({
        "families": len(plan_rows),
        "factor": args.factor,
        "report_root": str(report_root),
    }, indent=2))


if __name__ == "__main__":
    main()
