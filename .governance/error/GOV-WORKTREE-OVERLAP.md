# GOV-WORKTREE-OVERLAP

## Situation

Kody `GOV-WORKTREE-OVERLAP-001`–`003` oznaczają, że dwa lub więcej checkoutów
tej samej tożsamości repozytorium jednocześnie zmienia te same ścieżki, albo
że ich aktywne `allowedPaths` nachodzą się bez `conflictsWith`.

To nie jest ten sam finding co `GOV-WORKSPACE-LIFECYCLE-*`. Tamten kod jest
terminalny (pozostały worktree po merge). Ten kod jest **proaktywny**:
równoległe worktree są dozwolone, nachodzące zmiany nie.

## Meaning

`001` — przecięcie brudnych albo niezmergowanych ścieżek (`git status` +
`git diff` względem merge-base).
`002` — dwa `IN_PROGRESS` intent.json w różnych worktree deklarują nachodzące
`allowedPaths` i żadne nie wymienia drugiego w `conflictsWith`.
`003` — audyt nie dał się bezpiecznie dokończyć.

Zakres zgłoszenia jest w polu `scope` raportu. Bramka repozytorium
(`--identity-of` / `--scope repository`, domyślne w pre-commit) odpowiada tylko
za własną tożsamość repozytorium — konflikt w cudzym repo nie blokuje tu
commita. Skan workspace (timer, path unit) raportuje wszystko, co znajdzie.

`TODO.md`, `project/TICKETS.md` i `project/ticket-*/**` są ignorowane; każdy
intent je deklaruje, więc porównywanie ich dawałoby overlap dla każdej pary.
Ticket liczy się tylko w tym worktree, którego **branch** jest jego branchem —
scalona kopia katalogu ticketu w innym worktree nie jest drugim pisarzem.

## Safe resolution

1. Zatrzymaj jednego writera albo przenieś nachodzące ścieżki do jednego
   ticketu / workstreamu integracyjnego.
2. Dopisz `conflictsWith` po obu stronach i zostaw tylko jeden ticket
   `IN_PROGRESS` na ten zakres.
3. Nie merguj, dopóki overlap nie zniknie albo nie zostanie zserializowany.
4. Po zintegrowaniu pierwszego ticketu odpal guard ponownie na drugim.

## Verification

```bash
python3 scripts/worktree_overlap_check.py --workspace-root . --format text
# albo po adopcji:
python3 .governance/worktree_guard.py --root . --once
# skan całego workspace na timerze:
systemctl --user start worktree-guard@$(systemd-escape --path ~/github/subactor).service
cat ~/.local/state/worktree-guard/$(systemd-escape --path ~/github/subactor).json
```

Oczekiwany wynik: `GOV-WORKTREE-OVERLAP-PASS`.

## Do not

- Nie traktuj samego faktu „jest więcej niż jeden worktree” jako błędu.
- Nie usuwaj cudzego worktree automatycznie.
- Nie omijaj guarda przez `--allow` wzorcem; ten checker nie ma allowlisty
  na nachodzące ścieżki.

## Related rules

- `git-lifecycle` `local-commit` / `integrate` wymagają braku niezgłoszonego overlapu.
- `ticket-lifecycle` wymaga `conflictsWith` przy nachodzącym zakresie.
- `P-CORE` / `C-TICKET` rule 11 (parallel work) w `AGENTS.md`.
