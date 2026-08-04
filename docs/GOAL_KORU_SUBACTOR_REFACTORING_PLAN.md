# Goal URI/DSL/CQRS+ES refactoring plan

## Decision

Goal will evolve through a strangler migration into a deterministic release
process engine. It will reuse the architectural contracts known from Koru,
`nlp2uri` and Subactor without importing either orchestrator runtime into Goal.

The durable boundary is a versioned protocol. Koru may invoke Goal and consume
its events, while Goal remains independently usable as a Python CLI.

## Invariants

1. Existing `goal push` behavior remains compatible until an explicitly
   announced cutover.
2. Planning, querying and event replay never execute external effects.
3. A mutation executes only from an immutable plan with a matching
   `plan_hash` and workspace fingerprint.
4. Each external effect has a stable idempotency key and emits attempted,
   succeeded or failed evidence.
5. Success requires EQL-style read-back; process exit code alone is not proof.
6. DSL describes intent/capabilities and never executes arbitrary code.
7. Concrete URIs come from a versioned catalog/binding, not from an LLM.
8. Static Goal configuration remains conventional; Event Sourcing is limited
   to the `ReleaseRun` lifecycle.
9. Goal has no runtime dependency on Koru or Subactor.
10. JSON is the canonical auditable form; Protobuf is an optional wire/storage
    projection with compatibility tests.

## OpenRouter model policy

- `Gemini 3.1 Pro Preview` must not be selected or invoked through OpenRouter.
- The approved replacement model ID is `z-ai/glm-5.2`.
- Where Goal configuration expects a provider-qualified identifier, it uses
  `openrouter/z-ai/glm-5.2`.
- Environment or project overrides that explicitly request the forbidden model
  must fail validation or be replaced only through an explicit migration step;
  the runtime must not silently fall back to another expensive model.
- Tests use fakes and do not make live OpenRouter requests.

## Target bounded contexts

| Context | Responsibility | Write model | Read model |
| --- | --- | --- | --- |
| Release planning | Detect repository facts and freeze intended effects | `PlanRelease` | `ReleasePlanView` |
| Release execution | Enforce lifecycle, grants and idempotency | `ApplyRelease`, `RetryStep`, `AbortRelease` | `ReleaseStatusView` |
| Effect journal | Record external attempts and receipts | adapter-owned effect records | audit/history stream |
| Process catalog | Bind abstract capabilities to concrete URI Processes | versioned catalog changes | URI/capability lookup |
| Verification | Evaluate postconditions over read-back evidence | assertion results | EQL report |

## Canonical contracts

### ReleasePlan

The canonical JSON plan contains at least:

- schema/profile version;
- `run_id`, correlation and causation identifiers;
- repository identity, branch, `HEAD` and workspace fingerprint;
- current and target package versions;
- ordered steps with capability, concrete URI, risk class and dependencies;
- expected inputs/outputs and EQL assertion references;
- per-step idempotency key template;
- artifact/source hashes and canonical `plan_hash`.

The hash is computed over normalized UTF-8 JSON with stable key ordering and
without volatile display fields. Apply does not rescan and silently replace
the reviewed plan.

### Commands

- `PlanRelease`
- `ApplyRelease`
- `RetryReleaseStep`
- `AbortRelease`
- `RecordEffectReceipt`

### Queries

- `GetReleasePlan`
- `GetReleaseStatus`
- `ListReleaseRuns`
- `GetReleaseEventStream`
- `GetProcessCatalog`

### Domain events

- `ReleasePlanningStarted`, `ReleasePlanned`, `ReleasePlanRejected`
- `ReleaseApplyAuthorized`, `ReleaseApplyRejected`
- `StepExecutionAttempted`, `StepExecutionSucceeded`, `StepExecutionFailed`
- `TestsVerified`, `CommitCreated`, `VersionWritten`, `PackagePublished`
- `TagCreated`, `RemotePushVerified`, `ReleaseCompleted`, `ReleaseFailed`

Events are facts in past tense. Failure attempts are persisted as first-class
events; only logging successful commands is insufficient for release recovery.

## URI Process catalog

Initial stable capability bindings should include:

| Capability | Example URI | Risk |
| --- | --- | --- |
| inspect repository | `git://repository/query/status` | read_only |
| run tests | `test://project/query/run` | reversible |
| write version | `file://release-version/command/write` | reversible |
| create commit | `git://repository/command/commit` | reversible |
| publish package | `registry://package/command/publish` | boundary |
| create tag | `git://repository/command/tag` | boundary |
| push branch | `git://repository/command/push` | boundary |
| verify registry | `registry://package/query/version` | read_only |

The URI identifies a governed process, not raw shell text. Shell commands and
credentials remain inside the adapter selected by the catalog.

## DSL profiles

- `goal:intent/v1`: non-executable user/release intent.
- `goal:release-plan/v1`: deterministic execution IR.
- `goal:aql-contract/v1`: actor, risk and URI allowlists.
- `goal:eql-release/v1`: expected postconditions and evidence bindings.
- Text DSL and Protobuf are reversible projections of the same IR.

