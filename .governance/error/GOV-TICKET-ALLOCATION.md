# GOV-TICKET-ALLOCATION i GOV-TICKET-LOCK

## Situation

Runbook obejmuje `GOV-TICKET-ALLOCATION-001`,
`GOV-TICKET-ALLOCATION-002` oraz `GOV-TICKET-LOCK-001`–`004`. Kody oznaczają
aktywny lub uszkodzony lock, nieczytelny high-water, istniejący katalog,
nieodświeżone zdalne refy, ticket poza rezerwacją albo dwa różne intenty z tym
samym numerem.

## Meaning

Numer ticketu jest zasobem całego klonu, a nie pojedynczego worktree.
`project/new-ticket.sh` musi odświeżyć refy, zdobyć wspólny lock i podnieść
high-water przed utworzeniem katalogu. Ręczne `mkdir` lub skopiowanie
`project/ticket-{NNN}` nie tworzy tej rezerwacji.

## Safe resolution

1. Zatrzymaj nowych writerów i zinwentaryzuj wszystkie linked worktree.
2. Zachowaj dirty state i oba HEAD-y; nie wybieraj zwycięzcy po nazwie.
3. Ustal wcześniejszą prawidłową rezerwację z refów, high-water i historii
   allocatora.
4. Pozostaw wcześniejszy intent przy jego numerze. Dla drugiej pracy uruchom
   `project/new-ticket.sh` i odtwórz branch wyłącznie z jej własnych zmian.
5. Przy błędzie refów napraw łączność z `origin` i ponów allocator. Przy
   aktywnym locku zaczekaj; usuwaj stale lock tylko po potwierdzeniu braku
   procesu.

## Verification

- `git worktree list --porcelain` pokazuje każdy sklasyfikowany checkout.
- Wspólny high-water jest nie mniejszy od najwyższego niescalonego claimu.
- Każdy numer ma jedną tożsamość `ticket + summary + workstream`.
- Ponowne uruchomienie workspace checkera nie emituje kodów allocation.

## Do not

- Nie zmieniaj numeru przez ręczne `mv` i nie kopiuj historii obu branchy.
- Nie usuwaj dirty/unreachable worktree ani locka bez identyfikacji procesu.
- Nie przydzielaj numeru offline ze starych refów.

## Related rules

- `P-CORE-022`
- `C-CONCURRENCY-001`, `C-CONCURRENCY-002`, `C-CONCURRENCY-003`
- `P-WORKSPACE-001`, `C-WORKSPACE-001`
