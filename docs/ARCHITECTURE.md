# Goal target architecture

This document visualizes the architecture governed by
`GOAL_KORU_SUBACTOR_REFACTORING_PLAN.md`.

```mermaid
flowchart LR
    Human[Human / existing CLI]
    Koru[Koru orchestrator]
    Protocol[Versioned Goal protocol<br/>JSON / DSL / Protobuf]
    CLI[CLI adapter]
    App[Release application service<br/>commands + queries]
    Domain[ReleaseRun domain<br/>state machine + reducer]
    Store[(Append-only event store)]
    Projection[Read models / status]
    Catalog[Capability and URI catalog]
    Authority[AQL / plan hash / apply grant]
    Dispatcher[URI Process dispatcher]
    Git[Git adapter]
    Tests[Test/build adapter]
    Registry[Registry adapter]
    Files[Filesystem adapter]
    EQL[EQL verifier + receipts]

    Human --> CLI
    Koru --> Protocol
    Protocol --> CLI
    CLI --> App
    App --> Domain
    Domain --> Store
    Store --> Projection
    App --> Catalog
    App --> Authority
    Authority --> Dispatcher
    Catalog --> Dispatcher
    Dispatcher --> Git
    Dispatcher --> Tests
    Dispatcher --> Registry
    Dispatcher --> Files
    Git --> EQL
    Tests --> EQL
    Registry --> EQL
    Files --> EQL
    EQL --> Store
    Projection --> CLI
    Projection --> Protocol
```

## Dependency rules

```mermaid
flowchart TD
    Interfaces[CLI / stdio / MCP adapters] --> Application
    Application --> Domain
    Application --> Ports
    Adapters --> Ports
    Adapters --> External[Git / filesystem / test tools / registries]
    Protocol[Pure contracts and codecs] --> Domain
    KoruAdapter[Koru/Subactor compatibility adapter] --> Protocol

    Domain -. forbidden .-> Interfaces
    Domain -. forbidden .-> Adapters
    Domain -. forbidden .-> External
    Domain -. forbidden .-> KoruAdapter
```

The application depends on port interfaces, while concrete adapters implement
those ports. Koru/Subactor integration sees public protocol contracts only.
