from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_REPORT_DIR = "hf-dataset/reports/dedup"
ID_PATTERN = re.compile(r"\b[a-z_]+\.[a-z0-9_]+\.\d{6}\b")
NUMERIC_SUFFIX_PATTERN = re.compile(r"_[0-9]{5,6}\b")


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)


def normalize_text(text: str) -> str:
    text = ID_PATTERN.sub("<example-id>", text)
    text = NUMERIC_SUFFIX_PATTERN.sub("_<n>", text)
    return text


def semantic_key(record: dict[str, object]) -> str:
    normalized = {
        "category": record["category"],
        "tier": record["tier"],
        "tags": sorted(record.get("tags", [])),
        "prompt": normalize_text(record.get("prompt", "")),
        "completion": normalize_text(record.get("completion", "")),
        "workspace_files": [
            {
                "path": file_obj["path"],
                "content": normalize_text(file_obj["content"]),
            }
            for file_obj in record.get("workspace_files", [])
        ],
        "target_files": [
            {
                "path": file_obj["path"],
                "content": normalize_text(file_obj["content"]),
            }
            for file_obj in record.get("target_files", [])
        ],
    }
    blob = json.dumps(normalized, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Find near-duplicate RustForge HF records using normalized semantic hashes.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / args.input_dir / "data"
    report_dir = repo_root / args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[str]] = defaultdict(list)
    category_counts: Counter[str] = Counter()
    total = 0
    for record in iter_records(data_dir):
        total += 1
        category_counts[str(record["category"])] += 1
        groups[semantic_key(record)].append(str(record["id"]))

    duplicates = {key: ids for key, ids in groups.items() if len(ids) > 1}
    summary = {
        "total_records": total,
        "unique_semantic_keys": len(groups),
        "duplicate_group_count": len(duplicates),
        "duplicate_record_count": sum(len(ids) for ids in duplicates.values()),
        "category_counts": dict(category_counts),
    }

    (report_dir / "dedup-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with (report_dir / "duplicate-groups.jsonl").open("w", encoding="utf-8") as handle:
        for key, ids in duplicates.items():
            handle.write(json.dumps({"semantic_key": key, "ids": ids}, ensure_ascii=False) + "\n")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
