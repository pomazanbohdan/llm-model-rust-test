from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_REPORT_DIR = "hf-dataset/reports/aux-validation"


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    yield shard_path.name, line_number, json.loads(line)


def _contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle in lowered for needle in needles)


def validate_auxiliary_record(record: dict[str, object]) -> dict[str, object]:
    category = str(record["category"])
    family_id = derive_family_id(record)
    tier = str(record["tier"])
    prompt = str(record.get("prompt", "")).strip()
    completion = str(record.get("completion", "")).strip()
    system = str(record.get("system", "")).strip()
    messages = record.get("messages", [])
    tags = record.get("tags", [])

    checks: list[dict[str, object]] = []

    def add_check(name: str, ok: bool, note: str) -> None:
        checks.append({"name": name, "ok": ok, "note": note})

    add_check("tier_auxiliary", tier == "auxiliary", "Record must belong to the auxiliary tier.")
    add_check("edition_2024", str(record.get("edition", "")) == "2024", "Record must target Rust 2024.")
    add_check("prompt_present", bool(prompt), "Prompt must be non-empty.")
    add_check("completion_present", bool(completion), "Completion must be non-empty.")
    add_check("system_present", bool(system), "System prompt must be non-empty.")
    add_check("messages_shape", isinstance(messages, list) and len(messages) == 3, "Messages must contain system, user, assistant turns.")
    add_check(
        "messages_roles",
        isinstance(messages, list)
        and len(messages) == 3
        and [item.get("role") for item in messages] == ["system", "user", "assistant"],
        "Messages must follow the system/user/assistant order.",
    )
    add_check("tags_present", isinstance(tags, list) and len(tags) > 0, "Tags must be present.")
    add_check("rust_signal", _contains_any(prompt + "\n" + completion, ["rust", "borrow", "unsafe", "async", "result", "panic", "cargo", "edition"]), "Prompt/completion must contain Rust-specific cues.")

    if family_id == "rust_qa.borrow_rules":
        add_check("family_keywords", _contains_any(completion, ["borrow", "exclusive", "clone", "lifetime"]), "Borrow-rules QA should mention borrow exclusivity or a typical fix.")
    elif family_id == "rust_qa.env_2024":
        add_check("family_keywords", _contains_any(completion, ["unsafe", "environment", "single-thread", "single threaded"]), "Rust 2024 env QA should mention unsafe environment mutation assumptions.")
    elif family_id == "rust_qa.async_locking":
        add_check("family_keywords", _contains_any(completion, ["await", "lock", "deadlock", "starvation", "guard"]), "Async locking QA should mention await/lock risks.")
    elif family_id == "review_preference.parse_port_review":
        add_check("family_keywords", _contains_any(completion, ["patch b", "result", "panic", "idiomatic", "safer"]), "Review preference should justify the better patch with Rust API reasoning.")
    else:
        add_check("family_keywords", True, "No extra family-specific rule configured.")

    ok = all(item["ok"] for item in checks)
    return {
        "id": record["id"],
        "category": category,
        "family_id": family_id,
        "tier": tier,
        "status": "validated" if ok else "failed",
        "validation_tier": "auxiliary_schema",
        "checks": checks,
        "validation": {
            "check": None,
            "clippy": None,
            "test": None,
            "fmt": None,
            "doc": None,
            "doctest": None,
            "notes": "Validated with auxiliary schema and Rust-content checks.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RustForge auxiliary records with schema and content checks.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    parser.add_argument("--category-include", default="", help="Comma-separated categories to keep. Empty means all auxiliary categories.")
    parser.add_argument("--family-include", default="", help="Comma-separated family ids to keep. Empty means all.")
    parser.add_argument("--start-per-family", type=int, default=0)
    parser.add_argument("--max-per-family", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    data_dir = repo_root / args.input_dir / "data"
    report_dir = repo_root / args.report_dir

    if report_dir.exists():
        shutil.rmtree(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    allowed_categories = {item.strip() for item in args.category_include.split(",") if item.strip()}
    allowed_families = {item.strip() for item in args.family_include.split(",") if item.strip()}
    seen_per_family: Counter[str] = Counter()
    kept_per_family: Counter[str] = Counter()
    reports: list[dict[str, object]] = []

    for _shard_name, _line_number, record in iter_records(data_dir):
        if str(record.get("tier")) != "auxiliary":
            continue
        category = str(record["category"])
        family_id = derive_family_id(record)
        if allowed_categories and category not in allowed_categories:
            continue
        if allowed_families and family_id not in allowed_families:
            continue
        if seen_per_family[family_id] < args.start_per_family:
            seen_per_family[family_id] += 1
            continue
        if args.max_per_family and kept_per_family[family_id] >= args.max_per_family:
            continue
        report = validate_auxiliary_record(record)
        reports.append(report)
        kept_per_family[family_id] += 1
        seen_per_family[family_id] += 1
        if args.limit and len(reports) >= args.limit:
            break

    summary = {
        "validated_records": len(reports),
        "validation_tier": "auxiliary_schema",
        "status_counts": dict(Counter(item["status"] for item in reports)),
        "category_counts": dict(Counter(item["category"] for item in reports)),
        "family_counts": dict(Counter(item["family_id"] for item in reports)),
    }

    (report_dir / "validation-report.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in reports) + ("\n" if reports else ""),
        encoding="utf-8",
    )
    (report_dir / "validation-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
