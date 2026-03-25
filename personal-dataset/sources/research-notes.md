# Research Notes

These sources are the initial external references that define the personal dataset policy.

## Official Rust sources

- Rust 2024 Edition Guide: <https://doc.rust-lang.org/edition-guide/rust-2024/index.html>
- Cargo features reference: <https://doc.rust-lang.org/stable/cargo/reference/features.html>
- Rust Reference, macros by example: <https://doc.rust-lang.org/reference/macros-by-example.html>
- Rustdoc documentation tests: <https://doc.rust-lang.org/beta/rustdoc/write-documentation/documentation-tests.html>
- Rustonomicon, Send and Sync: <https://doc.rust-lang.org/stable/nomicon/send-and-sync.html>

## Dataset donor sources reviewed

- Strandset-Rust-v1: <https://huggingface.co/datasets/Fortytwo-Network/Strandset-Rust-v1>
- Strand-Rust-Coder technical report: <https://huggingface.co/blog/Fortytwo-Network/strand-rust-coder-tech-report>
- rustbench-single-file-patch-only: <https://huggingface.co/datasets/nmuendler/rustbench-single-file-patch-only>
- Rust_Master_QA_Dataset: <https://huggingface.co/datasets/dmeldrum6/Rust_Master_QA_Dataset>
- DCAgent/a1_stack_rust: <https://huggingface.co/datasets/DCAgent/a1_stack_rust>
- DCAgent/exp_rpt_stack-rust_10k: <https://huggingface.co/datasets/DCAgent/exp_rpt_stack-rust_10k>
- DCAgent/exp_rpt_stack-rust: <https://huggingface.co/datasets/DCAgent/exp_rpt_stack-rust>
- DCAgent/exp_rpt_stack-rust-v3-test: <https://huggingface.co/datasets/DCAgent/exp_rpt_stack-rust-v3-test>
- DCAgent2 swebench/dev/terminal trace families reviewed in donor matrix

## Publication and training format references

- Hugging Face Datasets, build and load: <https://huggingface.co/docs/datasets/en/about_dataset_load>
- Hugging Face Datasets, share and structure your repository: <https://huggingface.co/docs/datasets/main/en/repository_structure>
- Unsloth datasets guide: <https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/datasets-guide>
- Unsloth chat templates: <https://unsloth.ai/docs/basics/chat-templates>

## Immediate implications

- execution-grounded code data should dominate the train mix
- Rust 2024 behavior must be oversampled
- benchmark-aligned repair and semantic tasks are higher priority than explanation or naming tasks
- trajectory datasets require separate process-only handling and should not be mixed into core supervised code training
- publish the final dataset as a standard Hugging Face dataset repository with data files plus a dataset-card `README.md`
- keep one unified SFT export with ChatML-style `messages` so it can be consumed directly by Unsloth flows
- include `prompt` and `completion` convenience columns for training UIs that do not natively read `messages`
