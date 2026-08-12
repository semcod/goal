# GOV-WORKSPACE-LIFECYCLE

## Situation

Kody `GOV-WORKSPACE-LIFECYCLE-001`–`003` oznaczają pozostały linked worktree,
duplikat klonu albo audyt, którego nie da się bezpiecznie zakończyć.

## Meaning

Stan terminalny wymaga jednego podstawowego checkoutu, lecz żaden checker nie
ma prawa automatycznie niszczyć nieznanych danych. Lokalny filesystem i zdalny
GitHub są osobnymi granicami dowodu.

## Safe resolution

1. Dla każdego checkoutu zapisz dirty state, branch, HEAD i tożsamość remote.
2. Potwierdź, że HEAD jest zintegrowany albo że właściciel jawnie porzucił
   unmerged pilot.
3. Linked worktree usuń przez `git worktree remove <dokładna-ścieżka>`, potem
   `git worktree prune` i dopiero wtedy usuń zwolniony lokalny branch.
4. Zweryfikowany duplikat klonu przenieś do odzyskiwalnego kosza.

## Verification

- Lokalny workspace checker kończy się `GOV-WORKSPACE-PASS` bez
  nieallowlistowanych checkoutów.
- Osobny workflow GitHub potwierdza tylko `main`, brak otwartych PR i
  `delete_branch_on_merge=true`.

## Do not

- Nie używaj globów rekurencyjnych ani nie usuwaj primary worktree.
- Nie uznawaj zielonego CI za dowód stanu lokalnego dysku.
- Nie usuwaj danych dirty lub unreachable bez decyzji właściciela.

## Related rules

- `P-WORKSPACE-001`–`004`
- `C-WORKSPACE-001`–`004`
