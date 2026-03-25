from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path


DEFAULT_REPO_ID = "pomazanbohdan/rustforge-personal-rust-dataset"
DEFAULT_OUTPUT_DIR = "hf-dataset"
DEFAULT_SOURCE_DIR = "hf-source/batches"
DATASET_VERSION = "0.3.0"
SHARD_SIZE = 5000

NOUNS = [
    "header", "token", "cache", "endpoint", "session", "config", "packet", "job",
    "window", "channel", "frame", "route", "buffer", "cookie", "tenant", "cluster",
    "bucket", "digest", "metric", "signal",
]
QUALIFIERS = ["primary", "backup", "local", "remote", "stable", "fast", "strict", "compact", "shared", "edge"]
DIRECTIVES = ["max-age", "retry", "limit", "burst", "ttl", "window"]
DOC_TYPES = ["UserId", "TenantId", "MetricName", "RouteKey", "HeaderValue"]
COLORS = ["red", "green", "blue", "amber", "cyan", "gray"]


def pick(values: list[str], idx: int, offset: int = 0) -> str:
    return values[(idx + offset) % len(values)]


def cargo_toml(crate_name: str, deps: list[str] | None = None) -> str:
    lines = [
        "[package]",
        f'name = "{crate_name}"',
        'version = "0.1.0"',
        'edition = "2024"',
        "",
    ]
    if deps:
        lines.append("[dependencies]")
        lines.extend(deps)
        lines.append("")
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
        out.append(f"File: {file['path']}")
        out.append(f"```{fence_lang(file['path'])}")
        out.append(file["content"].rstrip())
        out.append("```")
        out.append("")
    return "\n".join(out).rstrip()


def render_file_blocks(files: list[dict[str, str]]) -> str:
    out: list[str] = []
    for file in files:
        out.append(f'<file path="{file["path"]}">')
        out.append(file["content"].rstrip())
        out.append("</file>")
        out.append("")
    return "\n".join(out).rstrip()


def build_validation(note: str) -> dict[str, object]:
    return {
        "check": False,
        "clippy": False,
        "test": False,
        "fmt": False,
        "doc": False,
        "doctest": False,
        "notes": note,
    }


def make_code_record(
    *,
    example_id: str,
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
    prompt = "\n".join(
        [
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
        ]
    )
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
        "validation": build_validation(note),
        "tags": tags,
    }


def make_text_record(
    *,
    example_id: str,
    category: str,
    difficulty: str,
    tier: str,
    user_prompt: str,
    assistant_text: str,
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
        "category": category,
        "difficulty": difficulty,
        "edition": "2024",
        "tier": tier,
        "source_type": "synthetic_program_generator",
        "source_name": source_name,
        "source_license_status": "internal_synthetic",
        "source_leakage_risk": "low",
        "prompt": user_prompt,
        "completion": assistant_text,
        "system": system,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_text},
        ],
        "workspace_files": [],
        "target_files": [],
        "hidden_file_count": 0,
        "validation": build_validation(note),
        "tags": tags,
    }