Unknown verbs, fields, capabilities, ambiguous bindings and schema versions
fail closed. The initial DSL should expose only a small set of release verbs,
not become a general-purpose programming language.

## Module boundaries

The exact package names may be refined by their implementation ticket, but the
dependency direction is fixed:

```text
goal.cli -> application -> domain
goal.cli -> projections
application -> ports -> adapters
adapters -> git/test/build/registry/filesystem
protocol -> pure contracts/codecs
koru/subactor adapter -> protocol/CLI, never domain internals
```

No domain or application module imports Click, subprocess, filesystem adapters,
Koru or Subactor.

## Sequential ticket roadmap

Only the current ticket is allocated now. The next ticket is created after its
predecessor is accepted or completed; IDs below are logical phases, not reserved
directory numbers.

| Phase | Workstream | Deliverable | Entry gate | Exit evidence |
| --- | --- | --- | --- | --- |
| P0 | integration | This blueprint and diagrams | repository analysis | human plan approval |
| P1 | governance | Pinned governance adoption, target manifest and ticket tooling | published immutable standard | governance gate reaches deterministic result |
| P2 | infrastructure | Root Dockerfile/compose and pinned Python test image | P1 complete | container build and smoke test |
| P3 | application | Characterization tests and external-effect inventory | green governance/Docker | current CLI behavior captured |
| P4 | application | Pure `ReleasePlan`, canonical JSON, fingerprints and `plan_hash` | P3 green | golden/hash/property tests |
| P5 | application | Commands, queries, events, JSONL store and projections in dual-write mode | P4 stable | replay equivalence tests |
| P6 | application | Ports/adapters, effect journal, receipts and idempotency | P5 green | crash/fault-injection tests |
| P7 | application | URI catalog, DSL compiler, Process Envelope, AQL and EQL | P6 green | fail-closed contract suite |
| P8 | interfaces/integration | Protobuf codecs and structured JSONL/stdio adapter | P7 schemas stable | JSON/Proto parity and compatibility tests |
| P9 | application | Koru/Subactor integration and closed-loop status | P8 stable | cross-repo contract E2E |
| P10 | application | CLI cutover, deprecation and legacy removal | parity window complete | release E2E and migration notes |

Every phase receives a separate ticket with narrow `allowedPaths`. A waiting
phase is `BACKLOG` or `PLAN`; only the currently executing phase becomes
`IN_PROGRESS`.

## Migration rules

### Dual-run before cutover

The legacy workflow remains authoritative while the new path observes and
produces plans/events. Then the new application service calls existing stages
through adapters. Finally the CLI switches to the new service after outputs and
effects show parity.

### Effect safety

- Event replay never calls adapters.
- `ApplyRelease` checks `HEAD`, workspace digest and `plan_hash` immediately
  before the first effect.
- Each adapter first claims an idempotency key, then records attempted/result
  evidence.
- Retries inspect the effect journal and external read model before executing.
- Publish/tag/push use separate receipts; absence of one is not inferred as
  failure or success.
- Compensation is a new governed command, never an automatic consequence of
  replay.

### Compatibility

- Existing flags map to `goal:intent/v1` without behavioral changes.
- Existing human output remains default during the compatibility window.
- Structured JSONL is opt-in, then becomes the integration interface.
- Event and plan schemas are versioned; readers tolerate additive fields but
  reject unsupported major versions.
- Protobuf field numbers are never reused and breaking changes require a new
  package version.

## Test strategy

1. **Characterization**: current CLI sequence, prompts, exit codes and skipped
   stages under temporary Git repositories.
2. **Domain/unit**: reducers and state transitions are pure and deterministic.
3. **Property tests**: canonicalization and `plan_hash` stability.
4. **Codec parity**: DSL/JSON/Protobuf round trips preserve the IR.
5. **Replay**: projection rebuilt from the same stream is identical and causes
   zero adapter calls.
6. **Idempotency**: duplicate apply/retry creates one effect and a duplicate
   receipt.
7. **Fault injection**: process interruption between every pair of release
   steps, especially publish/tag/push.
8. **Contract tests**: unknown URI/verb/profile and widened authority fail closed.
9. **Docker E2E**: local bare Git remote plus fake package registry; no live
   publication during tests.
10. **Cross-repo E2E**: Koru sends a protocol command and observes Goal receipts
    without importing Goal internals.

## Metrics and exit criteria

- zero unplanned adapter calls during plan/query/replay;
- 100% release transitions covered by reducer tests;
- deterministic plan hash across supported Python versions;
- one terminal receipt per attempted external step;
- duplicate apply has no duplicate external effect;
- legacy/new parity for supported `goal push` scenarios;
- governance gate, container tests and compatibility tests green before each
  ticket is closed.

## Current blockers

The Goal repository currently lacks a root Dockerfile/compose configuration and
an adopted `.governance` package. The local Governance Hub contains unpublished
0.9.0 adoption work, while its current published commit identifies version
0.8.0 and does not contain the immutable adoption generator. Therefore P1 must
wait for a reviewed, published full revision or use another explicitly approved
published standard revision that satisfies the current policy.
