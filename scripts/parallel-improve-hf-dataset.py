from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_OUTPUT_DIR = "hf-dataset/reports/parallel-improve"


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def run_command(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)


def validate_family_window(
    *,
    repo_root: Path,
    python: str,
    output_dir: Path,
    family_id: str,
    start_per_family: int,
    max_per_family: int,
    timeout_sec: int,
    validation_tier: str,
) -> dict[str, object]:
    safe_name = family_id.replace(".", "_")
    report_dir = output_dir / validation_tier / f"{safe_name}-start-{start_per_family:04d}"
    command = [
        python,
        "scripts/validate-hf-dataset.py",
        "--tiers",
        "core",
        "--validation-tier",
        validation_tier,
        "--family-include",
        family_id,
        "--start-per-family",
        str(start_per_family),
        "--max-per-family",
        str(max_per_family),
        "--timeout-sec",
        str(timeout_sec),
        "--report-dir",
        str(report_dir.relative_to(repo_root)),
    ]
    result = run_command(repo_root, command)
    if result.returncode != 0:
        return {
            "family_id": family_id,
            "start_per_family": start_per_family,
            "validation_tier": validation_tier,
            "status": "process_failed",
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }
    summary = json.loads((report_dir / "validation-summary.json").read_text(encoding="utf-8"))
    status_counts = summary.get("status_counts", {})
    checked = int(summary.get("validated_records", 0))
    validated = int(status_counts.get("validated", 0))
    failed = int(status_counts.get("failed", 0))
    status = "validated" if checked and failed == 0 else "failed"
    return {
        "family_id": family_id,
        "start_per_family": start_per_family,
        "validation_tier": validation_tier,
        "status": status,
        "checked": checked,
        "validated": validated,
        "failed": failed,
        "report_dir": str(report_dir.relative_to(repo_root)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a parallel family-depth dataset improvement pass and refresh quality artifacts.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--validation-tier", choices=["cheap", "medium", "full"], default="full")
    parser.add_argument("--window-size", type=int, default=2)
    parser.add_argument("--waves", type=int, default=2)
    parser.add_argument("--start-offset", type=int, default=1)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--target-rows", type=int, default=15000)
    parser.add_argument("--aux-share", type=float, default=0.05)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable
    input_dir = repo_root / args.input_dir
    output_dir = repo_root / args.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    family_ids = sorted(
        {
            derive_family_id(record)
            for record in iter_records(input_dir / "data")
            if str(record.get("tier")) == "core"
        }
    )

    tasks: list[tuple[str, int]] = []
    for wave_index in range(args.waves):
        start_per_family = args.start_offset + wave_index * args.window_size
        for family_id in family_ids:
            tasks.append((family_id, start_per_family))

    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(
                validate_family_window,
                repo_root=repo_root,
                python=python,
                output_dir=output_dir,
                family_id=family_id,
                start_per_family=start_per_family,
                max_per_family=args.window_size,
                timeout_sec=args.timeout_sec,
                validation_tier=args.validation_tier,
            )
            for family_id, start_per_family in tasks
        ]
        for future in as_completed(futures):
            rows.append(future.result())

    rows.sort(key=lambda row: (str(row["family_id"]), int(row["start_per_family"])))
    summary = {
        "validation_tier": args.validation_tier,
        "family_count": len(family_ids),
        "waves": args.waves,
        "window_size": args.window_size,
        "workers": args.workers,
        "status_counts": dict(Counter(str(row["status"]) for row in rows)),
        "fully_validated_task_count": sum(1 for row in rows if row["status"] == "validated"),
        "failed_task_count": sum(1 for row in rows if row["status"] != "validated"),
    }
    (output_dir / "parallel-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "parallel-rows.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    family_score_dir = output_dir / "family-scores"
    score_command = [
        python,
        "scripts/score-hf-families.py",
        "--input-dir",
        args.input_dir,
        "--full-report-dir",
        str(output_dir.relative_to(repo_root)),
        "--output-dir",
        str(family_score_dir.relative_to(repo_root)),
    ]
    score_result = run_command(repo_root, score_command)
    if score_result.returncode != 0:
        raise SystemExit(score_result.stderr or score_result.stdout)

    priority_dir = repo_root / "hf-dataset-priority-v3"
    build_command = [
        python,
        "scripts/build-priority-train.py",
        "--input-dir",
        args.input_dir,
        "--full-report-dir",
        str(output_dir.relative_to(repo_root)),
        "--family-score-dir",
        str(family_score_dir.relative_to(repo_root)),
        "--output-dir",
        str(priority_dir.relative_to(repo_root)),
        "--target-rows",
        str(args.target_rows),
        "--min-family-validated",
        str(args.window_size * args.waves),
        "--min-family-pass-rate",
        "1.0",
        "--aux-share",
        str(args.aux_share),
    ]
    build_result = run_command(repo_root, build_command)
    if build_result.returncode != 0:
        raise SystemExit(build_result.stderr or build_result.stdout)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
