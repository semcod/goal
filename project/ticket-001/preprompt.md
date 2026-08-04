# Preprompt i wytyczne techniczne (ticket-001)

- **Tytuł zadania**: Blueprint refaktoryzacji Goal do URI/DSL/CQRS+ES
- **Utworzono**: 2026-08-04T12:49:48Z
- **Tryb**: planowanie; bez zmian implementacyjnych

## Wymagania techniczne

- Zachować kompatybilność istniejącego CLI podczas migracji strangler.
- Ograniczyć Event Sourcing do bounded contextu `ReleaseRun`; statyczna
  konfiguracja pozostaje konwencjonalna.
- Oddzielić read model od komend oraz czyste planowanie od adapterów efektów.
- Każda mutacja musi wynikać z zamrożonego planu, być skorelowana,
  idempotentna i posiadać receipt z późniejszym read-backiem.
- DSL nie wykonuje kodu i nie nadaje authority. URI pochodzi wyłącznie z
  wersjonowanego katalogu/bindingu.
- Protobuf jest opcjonalną granicą wire-format; kanoniczny JSON pozostaje
  audytowalną reprezentacją do fingerprintu i plan hash.
- Nie dodawać zależności runtime `goal -> koru`; Koru może zależeć od Goal albo
  komunikować się przez stabilny protokół.
- Wszystkie późniejsze testy wykonywać w zadeklarowanym środowisku Docker.

## Źródła referencyjne

- `repo://semcod/goal/goal/push/core.py`
- `repo://semcod/koru/src/koru/cqrs/event_store.py`
- `repo://semcod/koru/packages/dsl2koru`
- `repo://semcod/nlp2uri/schemas/common/v1`
- `knowledge://subactor/architecture.autonomy-execution-pipeline/v2`
- `knowledge://subactor/architecture.strategy-dsl/v1`
- `knowledge://subactor/architecture.uri-twin-scope/v3`

## Dyrektywy wykonawcze

- Przed implementacją przedstawić `ai-codex.md`, `TODO.md` i `intent.json`.
- Po zatwierdzeniu otwierać następny ticket tylko dla aktualnego, odrębnego
  workstreamu i nie przenosić authority przez `integrationTicket`.
- Nie tworzyć ani nie modyfikować `user-*.md`.
- Nie przypisywać istniejących, niepowiązanych zmian worktree do tego ticketu.
