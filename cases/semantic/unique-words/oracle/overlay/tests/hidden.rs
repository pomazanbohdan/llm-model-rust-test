use semantic_unique_words::unique_words;

#[test]
fn preserves_first_seen_order() {
    assert_eq!(
        unique_words("Borrow checker borrow traits checker"),
        vec![
            "borrow".to_string(),
            "checker".to_string(),
            "traits".to_string(),
        ]
    );
}

#[test]
fn lowercases_and_splits_on_whitespace() {
    assert_eq!(
        unique_words("  Tokio\tasync\nTOKIO "),
        vec!["tokio".to_string(), "async".to_string()]
    );
}

#[test]
fn handles_empty_input() {
    let words: Vec<String> = Vec::new();
    assert_eq!(unique_words(""), words);
}

