# Compile Layer: repair-push-slug

Fix the crate with the smallest reasonable change.

Requirements:

- keep the public API unchanged
- preserve the current behavior
- avoid cloning the entire vector
- keep the result Clippy-clean

