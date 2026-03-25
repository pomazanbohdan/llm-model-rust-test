from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


DEFAULT_REPORT_BASE = "hf-dataset/reports/validation-windows"
DEFAULT_COMBINED_REPORT_DIR = "hf-dataset/reports/validation-expanded"
DEFAULT_OUTPUT_DIR = "hf-dataset-verified-expanded"


def run_step(repo_root: Path, command: list[str]) -> None:
    print(f"[rustforge] {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed with exit code {result.returncode}: {' '.join(command)}")


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Grow the RustForge verified subset by validating multiple rolling windows.")
    parser.add_argument("--window-size", type=int, default=10)
    parser.add_argument("--windows", type=int, default=3)
    parser.add_argument("--start-offset", type=int, default=0)
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--report-base", default=DEFAULT_REPORT_BASE)
    parser.add_argument("--combined-report-dir", default=DEFAULT_COMBINED_REPORT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable
    report_base = repo_root / args.report_base
    combined_report_dir = repo_root / args.combined_report_dir

    if report_base.exists():
        shutil.rmtree(report_base)
    report_base.mkdir(parents=True, exist_ok=True)

    all_reports: dict[str, dict[str, object]] = {}
    window_summaries: list[dict[str, object]] = []

    for window_index in range(args.windows):
        start = args.start_offset + window_index * args.window_size
        report_dir = report_base / f"window-{window_index:03d}"
        run_step(
            repo_root,
            [
                python,
                "scripts/validate-hf-dataset.py",
                "--tiers",
                "core",
                "--start-per-category",
                str(start),
                "--max-per-category",
                str(args.window_size),
                "--timeout-sec",
                str(args.timeout_sec),
                "--report-dir",
                str(report_dir.relative_to(repo_root)),
            ],
        )
        summary = json.loads((report_dir / "validation-summary.json").read_text(encoding="utf-8"))
        summary["window_index"] = window_index
        summary["start_per_category"] = start
        window_summaries.append(summary)
        for item in load_jsonl(report_dir / "validation-report.jsonl"):
            all_reports[str(item["id"])] = item

    if combined_report_dir.exists():
        shutil.rmtree(combined_report_dir)
    combined_report_dir.mkdir(parents=True, exist_ok=True)

    combined_rows = list(all_reports.values())
    combined_rows.sort(key=lambda item: str(item["id"]))
    combined_summary = {
        "windows": args.windows,
        "window_size": args.window_size,
        "start_offset": args.start_offset,
        "validated_records": len(combined_rows),
        "status_counts": dict(Counter(item["status"] for item in combined_rows)),
        "category_counts": dict(Counter(item["category"] for item in combined_rows)),
        "window_summaries": window_summaries,
    }

    (combined_report_dir / "validation-report.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in combined_rows) + ("\n" if combined_rows else ""),
        encoding="utf-8",
    )
    (combined_report_dir / "validation-summary.json").write_text(json.dumps(combined_summary, indent=2), encoding="utf-8")

    run_step(
        repo_root,
        [
            python,
            "scripts/promote-hf-verified.py",
            "--report-dir",
            str(combined_report_dir.relative_to(repo_root)),
            "--output-dir",
            args.output_dir,
        ],
    )
    print(json.dumps(combined_summary, indent=2))


if __name__ == "__main__":
    main()
