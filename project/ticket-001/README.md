# Ticket 001: Blueprint refaktoryzacji Goal do URI/DSL/CQRS+ES

- **ID**: ticket-001
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Utworzono**: 2026-08-04
- **Workstream**: integration
- **Response required from**: none

## Cel i zakres

Przygotować zatwierdzalny blueprint stopniowej refaktoryzacji pakietu Goal,
wykorzystujący wzorce z Koru, `nlp2uri` i Subactor: adresowalne procesy URI,
deklaratywne DSL, CQRS z Event Sourcingiem dla przebiegu release, bramki
`plan_hash`/apply-grant, EQL receipts oraz opcjonalny transport Protobuf.

Ten ticket obejmuje wyłącznie dokumentację architektury, przepływu i kolejności
ticketów. Nie zezwala na zmianę kodu wykonawczego, testów ani zależności.

## Artefakty planu

- [`docs/GOAL_KORU_SUBACTOR_REFACTORING_PLAN.md`](../../docs/GOAL_KORU_SUBACTOR_REFACTORING_PLAN.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/LOGIC_FLOW.md`](../../docs/LOGIC_FLOW.md)
- [`intent.json`](intent.json)
- [`ai-codex.md`](ai-codex.md)

## Kryteria odbioru

- [x] AC-01: Plan definiuje granice domeny release i regułę braku zależności
  `goal -> koru`.
- [x] AC-02: Plan rozdziela intencję, plan, authority, wykonanie i weryfikację.
- [x] AC-03: Plan zawiera sekwencyjne etapy migracji i warunki wejścia/wyjścia.
- [x] AC-04: Plan zawiera strategię kompatybilności dla istniejącego `goal push`.
- [x] AC-05: Plan zawiera testy replay, idempotency, fault injection i E2E.
- [x] AC-06: Diagramy Mermaid opisują architekturę i przepływy plan/apply/failure.
- [x] AC-07: Człowiek zatwierdza plan, checklistę i machine-readable intent przed
  jakąkolwiek zmianą implementacji.

## Decyzja sesji

Plan został zaakceptowany interaktywnie 2026-08-04. Akceptacja zezwala na
przygotowanie kolejnego ticketu, ale nie jest zaufanym dowodem merge ani
zewnętrznym review.

## Ryzyka i mitygacje

- **Powtórzenie skutków podczas replay**: replay redukuje wyłącznie zdarzenia;
  adaptery efektów nie są wywoływane.
- **Cykl zależności Koru/Goal**: integracja odbywa się przez kontrakt i adapter,
  nigdy przez zależność `goal -> koru`.
- **Niejawne skutki obecnego workflow**: przed ekstrakcją powstają testy
  charakteryzacyjne oraz jawny katalog efektów.
- **Rozrost DSL**: jeden kanoniczny IR; tekst, JSON i Protobuf są projekcjami.
- **Niedojrzały governance targetu**: implementacja pozostaje zablokowana do
  adopcji opublikowanego standardu, utworzenia Docker runtime i zielonej bramki.

## Uczestnicy

- Human participant: unresolved; agent nie utworzył pliku `user-*`.
- Agent participant: [`ai-codex.md`](ai-codex.md).

## Granica katalogu

Katalog ticketu przechowuje wyłącznie governance, decyzje, logi i dowody.
Kod wykonywalny, testy i skrypty badawcze pozostają w standardowych katalogach
repozytorium.
