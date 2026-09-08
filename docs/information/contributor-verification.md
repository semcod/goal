---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "contributor-verification",
  "kind": "information",
  "version": 1,
  "title": "Verify and publish a Goal contribution",
  "status": "proposed",
  "owner": "semcod/goal",
  "created": "2026-09-08",
  "updated": "2026-09-08",
  "review_after": "2026-09-15",
  "source_revision": "64e433beccfb94d3bdd9cb28309f4e8dacd86b09",
  "affected_repositories": ["semcod/goal"],
  "evidence": [
    "https://github.com/semcod/goal/pull/137",
    "https://github.com/semcod/goal/blob/64e433beccfb94d3bdd9cb28309f4e8dacd86b09/.github/workflows/ci.yml",
    "https://github.com/semcod/goal/blob/64e433beccfb94d3bdd9cb28309f4e8dacd86b09/.github/main-protection.json",
    "https://github.com/subactor/onedev-agent/pull/214"
  ]
}
---

# Verify and publish a Goal contribution

<!-- docs:section purpose -->
## Purpose

Give contributors a repeatable route from a scoped change to independent review and protected publication. A local test pass, a configured CI profile and a successful check on the current PR are separate evidence.

<!-- docs:section scope -->
## Scope

These instructions apply to contributions to `semcod/goal`. Follow the repository [agent contract](../../AGENTS.md) for ticket allocation, ownership and worktree placement. Generic Goal CLI examples elsewhere do not override this repository's publication requirements.

<!-- docs:section evidence -->
## Evidence and current checks

The source revision in the metadata defines the following server-required checks:

| Check | Responsibility |
| --- | --- |
| `test (3.12)` | Product tests, publication-policy unit tests and public live ruleset readback on Python 3.12 |
| `test (3.13)` | The same checks on Python 3.13 |
| `governance / enforce` | Managed standard, scoped intent and repository governance |
| `governance / remote lifecycle` | GitHub branch lifecycle |

The [versioned main policy](../../.github/main-protection.json) requires current independent approval as well as those checks. A separate update restriction permits the trusted Validator App to publish to `main`; it does not let that App bypass the required checks or review rules.

OneDev additionally provides `onedev/local-verify`. Its protected Goal profile runs both Python versions offline with dependencies pinned during image build. The [OneDev-owned runbook](https://github.com/subactor/onedev-agent/blob/b6f08923420ec8cccb0b48b1f598ff0c12b78cbd/docs/information/goal-verification.md) records the profile, dependency-update procedure and historical replay evidence. Deployment and replay alone do not prove that a new PR has passed: observe the receipt for its exact head and current `main` before claiming that result.

<!-- docs:section content -->
## Contributor workflow

1. Fetch the target, inspect unfinished tickets and registered worktrees, and allocate or resume the matching ticket through `project/new-ticket.sh`. Use its canonical worktree and declared write scope. Preserve unrelated dirty changes in the primary checkout.
2. Review and stage only the ticket's files, record the required continuity checkpoint, and create a material commit with the installed hooks. In a development environment with the dev dependencies installed, run the checks below on that commit. The standalone governance command examines the committed range, so run it after the material commit exists. Resolve `origin/main` after fetching; do not substitute the feature branch's own head for the trusted base.

   ```bash
   git fetch origin --prune
   export WELLMANIFEST_BASE_SHA="$(git rev-parse origin/main)"
   ./project/governance-check.sh --base "$WELLMANIFEST_BASE_SHA"
   python3 -m pytest tests/ -q
   python3 -m unittest discover -s .github/tests -v
   python3 .github/scripts/check_main_protection.py
   docker compose config --quiet
   ```

   Run product and policy tests on both Python 3.12 and 3.13. A single local interpreter does not establish matrix coverage. Use the existing local test identity; CI configures its own deterministic identity. The default protection checker validates the declaration. An authorized operator can additionally run `python3 .github/scripts/check_main_protection.py --live` with an existing authenticated GitHub CLI session for full ruleset readback. CI uses `--public-live`, which explicitly cannot attest private bypass-actor fields.
3. Record the validation checkpoint and, from the verified clean committed worktree, publish through Goal:

   ```bash
   goal --delivery-mode pull-request --no-publish -a push \
     --ticket ticket-NNN --no-tag --no-changelog --no-version-sync \
     -m 'docs: explain contributor verification'
   ```

   Replace the allocated ticket and message. The flags above suit a documentation change without a release; they do not waive governance or independent review. Goal publishes the ticket PR branch. Keep its head frozen during validation.
4. Observe all four required checks and the supplemental OneDev receipt. For OneDev, bind the repository, PR number, head SHA, tested `main` SHA and profile digest. A stale green check is insufficient if `main` has advanced. Follow the [protected local publication policy](../../.governance/docs/LOCAL_CI_PUBLICATION.md) to reuse an existing reconciliation or invoke the deployed independent Validator adapter with the exact bindings and existing protected key reference. Authorized publication permits its `--merge` operation; the contributor must not approve or merge their own PR.
5. Confirm the merged commit, exact-head trusted review and branch lifecycle from GitHub. Complete the workspace audit through Goal, removing only the verified released worktree and branch. Preserve external receipts; do not create a ticket-closing commit.

## Recovering a blocked check

| Observation | Next action |
| --- | --- |
| OneDev is pending | Inspect the protected coordinator queue and current running job; do not interrupt another contribution's test run. |
| Tested base differs from live `main` | Request or await protected reconciliation against the new base; retain the previous receipt as historical evidence. |
| Dependency fingerprint differs | Publish a reviewed OneDev dependency pin and executor update before retrying; the offline PR job cannot install new dependencies. |
| Required hosted check fails | Fix the failing behavior or resolve its actual transport problem. The supplemental local status does not waive the hosted requirement. |
| Validator reports a changed binding | Re-observe the PR, current head/base and any trusted merge before retrying. Another protected process may already have completed it. |
| Documentation needs revision | Update this stable document, increment its metadata version and review date, and retain the index link. |

<!-- docs:section limitations -->
## Limitations

This runbook does not change server policy or certify a particular future PR. Environment-dependent skipped tests must be reported with their reason and cannot be counted as executed coverage. Offline policy unit tests do not attest live GitHub protection. Goal currently has documentation placement instructions but no `.governance/docs.json` adoption pin; this document is not evidence of protected documentation-checker enforcement. The OneDev standard-pack audit also reports missing declarations separately from its managed-byte and governance checks. No test here proves BoardNet/StackNet connectivity or safe physical motor/output operation.

<!-- docs:section next_actions -->
## Remaining acceptance work

First, retain a real new Goal PR's OneDev receipt bound to its exact head and current base, alongside its hosted checks and trusted publication result. Next, any proposal to make the local check mandatory or retire a hosted check needs a separate protected policy review, equivalent coverage evidence and a protected transport for live ruleset readback. Documentation-checker adoption and missing standard-pack declarations remain separate bounded integration tasks. Preserve the existing server requirements until those conditions are verified.
