pub fn push_first_slug(tags: &mut Vec<String>) {
    let first = tags.first().unwrap_or(&String::from("default"));
    tags.push(first.to_lowercase());
}
