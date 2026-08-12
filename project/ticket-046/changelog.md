# Ticket Changelog (ticket-046)

## [0.1.0] - 2026-08-12

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Bounded the repair to one shared Goal source-hub health runner, its two
  existing dispatch points and focused regression coverage.
- Implemented fail-closed source-hub JSON, CI wiring, required-check and shell
  suite execution with successful-run Git state immutability.
- Routed both `goal governance check` and governed delivery through the shared
  runner while retaining adopted-target behavior.
- Passed 54 focused tests, Ruff, governance and a read-only real source-hub
  execution over 15 JSON documents and 9 Linux shell suites.
- Passed 581 full tests (2 existing skips), wheel/sdist and Docker builds, then
  removed their local artifacts.
- Entered governed pull-request publication after implementation commit
  `fec3d73` passed the complete local contract.
- CI and Validator Agent approved exact PR head `f15b687`; PR #70 merged as
  `main@3ba0aa0` with an identical tree and passed the clean-merge retest.
- Released the application workstream by blocking only on a dependent,
  separately budgeted 2.1.297 integration release and downstream proof.
- Published Goal 2.1.297 and verified its fresh public install runs the real
  new-project candidate health contract without Git-state mutation.
- Used the repaired public path for governed new-project PR #96, exact-head
  protected validation and trusted merge, then verified final v0.15.0 against
  live glon in read-only mode.
