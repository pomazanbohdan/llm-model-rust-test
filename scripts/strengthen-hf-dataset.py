from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_VALIDATION_DIR = "hf-dataset/reports/validation"
DEFAULT_DEDUP_DIR = "hf-dataset/reports/dedup"
DEFAULT_STRENGTHEN_DIR = "hf-dataset/reports/strengthen"


def run_step(repo_root: Path, title: str, command: list[str]) -> None:
    print(f"[rustforge] {title}: {' '.join(command)}")
    result = subprocess.run(command, cwd=repo_root, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {title} (exit code {result.returncode})")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary(
    dedup_summary: dict[str, object],
    validation_summary: dict[str, object],
    verified_manifest: dict[str, object],
    validation_sample_size: int,
) -> dict[str, object]:
    total_records = int(dedup_summary["total_records"])
    unique_semantic_keys = int(dedup_summary["unique_semantic_keys"])
    duplicate_record_count = int(dedup_summary["duplicate_record_count"])
    validated_records = int(validation_summary["validated_records"])
    status_counts = validation_summary["status_counts"]
    validated_core = int(status_counts.get("validated", 0))
    failed_core = int(status_counts.get("failed", 0))
    skipped_auxiliary = int(status_counts.get("skipped_auxiliary", 0))
    skipped_infra = int(status_counts.get("skipped_infra", 0))
    checked_core = validated_core + failed_core
    unique_ratio = unique_semantic_keys / total_records if total_records else 0.0
    duplicate_ratio = duplicate_record_count / total_records if total_records else 0.0
    core_validation_pass_rate = validated_core / checked_core if checked_core else 0.0

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_records": total_records,
        "unique_semantic_keys": unique_semantic_keys,
        "unique_ratio": round(unique_ratio, 6),
        "duplicate_record_count": duplicate_record_count,
        "duplicate_ratio": round(duplicate_ratio, 6),
        "validation_sample_size": validation_sample_size,
        "validated_records": validated_records,
        "validated_core_records": validated_core,
        "failed_core_records": failed_core,
        "skipped_auxiliary_records": skipped_auxiliary,
        "skipped_infra_records": skipped_infra,
        "core_validation_pass_rate": round(core_validation_pass_rate, 6),
        "verified_rows": int(verified_manifest["verified_rows"]),
        "verified_category_counts": verified_manifest["category_counts"],
    }


def build_markdown(summary: dict[str, object]) -> str:
    return f"""# HF Dataset Strengthen Report

Date: `{datetime.now().date().isoformat()}`

## Result

- total rows: `{summary["total_records"]}`
- unique semantic keys: `{summary["unique_semantic_keys"]}`
- unique ratio: `{summary["unique_ratio"]:.2%}`
- duplicate-covered rows: `{summary["duplicate_record_count"]}`
- duplicate ratio: `{summary["duplicate_ratio"]:.2%}`
- validation sample size per category: `{summary["validation_sample_size"]}`
- validated core rows in sample: `{summary["validated_core_records"]}`
- failed core rows in sample: `{summary["failed_core_records"]}`
- skipped auxiliary rows in sample: `{summary["skipped_auxiliary_records"]}`
- skipped infra-blocked rows in sample: `{summary["skipped_infra_records"]}`
- core validation pass rate: `{summary["core_validation_pass_rate"]:.2%}`
- verified rows promoted: `{summary["verified_rows"]}`

## Interpretation

- this run is stronger than a one-row smoke sample because it validates multiple rows per category
- dataset quality is moving in the right direction when duplicate ratio goes down and verified rows go up
- reaching a real 100% target still depends on expanding verified coverage, reducing remaining duplicates, and harvesting benchmark failures back into train data
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the RustForge HF dataset strengthen pipeline end-to-end.")
    parser.add_argument("--max-per-category", type=int, default=10)
    parser.add_argument("--timeout-sec", type=int, default=90)
    parser.add_argument("--skip-generate", action="store_true")
    parser.add_argument("--skip-dedup", action="store_true")
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-promote", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    python = sys.executable

    if not args.skip_generate:
        run_step(repo_root, "generate", [python, "scripts/generate-hf-rustforge-50k.py"])

    if not args.skip_dedup:
        run_step(repo_root, "dedup", [python, "scripts/dedup-hf-dataset.py"])

    if not args.skip_validate:
        run_step(
            repo_root,
            "validate",
            [
                python,
                "scripts/validate-hf-dataset.py",
                "--max-per-category",
                str(args.max_per_category),
                "--timeout-sec",
                str(args.timeout_sec),
            ],
        )

    if not args.skip_promote:
        run_step(repo_root, "promote", [python, "scripts/promote-hf-verified.py"])

    dedup_summary = load_json(repo_root / DEFAULT_DEDUP_DIR / "dedup-summary.json")
    validation_summary = load_json(repo_root / DEFAULT_VALIDATION_DIR / "validation-summary.json")
    verified_manifest = load_json(repo_root / "hf-dataset-verified" / "manifest.json")

    strengthen_dir = repo_root / DEFAULT_STRENGTHEN_DIR
    strengthen_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(dedup_summary, validation_summary, verified_manifest, args.max_per_category)
    (strengthen_dir / "strengthen-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (strengthen_dir / "strengthen-report.md").write_text(build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
