from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_REPORT_DIR = "hf-dataset/reports/validation"
DEFAULT_OUTPUT_DIR = "hf-dataset-verified"
SHARD_SIZE = 1000


def load_validation_results(report_path: Path) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    with report_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            results[item["id"]] = item
    return results


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote validated RustForge HF rows into a verified subset package.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / args.input_dir
    report_dir = repo_root / args.report_dir
    output_dir = repo_root / args.output_dir
    data_dir = output_dir / "data"

    validation_results = load_validation_results(report_dir / "validation-report.jsonl")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    verified_rows = []
    counts: Counter[str] = Counter()
    for record in iter_records(input_dir / "data"):
        result = validation_results.get(str(record["id"]))
        if not result or result["status"] != "validated":
            continue
        record["example_state"] = "validated_candidate"
        record["validation"] = result["validation"]
        verified_rows.append(record)
        counts[str(record["category"])] += 1

    for shard_index in range(0, len(verified_rows), SHARD_SIZE):
        shard_rows = verified_rows[shard_index:shard_index + SHARD_SIZE]
        shard_name = f"train-{shard_index // SHARD_SIZE:05d}-of-{max(1, (len(verified_rows) + SHARD_SIZE - 1) // SHARD_SIZE):05d}.jsonl"
        with (data_dir / shard_name).open("w", encoding="utf-8", newline="\n") as handle:
            for row in shard_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    readme = f"""---
language:
- en
pretty_name: RustForge Personal Rust Dataset (Verified Subset)
license: other
task_categories:
- text-generation
tags:
- rust
- code
- verified
- chatml
- unsloth
- sft
---

# RustForge Personal Rust Dataset (Verified Subset)

This package contains only rows that passed the local validation pipeline from the current RustForge HF dataset build.

- verified rows: `{len(verified_rows)}`
- categories covered: `{len(counts)}`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    manifest = {
        "verified_rows": len(verified_rows),
        "category_counts": dict(counts),
        "source_dataset": str(input_dir.name),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
