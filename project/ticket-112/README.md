# Ticket 112: Refactor documentation into compact topic guides

- **ID**: ticket-112
- **Owner**: codex
- **Status**: IN_PROGRESS
- **Workflow state**: VALIDATION
- **Created**: 2026-09-14

## Goal and scope

Refactor existing documentation into compact topic guides. Preserve legacy
entry files and heading anchors, index every new document and link the change
from CHANGELOG.md. This is a local pilot of document/v2 from wellmanifest/docs
commit ec838fddbda7a6f5a19d90cf3700e0e0fcf0a702, not protected fleet adoption.

## Acceptance criteria

- [x] AC-01: Each new guide has a precise uppercase name and one bounded topic.
- [x] AC-02: Old entry paths and headings resolve to the replacement topics.
- [x] AC-03: Changed-document format, links, managed governance and relevant stack checks pass; full-adoption gaps are recorded below.

## Validation evidence (2026-09-14)

- Managed governance: GOV-PASS, zero errors and warnings.
- 45 formatter/CLI tests passed; Docker Compose configuration passed.
- Changed compact guides and legacy maps: no checker findings; every local
  guide link exists and 29 original heading lines are preserved in order.
- Selected documents: 1444 → 825 words including replacement metadata and maps.
- Full docs audit remains non-passing: DOCS_ADOPTION (unpublished candidate)
  and 2 DOCS_METADATA findings in unchanged legacy documents.
  This pilot does not grant protected adoption or publication authority.
- Canonical result: [documentation index](../../docs/README.md).

Local validation is complete. No push, PR, merge or release was performed.
Ticket remains IN_PROGRESS pending a separately authorized publication.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
