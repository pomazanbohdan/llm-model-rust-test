from __future__ import annotations


def row_index_from_id(example_id: str) -> int:
    try:
        return max(0, int(str(example_id).split(".")[-1]) - 1)
    except (ValueError, IndexError):
        return 0


def derive_family_id(record: dict[str, object]) -> str:
    explicit = record.get("family_id")
    if explicit:
        return str(explicit)

    category = str(record.get("category", "unknown"))
    idx = row_index_from_id(str(record.get("id", "")))

    if category == "compile_repair":
        return f"{category}.{'push_first_clone' if idx % 2 == 0 else 'normalize_owned'}"
    if category == "semantic_impl":
        return f"{category}.{['directive_parser', 'endpoint_parser', 'csv_parser', 'pairs_map'][idx % 4]}"
    if category == "test_driven_bugfix":
        return f"{category}.{'normalize_path' if idx % 2 == 0 else 'moving_average'}"
    if category == "edition2024_migration":
        return f"{category}.{['unsafe_env', 'unsafe_extern', 'unsafe_attribute'][idx % 3]}"
    if category == "async_concurrency_fix":
        return f"{category}.{['mutex_refresh', 'channel_collect', 'retry_loop'][idx % 3]}"
    if category == "unsafe_ffi_fix":
        return f"{category}.{['cstr_from_ptr', 'slice_from_raw_parts', 'maybeuninit_init'][idx % 3]}"
    if category == "clippy_fmt_cleanup":
        return f"{category}.unwrap_or_default"
    if category == "macro_fix":
        return f"{category}.expr_fragment_2021"
    if category == "api_refactor":
        return f"{category}.{'panic_to_result' if idx % 2 == 0 else 'builder_pattern'}"
    if category == "doctest_doc_fix":
        return f"{category}.crate_qualified_doc_example"
    if category == "cargo_workspace_fix":
        return f"{category}.{'workspace_dependency_path' if idx % 2 == 0 else 'workspace_resolver'}"
    if category == "rust_qa":
        return f"{category}.{['borrow_rules', 'env_2024', 'async_locking'][idx % 3]}"
    if category == "review_preference":
        return f"{category}.parse_port_review"
    return f"{category}.default"
