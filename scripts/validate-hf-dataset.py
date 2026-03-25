from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_REPORT_DIR = "hf-dataset/reports/validation"
CHECKS = [
    ("check", ["cargo", "check"]),
    ("clippy", ["cargo", "clippy", "--", "-D", "warnings"]),
    ("test", ["cargo", "test"]),
    ("fmt", ["cargo", "fmt", "--check"]),
    ("doc", ["cargo", "doc", "--no-deps"]),
    ("doctest", ["cargo", "test", "--doc"]),
]


def iter_records(data_dir: Path):
    for shard_path in sorted(data_dir.glob("train-*.jsonl")):
        with shard_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    yield shard_path.name, line_number, json.loads(line)


def materialize_workspace(work_dir: Path, record: dict[str, object]) -> None:
    for file_obj in record.get("workspace_files", []):
        path = work_dir / file_obj["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file_obj["content"], encoding="utf-8")

    for file_obj in record.get("target_files", []):
        path = work_dir / file_obj["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file_obj["content"], encoding="utf-8")


def run_check(work_dir: Path, name: str, command: list[str], timeout_sec: int) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        return {
            "name": name,
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
        }
    except FileNotFoundError as exc:
        return {
            "name": name,
            "ok": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "infra_error": "command_not_found",
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "ok": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": f"Timed out after {timeout_sec} seconds.",
            "infra_error": "timeout",
        }


def validate_record(record: dict[str, object], timeout_sec: int) -> dict[str, object]:
    category = str(record["category"])
    tier = str(record["tier"])
    if tier == "auxiliary":
        return {
            "id": record["id"],
            "category": category,
            "tier": tier,
            "status": "skipped_auxiliary",
            "checks": [],
            "validation": record["validation"],
        }

    with tempfile.TemporaryDirectory(prefix="rustforge-validate-") as temp_dir:
        work_dir = Path(temp_dir)
        materialize_workspace(work_dir, record)
        check_results = [run_check(work_dir, name, command, timeout_sec) for name, command in CHECKS]
        validation = {
            "check": next(item["ok"] for item in check_results if item["name"] == "check"),
            "clippy": next(item["ok"] for item in check_results if item["name"] == "clippy"),
            "test": next(item["ok"] for item in check_results if item["name"] == "test"),
            "fmt": next(item["ok"] for item in check_results if item["name"] == "fmt"),
            "doc": next(item["ok"] for item in check_results if item["name"] == "doc"),
            "doctest": next(item["ok"] for item in check_results if item["name"] == "doctest"),
            "notes": "Validated from target_files over workspace_files.",
        }
        status = "validated" if all(validation[key] for key in ("check", "clippy", "test", "fmt", "doc", "doctest")) else "failed"
        return {
            "id": record["id"],
            "category": category,
            "tier": tier,
            "status": status,
            "checks": check_results,
            "validation": validation,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RustForge HF dataset records by materializing and running cargo checks.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of records to validate. 0 means all.")
    parser.add_argument("--max-per-category", type=int, default=0, help="Maximum validations per category. 0 means unlimited.")
    parser.add_argument("--timeout-sec", type=int, default=60)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    input_dir = repo_root / args.input_dir
    data_dir = input_dir / "data"
    report_dir = repo_root / args.report_dir

    if report_dir.exists():
        shutil.rmtree(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, object]] = []
    per_category: Counter[str] = Counter()

    for _shard_name, _line_number, record in iter_records(data_dir):
        category = str(record["category"])
        if args.max_per_category and per_category[category] >= args.max_per_category:
            continue
        report = validate_record(record, args.timeout_sec)
        reports.append(report)
        per_category[category] += 1
        if args.limit and len(reports) >= args.limit:
            break

    summary = {
        "validated_records": len(reports),
        "status_counts": dict(Counter(item["status"] for item in reports)),
        "category_counts": dict(Counter(item["category"] for item in reports)),
    }

    (report_dir / "validation-report.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in reports) + ("\n" if reports else ""),
        encoding="utf-8",
    )
    (report_dir / "validation-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
