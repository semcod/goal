# GOV-TICKET-001: brak aktywnego właściciela implementacji

## Situation

Kod pojawia się, gdy diff implementacyjny nie ma dokładnie jednego ticketu ze
statusem `IN_PROGRESS`. Typowy przypadek to ustawienie `DONE / DONE` na branchu
PR przed trusted merge.

## Meaning

Zamknięty ticket nie udziela już uprawnienia do swojego `allowedPaths`.
Implementacyjny PR musi zachować `IN_PROGRESS / PUBLICATION` aż exact-head
review zostanie zintegrowany z gałęzią domyślną.

## Safe resolution

1. Sprawdź, czy PR nadal wskazuje oczekiwany HEAD i dokładnie jeden ticket.
2. Jeżeli implementacja nie została scalona, przywróć ticket do
   `IN_PROGRESS / PUBLICATION` na tym samym branchu i ponów bramę.
3. Po trusted merge utwórz nowy governance-only closure z aktualnego `main`.
4. W closure ustaw `DONE / DONE` i zapisz merge SHA oraz post-merge checks.

## Verification

- Diff implementacyjnego PR zawiera aktywny ticket i przechodzi governance
  gate.
- Diff closure nie zawiera implementacji, a zapisany merge SHA jest przodkiem
  bieżącego `main`.
- Zdalny branch implementacyjny znika dopiero po merge.

## Do not

- Nie osłabiaj `activeStatuses` i nie zezwalaj `DONE` na autoryzowanie diffu.
- Nie dopisuj closure do niescalonego full-diff branchu.
- Nie traktuj lokalnego statusu Markdown jako trusted approval.

## Related rules

- `P-CORE-014`, `P-CORE-023`
- `C-TICKET-017`
- `C-PUBLISH-003`, `C-PUBLISH-009`
