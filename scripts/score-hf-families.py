from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_FULL_REPORT = "hf-dataset/reports/validation-expanded"
DEFAULT_OUTPUT_DIR = "hf-dataset/reports/family-scores"


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


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
    parser = argparse.ArgumentParser(description="Score RustForge dataset families by validation stability.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--full-report-dir", default=DEFAULT_FULL_REPORT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / args.input_dir
    report_dir = repo_root / args.full_report_dir
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows_by_id: dict[str, dict[str, object]] = {}
    family_totals: Counter[str] = Counter()
    category_by_family: dict[str, str] = {}
    for record in iter_records(input_dir / "data"):
        record_id = str(record["id"])
        family_id = derive_family_id(record)
        rows_by_id[record_id] = record
        family_totals[family_id] += 1
        category_by_family[family_id] = str(record["category"])

    validation_rows = load_jsonl(report_dir / "validation-report.jsonl")
    family_stats: dict[str, dict[str, object]] = defaultdict(lambda: {
        "validated": 0,
        "failed": 0,
        "skipped_infra": 0,
        "skipped_auxiliary": 0,
        "rows_seen": 0,
        "validation_tiers": Counter(),
    })

    for item in validation_rows:
        family_id = str(item.get("family_id") or derive_family_id(rows_by_id[str(item["id"])]))
        stats = family_stats[family_id]
        stats["rows_seen"] += 1
        stats["validation_tiers"][str(item.get("validation_tier", "full"))] += 1
        status = str(item["status"])
        stats[status] = int(stats.get(status, 0)) + 1

    family_rows: list[dict[str, object]] = []
    for family_id in sorted(family_totals):
        stats = family_stats.get(family_id, {
            "validated": 0,
            "failed": 0,
            "skipped_infra": 0,
            "skipped_auxiliary": 0,
            "rows_seen": 0,
            "validation_tiers": Counter(),
        })
        validated = int(stats.get("validated", 0))
        failed = int(stats.get("failed", 0))
        checked = validated + failed
        pass_rate = (validated / checked) if checked else 0.0
        coverage = validated / family_totals[family_id] if family_totals[family_id] else 0.0
        stability_score = round(pass_rate * 70 + min(validated, 100) / 100 * 20 + coverage * 10, 4)
        family_rows.append({
            "family_id": family_id,
            "category": category_by_family[family_id],
            "total_rows": family_totals[family_id],
            "validated_rows": validated,
            "failed_rows": failed,
            "rows_seen": int(stats.get("rows_seen", 0)),
            "pass_rate": round(pass_rate, 6),
            "coverage": round(coverage, 6),
            "stability_score": stability_score,
            "validation_tiers": dict(stats["validation_tiers"]),
        })

    summary = {
        "families": len(family_rows),
        "validated_rows": sum(int(row["validated_rows"]) for row in family_rows),
        "failed_rows": sum(int(row["failed_rows"]) for row in family_rows),
        "stable_families": sum(1 for row in family_rows if row["pass_rate"] == 1.0 and row["validated_rows"] >= 50),
    }

    (output_dir / "family-scores.json").write_text(json.dumps({
        "summary": summary,
        "families": family_rows,
    }, indent=2), encoding="utf-8")

    with (output_dir / "family-scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "family_id",
                "category",
                "total_rows",
                "validated_rows",
                "failed_rows",
                "rows_seen",
                "pass_rate",
                "coverage",
                "stability_score",
            ],
        )
        writer.writeheader()
        writer.writerows([{k: row[k] for k in writer.fieldnames} for row in family_rows])

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
