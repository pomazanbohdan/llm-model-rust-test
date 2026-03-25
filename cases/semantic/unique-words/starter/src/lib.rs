/// Return distinct lowercase words in first-seen order.
///
/// # Examples
///
/// ```
/// use semantic_unique_words::unique_words;
///
/// assert_eq!(
///     unique_words("Rust rust async RUST"),
///     vec!["rust".to_string(), "async".to_string()]
/// );
/// ```
pub fn unique_words(input: &str) -> Vec<String> {
    todo!("Implement with stable first-seen ordering")
}

