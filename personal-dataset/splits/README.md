# Split Policy

This directory will contain generated split manifests.

Planned files:

- `train.json`
- `dev.json`
- `blind-test.json`
- `red-team.json`

Rules:

- no crate-family overlap between `train` and `blind-test`
- no exact task-template overlap between `train` and `blind-test`
- donor datasets marked as dev/test/verified benchmark are excluded from `train`

