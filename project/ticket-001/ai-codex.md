---
participant-id: agent:codex
participant: codex
role: agent
ticket: ticket-001
---
# Participant: Codex (AI agent)

## Understanding

Użytkownik chce nie tylko opisu możliwości, lecz kontrolowanej refaktoryzacji
Goal krok po kroku, według ticketów. Docelowy Goal ma reużywać wzorce Koru,
`nlp2uri` i Subactor bez kopiowania całych runtime'ów oraz bez utworzenia cyklu
zależności. Pierwszym rezultatem jest blueprint przeznaczony do weryfikacji;
implementacja zacznie się dopiero po jego akceptacji.

## Intent

Przekształcić monolityczny workflow release w deterministyczny, audytowalny
bounded context, w którym planowanie jest czyste, mutacje wymagają authority,
a każda operacja zewnętrzna ma idempotency key, zdarzenie i weryfikowalny receipt.

## Scope

- architektura docelowa i granice modułów;
- kanoniczny `ReleasePlan`, `plan_hash` i workspace fingerprint;
- model Commands/Queries/Events/Projections;
- URI Process catalog i deklaratywny DSL;
- AQL/apply-grant/EQL oraz receipts;
- opcjonalny Protobuf na granicy integracji;
- sekwencja późniejszych ticketów i strategia testowa.

## Non-goals tego ticketu

- zmiana `goal push` lub innych komend;
- dodanie zależności;
- utworzenie event store w kodzie;
- publikacja, commit lub push;
- rozwiązanie wcześniejszych zmian governance-adoption obecnych w worktree.

## Execution plan

1. Zatwierdzić blueprint, diagramy i machine-readable intent.
2. W odrębnym tickecie governance zaadoptować opublikowany standard i
   skonfigurować docelowe workstreamy.
3. W odrębnym tickecie infrastructure zapewnić rootowy Docker runtime.
4. Scharakteryzować zachowanie i efekty istniejącego workflow testami.
5. Dodać czyste kontrakty planu i fingerprint bez zmiany zachowania CLI.
6. Dodać CQRS/ES i read models w trybie dual-write.
7. Obudować skutki portami/adapters oraz idempotentnymi receipts.
8. Dodać URI/DSL, authority i EQL.
9. Dodać opcjonalny Protobuf oraz adapter Koru/Subactor.
10. Przełączyć CLI etapami i usunąć legacy dopiero po dowodach parytetu.

## Acceptance criteria interpretation

Akceptacja ticketu oznacza zgodę na kierunek i kolejność, nie zgodę na dowolne
zmiany implementacyjne. Każdy następny ticket otrzyma własne `allowedPaths`,
kryteria odbioru i osobną bramkę przed edycją.

## Actual changes

- Utworzono dokument planu i dwa diagramy Mermaid.
- Utworzono ticket planistyczny, intent oraz indeks ticketów.
- Dodano odwołanie projektowe do `TODO.md`.
- Zapisano zatwierdzony model OpenRouter `z-ai/glm-5.2` i zakaz użycia
  `Gemini 3.1 Pro Preview`.
- Nie zmieniono kodu wykonawczego ani testów.

## Session authorization

- 2026-08-04: użytkownik polecił kontynuować po przedstawieniu ticket-001.
- Zakres autoryzacji: zamknięcie P0 oraz przygotowanie planu P1.
- Ta autoryzacja nie jest zaufanym review merge.

## Risks

- Replay może ponownie wykonać skutek, jeśli adaptery nie będą odizolowane.
- Częściowy failure pomiędzy publish/tag/push wymaga jawnej maszyny stanów.
- Protobuf użyty zbyt wcześnie zwiększy koszt migracji schematów.
- Aktualny standard 0.9.0 w Governance Hub nie jest jeszcze czystym,
  opublikowanym revision zawierającym generator adopcji.

## Blockers

- Ticket planistyczny nie ma dalszych blockerów.
- Implementacja kolejnych ticketów nadal wymaga opublikowanego, immutable
  revision Governance Hub oraz zielonej bramki w repozytorium Goal.

## Response routing

- responseRequiredFrom: none
