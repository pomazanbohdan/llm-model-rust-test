from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter, defaultdict, deque
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_FULL_REPORT_DIR = "hf-dataset/reports/validation-expanded"
DEFAULT_FAMILY_SCORE_DIR = "hf-dataset/reports/family-scores"
DEFAULT_OUTPUT_DIR = "hf-dataset-priority"
SHARD_SIZE = 5000
CORE_CATEGORIES = {
    "compile_repair",
    "semantic_impl",
    "test_driven_bugfix",
    "edition2024_migration",
    "async_concurrency_fix",
    "unsafe_ffi_fix",
    "clippy_fmt_cleanup",
    "macro_fix",
    "api_refactor",
    "doctest_doc_fix",
    "cargo_workspace_fix",
}


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def load_validation_results(report_path: Path) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    if report_path.is_file():
        with report_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                item = json.loads(line)
                results[str(item["id"])] = item
        return results
    if report_path.is_dir():
        for nested in sorted(report_path.rglob("validation-report.jsonl")):
            with nested.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    results[str(item["id"])] = item
    return results


def round_robin_take(family_queues: dict[str, deque[dict[str, object]]], family_order: list[str], amount: int) -> list[dict[str, object]]:
    picked: list[dict[str, object]] = []
    while len(picked) < amount and any(family_queues.values()):
        progressed = False
        for family_id in family_order:
            queue = family_queues.get(family_id)
            if not queue:
                continue
            if queue:
                picked.append(queue.popleft())
                progressed = True
                if len(picked) >= amount:
                    break
        if not progressed:
            break
    return picked


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a smaller high-confidence RustForge priority training set.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--full-report-dir", default=DEFAULT_FULL_REPORT_DIR)
    parser.add_argument("--family-score-dir", default=DEFAULT_FAMILY_SCORE_DIR)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-rows", type=int, default=15000)
    parser.add_argument("--min-family-validated", type=int, default=20)
    parser.add_argument("--min-family-pass-rate", type=float, default=1.0)
    parser.add_argument("--aux-share", type=float, default=0.05)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / args.input_dir
    output_dir = repo_root / args.output_dir
    family_score_dir = repo_root / args.family_score_dir
    report_dir = repo_root / args.full_report_dir

    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "data").mkdir(parents=True, exist_ok=True)

    validation_results = load_validation_results(report_dir / "validation-report.jsonl")
    if not validation_results:
        validation_results = load_validation_results(report_dir)
    family_scores = json.loads((family_score_dir / "family-scores.json").read_text(encoding="utf-8"))["families"]
    stable_families = {
        row["family_id"]
        for row in family_scores
        if float(row["pass_rate"]) >= args.min_family_pass_rate and int(row["validated_rows"]) >= args.min_family_validated
    }
    family_score_map = {row["family_id"]: float(row["stability_score"]) for row in family_scores}

    all_rows = list(iter_records(input_dir / "data"))
    category_totals = Counter(str(row["category"]) for row in all_rows if str(row["category"]) in CORE_CATEGORIES)

    verified_core_by_category: dict[str, list[dict[str, object]]] = defaultdict(list)
    stable_core_by_category_family: dict[str, dict[str, deque[dict[str, object]]]] = defaultdict(lambda: defaultdict(deque))
    auxiliary_rows_by_category: dict[str, list[dict[str, object]]] = defaultdict(list)

    for row in all_rows:
        row_id = str(row["id"])
        category = str(row["category"])
        family_id = derive_family_id(row)
        row["family_id"] = family_id
        row["priority_score"] = family_score_map.get(family_id, 0.0)
        if category in CORE_CATEGORIES:
            result = validation_results.get(row_id)
            if result and result["status"] == "validated":
                row["train_bucket"] = "verified_core"
                row["validation"] = result["validation"]
                verified_core_by_category[category].append(row)
            elif family_id in stable_families:
                row["train_bucket"] = "stable_core"
                stable_core_by_category_family[category][family_id].append(row)
        else:
            row["train_bucket"] = "auxiliary_tail"
            auxiliary_rows_by_category[category].append(row)

    aux_target = int(args.target_rows * args.aux_share)
    core_target = max(0, args.target_rows - aux_target)
    total_core_available = sum(category_totals.values())

    selected_rows: list[dict[str, object]] = []
    manifest_categories: Counter[str] = Counter()
    bucket_counts: Counter[str] = Counter()

    for category in sorted(CORE_CATEGORIES):
        quota = math.floor(core_target * (category_totals[category] / total_core_available)) if total_core_available else 0
        verified_rows = verified_core_by_category.get(category, [])
        selected_rows.extend(verified_rows[:quota])
        bucket_counts["verified_core"] += min(len(verified_rows), quota)
        manifest_categories[category] += min(len(verified_rows), quota)

        remaining = max(0, quota - len(verified_rows))
        if remaining:
            family_order = sorted(
                stable_core_by_category_family[category],
                key=lambda family_id: family_score_map.get(family_id, 0.0),
                reverse=True,
            )
            picked = round_robin_take(stable_core_by_category_family[category], family_order, remaining)
            selected_rows.extend(picked)
            bucket_counts["stable_core"] += len(picked)
            manifest_categories[category] += len(picked)

    aux_per_category = aux_target // max(1, len(auxiliary_rows_by_category))
    for category in sorted(auxiliary_rows_by_category):
        picked = auxiliary_rows_by_category[category][:aux_per_category]
        selected_rows.extend(picked)
        bucket_counts["auxiliary_tail"] += len(picked)
        manifest_categories[category] += len(picked)

    selected_rows.sort(key=lambda row: (str(row["category"]), str(row["id"])))
    shard_count = max(1, math.ceil(len(selected_rows) / SHARD_SIZE))
    for shard_index in range(shard_count):
        shard_rows = selected_rows[shard_index * SHARD_SIZE:(shard_index + 1) * SHARD_SIZE]
        shard_name = f"train-{shard_index:05d}-of-{shard_count:05d}.jsonl"
        with (output_dir / "data" / shard_name).open("w", encoding="utf-8", newline="\n") as handle:
            for row in shard_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    readme = f"""---
language:
- en
pretty_name: RustForge Priority Rust Train Set
license: other
task_categories:
- text-generation
tags:
- rust
- code
- verified
- stable-families
- chatml
- unsloth
- sft
---

# RustForge Priority Rust Train Set

This package is a smaller high-confidence training subset built from:

- locally validated core rows
- additional synthetic rows from stable family templates
- a small auxiliary tail

- total rows: `{len(selected_rows)}`
- verified core rows: `{bucket_counts["verified_core"]}`
- stable synthetic core rows: `{bucket_counts["stable_core"]}`
- auxiliary rows: `{bucket_counts["auxiliary_tail"]}`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    manifest = {
        "total_rows": len(selected_rows),
        "bucket_counts": dict(bucket_counts),
        "category_counts": dict(manifest_categories),
        "source_dataset": input_dir.name,
        "min_family_validated": args.min_family_validated,
        "min_family_pass_rate": args.min_family_pass_rate,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
