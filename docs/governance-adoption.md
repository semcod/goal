# Pinned governance adoption

`goal governance adopt` installs or checks the governance package published by
`wellmanifest/new-project`. It is intended for existing repositories that
already use Goal and need deterministic policy-as-code adoption.

## Preflight without writes

```bash
goal governance adopt \
  --source-revision <FULL_PUBLISHED_SHA> \
  --target-root . \
  --check
```

The command accepts only a lowercase 40-character commit SHA. It fetches that
exact revision into a temporary checkout and verifies `HEAD` before executing
the adoption generator. Exit code `0` means the project is current; exit code
`1` with `CREATE`, `UPDATE`, or `CHMOD` lines means changes are required.

## Adopt or upgrade

```bash
# First adoption
goal governance adopt --source-revision <FULL_PUBLISHED_SHA>

# Reviewed replacement of standard-managed drift
goal governance adopt \
  --source-revision <NEW_FULL_PUBLISHED_SHA> \
  --upgrade
```

The generator preserves a version-compatible local governance manifest. It
does not invent stack-specific Docker configuration, approve a ticket, or
overwrite differing managed files without `--upgrade`.

After first adoption, complete the project-local bootstrap files, create a
ticket with `./project/new-ticket.sh`, obtain plan approval, and run
`./project/governance-check.sh` before implementation tests.

## Mirrors and local integration tests

The default source is `https://github.com/wellmanifest/new-project.git`. A
trusted mirror or local checkout can be selected explicitly:

```bash
goal governance adopt \
  --standard-repository ../new-project \
  --source-revision <FULL_COMMIT_SHA> \
  --check
```

The selected repository supplies executable generator code. Do not use an
untrusted fork or a moving branch in place of a reviewed full SHA.

`new-project` 0.9.0 must be published with green CI and trusted current-head
review before its SHA is used for production adoption.
