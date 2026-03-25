# Dropbox Workflow

This folder is the simple entrypoint for testing one case at a time.

## Step 1

Load a case into this folder:

```powershell
.\scripts\load-dropbox.ps1 semantic/parse-endpoint
```

That command will populate:

- `dropbox/prompt.md`
- `dropbox/meta.yaml`
- `dropbox/work/`
- `dropbox/results/`

## Step 2

Put the model output into `dropbox/work/`.

You should edit only files inside `dropbox/work/`.

## Step 3

Run evaluation:

```powershell
.\dropbox\run-tests.ps1
```

Results will appear in:

- `dropbox/results/report.json`
- `dropbox/results/.eval-logs/`

## Notes

- the currently loaded case id is stored in `dropbox/case-id.txt`
- loading a new case replaces `dropbox/work/`
- each run replaces `dropbox/results/`

