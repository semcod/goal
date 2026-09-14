---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "adoption-command-adapter",
  "kind": "information",
  "version": 1,
  "title": "Existing Goal command adapter for adoption transactions",
  "status": "proposed",
  "owner": "semcod/goal",
  "created": "2026-09-14",
  "updated": "2026-09-14",
  "review_after": "2026-09-21",
  "source_revision": "cc0614da3a0afb9e3e09525789a897559b1a4e77",
  "affected_repositories": ["semcod/goal"],
  "evidence": ["goal/governance/adoption_transaction.py", "tests/test_adoption_transaction.py", "goal/cli/governance_cmd.py"]
}
---

# Existing Goal command adapter

<!-- docs:section purpose -->
## Purpose

`GoalAdoptionAdapter` connects the accepted transaction protocol to the existing
`goal governance adopt` command. It does not clone the generator, invent another
journal, or supply independent authorization and receipt providers.

<!-- docs:section content -->
## Contract

Construct the adapter with the pinned planner inputs, declared repository,
ticket and scope, protected profile digest, absolute Goal executable path,
positive finite command deadline, and an independent `AdoptionAdapter` delegate.
Use its `plan` as the transaction subject. Supported-pin retention needs no
adapter; blocked and multi-step plans remain refused.

The protected caller must bind the complete executable/runtime installation and
deadline to the profile, and verify that profile, catalog provenance, ticket
scope and writer lease. An absolute path or a locally computed digest is not
proof of trust. Do not load executable choices or grants from candidate prose.

For adoption, the adapter reobserves planning inputs before authorization and
again after authorization. The fixed invocation uses the canonical standard
repository, exact destination SHA, exact target root and `--upgrade`. It never
selects `latest` or enables unpublished fixtures in production.

Validation, publication and merge remain delegated to existing independent
controllers. Every application requires fresh delegated authorization, including
direct calls outside the transaction controller. No authorization is cached.

<!-- docs:section evidence -->
## Readback and retries

All observations come from the independent delegate. A successful exit is not
an APPLIED receipt; matching lock contents alone are also insufficient. The
transaction controller must validate subject-bound evidence before advancing.
The CLI does not consume the transaction idempotency key; safe retries therefore
still depend on the existing journal and authoritative readback, not on a claim
that the generator itself is idempotent.

A timeout or interruption kills the POSIX process group and reaps its leader.
A partial write remains possible and requires reconciliation. It does not become
a clean failure eligible for blind retry. Ordinary nonzero exits likewise need
readback. Standard output/error are discarded here rather than copied into
receipts or agent context; the independent evidence provider owns redacted,
bounded diagnostics. Processes that deliberately escape the process group are
outside this adapter's containment contract; the execution profile must prevent
that behavior or provide a stronger supervisor.

<!-- docs:section validation -->
## Validation

Isolated Git fixtures cover stale inputs, foreign subjects and keys, authority
revocation, bounded process cleanup, delegated phases and unchanged observation
ownership. An integration fixture invokes the actual adoption Click command and
its generator subprocess, replacing only the standard checkout transport with a
synthetic local fixture. Existing command tests cover immutable release fetching.
These tests do not contact a consumer, access real credentials or attest a live
migration.

<!-- docs:section limitations -->
## Remaining integration

This is an optional library adapter, not a deployed migration daemon. Before a
live pilot, supply protected profile/catalog resolution, authoritative adoption
readback, scoped lease authorization and real validation/publication delegates.
Configure a deadline from the execution profile rather than silently raising a
global timeout. Neither a package release nor fleet readiness is implied by
merging this source. Rollback is to stop selecting the adapter; this delivery
changes no adopter data or journal format.
