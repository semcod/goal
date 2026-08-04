# Goal release logic flow

## Plan and apply

```mermaid
sequenceDiagram
    actor U as User or Koru
    participant C as Goal CLI/protocol
    participant P as Planner
    participant S as Event store
    participant A as Authority gate
    participant D as URI dispatcher
    participant X as Effect adapter
    participant V as EQL verifier

    U->>C: PlanRelease(intent)
    C->>P: inspect through read-only ports
    P-->>C: canonical ReleasePlan + plan_hash
    C->>S: append ReleasePlanned
    C-->>U: plan preview and hash
    U->>C: ApplyRelease(plan_hash, grant)
    C->>A: verify actor, workspace, hash, risk, anti-replay
    alt authority denied or workspace changed
        A-->>C: reject
        C->>S: append ReleaseApplyRejected
        C-->>U: fail closed
    else authorized
        A-->>C: bounded authority
        loop each planned step
            C->>D: execute exact URI + idempotency key
            D->>X: claim and execute effect
            X-->>D: result + evidence
            D->>V: read back expected state
            V-->>C: EQL assertions + receipt
            C->>S: append attempted/result/verified events
        end
        C-->>U: terminal ReleaseStatusView
    end
```

## Failure, retry and replay

```mermaid
stateDiagram-v2
    [*] --> Planned
    Planned --> Authorized: valid grant and exact plan hash
    Planned --> Rejected: authority or fingerprint mismatch
    Authorized --> Executing
    Executing --> Verifying: adapter returned evidence
    Executing --> Failed: adapter error or interruption
    Verifying --> Executing: next planned step
    Verifying --> Failed: EQL failed
    Verifying --> Completed: all EQL assertions passed
    Failed --> RetryPlanned: explicit governed retry
    RetryPlanned --> Executing: idempotency/read-back permit retry
    Failed --> Aborted: explicit abort
    Completed --> [*]
    Rejected --> [*]
    Aborted --> [*]
```

Replay follows only `event stream -> reducer -> projection`. It has no edge to
the URI dispatcher or effect adapters. A repair or compensation requires a new
command, plan and authority decision.
