# Internal dependency updates

Goal 2.2.0 requires Python 3.12 or later. Run the tool separately from applications supporting older Python versions. The reviewed catalog is `integration/internal-dependencies.json` in this repository; package ownership is explicit and must be reviewed before adding entries. Folder names alone are not identity evidence.

```sh
uvx --python 3.12 --from 'goal==2.2.0' goal dependencies --catalog integration/internal-dependencies.json --project /path/to/consumer --check
```

The command compares catalogued uv.lock entries with the highest published, non-yanked stable three-part PyPI version. Exit status 1 reports stale or blocked entries. JSON includes source digests, observed time, target versions and exact upgrade arguments. It does not claim that installed environments are current. npm, Poetry, private indexes and other version formats are outside this contract.

For a clean standalone checkout, replace `--check` with `--update` to resolve exact targets in isolation and atomically replace only a verified uv.lock. Then run the repository's locked test matrix and build before its normal PR delivery. A Python/API conflict retains the previous lock and is a reported blocker. Local path, editable and Git sources are never silently replaced by PyPI. Governed repositories require their own integration ticket and protected delivery instead of this direct updater.

A `>=` declaration permits new versions but does not refresh an existing lockfile. Install and deploy with `uv sync --locked`; update locks in a separate tested change. Tool dependencies that require a newer Python can use:

```toml
[dependency-groups]
automation = ["goal>=2.2.0"]

[tool.uv.dependency-groups]
automation = { requires-python = ">=3.12" }
```

Move an existing tool-only declaration into that group; do not move a runtime dependency without checking imports.

## Scheduled consumers

Dependabot supports the `uv` ecosystem and uv.lock. For ordinary consumer repositories, use a repository-owned `.github/dependabot.yml` with an explicit internal package allowlist, `dependency-type: all` for transitive packages, one grouped update and a daily cron schedule. A cron schedule can include weekends; `interval: daily` runs on weekdays. Include all SemVer update levels when the target is the newest stable release. CI still decides compatibility; a constraint conflict is not permission to discard source or Python policy.

Dependabot opens update PRs; it does not itself guarantee successful tests, approval, merge, installation or immediate response to a registry publication. Keep independent freshness checks to expose unresolved targets. Governed consumers need a ticket-aware delivery adapter before enabling unattended version PRs. Respect repositories that intentionally set `open-pull-requests-limit: 0`.

References: [uv and Dependabot](https://docs.astral.sh/uv/guides/integration/dependabot/), [Dependabot options](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference), [uv lock and sync](https://docs.astral.sh/uv/concepts/projects/sync/).
