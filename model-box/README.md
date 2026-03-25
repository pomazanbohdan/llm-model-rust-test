# Model Box

This is the single folder you give to the model.

Everything needed for one task lives here:

- `prompt.md`
- `meta.yaml`
- `workspace/`
- `results/`
- `run-tests.ps1`
- `invoke-model.ps1`
- `run-benchmark.ps1`

## Use

Load a case:

```powershell
.\load-case.ps1 semantic/parse-endpoint
```

Then:

1. give the model `prompt.md`
2. let it edit only `workspace/`
3. run:

```powershell
.\run-tests.ps1
```

Results appear in `results/`.

## Full model benchmark

`run-tests.ps1` checks one ready solution for one case.

If you want to test the model itself across many cases, configure `invoke-model.ps1` and run:

```powershell
.\run-benchmark.ps1
```

Optional filters:

```powershell
.\run-benchmark.ps1 -Layer semantic
.\run-benchmark.ps1 -Case semantic/parse-endpoint
.\run-benchmark.ps1 -MaxCases 5
```

Benchmark outputs appear in `benchmark/`.

Per case, the runner will:

1. prepare a fresh workspace
2. copy `prompt.md` and `meta.yaml`
3. call `invoke-model.ps1`
4. run hidden evaluation
5. write per-case results and aggregate summary
