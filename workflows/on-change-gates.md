# On-Change Gates

This repository uses three pre-complete quality gates in the Koru flow:

- `task test` (primary local test entrypoint)
- `testql` scenarios (behavior checks, when scenarios exist)
- `wup` + `regix` (change-aware regression detection)

## Bootstrap

Run once in project root:

```bash
wup init
regix init
```

Current baseline configs are stored in:

- `wup.yaml`
- `regix.yaml`

## Daily Workflow

Before marking a ticket as done:

```bash
task koru-gate
```

`task koru-gate` is strict: it exits non-zero when required gates fail (including `regix gates` when configured).

## Optional Continuous Watching

For long coding sessions:

```bash
wup map-deps .
wup watch .
```

## Notes

- `wup.yaml` is tuned to monitor `goal/**`, `tests/**`, and core config files.
- `regix.yaml` uses practical hard gates and stricter target gates.
- Keep thresholds stable for at least one sprint; then tighten based on trend data.
