# Ticket 210: Push the release tag on publish completion

- **ID**: ticket-210
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-25

## Goal and scope

Governed modes skip the remote release tag before the merge because the
release commit is not on the base branch yet; the completion published the
registry but left no tag, so releases had to be tagged by hand and the tag
could not serve as release evidence. On publish completion (post-merge,
successful upload) goal now creates the annotated tag when missing and pushes
only that tag under the governed push capability - no branch is ever moved.

## Acceptance criteria

- [ ] AC-01: Completion creates an annotated tag when missing and pushes it; an existing local tag is reused without re-creating.
- [ ] AC-02: A tag push failure is reported and does not fail the completed publication.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
