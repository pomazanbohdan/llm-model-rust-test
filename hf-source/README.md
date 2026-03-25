# HF Source Layer

This directory is the editable source layer for the Hugging Face dataset build.

Rules:

1. Keep source planning and batch definitions here.
2. Generate the final publishable dataset into `hf-dataset/`.
3. Do not hand-edit the final `train-*.jsonl` shards.
4. Adjust category counts and generation policy in the batch manifests, then rebuild.

Current layout:

- `batches/core-mix.json`
- `batches/aux-mix.json`

The generated Hugging Face artifact remains a single unified dataset, but its editable source stays split into small maintainable files.

Validation and curation outputs live separately under:

- `hf-dataset/reports/dedup/`
- `hf-dataset/reports/validation/`
- `hf-dataset-verified/`