def load_batch_specs(source_dir: Path) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for path in sorted(source_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        specs.extend(data["categories"])
    return specs


def generate_compile_repair(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    fallback = f"{pick(QUALIFIERS, idx)}-{noun}"
    crate_name = f"compile_repair_{noun}_{idx:05d}"
    workspace = (
        f"pub fn push_first_{noun}_key(keys: &mut Vec<String>) {{\n"
        f"    let first = keys.first().unwrap_or(&String::from(\"{fallback}\"));\n"
        "    keys.push(first.to_ascii_lowercase());\n"
        "}\n"
    )
    target = (
        f"pub fn push_first_{noun}_key(keys: &mut Vec<String>) {{\n"
        "    let first = keys\n"
        "        .first()\n"
        "        .cloned()\n"
        f"        .unwrap_or_else(|| \"{fallback}\".to_string());\n"
        "    keys.push(first.to_ascii_lowercase());\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"compile_repair.{noun}.{idx + 1:06d}",
        category="compile_repair",
        difficulty="easy",
        tier=tier,
        instruction=f"Fix the borrow-checker issue in push_first_{noun}_key with the smallest correct patch.",
        constraints=["Keep the public API unchanged.", "Target Rust edition 2024.", "Prefer a minimal compile fix."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["borrow-checker", "minimal-patch", noun],
        source_name="compile_repair_generator_v1",
        note="Synthetic compile-repair example pending validation.",
    )


def generate_semantic_impl(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    directive = pick(DIRECTIVES, idx)
    crate_name = f"semantic_impl_{noun}_{idx:05d}"
    workspace = (
        "#[derive(Debug, PartialEq, Eq)]\n"
        "pub enum ParseError {\n"
        "    InvalidDirective,\n"
        "    InvalidNumber,\n"
        "}\n\n"
        f"pub fn parse_{noun}_{directive.replace('-', '_')}(input: &str) -> Result<u64, ParseError> {{\n"
        "    todo!()\n"
        "}\n"
    )
    target = (
        "#[derive(Debug, PartialEq, Eq)]\n"
        "pub enum ParseError {\n"
        "    InvalidDirective,\n"
        "    InvalidNumber,\n"
        "}\n\n"
        f"pub fn parse_{noun}_{directive.replace('-', '_')}(input: &str) -> Result<u64, ParseError> {{\n"
        "    let trimmed = input.trim();\n"
        "    let (name, value) = trimmed.split_once('=').ok_or(ParseError::InvalidDirective)?;\n"
        f"    if name.trim() != \"{directive}\" {{\n"
        "        return Err(ParseError::InvalidDirective);\n"
        "    }\n"
        "    value.trim().parse::<u64>().map_err(|_| ParseError::InvalidNumber)\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"semantic_impl.{noun}.{idx + 1:06d}",
        category="semantic_impl",
        difficulty="medium",
        tier=tier,
        instruction=f"Implement the parser for a {directive}=<number> directive.",
        constraints=["Keep the public API unchanged.", "Trim surrounding whitespace.", "Reject malformed inputs."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["semantic", "parser", directive, noun],
        source_name="semantic_impl_generator_v1",
        note="Synthetic semantic implementation example pending validation.",
        hidden_file_count=1,
    )


def generate_bugfix(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"bugfix_{noun}_{idx:05d}"
    workspace = (
        f"pub fn normalize_{noun}_path(path: &str) -> String {{\n"
        "    path.replace(\"//\", \"/\").trim_end_matches('/').to_string()\n"
        "}\n"
    )
    target = (
        f"pub fn normalize_{noun}_path(path: &str) -> String {{\n"
        "    let mut normalized = path.replace(\"//\", \"/\");\n"
        "    if normalized.len() > 1 {\n"
        "        normalized = normalized.trim_end_matches('/').to_string();\n"
        "    }\n"
        "    normalized\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"test_driven_bugfix.{noun}.{idx + 1:06d}",
        category="test_driven_bugfix",
        difficulty="medium",
        tier=tier,
        instruction=f"Fix normalize_{noun}_path so it does not collapse the root path into an empty string.",
        constraints=["Keep the public API unchanged.", "Prefer the smallest correct patch.", "Preserve the other normalization behavior."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["bugfix", "paths", noun],
        source_name="bugfix_generator_v1",
        note="Synthetic bugfix example pending fail-to-pass validation.",
        hidden_file_count=1,
    )


def generate_edition(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"edition2024_{noun}_{idx:05d}"
    workspace = (
        "pub fn bootstrap_env(value: &str) {\n"
        f"    std::env::set_var(\"APP_{noun.upper()}\", value);\n"
        "}\n"
    )
    target = (
        "pub fn bootstrap_env(value: &str) {\n"
        "    // SAFETY: This helper is intended to run during single-threaded process bootstrap.\n"
        "    unsafe {\n"
        f"        std::env::set_var(\"APP_{noun.upper()}\", value);\n"
        "    }\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"edition2024_migration.{noun}.{idx + 1:06d}",
        category="edition2024_migration",
        difficulty="hard",
        tier=tier,
        instruction="Migrate the helper to Rust 2024 environment mutation rules.",
        constraints=["Target Rust edition 2024.", "Keep the API stable.", "Add the required safety context."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["edition2024", "env", noun],
        source_name="edition2024_generator_v1",
        note="Synthetic Rust 2024 migration example pending toolchain validation.",
    )


def generate_async(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"async_fix_{noun}_{idx:05d}"
    cargo = cargo_toml(crate_name, ['tokio = { version = "1", features = ["sync", "rt", "time"] }'])
    workspace = (
        "use std::sync::Arc;\n"
        "use tokio::sync::Mutex;\n\n"
        f"pub async fn refresh_{noun}(cache: Arc<Mutex<Option<String>>>) -> String {{\n"
        "    let mut guard = cache.lock().await;\n"
        "    if let Some(value) = &*guard {\n"
        "        return value.clone();\n"
        "    }\n"
        "    let loaded = load_value().await;\n"
        "    *guard = Some(loaded.clone());\n"
        "    loaded\n"
        "}\n\n"
        "async fn load_value() -> String {\n"
        '    "loaded".to_string()\n'
        "}\n"
    )
    target = (
        "use std::sync::Arc;\n"
        "use tokio::sync::Mutex;\n\n"
        f"pub async fn refresh_{noun}(cache: Arc<Mutex<Option<String>>>) -> String {{\n"
        "    {\n"
        "        let guard = cache.lock().await;\n"
        "        if let Some(value) = &*guard {\n"
        "            return value.clone();\n"
        "        }\n"
        "    }\n\n"
        "    let loaded = load_value().await;\n"
        "    let mut guard = cache.lock().await;\n"
        "    if let Some(value) = &*guard {\n"
        "        return value.clone();\n"
        "    }\n"
        "    *guard = Some(loaded.clone());\n"
        "    loaded\n"
        "}\n\n"
        "async fn load_value() -> String {\n"
        '    "loaded".to_string()\n'
        "}\n"
    )
    return make_code_record(
        example_id=f"async_concurrency_fix.{noun}.{idx + 1:06d}",
        category="async_concurrency_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Fix refresh_{noun} so it does not await while holding a mutex guard.",
        constraints=["Keep the public API unchanged.", "Preserve caching behavior.", "Avoid lock-scope bugs."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["async", "mutex", "await-scope", noun],
        source_name="async_generator_v1",
        note="Synthetic async example pending runtime validation.",
        hidden_file_count=1,
    )


def generate_unsafe(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"unsafe_fix_{noun}_{idx:05d}"
    workspace = (
        "use std::ffi::CStr;\n"
        "use std::os::raw::c_char;\n\n"
        f"pub fn from_{noun}_name(name: *const c_char) -> Result<String, std::str::Utf8Error> {{\n"
        "    let c_str = unsafe { CStr::from_ptr(name) };\n"
        "    Ok(c_str.to_str()?.to_string())\n"
        "}\n"
    )
    target = (
        "use std::ffi::CStr;\n"
        "use std::os::raw::c_char;\n\n"
        f"pub fn from_{noun}_name(name: *const c_char) -> Result<String, std::str::Utf8Error> {{\n"
        "    // SAFETY: The caller must provide a valid non-null pointer to a NUL-terminated C string.\n"
        "    // The function reads the string but does not take ownership of the allocation.\n"
        "    let c_str = unsafe { CStr::from_ptr(name) };\n"
        "    Ok(c_str.to_str()?.to_string())\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"unsafe_ffi_fix.{noun}.{idx + 1:06d}",
        category="unsafe_ffi_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Repair the FFI helper for {noun} names and document the safety boundary.",
        constraints=["Keep the public API unchanged.", "Use a local unsafe block.", "Document the safety assumptions."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["unsafe", "ffi", "cstr", noun],
        source_name="unsafe_generator_v1",
        note="Synthetic unsafe/FFI example pending soundness review and validation.",
    )


def generate_clippy(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"clippy_fix_{noun}_{idx:05d}"
    workspace = (
        f"pub fn maybe_{noun}_name(input: Option<&str>) -> String {{\n"
        "    match input {\n"
        "        Some(value) => value.to_string(),\n"
        "        None => String::new(),\n"
        "    }\n"
        "}\n"
    )
    target = (
        f"pub fn maybe_{noun}_name(input: Option<&str>) -> String {{\n"
        "    input.unwrap_or_default().to_string()\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"clippy_fmt_cleanup.{noun}.{idx + 1:06d}",
        category="clippy_fmt_cleanup",
        difficulty="easy",
        tier=tier,
        instruction=f"Clean up maybe_{noun}_name into a clippy-clean idiomatic implementation.",
        constraints=["Preserve semantics.", "Keep the patch minimal.", "Target a clippy-clean result."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["clippy", "style", noun],
        source_name="clippy_generator_v1",
        note="Synthetic clippy cleanup example pending validation.",
    )


def generate_macro(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"macro_fix_{noun}_{idx:05d}"
    workspace = (
        "#[macro_export]\n"
        f"macro_rules! {noun}_map {{\n"
        "    ($($key:expr => $value:expr),* $(,)?) => {{\n"
        "        let mut out = Vec::new();\n"
        "        $(out.push(($key.to_string(), $value));)*\n"
        "        out\n"
        "    }};\n"
        "}\n"
    )
    target = (
        "#[macro_export]\n"
        f"macro_rules! {noun}_map {{\n"
        "    ($($key:expr_2021 => $value:expr),* $(,)?) => {{\n"
        "        let mut out = Vec::new();\n"
        "        $(out.push(($key.to_string(), $value));)*\n"
        "        out\n"
        "    }};\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"macro_fix.{noun}.{idx + 1:06d}",
        category="macro_fix",
        difficulty="hard",
        tier=tier,
        instruction=f"Update the {noun}_map macro for Rust 2024 fragment behavior.",
        constraints=["Keep the macro API stable.", "Target Rust 2024-compatible behavior.", "Prefer a minimal macro patch."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["macro", "expr_2021", noun],
        source_name="macro_generator_v1",
        note="Synthetic macro example pending compile validation.",
    )


def generate_api(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    crate_name = f"api_refactor_{noun}_{idx:05d}"
    workspace = (
        f"pub fn parse_{noun}_port(input: &str) -> u16 {{\n"
        "    input.parse::<u16>().unwrap()\n"
        "}\n"
    )
    target = (
        "#[derive(Debug, PartialEq, Eq)]\n"
        "pub enum ParsePortError {\n"
        "    InvalidPort,\n"
        "}\n\n"
        f"pub fn parse_{noun}_port(input: &str) -> Result<u16, ParsePortError> {{\n"
        "    input.parse::<u16>().map_err(|_| ParsePortError::InvalidPort)\n"
        "}\n"
    )
    return make_code_record(
        example_id=f"api_refactor.{noun}.{idx + 1:06d}",
        category="api_refactor",
        difficulty="hard",
        tier=tier,
        instruction=f"Refactor parse_{noun}_port into a panic-free Rust API.",
        constraints=["Improve API ergonomics.", "Avoid panic-oriented design.", "Target idiomatic Rust."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["api", "result", noun],
        source_name="api_generator_v1",
        note="Synthetic API refactor example pending validation.",
    )


def generate_doctest(idx: int, tier: str) -> dict[str, object]:
    doc_type = pick(DOC_TYPES, idx)
    color = pick(COLORS, idx)
    crate_name = f"doctest_fix_{doc_type.lower()}_{idx:05d}"
    workspace = (
        f"/// Represents a {doc_type}.\n"
        "///\n"
        "/// ```rust\n"
        f"/// let value = {doc_type}::new(\"{color}\");\n"
        "/// assert_eq!(value.as_str(), \"todo\");\n"
        "/// ```\n"
        f"pub struct {doc_type}(String);\n\n"
        f"impl {doc_type} {{\n"
        "    pub fn new(value: &str) -> Self {\n"
        "        Self(value.to_string())\n"
        "    }\n\n"
        "    pub fn as_str(&self) -> &str {\n"
        "        &self.0\n"
        "    }\n"
        "}\n"
    )
    target = workspace.replace('"todo"', f'"{color}"')
    return make_code_record(
        example_id=f"doctest_doc_fix.{doc_type.lower()}.{idx + 1:06d}",
        category="doctest_doc_fix",
        difficulty="medium",
        tier=tier,
        instruction=f"Fix the doctest so the example for {doc_type} matches the real API.",
        constraints=["Keep the public API unchanged.", "Make the doctest compile and pass.", "Target Rust edition 2024."],
        workspace_files=[{"path": "Cargo.toml", "content": cargo_toml(crate_name)}, {"path": "src/lib.rs", "content": workspace}],
        target_files=[{"path": "src/lib.rs", "content": target}],
        tags=["docs", "doctest", doc_type.lower()],
        source_name="doctest_generator_v1",
        note="Synthetic doctest repair example pending rustdoc validation.",
    )


def generate_rust_qa(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    variant = idx % 3
    if variant == 0:
        prompt = f"Why does borrowing {noun} mutably and immutably in the same scope usually fail in Rust?"
        answer = "Rust requires a mutable borrow to be exclusive. The usual fix is to shorten one borrow, clone only the needed data, or restructure the code so the read happens before the write."
        tags = ["qa", "borrowing", noun]
    elif variant == 1:
        prompt = f"What changed in Rust 2024 around environment mutation for {noun} setup code?"
        answer = "Mutating process environment variables is unsafe in Rust 2024 because concurrent access can cause undefined behavior. The migration pattern is an explicit unsafe block with a documented single-threaded bootstrap assumption."
        tags = ["qa", "edition2024", "env", noun]
    else:
        prompt = f"Why is awaiting while holding a mutex guard risky in async Rust for {noun} state?"
        answer = "It increases contention and can contribute to deadlocks or unnecessary blocking. The normal fix is to inspect or copy the needed state, drop the guard, await, and then reacquire the lock only if necessary."
        tags = ["qa", "async", "locks", noun]
    return make_text_record(
        example_id=f"rust_qa.{noun}.{idx + 1:06d}",
        category="rust_qa",
        difficulty="easy",
        tier=tier,
        user_prompt=prompt,
        assistant_text=answer,
        tags=tags,
        source_name="rust_qa_generator_v1",
        note="Synthetic Rust QA example intended as a low-weight auxiliary signal.",
    )


def generate_review_preference(idx: int, tier: str) -> dict[str, object]:
    noun = pick(NOUNS, idx)
    prompt = (
        f"Review two Rust API patches for parse_{noun}_port.\n\n"
        f"Patch A:\npub fn parse_{noun}_port(input: &str) -> u16 {{\n    input.parse().unwrap()\n}}\n\n"
        "Patch B:\n#[derive(Debug, PartialEq, Eq)]\npub enum ParsePortError {\n    InvalidPort,\n}\n\n"
        f"pub fn parse_{noun}_port(input: &str) -> Result<u16, ParsePortError> {{\n    input.parse().map_err(|_| ParsePortError::InvalidPort)\n}}\n\n"
        "Choose the better patch and explain why."
    )
    answer = "Patch B is better because it avoids panicking on invalid input and models failure explicitly with Result, which is the more idiomatic and composable Rust API design."
    return make_text_record(
        example_id=f"review_preference.{noun}.{idx + 1:06d}",
        category="review_preference",
        difficulty="medium",
        tier=tier,
        user_prompt=prompt,
        assistant_text=answer,
        tags=["review", "preference", "api", noun],
        source_name="review_preference_generator_v1",
        note="Synthetic review-preference example intended as a low-weight auxiliary signal.",
    )


GENERATOR_MAP = {
    "compile_repair": generate_compile_repair,
    "semantic_impl": generate_semantic_impl,
    "test_driven_bugfix": generate_bugfix,
    "edition2024_migration": generate_edition,
    "async_concurrency_fix": generate_async,
    "unsafe_ffi_fix": generate_unsafe,
    "clippy_fmt_cleanup": generate_clippy,
    "macro_fix": generate_macro,
    "api_refactor": generate_api,
    "doctest_doc_fix": generate_doctest,
    "rust_qa": generate_rust_qa,
    "review_preference": generate_review_preference,
}


def build_readme(repo_id: str, counts: dict[str, int]) -> str:
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

This is a single unified Rust SFT dataset published for Hugging Face and Unsloth workflows.

Current version: `{DATASET_VERSION}`

Target Hub repo: `{repo_id}`

## Scale

- total records: `50,000`
- format: ChatML-style `messages`
- storage: sharded JSONL

## Category mix

| Category | Count |
| --- | ---: |
| compile_repair | {counts.get("compile_repair", 0)} |
| semantic_impl | {counts.get("semantic_impl", 0)} |
| test_driven_bugfix | {counts.get("test_driven_bugfix", 0)} |
| edition2024_migration | {counts.get("edition2024_migration", 0)} |
| async_concurrency_fix | {counts.get("async_concurrency_fix", 0)} |
| unsafe_ffi_fix | {counts.get("unsafe_ffi_fix", 0)} |
| clippy_fmt_cleanup | {counts.get("clippy_fmt_cleanup", 0)} |
| macro_fix | {counts.get("macro_fix", 0)} |
| api_refactor | {counts.get("api_refactor", 0)} |
| doctest_doc_fix | {counts.get("doctest_doc_fix", 0)} |
| rust_qa | {counts.get("rust_qa", 0)} |
| review_preference | {counts.get("review_preference", 0)} |

## Unsloth compatibility

Use `messages` as the conversation field. If a UI asks for manual pairwise mapping, use:

- `prompt` as the user field
- `completion` as the assistant field

```python
from datasets import load_dataset
from unsloth.chat_templates import get_chat_template

dataset = load_dataset("{repo_id}", split="train")
tokenizer = get_chat_template(tokenizer, chat_template="chatml")

def formatting_prompts_func(examples):
    texts = [
        tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        for messages in examples["messages"]
    ]
    return {{"text": texts}}

dataset = dataset.map(formatting_prompts_func, batched=True)
```

## Important note

This 50k release is a synthetic HF-first Rust corpus aligned to the benchmark plan.
Rows remain marked as synthetic candidates until they are execution-validated and promoted into a verified subset.
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
        "notes": "50k synthetic HF-first corpus generated from source batch manifests.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the HF-first 50k RustForge dataset.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    output_dir = repo_root / args.output_dir
    data_dir = output_dir / "data"
    source_dir = repo_root / args.source_dir

    if output_dir.exists():
        shutil.rmtree(output_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    specs = load_batch_specs(source_dir)
    counts: Counter[str] = Counter()
    total_rows = 0
    rows_in_shard = 0
    shard_index = -1
    shard_count = 0
    writer = None

    try:
        for spec in specs:
            category = str(spec["category"])
            generator = GENERATOR_MAP[str(spec["generator"])]
            tier = str(spec["tier"])
            count = int(spec["count"])
            for idx in range(count):
                if writer is None or rows_in_shard >= SHARD_SIZE:
                    if writer is not None:
                        writer.close()
                    shard_index += 1
                    shard_count += 1
                    rows_in_shard = 0
                    shard_path = data_dir / f"train-{shard_index:05d}-of-00010.jsonl"
                    writer = shard_path.open("w", encoding="utf-8", newline="\n")

                record = generator(idx, tier)
                writer.write(json.dumps(record, ensure_ascii=False) + "\n")
                rows_in_shard += 1
                total_rows += 1
                counts[category] += 1
    finally:
        if writer is not None:
            writer.close()

    (output_dir / "README.md").write_text(build_readme(args.repo_id, dict(counts)), encoding="utf-8")
    write_manifest(output_dir, args.repo_id, dict(counts), total_rows, shard_count)
    print(f"Generated {total_rows} rows in {shard_count} shards under {output_dir}")


if __name__ == "__main__":
    main()
