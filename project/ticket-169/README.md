# Ticket 169: Adopt wellmanifest docs standard and normalize documentation metadata

- **ID**: ticket-169
- **Owner**: agent:gemini
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-09-19
- **Authorization**: SESSION_EXECUTION_AUTHORIZATION

## Goal and scope

Adopt `wellmanifest/docs` standard in `semcod/goal` at revision `19efafbeb18923cfd51cc69bd519330488500137`, add `.governance/docs.json`, link canonical documentation in `docs/README.md`, and normalize information metadata and section markers to pass docs check.

## Acceptance criteria

- [x] AC-01: Add `.governance/docs.json` pinning `wellmanifest/docs@19efafbeb18923cfd51cc69bd519330488500137`.
- [x] AC-02: Normalize evidence URIs and required sections in `docs/information/`.
- [x] AC-03: Pass `python3 .../check.py` from `wellmanifest/docs`.
- [x] AC-04: Pass `./project/governance-check.sh`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
