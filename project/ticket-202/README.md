# Ticket 202: Treat dynamic __version__ declarations as observed contracts

- **ID**: ticket-202
- **Owner**: ai-claude
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-24

## Goal and scope

Live regression on paxlet-com/heyasa after its 0.2.0 release made
`heyasa/__init__.py:__version__` dynamic (`__version__ = _discover_version()`):
the static reader produced "selector __version__ was not found" and the
governed release workflow aborted with "Version sources are unreadable or
unsupported" even though VERSION and pyproject.toml carry the managed version.
A `__version__` assignment with a non-literal RHS is a dynamic declaration:
the module observes the released version at runtime, so the version state now
treats it as an observed contract (not managed, no error) instead of an
unreadable source.

## Acceptance criteria

- [ ] AC-01: A `__version__ = <dynamic expression>` module yields a contract source (no error) and the release decision resolves without VersionStateError.
- [ ] AC-02: Static literal sources keep their managed behavior; boundary/completion tests still pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
