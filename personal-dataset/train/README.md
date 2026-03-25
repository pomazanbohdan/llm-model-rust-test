# Train Split

This directory is divided into two logical states:

- `seed/`: generated draft candidates
- accepted core examples: to be added only after execution validation

## Promotion rule

An example from `seed/` may be promoted into the accepted train split only after:

1. metadata review
2. provenance review
3. split overlap review
4. execution validation
5. rustfmt normalization

Until then, generated examples remain drafts and must not be treated as production training data.

