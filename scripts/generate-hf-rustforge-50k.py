from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path


DEFAULT_REPO_ID = "pomazanbohdan/rustforge-personal-rust-dataset"
DEFAULT_OUTPUT_DIR = "hf-dataset"
DEFAULT_SOURCE_DIR = "hf-source/batches"
DATASET_VERSION = "0.5.2"
SHARD_SIZE = 5000

MODIFIERS = [
    "alpha", "amber", "atlas", "aurora", "binary", "brisk", "cinder", "cobalt", "delta", "ember",
    "frost", "gamma", "granite", "harbor", "helios", "ion", "jade", "kepler", "lattice", "lumen",
    "matrix", "meridian", "nebula", "onyx", "orbit", "oxide", "parallel", "plasma", "quartz", "radial",
    "raven", "sable", "scarlet", "signal", "silver", "solar", "sonic", "static", "stellar", "swift",
    "terra", "titan", "vector", "vivid", "volta", "zenith", "zircon",
]
ENTITIES = [
    "account", "address", "buffer", "bucket", "cache", "channel", "checkpoint", "cluster", "command", "config",
    "cursor", "dataset", "digest", "endpoint", "entry", "event", "feature", "frame", "gateway", "handle",
    "header", "index", "job", "key", "label", "ledger", "limit", "listener", "metric", "module",
    "node", "packet", "payload", "port", "queue", "record", "region", "request", "route", "scope",
    "segment", "session", "signal", "slot", "source", "stream", "tenant", "token", "trace", "window",
]
DOMAINS = [
    "api", "auth", "bridge", "codec", "core", "ffi", "guard", "http", "io", "json",
    "log", "mail", "net", "parser", "queue", "rpc", "store", "sync", "task", "time",
]
DIRECTIVES = ["max-age", "retry", "limit", "burst", "ttl", "window", "keep-alive", "idle"]
DOC_TYPES = ["UserId", "TenantId", "MetricName", "RouteKey", "HeaderValue", "SessionTag", "ClusterId", "TokenRef"]
COLORS = ["red", "green", "blue", "amber", "cyan", "gray", "white", "black"]


def pick(values: list[str], idx: int, offset: int = 0) -> str:
    return values[(idx + offset) % len(values)]


def symbol(idx: int, salt: int = 0) -> str:
    return f"{pick(MODIFIERS, idx, salt)}_{pick(ENTITIES, idx * 3 + salt, 1)}_{pick(DOMAINS, idx * 7 + salt, 2)}"


def title_symbol(value: str) -> str:
    return "".join(part.title() for part in value.split("_"))


def cargo_toml(crate_name: str, deps: list[str] | None = None) -> str:
    lines = ["[package]", f'name = "{crate_name}"', 'version = "0.1.0"', 'edition = "2024"', ""]
    if deps:
        lines.extend(["[dependencies]", *deps, ""])
    return "\n".join(lines)


def fence_lang(path: str) -> str:
    if path.endswith(".rs"):
        return "rust"
    if path.endswith(".toml"):
        return "toml"
    if path.endswith(".md"):
        return "markdown"
    return "text"


def render_workspace(files: list[dict[str, str]]) -> str:
    out: list[str] = []
    for file in files:
        out.extend([f"File: {file['path']}", f"```{fence_lang(file['path'])}", file["content"].rstrip(), "```", ""])
    return "\n".join(out).rstrip()


def render_file_blocks(files: list[dict[str, str]]) -> str:
    out: list[str] = []
    for file in files:
        out.extend([f'<file path="{file["path"]}">', file["content"].rstrip(), "</file>", ""])
    return "\n".join(out).rstrip()


def base_validation(note: str) -> dict[str, object]:
    return {
        "check": False,
        "clippy": False,
        "test": False,
        "fmt": False,
        "doc": False,
        "doctest": False,
        "notes": note,
    }


def make_record(
    *,
    example_id: str,
    family_id: str,
    category: str,
    difficulty: str,
    tier: str,
    instruction: str,
    constraints: list[str],
    workspace_files: list[dict[str, str]],
    target_files: list[dict[str, str]],
    tags: list[str],
    source_name: str,
    note: str,
    hidden_file_count: int = 0,
) -> dict[str, object]:
    prompt = "\n".join([
        f"Rust task id: {example_id}",
        f"Category: {category}",
        f"Difficulty: {difficulty}",
        "Edition target: 2024",
        "",
        "Task:",
        instruction,
        "",
        "Constraints:",
        *[f"- {item}" for item in dict.fromkeys(constraints)],
        "",
        "Editable workspace files:",
        render_workspace(workspace_files),
        "",
        "Response format:",
        '<file path="relative/path">',
        "...final file contents...",
        "</file>",
        "",
        "Return only the changed files.",
    ])
    completion = render_file_blocks(target_files)
    system = (
        "You are a Rust coding assistant.\n"
        "Solve the task using Rust edition 2024 semantics unless the prompt explicitly asks for a migration.\n"
        'Return only the final contents of the changed files using <file path="..."> blocks.'
    )
    return {
        "dataset_version": DATASET_VERSION,
        "split": "train",
        "record_format": "chatml_messages",
        "example_state": "synthetic_candidate",
        "id": example_id,
        "family_id": family_id,
        "category": category,
        "difficulty": difficulty,
        "edition": "2024",
        "tier": tier,
        "source_type": "synthetic_program_generator",
        "source_name": source_name,
        "source_license_status": "internal_synthetic",
        "source_leakage_risk": "low",
        "prompt": prompt,
        "completion": completion,
        "system": system,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": completion},
        ],
        "workspace_files": workspace_files,
        "target_files": target_files,
        "hidden_file_count": hidden_file_count,
        "validation": base_validation(note),
        "tags": tags,
    }


def make_text_record(
    *,
    example_id: str,
    family_id: str,
    category: str,
    difficulty: str,
    tier: str,
    prompt: str,
    completion: str,
    tags: list[str],
    source_name: str,
    note: str,
) -> dict[str, object]:
    system = "You are a senior Rust assistant. Answer concisely and correctly with Rust-specific reasoning."
    return {
        "dataset_version": DATASET_VERSION,
        "split": "train",
        "record_format": "chatml_messages",
        "example_state": "synthetic_candidate",
        "id": example_id,
        "family_id": family_id,
        "category": category,
        "difficulty": difficulty,
        "edition": "2024",
        "tier": tier,
        "source_type": "synthetic_program_generator",
        "source_name": source_name,
        "source_license_status": "internal_synthetic",
        "source_leakage_risk": "low",
        "prompt": prompt,
        "completion": completion,
        "system": system,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": completion},
        ],
        "workspace_files": [],
        "target_files": [],
        "hidden_file_count": 0,
        "validation": base_validation(note),
        "tags": tags,
    }


def load_batch_specs(source_dir: Path) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for path in sorted(source_dir.glob("*.json")):
        specs.extend(json.loads(path.read_text(encoding="utf-8"))["categories"])
    return specs


