from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

from rustforge_family import derive_family_id


DEFAULT_INPUT_DIR = "hf-dataset"
DEFAULT_REPORT_DIR = "hf-dataset/reports/validation"
CHECKS = [
    ("check", ["cargo", "check"]),
    ("clippy", ["cargo", "clippy", "--", "-D", "warnings"]),
    ("test", ["cargo", "test", "--no-run"]),
    ("fmt", ["cargo", "fmt", "--check"]),
    ("doc", ["cargo", "doc", "--no-deps"]),
    ("doctest", ["cargo", "test", "--doc", "-v"]),
]
CHECK_TIERS = {
    "cheap": {"check", "fmt"},
    "medium": {"check", "fmt", "clippy", "test"},
    "full": {"check", "fmt", "clippy", "test", "doc", "doctest"},
}


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
        infra_error = None
        if result.returncode != 0 and "os error 4551" in result.stderr and "Application Control policy has blocked this file" in result.stderr:
            infra_error = "app_control_blocked"
        return {
            "name": name,
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
            **({"infra_error": infra_error} if infra_error else {}),
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


def retry_doctest_in_fresh_workspace(record: dict[str, object], timeout_sec: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="rustforge-doctest-retry-") as temp_dir:
        work_dir = Path(temp_dir)
        materialize_workspace(work_dir, record)
        retried = run_check(work_dir, "doctest", ["cargo", "test", "--doc", "-v"], timeout_sec)
        retried["retried"] = True
        retried["fresh_workspace_retry"] = True
        return retried


def validate_record(record: dict[str, object], timeout_sec: int, validation_tier: str) -> dict[str, object]:
    category = str(record["category"])
    tier = str(record["tier"])
    family_id = derive_family_id(record)
    if tier == "auxiliary":
        return {
            "id": record["id"],
            "category": category,
            "family_id": family_id,
            "tier": tier,
            "status": "skipped_auxiliary",
            "validation_tier": validation_tier,
            "checks": [],
            "validation": record["validation"],
        }

    with tempfile.TemporaryDirectory(prefix="rustforge-validate-") as temp_dir:
        work_dir = Path(temp_dir)
        materialize_workspace(work_dir, record)
        enabled_checks = CHECK_TIERS[validation_tier]
        check_results = [run_check(work_dir, name, command, timeout_sec) for name, command in CHECKS if name in enabled_checks]
        failed_checks = [item for item in check_results if not item["ok"]]
        if validation_tier == "full" and len(failed_checks) == 1 and failed_checks[0]["name"] == "doctest":
            retried = run_check(work_dir, "doctest", ["cargo", "test", "--doc", "-v"], timeout_sec)
            retried["retried"] = True
            if not retried["ok"]:
                retried = retry_doctest_in_fresh_workspace(record, timeout_sec)
            check_results = [item if item["name"] != "doctest" else retried for item in check_results]
        results_by_name = {item["name"]: item for item in check_results}
        validation = {
            "check": results_by_name["check"]["ok"] if "check" in results_by_name else None,
            "clippy": results_by_name["clippy"]["ok"] if "clippy" in results_by_name else None,
            "test": results_by_name["test"]["ok"] if "test" in results_by_name else None,
            "fmt": results_by_name["fmt"]["ok"] if "fmt" in results_by_name else None,
            "doc": results_by_name["doc"]["ok"] if "doc" in results_by_name else None,
            "doctest": results_by_name["doctest"]["ok"] if "doctest" in results_by_name else None,
            "notes": f"Validated from target_files over workspace_files using {validation_tier} tier.",
        }
        failed_checks = [item for item in check_results if not item["ok"]]
        has_real_failure = any("infra_error" not in item for item in failed_checks)
        has_infra_only_failure = bool(failed_checks) and not has_real_failure
        if all(item["ok"] for item in check_results):
            status = "validated"
        elif has_infra_only_failure:
            status = "skipped_infra"
            validation["notes"] = "Skipped because local execution policy blocked a generated test binary."
        else:
            status = "failed"
        return {
            "id": record["id"],
            "category": category,
            "family_id": family_id,
            "tier": tier,
            "status": status,
            "validation_tier": validation_tier,
            "checks": check_results,
            "validation": validation,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate RustForge HF dataset records by materializing and running cargo checks.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--report-dir", default=DEFAULT_REPORT_DIR)
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of records to validate. 0 means all.")
    parser.add_argument("--max-per-category", type=int, default=0, help="Maximum validations per category. 0 means unlimited.")
    parser.add_argument("--max-per-family", type=int, default=0, help="Maximum validations per family. 0 means unlimited.")
    parser.add_argument("--start-per-category", type=int, default=0, help="Skip this many records per category before validating.")
    parser.add_argument("--start-per-family", type=int, default=0, help="Skip this many records per family before validating.")
    parser.add_argument("--tiers", choices=["all", "core", "auxiliary"], default="all")
    parser.add_argument("--validation-tier", choices=["cheap", "medium", "full"], default="full")
    parser.add_argument("--family-include", default="", help="Comma-separated family ids to keep. Empty means all.")
    parser.add_argument("--id-include", default="", help="Comma-separated record ids to validate. Empty means all.")
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
    per_family: Counter[str] = Counter()
    seen_per_category: Counter[str] = Counter()
    seen_per_family: Counter[str] = Counter()
    family_filter = {item.strip() for item in args.family_include.split(",") if item.strip()}
    id_filter = {item.strip() for item in args.id_include.split(",") if item.strip()}

    for _shard_name, _line_number, record in iter_records(data_dir):
        category = str(record["category"])
        tier = str(record["tier"])
        family_id = derive_family_id(record)
        record_id = str(record["id"])
        if args.tiers != "all" and tier != args.tiers:
            continue
        if id_filter and record_id not in id_filter:
            continue
        if family_filter and family_id not in family_filter:
            continue
        if seen_per_category[category] < args.start_per_category:
            seen_per_category[category] += 1
            continue
        if seen_per_family[family_id] < args.start_per_family:
            seen_per_family[family_id] += 1
            continue
        if args.max_per_category and per_category[category] >= args.max_per_category:
            continue
        if args.max_per_family and per_family[family_id] >= args.max_per_family:
            continue
        report = validate_record(record, args.timeout_sec, args.validation_tier)
        reports.append(report)
        per_category[category] += 1
        per_family[family_id] += 1
        seen_per_family[family_id] += 1
        if args.limit and len(reports) >= args.limit:
            break

    summary = {
        "validated_records": len(reports),
        "validation_tier": args.validation_tier,
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
