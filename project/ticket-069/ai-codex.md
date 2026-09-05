# Execution authority

SESSION_EXECUTION_AUTHORIZATION: user requested “napraw i opublikuj przez goal -a”
and supplied the follow-up Koru failure. This ticket fixes the Goal preflight
ordering and publishes that fix; it does not adopt unrelated dirty Koru changes.

SESSION_EXECUTION_AUTHORIZATION: current user requested “uruchom, prztetstuj czy goal -a dziala i napraw jesli nie”, then “kontynuuj” after the ticket-069 overlap was reported. Continue this bounded preflight repair in its existing worktree, preserving the staged implementation. This continuation does not request publication.

SESSION_EXECUTION_AUTHORIZATION: user now explicitly says “wdrazaj i tetsuj”. Continue the existing ticket and protected PR publication after the failed frozen review ends, preserving the original preflight implementation and removing the accidental generated out-of-scope Planfile delta.