def gen_compile_repair(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 1)
    crate_name = f"compile_repair_{name}"
    fallback = f"{pick(MODIFIERS, idx, 2)}-{pick(ENTITIES, idx, 3)}"
    variant = idx % 6
    if variant == 0:
        family_id = "compile_repair.push_first_clone"
        workspace = (
            f"pub fn push_first_{name}(items: &mut Vec<String>) {{\n"
            f"    let first = items.first().unwrap_or(&String::from(\"{fallback}\"));\n"
            "    items.push(first.to_ascii_lowercase());\n"
            "}\n"
        )
        target = (
            f"pub fn push_first_{name}(items: &mut Vec<String>) {{\n"
            "    let first = items\n"
            "        .first()\n"
            "        .cloned()\n"
            f"        .unwrap_or_else(|| \"{fallback}\".to_string());\n"
            "    items.push(first.to_ascii_lowercase());\n"
            "}\n"
        )
    elif variant == 1:
        family_id = "compile_repair.normalize_owned"
        workspace = (
            f"pub fn normalize_{name}(input: &str) -> &str {{\n"
            "    let lowered = input.trim().to_ascii_lowercase();\n"
            "    lowered.as_str()\n"
            "}\n"
        )
        target = (
            f"pub fn normalize_{name}(input: &str) -> String {{\n"
            "    input.trim().to_ascii_lowercase()\n"
            "}\n"
        )
    elif variant == 2:
        family_id = "compile_repair.join_labels_owned"
        workspace = (
            f"pub fn join_{name}_labels(labels: &[String]) -> &str {{\n"
            "    let joined = labels.join(\",\");\n"
            "    joined.as_str()\n"
            "}\n"
        )
        target = (
            f"pub fn join_{name}_labels(labels: &[String]) -> String {{\n"
            "    labels.join(\",\")\n"
            "}\n"
        )
    elif variant == 3:
        family_id = "compile_repair.parse_ports_collect"
        signature = f"pub fn parse_{name}_ports(input: &[String]) -> Result<Vec<u16>, std::num::ParseIntError> {{"
        if len(signature) > 100:
            signature = (
                f"pub fn parse_{name}_ports(\n"
                "    input: &[String],\n"
                ") -> Result<Vec<u16>, std::num::ParseIntError> {"
            )
        workspace = (
            f"pub fn parse_{name}_ports(input: &[String]) -> Vec<u16> {{\n"
            "    input.iter().map(|item| item.parse::<u16>().unwrap()).collect()\n"
            "}\n"
        )
        target = (
            f"{signature}\n"
            "    input.iter().map(|item| item.parse::<u16>()).collect()\n"
            "}\n"
        )
    else:
        family_id = "compile_repair.stringify_collect_owned"
        workspace = (
            f"pub fn stringify_{name}<T: ToString>(input: &[T]) -> Vec<&str> {{\n"
            "    input\n"
            "        .iter()\n"
            "        .map(|item| item.to_string().trim())\n"
            "        .collect()\n"
            "}\n"
        )
        target = (
            f"pub fn stringify_{name}<T: ToString>(input: &[T]) -> Vec<String> {{\n"
            "    input\n"
            "        .iter()\n"
            "        .map(|item| item.to_string())\n"
            "        .map(|item| item.trim().to_string())\n"
            "        .collect()\n"
            "}\n"
        )
    return make_record(
        example_id=f"compile_repair.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="compile_repair",
        difficulty="easy" if variant == 0 else "medium",
        tier=tier,
        instruction=f"Repair the compile issue in the {name} helper with the smallest correct patch.",
        constraints=["Keep the public API unchanged where possible.", "Target Rust edition 2024.", "Prefer a minimal compile fix."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["compile", "ownership", name],
        source_name="compile_repair_generator_v3",
        note="Synthetic compile-repair example pending validation.",
    )


def gen_semantic_impl(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 2)
    crate_name = f"semantic_impl_{name}"
    variant = idx % 8
    if variant == 0:
        family_id = "semantic_impl.directive_parser"
        directive = pick(DIRECTIVES, idx, 1)
        workspace = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseDirectiveError {\n"
            "    InvalidDirective,\n"
            "    InvalidNumber,\n"
            "}\n\n"
            f"pub fn parse_{name}_directive(input: &str) -> Result<u64, ParseDirectiveError> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseDirectiveError {\n"
            "    InvalidDirective,\n"
            "    InvalidNumber,\n"
            "}\n\n"
            f"pub fn parse_{name}_directive(input: &str) -> Result<u64, ParseDirectiveError> {{\n"
            "    let trimmed = input.trim();\n"
            "    let (directive, value) = trimmed\n"
            "        .split_once('=')\n"
            "        .ok_or(ParseDirectiveError::InvalidDirective)?;\n"
            f"    if directive.trim() != \"{directive}\" {{\n"
            "        return Err(ParseDirectiveError::InvalidDirective);\n"
            "    }\n"
            "    value\n"
            "        .trim()\n"
            "        .parse::<u64>()\n"
            "        .map_err(|_| ParseDirectiveError::InvalidNumber)\n"
            "}\n"
        )
    elif variant == 1:
        family_id = "semantic_impl.endpoint_parser"
        signature = f"pub fn parse_{name}_endpoint(input: &str) -> Result<(String, u16), ParseEndpointError> {{"
        if len(signature) > 100:
            signature = (
                f"pub fn parse_{name}_endpoint(\n"
                "    input: &str,\n"
                ") -> Result<(String, u16), ParseEndpointError> {"
            )
        workspace = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseEndpointError {\n"
            "    InvalidShape,\n"
            "    InvalidPort,\n"
            "}\n\n"
            f"{signature}\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseEndpointError {\n"
            "    InvalidShape,\n"
            "    InvalidPort,\n"
            "}\n\n"
            f"{signature}\n"
            "    let trimmed = input.trim();\n"
            "    let (host, port) = trimmed\n"
            "        .split_once(':')\n"
            "        .ok_or(ParseEndpointError::InvalidShape)?;\n"
            "    let host = host.trim();\n"
            "    if host.is_empty() {\n"
            "        return Err(ParseEndpointError::InvalidShape);\n"
            "    }\n"
            "    let port = port\n"
            "        .trim()\n"
            "        .parse::<u16>()\n"
            "        .map_err(|_| ParseEndpointError::InvalidPort)?;\n"
            "    Ok((host.to_string(), port))\n"
            "}\n"
        )
    elif variant == 2:
        family_id = "semantic_impl.csv_parser"
        workspace = (
            f"pub fn parse_{name}_csv(input: &str) -> Vec<String> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            f"pub fn parse_{name}_csv(input: &str) -> Vec<String> {{\n"
            "    input\n"
            "        .split(',')\n"
            "        .map(str::trim)\n"
            "        .filter(|item| !item.is_empty())\n"
            "        .map(|item| item.to_string())\n"
            "        .collect()\n"
            "}\n"
        )
    elif variant == 3:
        family_id = "semantic_impl.pairs_map"
        workspace = (
            "use std::collections::BTreeMap;\n\n"
            f"pub fn parse_{name}_pairs(input: &str) -> BTreeMap<String, String> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "use std::collections::BTreeMap;\n\n"
            f"pub fn parse_{name}_pairs(input: &str) -> BTreeMap<String, String> {{\n"
            "    input\n"
            "        .split(';')\n"
            "        .filter_map(|pair| {\n"
            "            let (key, value) = pair.split_once('=')?;\n"
            "            let key = key.trim();\n"
            "            let value = value.trim();\n"
            "            if key.is_empty() {\n"
            "                return None;\n"
            "            }\n"
            "            Some((key.to_string(), value.to_string()))\n"
            "        })\n"
            "        .collect()\n"
            "}\n"
        )
    elif variant == 4:
        family_id = "semantic_impl.bool_flag"
        workspace = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseFlagError {\n"
            "    InvalidValue,\n"
            "}\n\n"
            f"pub fn parse_{name}_flag(input: &str) -> Result<bool, ParseFlagError> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseFlagError {\n"
            "    InvalidValue,\n"
            "}\n\n"
            f"pub fn parse_{name}_flag(input: &str) -> Result<bool, ParseFlagError> {{\n"
            "    match input.trim().to_ascii_lowercase().as_str() {\n"
            "        \"true\" | \"yes\" | \"1\" => Ok(true),\n"
            "        \"false\" | \"no\" | \"0\" => Ok(false),\n"
            "        _ => Err(ParseFlagError::InvalidValue),\n"
            "    }\n"
            "}\n"
        )
    elif variant == 5:
        family_id = "semantic_impl.duration_seconds"
        workspace = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseDurationError {\n"
            "    InvalidShape,\n"
            "    InvalidNumber,\n"
            "}\n\n"
            f"pub fn parse_{name}_seconds(input: &str) -> Result<u64, ParseDurationError> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseDurationError {\n"
            "    InvalidShape,\n"
            "    InvalidNumber,\n"
            "}\n\n"
            f"pub fn parse_{name}_seconds(input: &str) -> Result<u64, ParseDurationError> {{\n"
            "    let trimmed = input.trim();\n"
            "    let value = trimmed\n"
            "        .strip_suffix('s')\n"
            "        .ok_or(ParseDurationError::InvalidShape)?;\n"
            "    value\n"
            "        .trim()\n"
            "        .parse::<u64>()\n"
            "        .map_err(|_| ParseDurationError::InvalidNumber)\n"
            "}\n"
        )
    elif variant == 6:
        family_id = "semantic_impl.header_map"
        workspace = (
            "use std::collections::BTreeMap;\n\n"
            f"pub fn parse_{name}_headers(input: &str) -> BTreeMap<String, String> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            "use std::collections::BTreeMap;\n\n"
            f"pub fn parse_{name}_headers(input: &str) -> BTreeMap<String, String> {{\n"
            "    input\n"
            "        .lines()\n"
            "        .filter_map(|line| {\n"
            "            let (key, value) = line.split_once(':')?;\n"
            "            let key = key.trim();\n"
            "            let value = value.trim();\n"
            "            if key.is_empty() {\n"
            "                return None;\n"
            "            }\n"
            "            Some((key.to_string(), value.to_string()))\n"
            "        })\n"
            "        .collect()\n"
            "}\n"
        )
    else:
        family_id = "semantic_impl.key_list"
        workspace = (
            f"pub fn parse_{name}_keys(input: &str) -> Vec<String> {{\n"
            "    todo!()\n"
            "}\n"
        )
        target = (
            f"pub fn parse_{name}_keys(input: &str) -> Vec<String> {{\n"
            "    input\n"
            "        .split('|')\n"
            "        .map(str::trim)\n"
            "        .filter(|item| !item.is_empty())\n"
            "        .map(|item| item.to_string())\n"
            "        .collect()\n"
            "}\n"
        )
    return make_record(
        example_id=f"semantic_impl.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="semantic_impl",
        difficulty="medium",
        tier=tier,
        instruction=f"Implement the semantic Rust task for {name}.",
        constraints=["Keep the public API unchanged.", "Target Rust edition 2024.", "Return deterministic results for malformed input."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["semantic", name],
        source_name="semantic_impl_generator_v2",
        note="Synthetic semantic example pending hidden-test validation.",
        hidden_file_count=1,
    )


def gen_bugfix(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 3)
    crate_name = f"bugfix_{name}"
    variant = idx % 6
    if variant == 0:
        family_id = "test_driven_bugfix.normalize_path"
        workspace = (
            f"pub fn normalize_{name}_path(path: &str) -> String {{\n"
            "    path.replace(\"//\", \"/\").trim_end_matches('/').to_string()\n"
            "}\n"
        )
        target = (
            f"pub fn normalize_{name}_path(path: &str) -> String {{\n"
            "    let mut normalized = path.replace(\"//\", \"/\");\n"
            "    if normalized.len() > 1 {\n"
            "        normalized = normalized.trim_end_matches('/').to_string();\n"
            "    }\n"
            "    normalized\n"
            "}\n"
        )
    elif variant == 1:
        family_id = "test_driven_bugfix.moving_average"
        workspace = (
            f"pub fn moving_average_{name}(values: &[u32], window: usize) -> Vec<u32> {{\n"
            "    if window == 0 {\n"
            "        return vec![0];\n"
            "    }\n"
            "    values\n"
            "        .windows(window)\n"
            "        .map(|slice| slice.iter().sum::<u32>() / window as u32)\n"
            "        .collect()\n"
            "}\n"
        )
        target = (
            f"pub fn moving_average_{name}(values: &[u32], window: usize) -> Vec<u32> {{\n"
            "    if window == 0 || window > values.len() {\n"
            "        return Vec::new();\n"
            "    }\n"
            "    values\n"
            "        .windows(window)\n"
            "        .map(|slice| slice.iter().sum::<u32>() / window as u32)\n"
            "        .collect()\n"
            "}\n"
        )
    elif variant == 2:
        family_id = "test_driven_bugfix.dedup_sorted"
        workspace = (
            f"pub fn dedup_{name}_sorted(values: &[u32]) -> Vec<u32> {{\n"
            "    let mut out = Vec::new();\n"
            "    for value in values {\n"
            "        if out.last() != Some(value) {\n"
            "            out.push(*value);\n"
            "        }\n"
            "    }\n"
            "    out.sort_unstable();\n"
            "    out\n"
            "}\n"
        )
        target = workspace.replace("    out.sort_unstable();\n", "")
    else:
        family_id = "test_driven_bugfix.nonempty_lines"
        workspace = (
            f"pub fn nonempty_{name}_lines(input: &str) -> Vec<&str> {{\n"
            "    input.lines().collect()\n"
            "}\n"
        )
        target = (
            f"pub fn nonempty_{name}_lines(input: &str) -> Vec<&str> {{\n"
            "    input\n"
            "        .lines()\n"
            "        .map(str::trim)\n"
            "        .filter(|line| !line.is_empty())\n"
            "        .collect()\n"
            "}\n"
        )
    return make_record(
        example_id=f"test_driven_bugfix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="test_driven_bugfix",
        difficulty="medium",
        tier=tier,
        instruction=f"Fix the bug in the {name} helper without changing the public API.",
        constraints=["Keep the public API unchanged.", "Prefer the smallest correct patch.", "Preserve intended semantics."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["bugfix", name],
        source_name="bugfix_generator_v2",
        note="Synthetic bugfix example pending validation.",
        hidden_file_count=1,
    )


def gen_edition(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 4)
    crate_name = f"edition2024_{name}"
    variant = idx % 6
    if variant == 0:
        family_id = "edition2024_migration.unsafe_env_set"
        workspace = f'pub fn bootstrap_env(value: &str) {{\n    std::env::set_var("APP_{name.upper()}", value);\n}}\n'
        target = f'pub fn bootstrap_env(value: &str) {{\n    // SAFETY: This helper runs during single-threaded process bootstrap.\n    unsafe {{\n        std::env::set_var("APP_{name.upper()}", value);\n    }}\n}}\n'
    elif variant == 1:
        family_id = "edition2024_migration.unsafe_extern"
        workspace = f'use std::os::raw::c_char;\n\nextern "C" {{\n    pub fn load_{name}(value: *const c_char) -> i32;\n}}\n'
        target = f'use std::os::raw::c_char;\n\nunsafe extern "C" {{\n    pub fn load_{name}(value: *const c_char) -> i32;\n}}\n'
    elif variant == 2:
        family_id = "edition2024_migration.unsafe_attribute"
        workspace = f'#[no_mangle]\npub extern "C" fn export_{name}() -> usize {{\n    1\n}}\n'
        target = f'#[unsafe(no_mangle)]\npub extern "C" fn export_{name}() -> usize {{\n    1\n}}\n'
    elif variant == 3:
        family_id = "edition2024_migration.unsafe_env_remove"
        workspace = f'pub fn clear_env() {{\n    std::env::remove_var("APP_{name.upper()}");\n}}\n'
        target = f'pub fn clear_env() {{\n    // SAFETY: This helper runs during single-threaded process bootstrap.\n    unsafe {{\n        std::env::remove_var("APP_{name.upper()}");\n    }}\n}}\n'
    elif variant == 4:
        family_id = "edition2024_migration.unsafe_op_in_unsafe_fn"
        workspace = (
            "use std::slice;\n\n"
            f"pub unsafe fn slice_{name}<'a>(ptr: *const u8, len: usize) -> &'a [u8] {{\n"
            "    slice::from_raw_parts(ptr, len)\n"
            "}\n"
        )
        target = (
            "use std::slice;\n\n"
            "/// # Safety\n"
            "/// The caller must ensure ptr is valid for reads of len bytes.\n"
            f"pub unsafe fn slice_{name}<'a>(ptr: *const u8, len: usize) -> &'a [u8] {{\n"
            "    unsafe { slice::from_raw_parts(ptr, len) }\n"
            "}\n"
        )
    else:
        family_id = "edition2024_migration.static_mut_once_lock"
        workspace = (
            "static mut CONFIG: Option<String> = None;\n\n"
            f"pub fn config_{name}() -> &'static str {{\n"
            "    unsafe {\n"
            f"        CONFIG.get_or_insert_with(|| \"{name}\".to_string()).as_str()\n"
            "    }\n"
            "}\n"
        )
        target = (
            "use std::sync::OnceLock;\n\n"
            "static CONFIG: OnceLock<String> = OnceLock::new();\n\n"
            f"pub fn config_{name}() -> &'static str {{\n"
            "    CONFIG\n"
            f"        .get_or_init(|| \"{name}\".to_string())\n"
            "        .as_str()\n"
            "}\n"
        )
    return make_record(
        example_id=f"edition2024_migration.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="edition2024_migration",
        difficulty="hard",
        tier=tier,
        instruction=f"Apply the Rust 2024 migration fix for {name}.",
        constraints=["Target Rust edition 2024.", "Keep the API stable where possible.", "Add explicit safety context when required."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["edition2024", name],
        source_name="edition2024_generator_v3",
        note="Synthetic Rust 2024 migration example pending validation.",
    )


def gen_async(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 5)
    crate_name = f"async_fix_{name}"
    cargo = cargo_toml(crate_name, ['tokio = { version = "1", features = ["sync", "rt", "time"] }'])
    variant = idx % 6
    if variant == 0:
        family_id = "async_concurrency_fix.mutex_refresh"
        workspace = (
            "use std::sync::Arc;\nuse tokio::sync::Mutex;\n\n"
            f"pub async fn refresh_{name}(cache: Arc<Mutex<Option<String>>>) -> String {{\n"
            "    let mut guard = cache.lock().await;\n"
            "    if let Some(value) = &*guard {\n        return value.clone();\n    }\n"
            "    let loaded = load_value().await;\n"
            "    *guard = Some(loaded.clone());\n"
            "    loaded\n}\n\nasync fn load_value() -> String {\n    \"loaded\".to_string()\n}\n"
        )
        target = (
            "use std::sync::Arc;\nuse tokio::sync::Mutex;\n\n"
            f"pub async fn refresh_{name}(cache: Arc<Mutex<Option<String>>>) -> String {{\n"
            "    {\n        let guard = cache.lock().await;\n        if let Some(value) = &*guard {\n            return value.clone();\n        }\n    }\n"
            "    let loaded = load_value().await;\n"
            "    let mut guard = cache.lock().await;\n"
            "    if let Some(value) = &*guard {\n        return value.clone();\n    }\n"
            "    *guard = Some(loaded.clone());\n"
            "    loaded\n}\n\nasync fn load_value() -> String {\n    \"loaded\".to_string()\n}\n"
        )
    elif variant == 1:
        family_id = "async_concurrency_fix.channel_collect"
        workspace = (
            "use tokio::sync::mpsc;\n\n"
            f"pub async fn collect_{name}(mut rx: mpsc::Receiver<String>) -> Vec<String> {{\n"
            "    let mut out = Vec::new();\n"
            "    while let Some(item) = rx.recv().await {\n        out.push(item);\n        break;\n    }\n"
            "    out\n}\n"
        )
        target = workspace.replace("        break;\n", "")
    elif variant == 2:
        family_id = "async_concurrency_fix.retry_loop"
        workspace = (
            "use tokio::time::{Duration, sleep};\n\n"
            f"pub async fn retry_{name}(retries: usize) -> usize {{\n"
            "    let mut attempt = 0;\n"
            "    while attempt <= retries {\n        attempt += 1;\n        sleep(Duration::from_millis(1)).await;\n    }\n"
            "    attempt\n}\n"
        )
        target = workspace.replace("<= retries", "< retries")
    elif variant == 3:
        family_id = "async_concurrency_fix.read_write_lock"
        cargo = cargo_toml(crate_name, ['tokio = { version = "1", features = ["sync", "rt"] }'])
        workspace = (
            "use std::sync::Arc;\nuse tokio::sync::RwLock;\n\n"
            f"pub async fn bump_{name}(state: Arc<RwLock<u64>>) -> u64 {{\n"
            "    let read = state.read().await;\n"
            "    let next = *read + 1;\n"
            "    let mut write = state.write().await;\n"
            "    *write = next;\n"
            "    next\n"
            "}\n"
        )
        target = (
            "use std::sync::Arc;\nuse tokio::sync::RwLock;\n\n"
            f"pub async fn bump_{name}(state: Arc<RwLock<u64>>) -> u64 {{\n"
            "    let next = {\n"
            "        let read = state.read().await;\n"
            "        *read + 1\n"
            "    };\n"
            "    let mut write = state.write().await;\n"
            "    *write = next;\n"
            "    next\n"
            "}\n"
        )
    elif variant == 4:
        family_id = "async_concurrency_fix.timeout_default"
        cargo = cargo_toml(crate_name, ['tokio = { version = "1", features = ["time", "rt"] }'])
        workspace = (
            "use tokio::time::{timeout, Duration};\n\n"
            f"pub async fn load_{name}() -> String {{\n"
            "    let result = timeout(Duration::from_millis(1), async {\n"
            "        \"ready\".to_string()\n"
            "    })\n"
            "    .await;\n"
            "    result.unwrap()\n"
            "}\n"
        )
        target = (
            "use tokio::time::{Duration, timeout};\n\n"
            f"pub async fn load_{name}() -> String {{\n"
            "    timeout(Duration::from_millis(1), async { \"ready\".to_string() })\n"
            "        .await\n"
            "        .unwrap_or_default()\n"
            "}\n"
        )
    else:
        family_id = "async_concurrency_fix.watch_shutdown"
        cargo = cargo_toml(crate_name, ['tokio = { version = "1", features = ["sync", "rt"] }'])
        workspace = (
            "use tokio::sync::watch;\n\n"
            f"pub async fn wait_{name}_shutdown(mut rx: watch::Receiver<bool>) -> bool {{\n"
            "    while !*rx.borrow() {\n"
            "        rx.changed().await.unwrap();\n"
            "    }\n"
            "    true\n"
            "}\n"
        )
        target = (
            "use tokio::sync::watch;\n\n"
            f"pub async fn wait_{name}_shutdown(mut rx: watch::Receiver<bool>) -> bool {{\n"
            "    while !*rx.borrow() {\n"
            "        if rx.changed().await.is_err() {\n"
            "            return false;\n"
            "        }\n"
            "    }\n"
            "    true\n"
            "}\n"
        )
    return make_record(
        example_id=f"async_concurrency_fix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="async_concurrency_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Fix the async coordination issue in the {name} helper.",
        constraints=["Keep the public API unchanged.", "Preserve idiomatic async Rust.", "Avoid hidden lock or coordination bugs."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["async", name],
        source_name="async_generator_v3",
        note="Synthetic async example pending validation.",
        hidden_file_count=1,
    )


def gen_unsafe(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 6)
    crate_name = f"unsafe_fix_{name}"
    variant = idx % 5
    if variant == 0:
        family_id = "unsafe_ffi_fix.cstr_from_ptr"
        unsafe_signature = f"pub unsafe fn from_{name}(input: *const c_char) -> Result<String, std::str::Utf8Error> {{"
        if len(unsafe_signature) > 100:
            unsafe_signature = (
                f"pub unsafe fn from_{name}(\n"
                "    input: *const c_char,\n"
                ") -> Result<String, std::str::Utf8Error> {"
            )
        workspace = (
            "use std::ffi::CStr;\nuse std::os::raw::c_char;\n\n"
            f"{unsafe_signature}\n"
            "    let c_str = CStr::from_ptr(input);\n"
            "    Ok(c_str.to_str()?.to_string())\n}\n"
        )
        target = (
            "use std::ffi::CStr;\nuse std::os::raw::c_char;\n\n"
            "/// # Safety\n/// The caller must pass a valid non-null pointer to a NUL-terminated C string.\n"
            f"{unsafe_signature}\n"
            "    let c_str = unsafe { CStr::from_ptr(input) };\n"
            "    Ok(c_str.to_str()?.to_string())\n}\n"
        )
    elif variant == 1:
        family_id = "unsafe_ffi_fix.slice_from_raw_parts"
        workspace = (
            "use std::slice;\n\n"
            f"pub unsafe fn bytes_{name}<'a>(ptr: *const u8, len: usize) -> &'a [u8] {{\n"
            "    slice::from_raw_parts(ptr, len)\n}\n"
        )
        target = (
            "use std::slice;\n\n"
            "/// # Safety\n/// The caller must ensure ptr is valid for reads of len bytes and points to initialized memory.\n"
            f"pub unsafe fn bytes_{name}<'a>(ptr: *const u8, len: usize) -> &'a [u8] {{\n"
            "    unsafe { slice::from_raw_parts(ptr, len) }\n}\n"
        )
    elif variant == 2:
        family_id = "unsafe_ffi_fix.maybeuninit_init"
        workspace = (
            "use std::mem::MaybeUninit;\n\n"
            f"pub fn init_{name}() -> usize {{\n"
            "    let value: MaybeUninit<usize> = MaybeUninit::uninit();\n"
            "    unsafe { value.assume_init() }\n}\n"
        )
        target = (
            "use std::mem::MaybeUninit;\n\n"
            f"pub fn init_{name}() -> usize {{\n"
            "    let value = MaybeUninit::new(0usize);\n"
            "    unsafe { value.assume_init() }\n}\n"
        )
    elif variant == 3:
        family_id = "unsafe_ffi_fix.write_bytes_nonnull"
        workspace = (
            "use std::ptr;\n\n"
            f"pub unsafe fn zero_{name}(ptr: *mut u8, len: usize) {{\n"
            "    ptr::write_bytes(ptr, 0, len);\n"
            "}\n"
        )
        target = (
            "use std::ptr;\n\n"
            "/// # Safety\n/// The caller must pass a valid non-null pointer writable for len bytes.\n"
            f"pub unsafe fn zero_{name}(ptr: *mut u8, len: usize) {{\n"
            "    let ptr = std::ptr::NonNull::new(ptr).expect(\"pointer must be non-null\");\n"
            "    unsafe { ptr::write_bytes(ptr.as_ptr(), 0, len) };\n"
            "}\n"
        )
    else:
        family_id = "unsafe_ffi_fix.transmute_copy_free"
        workspace = (
            "use std::mem;\n\n"
            f"pub fn to_{name}_bytes(value: u32) -> [u8; 4] {{\n"
            "    unsafe { mem::transmute(value) }\n"
            "}\n"
        )
        target = (
            f"pub fn to_{name}_bytes(value: u32) -> [u8; 4] {{\n"
            "    value.to_ne_bytes()\n"
            "}\n"
        )
    return make_record(
        example_id=f"unsafe_ffi_fix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="unsafe_ffi_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Repair the unsafe boundary for {name}.",
        constraints=["Use explicit local unsafe blocks.", "Document safety assumptions where needed.", "Target Rust 2024 behavior."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["unsafe", name],
        source_name="unsafe_generator_v2",
        note="Synthetic unsafe example pending soundness review and validation.",
    )


def gen_clippy(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 7)
    crate_name = f"clippy_fix_{name}"
    variant = idx % 3
    if variant == 0:
        family_id = "clippy_fmt_cleanup.unwrap_or_default"
        workspace = f"pub fn maybe_{name}(input: Option<&str>) -> String {{\n    match input {{\n        Some(value) => value.to_string(),\n        None => String::new(),\n    }}\n}}\n"
        target = f"pub fn maybe_{name}(input: Option<&str>) -> String {{\n    input.unwrap_or_default().to_string()\n}}\n"
    elif variant == 1:
        family_id = "clippy_fmt_cleanup.manual_contains"
        workspace = f"pub fn has_{name}(items: &[String], needle: &str) -> bool {{\n    items.iter().any(|item| item == &needle.to_string())\n}}\n"
        target = f"pub fn has_{name}(items: &[String], needle: &str) -> bool {{\n    items.iter().any(|item| item == needle)\n}}\n"
    else:
        family_id = "clippy_fmt_cleanup.redundant_closure"
        workspace = f"pub fn lengths_{name}(items: &[String]) -> Vec<usize> {{\n    items.iter().map(|item| item.len()).collect()\n}}\n"
        target = f"pub fn lengths_{name}(items: &[String]) -> Vec<usize> {{\n    items.iter().map(String::len).collect()\n}}\n"
    return make_record(
        example_id=f"clippy_fmt_cleanup.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="clippy_fmt_cleanup",
        difficulty="easy",
        tier=tier,
        instruction=f"Clean up the {name} helper into a clippy-clean implementation.",
        constraints=["Preserve semantics.", "Keep the patch minimal.", "Target a clippy-clean result."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["clippy", name],
        source_name="clippy_generator_v2",
        note="Synthetic clippy cleanup example pending validation.",
    )


def gen_macro(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 8)
    crate_name = f"macro_fix_{name}"
    variant = idx % 3
    if variant == 0:
        family_id = "macro_fix.expr_fragment_2021"
        workspace = (
            "#[macro_export]\n"
            f"macro_rules! {name}_map {{\n"
            "    ($($key:expr => $value:expr),* $(,)?) => {{\n"
            "        let mut out = Vec::new();\n"
            "        $(out.push(($key.to_string(), $value));)*\n"
            "        out\n"
            "    }};\n"
            "}\n"
        )
        target = workspace.replace("$($key:expr => $value:expr)", "$($key:expr_2021 => $value:expr)")
    elif variant == 1:
        family_id = "macro_fix.trailing_comma"
        workspace = (
            "#[macro_export]\n"
            f"macro_rules! {name}_vec {{\n"
            "    ($($value:expr),*) => {{\n"
            "        let mut out = Vec::new();\n"
            "        $(out.push($value);)*\n"
            "        out\n"
            "    }};\n"
            "}\n"
        )
        target = workspace.replace("($($value:expr),*)", "($($value:expr),* $(,)?)")
    else:
        family_id = "macro_fix.block_capture"
        workspace = (
            "#[macro_export]\n"
            f"macro_rules! {name}_value {{\n"
            "    ($body:stmt) => {{\n"
            "        $body\n"
            "    }};\n"
            "}\n"
        )
        target = (
            "#[macro_export]\n"
            f"macro_rules! {name}_value {{\n"
            "    ($body:block) => {{ $body }};\n"
            "}\n"
        )
    return make_record(
        example_id=f"macro_fix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="macro_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Update the {name}_map macro for Rust 2024 behavior.",
        constraints=["Keep the macro API stable.", "Target Rust 2024-compatible behavior.", "Prefer a minimal macro patch."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["macro", name],
        source_name="macro_generator_v2",
        note="Synthetic macro example pending validation.",
    )


def gen_api(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 9)
    crate_name = f"api_refactor_{name}"
    variant = idx % 5
    if variant == 0:
        family_id = "api_refactor.panic_to_result"
        workspace = f"pub fn parse_{name}_port(input: &str) -> u16 {{\n    input.parse::<u16>().unwrap()\n}}\n"
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParsePortError {\n    InvalidPort,\n}\n\n"
            f"pub fn parse_{name}_port(input: &str) -> Result<u16, ParsePortError> {{\n"
            "    input\n        .parse::<u16>()\n        .map_err(|_| ParsePortError::InvalidPort)\n}\n"
        )
    elif variant == 1:
        family_id = "api_refactor.builder_pattern"
        builder = title_symbol(name)
        workspace = f"pub struct {builder}Config {{\n    pub limit: usize,\n}}\n\nimpl {builder}Config {{\n    pub fn new(limit: usize) -> Self {{\n        Self {{ limit }}\n    }}\n}}\n"
        target = f"pub struct {builder}Config {{\n    pub limit: usize,\n}}\n\nimpl {builder}Config {{\n    pub fn builder() -> {builder}ConfigBuilder {{\n        {builder}ConfigBuilder {{ limit: None }}\n    }}\n}}\n\npub struct {builder}ConfigBuilder {{\n    limit: Option<usize>,\n}}\n\nimpl {builder}ConfigBuilder {{\n    pub fn limit(mut self, limit: usize) -> Self {{\n        self.limit = Some(limit);\n        self\n    }}\n\n    pub fn build(self) -> {builder}Config {{\n        {builder}Config {{\n            limit: self.limit.unwrap_or(0),\n        }}\n    }}\n}}\n"
    elif variant == 2:
        family_id = "api_refactor.option_lookup"
        workspace = (
            f"pub fn find_{name}(items: &[String], needle: &str) -> String {{\n"
            "    items.iter().find(|item| item.as_str() == needle).unwrap().clone()\n"
            "}\n"
        )
        target = (
            f"pub fn find_{name}(items: &[String], needle: &str) -> Option<String> {{\n"
            "    items.iter().find(|item| item.as_str() == needle).cloned()\n"
            "}\n"
        )
    else:
        family_id = "api_refactor.error_enum"
        workspace = (
            f"pub fn parse_{name}_limit(input: &str) -> Result<usize, String> {{\n"
            "    input.parse::<usize>().map_err(|_| \"bad limit\".to_string())\n"
            "}\n"
        )
        target = (
            "#[derive(Debug, PartialEq, Eq)]\n"
            "pub enum ParseLimitError {\n    InvalidLimit,\n}\n\n"
            f"pub fn parse_{name}_limit(input: &str) -> Result<usize, ParseLimitError> {{\n"
            "    input\n"
            "        .parse::<usize>()\n"
            "        .map_err(|_| ParseLimitError::InvalidLimit)\n"
            "}\n"
        )
    return make_record(
        example_id=f"api_refactor.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="api_refactor",
        difficulty="hard",
        tier=tier,
        instruction=f"Refactor the public Rust API for {name}.",
        constraints=["Improve public API ergonomics.", "Avoid panic-oriented design.", "Target idiomatic Rust."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["api", name],
        source_name="api_generator_v2",
        note="Synthetic API refactor example pending validation.",
    )


def gen_doctest(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 10)
    crate_name = f"doctest_fix_{name}"
    doc_type = pick(DOC_TYPES, idx)
    color = pick(COLORS, idx, 1)
    variant = idx % 3
    if variant == 0:
        family_id = "doctest_doc_fix.crate_qualified_doc_example"
        workspace = f"/// Represents a {doc_type}.\n///\n/// ```rust\n/// use {crate_name}::{doc_type};\n/// let value = {doc_type}::new(\"{color}\");\n/// assert_eq!(value.as_str(), \"todo\");\n/// ```\npub struct {doc_type}(String);\n\nimpl {doc_type} {{\n    pub fn new(value: &str) -> Self {{\n        Self(value.to_string())\n    }}\n\n    pub fn as_str(&self) -> &str {{\n        &self.0\n    }}\n}}\n"
        target = workspace.replace('"todo"', f'"{color}"')
    elif variant == 1:
        family_id = "doctest_doc_fix.mutable_example"
        workspace = f"/// Keeps a mutable {doc_type}.\n///\n/// ```rust\n/// let value = {crate_name}::{doc_type}::new(\"{color}\");\n/// value.set(\"blue\");\n/// assert_eq!(value.as_str(), \"blue\");\n/// ```\npub struct {doc_type}(String);\n\nimpl {doc_type} {{\n    pub fn new(value: &str) -> Self {{\n        Self(value.to_string())\n    }}\n\n    pub fn set(&mut self, value: &str) {{\n        self.0 = value.to_string();\n    }}\n\n    pub fn as_str(&self) -> &str {{\n        &self.0\n    }}\n}}\n"
        target = workspace.replace("let value =", "let mut value =")
    else:
        family_id = "doctest_doc_fix.result_example"
        workspace = f"/// Parses a {doc_type}.\n///\n/// ```rust\n/// let value = {crate_name}::parse(\"7\").unwrap();\n/// assert_eq!(value, 8);\n/// ```\npub fn parse(input: &str) -> Result<u32, std::num::ParseIntError> {{\n    input.parse::<u32>()\n}}\n"
        target = workspace.replace("assert_eq!(value, 8);", "assert_eq!(value, 7);")
    return make_record(
        example_id=f"doctest_doc_fix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="doctest_doc_fix",
        difficulty="medium",
        tier=tier,
        instruction=f"Fix the doctest for {name} so the documented example matches the API.",
        constraints=["Keep the public API unchanged.", "Make the doctest compile and pass.", "Target Rust edition 2024."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["docs", "doctest", name],
        source_name="doctest_generator_v2",
        note="Synthetic doctest example pending validation.",
    )


def gen_workspace(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 11)
    core_name = f"{name}_core"
    app_name = f"{name}_app"
    root_workspace = "[workspace]\nmembers = [\"crates/core\", \"crates/app\"]\nresolver = \"3\"\n"
    variant = idx % 5
    if variant == 0:
        family_id = "cargo_workspace_fix.workspace_dependency_path"
        workspace_files = [
            {"path": "Cargo.toml", "content": root_workspace},
            {"path": "crates/core/Cargo.toml", "content": cargo_toml(core_name)},
            {"path": "crates/core/src/lib.rs", "content": f'pub fn label() -> &' + "'static str" + f' {{\n    "{name}"\n}}\n'},
            {"path": "crates/app/Cargo.toml", "content": f"[package]\nname = \"{app_name}\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n[dependencies]\n{core_name} = {{ path = \"../cor\" }}\n"},
            {"path": "crates/app/src/main.rs", "content": f"fn main() {{\n    println!(\"{{}}\", {core_name}::label());\n}}\n"},
        ]
        target_files = [{"path": "crates/app/Cargo.toml", "content": f"[package]\nname = \"{app_name}\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n[dependencies]\n{core_name} = {{ path = \"../core\" }}\n"}]
    elif variant == 1:
        family_id = "cargo_workspace_fix.workspace_resolver"
        workspace_files = [
            {"path": "Cargo.toml", "content": "[workspace]\nmembers = [\"crates/core\", \"crates/app\"]\n"},
            {"path": "crates/core/Cargo.toml", "content": cargo_toml(core_name)},
            {"path": "crates/core/src/lib.rs", "content": f'pub fn normalize() -> &' + "'static str" + f' {{\n    "{name}"\n}}\n'},
            {"path": "crates/app/Cargo.toml", "content": cargo_toml(app_name, [f'{core_name} = {{ path = "../core" }}'])},
            {"path": "crates/app/src/main.rs", "content": f"fn main() {{\n    println!(\"{{}}\", {core_name}::normalize());\n}}\n"},
        ]
        target_files = [{"path": "Cargo.toml", "content": root_workspace}]
    elif variant == 2:
        family_id = "cargo_workspace_fix.workspace_members"
        workspace_files = [
            {"path": "Cargo.toml", "content": "[workspace]\nmembers = [\"crates/core\"]\nresolver = \"3\"\n"},
            {"path": "crates/core/Cargo.toml", "content": cargo_toml(core_name)},
            {"path": "crates/core/src/lib.rs", "content": f'pub fn label() -> &' + "'static str" + f' {{\n    "{name}"\n}}\n'},
            {"path": "crates/app/Cargo.toml", "content": cargo_toml(app_name, [f'{core_name} = {{ path = "../core" }}'])},
            {"path": "crates/app/src/main.rs", "content": f"fn main() {{\n    println!(\"{{}}\", {core_name}::label());\n}}\n"},
        ]
        target_files = [{"path": "Cargo.toml", "content": root_workspace}]
    elif variant == 3:
        family_id = "cargo_workspace_fix.workspace_inheritance"
        workspace_files = [
            {"path": "Cargo.toml", "content": "[workspace]\nmembers = [\"crates/core\", \"crates/app\"]\nresolver = \"3\"\n\n[workspace.package]\nedition = \"2024\"\n"},
            {"path": "crates/core/Cargo.toml", "content": "[package]\nname = \"" + core_name + "\"\nversion = \"0.1.0\"\n\n"},
            {"path": "crates/core/src/lib.rs", "content": f'pub fn scope() -> &' + "'static str" + f' {{\n    "{name}"\n}}\n'},
            {"path": "crates/app/Cargo.toml", "content": "[package]\nname = \"" + app_name + "\"\nversion = \"0.1.0\"\n\n[dependencies]\n" + core_name + " = { path = \"../core\" }\n"},
            {"path": "crates/app/src/main.rs", "content": f"fn main() {{\n    println!(\"{{}}\", {core_name}::scope());\n}}\n"},
        ]
        target_files = [
            {"path": "crates/core/Cargo.toml", "content": "[package]\nname = \"" + core_name + "\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n"},
            {"path": "crates/app/Cargo.toml", "content": "[package]\nname = \"" + app_name + "\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n[dependencies]\n" + core_name + " = { path = \"../core\" }\n"},
        ]
    else:
        family_id = "cargo_workspace_fix.workspace_feature_flag"
        workspace_files = [
            {"path": "Cargo.toml", "content": root_workspace},
            {"path": "crates/core/Cargo.toml", "content": "[package]\nname = \"" + core_name + "\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n"},
            {"path": "crates/core/src/lib.rs", "content": "#[cfg(feature = \"extra\")]\npub fn feature_label() -> &'static str {\n    \"extra\"\n}\n"},
            {"path": "crates/app/Cargo.toml", "content": "[package]\nname = \"" + app_name + "\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n[dependencies]\n" + core_name + " = { path = \"../core\", features = [\"extra\"] }\n"},
            {"path": "crates/app/src/main.rs", "content": f"fn main() {{\n    println!(\"{{}}\", {core_name}::feature_label());\n}}\n"},
        ]
        target_files = [
            {"path": "crates/core/Cargo.toml", "content": "[package]\nname = \"" + core_name + "\"\nversion = \"0.1.0\"\nedition = \"2024\"\n\n[features]\nextra = []\n"},
        ]
    return make_record(
        example_id=f"cargo_workspace_fix.{name}.{idx + 1:06d}",
        family_id=family_id,
        category="cargo_workspace_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Fix the Cargo/workspace issue for the {name} workspace.",
        constraints=["Keep the workspace layout intact.", "Fix the Cargo issue with a minimal patch.", "Target current stable Cargo behavior."],
        workspace_files=workspace_files,
        target_files=target_files,
        tags=["cargo", "workspace", name],
        source_name="cargo_workspace_generator_v2",
        note="Synthetic Cargo/workspace example pending validation.",
    )


def gen_rust_qa(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 12)
    if idx % 3 == 0:
        prompt = f"Why does borrowing {name} mutably and immutably in the same scope usually fail in Rust?"
        completion = "Rust requires a mutable borrow to be exclusive. The normal fix is to shorten one borrow, clone only the needed data, or reorder the read and write so their lifetimes no longer overlap."
    elif idx % 3 == 1:
        prompt = f"What changed in Rust 2024 around environment mutation for {name} bootstrap code?"
        completion = "Mutating process environment variables became unsafe because concurrent access can cause undefined behavior. The correct Rust 2024 pattern is an explicit unsafe block with a documented single-threaded bootstrap assumption."
    else:
        prompt = f"Why is awaiting while holding a mutex guard risky in async Rust for {name} state?"
        completion = "Holding a lock across an await can increase contention and contribute to deadlocks or starvation. The usual fix is to inspect or copy the needed state, drop the guard, and reacquire only if necessary."
    return make_text_record(
        example_id=f"rust_qa.{name}.{idx + 1:06d}",
        family_id=f"rust_qa.{['borrow_rules', 'env_2024', 'async_locking'][idx % 3]}",
        category="rust_qa",
        difficulty="easy",
        tier=tier,
        prompt=prompt,
        completion=completion,
        tags=["qa", name],
        source_name="rust_qa_generator_v2",
        note="Synthetic Rust QA example intended as a low-weight auxiliary signal.",
    )


def gen_review_preference(idx: int, tier: str) -> dict[str, object]:
    name = symbol(idx, 13)
    prompt = (
        f"Review two Rust API patches for parse_{name}_port.\n\n"
        f"Patch A:\npub fn parse_{name}_port(input: &str) -> u16 {{\n    input.parse().unwrap()\n}}\n\n"
        "Patch B:\n#[derive(Debug, PartialEq, Eq)]\npub enum ParsePortError {\n    InvalidPort,\n}\n\n"
        f"pub fn parse_{name}_port(input: &str) -> Result<u16, ParsePortError> {{\n    input.parse().map_err(|_| ParsePortError::InvalidPort)\n}}\n\n"
        "Choose the better patch and explain why."
    )
    completion = "Patch B is better because it avoids panicking on invalid input and models failure explicitly with Result. That makes the API safer and more idiomatic for public Rust parsing code."
    return make_text_record(
        example_id=f"review_preference.{name}.{idx + 1:06d}",
        family_id="review_preference.parse_port_review",
        category="review_preference",
        difficulty="medium",
        tier=tier,
        prompt=prompt,
        completion=completion,
        tags=["review", "preference", name],
        source_name="review_preference_generator_v2",
        note="Synthetic review-preference example intended as a low-weight auxiliary signal.",
    )


GENERATOR_MAP = {
    "compile_repair": gen_compile_repair,
    "semantic_impl": gen_semantic_impl,
    "test_driven_bugfix": gen_bugfix,
    "edition2024_migration": gen_edition,
    "async_concurrency_fix": gen_async,
    "unsafe_ffi_fix": gen_unsafe,
    "clippy_fmt_cleanup": gen_clippy,
    "macro_fix": gen_macro,
    "api_refactor": gen_api,
    "doctest_doc_fix": gen_doctest,
    "cargo_workspace_fix": gen_workspace,
    "rust_qa": gen_rust_qa,
    "review_preference": gen_review_preference,
}


def build_readme(repo_id: str, counts: dict[str, int], total_rows: int) -> str:
    rows = "\n".join(f"| {name} | {counts.get(name, 0)} |" for name in sorted(counts))
    return f"""---
language:
- en
pretty_name: RustForge Personal Rust Dataset
license: other
task_categories:
- text-generation
tags:
- rust
- code
- synthetic
- instruction
- chatml
- unsloth
- sft
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*.jsonl
---

# RustForge Personal Rust Dataset

Current version: `{DATASET_VERSION}`

Target Hub repo: `{repo_id}`

Source repository:

- [pomazanbohdan/llm-model-rust-test](https://github.com/pomazanbohdan/llm-model-rust-test)

## Scale

- total records: `{total_rows:,}`
- format: ChatML-style `messages`
- storage: sharded JSONL

## Methodology

This dataset is built as a Rust-specific, benchmark-aligned training corpus rather than a generic code dump.

Construction principles:

- Rust edition target is fixed to `2024`
- examples are generated by task family, not only by category count
- the corpus is designed around real failure modes from a Rust evaluation suite
- records are emitted in one unified ChatML-compatible format for direct SFT use

The dataset generation workflow in the repository follows these stages:

1. Define a Rust task mix across compile repair, semantic implementation, bugfix, edition migration, async, unsafe, macros, API refactor, doctest, and Cargo/workspace tasks.
2. Generate sharded dataset rows from editable batch manifests under `hf-source/`.
3. Assign each generated row to an explicit `family_id` so quality can be tracked per template family.
4. Run normalized deduplication to measure semantic repetition.
5. Run tiered validation:
   - `cheap`: `cargo check` + `cargo fmt --check`
   - `medium`: adds `cargo clippy -- -D warnings` and `cargo test --no-run`
   - `full`: adds `cargo doc --no-deps` and `cargo test --doc`
6. Run family-first cascade and parallel depth validation to expand verified coverage without exhaustively validating every row.
7. Build smaller, higher-confidence priority subsets for lower-cost fine-tuning workflows.

## Design Goal

The goal is to train Rust-specialized coding models that perform well on:

- compile correctness
- semantic correctness
- Rust 2024 migration behavior
- async and concurrency patterns
- unsafe and FFI boundaries
- macro updates
- API refactoring
- doctest and Cargo workspace maintenance

## Intended Uses

Recommended uses:

- supervised fine-tuning of Rust-oriented coding models
- continued domain adaptation of general coding models toward Rust 2024
- curriculum construction for repair, migration, and maintenance-style Rust tasks
- building smaller high-confidence subsets for lower-cost training

This dataset is especially suited for models that should edit or generate Rust code in a crate or workspace context rather than only answer general programming questions.

## Limitations

- the current release is predominantly synthetic, although it is benchmark-aligned
- not every row in the 50k corpus is fully execution-validated
- some quality signals are tracked at the template-family level rather than by exhaustively validating every row
- the dataset is optimized for modern Rust application and library workflows, not for every possible Rust domain such as embedded, `no_std`, kernel, or GPU-specific development

For stricter training mixes, use the repository tooling to build validated or priority subsets on top of the canonical corpus.

## Quality Snapshot

Current quality work recorded in the repository includes:

- family-based generation with explicit `family_id`
- normalized semantic deduplication
- tiered validation across `cheap`, `medium`, and `full` execution gates
- family-level cascade validation across all expanded core families
- parallel family-depth validation to grow verified coverage efficiently
- optimized priority-train builders for lower-cost fine-tuning

Reference reports:

- [2026-03-25 HF dataset QC](https://github.com/pomazanbohdan/llm-model-rust-test/blob/main/reports/2026-03-25-hf-dataset-qc.md)
- [2026-03-25 Rust gap analysis](https://github.com/pomazanbohdan/llm-model-rust-test/blob/main/reports/2026-03-25-rust-gap-analysis.md)
- [2026-03-25 Parallel improvement program](https://github.com/pomazanbohdan/llm-model-rust-test/blob/main/reports/2026-03-25-parallel-improvement-program.md)

## Category mix

| Category | Count |
| --- | ---: |
{rows}

## Unsloth compatibility

Use `messages` as the conversation field. If a UI asks for pairwise mapping, use `prompt` and `completion`.

## Loading in Unsloth

This dataset is structured to work with ChatML-style training flows.

Typical loading path:

1. Load the dataset from Hugging Face.
2. Use the `messages` column as the chat conversation field.
3. Keep `prompt` and `completion` only as convenience columns for inspection or alternative trainers.

Example with `datasets`:

```python
from datasets import load_dataset

dataset = load_dataset(
    "pomazanbohdan/rustforge-personal-rust-dataset",
    split="train",
)

print(dataset.column_names)
print(dataset[0]["messages"])
```

If your Unsloth or trainer UI expects an instruction-response mapping instead of chat messages, use:

- input: `prompt`
- output: `completion`

## Repository Layout

The canonical implementation lives in:

- [repository root](https://github.com/pomazanbohdan/llm-model-rust-test)
- [`hf-source/`](https://github.com/pomazanbohdan/llm-model-rust-test/tree/main/hf-source)
- [`scripts/`](https://github.com/pomazanbohdan/llm-model-rust-test/tree/main/scripts)
- [`reports/`](https://github.com/pomazanbohdan/llm-model-rust-test/tree/main/reports)
"""


def write_manifest(output_dir: Path, repo_id: str, counts: dict[str, int], total_rows: int, shard_count: int) -> None:
    manifest = {
        "dataset_name": "RustForge Personal Rust Dataset",
        "dataset_version": DATASET_VERSION,
        "dataset_repo_id": repo_id,
        "train_rows": total_rows,
        "record_format": "chatml_messages",
        "unsloth_compatible": True,
        "shard_size": SHARD_SIZE,
        "shard_count": shard_count,
        "category_counts": counts,
        "notes": "HF-first synthetic Rust corpus generated from batch manifests with expanded diversity and workspace coverage.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the HF-first RustForge dataset.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / args.output_dir
    source_dir = repo_root / args.source_dir
    data_dir = output_dir / "data"

    if output_dir.exists():
        shutil.rmtree(data_dir, ignore_errors=True)
        for removable in ("README.md", "manifest.json"):
            path = output_dir / removable
            if path.exists():
                path.unlink()
    data_dir.mkdir(parents=True, exist_ok=True)

    specs = load_batch_specs(source_dir)
    counts: Counter[str] = Counter()
    total_rows = 0
    shard_index = 0
    rows_in_shard = 0
    writer = None

    try:
        for spec in specs:
            category = str(spec["category"])
            generator = GENERATOR_MAP[str(spec["generator"])]
            count = int(spec["count"])
            tier = str(spec["tier"])
            for idx in range(count):
                if writer is None or rows_in_shard >= SHARD_SIZE:
                    if writer is not None:
                        writer.close()
                    writer = (data_dir / f"train-{shard_index:05d}-of-00010.jsonl").open("w", encoding="utf-8", newline="\n")
                    shard_index += 1
                    rows_in_shard = 0
                record = generator(idx, tier)
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                counts[category] += 1
                total_rows += 1
                rows_in_shard += 1
    finally:
        if writer is not None:
            writer.close()

    (output_dir / "README.md").write_text(build_readme(args.repo_id, dict(counts), total_rows), encoding="utf-8")
    write_manifest(output_dir, args.repo_id, dict(counts), total_rows, shard_index)
    print(f"Generated {total_rows} rows in {shard_index} shards under {output_dir}")


if __name__ == "__main__":
    main()
