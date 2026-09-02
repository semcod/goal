#!/usr/bin/env bash
# Universal ticket scaffolder for target System X repositories.

set -euo pipefail

TITLE="New Task Ticket"
USERS=""
AGENT="antigravity"
WORKSTREAM=""
FORCE_NEW=false
ALLOCATION_KEY=""
ALLOCATION_RECEIPT=""
REFRESH_REMOTE=false

# Work classification for intent/v3. The defaults are the contract's own answer
# for an unclassified new ticket: rule W-CLASS-006 (work-request / maintenance)
# assigns SERVICE and health, and priorityDerivation.serviceDefault is P2.
# Declare --kind/--priority/--origin when the ticket is a defect or new behavior.
KIND="SERVICE"
PRIORITY="P2"
ORIGIN="health"

usage() {
  cat <<'EOF'
Usage: ./project/new-ticket.sh [options]

  -t, --title TITLE       Ticket title
  -a, --agent ID         Agent provider/id used for ai-{ID}.md
  -w, --workstream ID    Required workstream from the governance registry
  -u, --users IDS        Compatibility input only; human files are not created
  -k, --kind KIND        Work kind; default SERVICE
  -p, --priority P       Work priority; default P2
  -o, --origin ORIGIN    Work origin; default health
      --allocation-key K Stable Supervisor/task correlation for registered mode
      --allocation-receipt FILE
                          Receipt returned by the registered allocator process
      --force-new        Create a new ticket despite an unfinished ticket
      --refresh-remote   Fetch/prune origin before allocating; local refs are used by default
  -h, --help             Show this help

Accepted classification values are read from the work classification contract,
not hardcoded here. The defaults are that contract's own answer for an
unclassified new ticket (rule W-CLASS-006 plus the service priority default);
declare the three explicitly for a defect or new behavior.

Only a human may authorize --force-new. Human-owned user-*.md files must be
created and written by that human or by a trusted intake boundary.
EOF
}

require_value() {
  if [[ $# -lt 2 || -z "${2:-}" ]]; then
    echo "Missing value for $1" >&2
    usage >&2
    exit 2
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--title)
      require_value "$@"
      TITLE="$2"
      shift 2
      ;;
    -u|--users)
      require_value "$@"
      USERS="$2"
      shift 2
      ;;
    -a|--agent)
      require_value "$@"
      AGENT="$2"
      shift 2
      ;;
    -w|--workstream)
      require_value "$@"
      WORKSTREAM="$2"
      shift 2
      ;;
    -k|--kind)
      require_value "$@"
      KIND="$2"
      shift 2
      ;;
    -p|--priority)
      require_value "$@"
      PRIORITY="$2"
      shift 2
      ;;
    -o|--origin)
      require_value "$@"
      ORIGIN="$2"
      shift 2
      ;;
    --allocation-key)
      require_value "$@"
      ALLOCATION_KEY="$2"
      shift 2
      ;;
    --allocation-receipt)
      require_value "$@"
      ALLOCATION_RECEIPT="$2"
      shift 2
      ;;
    --force-new)
      FORCE_NEW=true
      shift
      ;;
    --refresh-remote)
      REFRESH_REMOTE=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$TITLE" == *$'\n'* || "$TITLE" == *$'\r'* ]]; then
  echo "Ticket title must fit on one line" >&2
  exit 2
fi

AGENT="$(printf '%s' "$AGENT" | tr '[:upper:]' '[:lower:]')"
if [[ ! "$AGENT" =~ ^[a-z0-9][a-z0-9._-]*$ ]]; then
  echo "Agent id must match [a-z0-9][a-z0-9._-]*" >&2
  exit 2
fi

governance_manifest() {
  local candidate
  for candidate in .governance/manifest.json .governance/manifest.base.json governance/manifest.hub.json; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! GOVERNANCE_MANIFEST="$(governance_manifest)"; then
  echo "GOV-MANIFEST-001: governance registry not found; cannot allocate a ticket." >&2
  echo "  remediation: restore .governance/manifest.json in an adopter or governance/manifest.hub.json in the hub." >&2
  exit 1
fi

if ! REGISTRY_VALUES="$(python3 - "$GOVERNANCE_MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)
ticket = manifest.get("ticket")
coordination = manifest.get("coordination")
statuses = ticket.get("activeStatuses") if isinstance(ticket, dict) else None
workstreams = coordination.get("workstreams") if isinstance(coordination, dict) else None
if (
    manifest.get("schema") != "new-project.governance/v2"
    or not isinstance(statuses, list)
    or not statuses
    or any(not isinstance(item, str) or not item for item in statuses)
    or len(statuses) != len(set(statuses))
    or not isinstance(workstreams, dict)
    or not workstreams
    or any(not isinstance(item, str) or not item for item in workstreams)
):
    raise SystemExit(1)
for status in statuses:
    print(f"status\t{status}")
for workstream in sorted(workstreams):
    print(f"workstream\t{workstream}")
PY
)"; then
  echo "GOV-MANIFEST-001: governance registry is invalid: $GOVERNANCE_MANIFEST" >&2
  echo "  remediation: restore a valid governance/v2 ticket and coordination registry." >&2
  exit 1
fi

ACTIVE_STATUSES="$(printf '%s\n' "$REGISTRY_VALUES" | sed -n 's/^status[[:space:]]//p')"
WORKSTREAM_REGISTRY="$(printf '%s\n' "$REGISTRY_VALUES" | sed -n 's/^workstream[[:space:]]//p')"

if [[ -z "$WORKSTREAM" ]]; then
  echo "Workstream is required; choose an id declared in $GOVERNANCE_MANIFEST" >&2
  exit 2
fi

WORKSTREAM="$(printf '%s' "$WORKSTREAM" | tr '[:upper:]' '[:lower:]')"
if [[ ! "$WORKSTREAM" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Workstream id must match [a-z0-9][a-z0-9-]*" >&2
  exit 2
fi
if ! printf '%s\n' "$WORKSTREAM_REGISTRY" | grep -Fxq -- "$WORKSTREAM"; then
  echo "GOV-WORKSTREAM-001: workstream '$WORKSTREAM' is not declared in $GOVERNANCE_MANIFEST." >&2
  echo "  accepted: $(printf '%s' "$WORKSTREAM_REGISTRY" | tr '\n' ' ')" >&2
  exit 1
fi

is_active_ticket() {
  local directory="$1" resolver status arguments=()
  [[ -f "$directory/README.md" ]] || return 1
  for resolver in .governance/ticket_activity.py scripts/ticket_activity.py; do
    [[ -f "$resolver" ]] && break
  done
  if [[ ! -f "$resolver" ]]; then
    echo "GOV-TICKET-ACTIVITY-001: managed ticket activity resolver is missing." >&2
    echo "  remediation: restore the complete pinned governance package before allocating." >&2
    exit 1
  fi
  while IFS= read -r status; do
    arguments+=(--active-status "$status")
  done <<< "$ACTIVE_STATUSES"
  if python3 "$resolver" --root . resolve --ticket-dir "$directory" "${arguments[@]}" >/dev/null; then
    status=0
  else
    status=$?
  fi
  case "$status" in
    0) return 0 ;;
    1) return 1 ;;
    *) exit 1 ;;
  esac
}

# The dimension vocabularies live in the work classification contract, which is
# shipped to targets as .governance/ and kept at governance/ in the hub. Reading
# them keeps this script from drifting away from the contract it must satisfy.
classification_dsl() {
  local candidate
  for candidate in .governance/work-classification.dsl.json governance/work-classification.dsl.json; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

require_classification_value() {
  local dimension="$1" value="$2" dsl
  if ! dsl="$(classification_dsl)"; then
    echo "GOV-CLASS-000: work classification contract not found; cannot validate --$dimension." >&2
    echo "  remediation: restore .governance/work-classification.dsl.json from the pinned package." >&2
    exit 1
  fi
  local allowed
  allowed="$(python3 -c 'import json,sys
data = json.load(open(sys.argv[1]))
print("\n".join(data["dimensions"][sys.argv[2]]))' "$dsl" "$dimension")"
  if ! printf '%s\n' "$allowed" | grep -Fxq -- "$value"; then
    echo "GOV-CLASS-001: '$value' is not a declared $dimension in $dsl." >&2
    echo "  accepted: $(printf '%s' "$allowed" | tr '\n' ' ')" >&2
    exit 1
  fi
}

require_classification_value kind "$KIND"
require_classification_value priority "$PRIORITY"
require_classification_value origin "$ORIGIN"

allocation_config() {
  local candidate
  for candidate in .governance/ticket-allocation.json governance/ticket-allocation.json; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

allocation_runtime() {
  local candidate
  for candidate in .governance/ticket_allocation.py scripts/ticket_allocation.py; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

ALLOCATION_MODE="local-single-clone"
ALLOCATION_CONFIG=""
ALLOCATION_RUNTIME=""
if ALLOCATION_CONFIG="$(allocation_config)"; then
  if ! ALLOCATION_RUNTIME="$(allocation_runtime)"; then
    echo "GOV-TICKET-ALLOCATION-003: ticket allocation policy exists but its managed validator is missing." >&2
    echo "  remediation: restore the complete pinned governance package before allocating." >&2
    exit 5
  fi
  if ! ALLOCATION_MODE="$(python3 "$ALLOCATION_RUNTIME" mode --config "$ALLOCATION_CONFIG")"; then
    echo "  remediation: restore a valid managed ticket-allocation/v1 policy." >&2
    exit 5
  fi
fi
if [[ "$ALLOCATION_MODE" == "local-single-clone" && ( -n "$ALLOCATION_KEY" || -n "$ALLOCATION_RECEIPT" ) ]]; then
  echo "GOV-TICKET-ALLOCATION-003: registered allocation inputs are forbidden in local-single-clone mode." >&2
  echo "  remediation: remove the inputs or adopt a registered allocator policy." >&2
  exit 5
fi

# Serialize allocation across every worktree sharing this clone. The high-water
# mark reserves a number even before its ticket is committed and therefore
# remains visible when another worktree cannot see the new directory.
allocation_lock=""
allocation_state=""
release_allocation_lock() {
  if [[ -n "$allocation_lock" ]]; then
    rmdir "$allocation_lock" 2>/dev/null || true
  fi
}
if git_common_dir="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
  allocation_lock="$git_common_dir/new-project-ticket-allocation.lock"
  allocation_state="$git_common_dir/new-project-ticket-high-water"
  if ! mkdir "$allocation_lock" 2>/dev/null; then
    echo "GOV-TICKET-LOCK-001: another ticket allocation is active in this clone." >&2
    echo "  remediation: wait for it to finish; remove a stale lock only after confirming no allocator is running." >&2
    exit 4
  fi
  trap release_allocation_lock EXIT INT TERM
fi

# The allocator owns the freshness requirement. Relying on a caller to fetch
# recreates the same partial view that clone-wide locking is meant to avoid.
if [[ "$REFRESH_REMOTE" == true ]] \
  && git rev-parse --git-dir >/dev/null 2>&1 \
  && git remote get-url origin >/dev/null 2>&1; then
  if ! git fetch --prune origin '+refs/heads/*:refs/remotes/origin/*' >/dev/null 2>&1; then
    echo "GOV-TICKET-LOCK-004: remote ticket refs could not be refreshed safely." >&2
    echo "  remediation: restore origin connectivity and retry, or omit --refresh-remote and rely on local refs plus protected merge collision detection." >&2
    exit 4
  fi
fi

# A ticket number taken on a branch is invisible on disk in another worktree.
# Consult every local and fetched remote branch known to this clone.
refs_highest() {
  local highest_ref=0 ref number decimal
  while read -r ref; do
    [[ -n "$ref" ]] || continue
    while read -r number; do
      decimal=$((10#$number))
      (( decimal > highest_ref )) && highest_ref=$decimal
    done < <(
      git ls-tree -d -r --name-only "$ref" -- project 2>/dev/null \
        | sed -nE 's|^project/ticket-([0-9]+)$|\1|p'
    )
  done < <(git for-each-ref --format='%(refname)' refs/heads refs/remotes 2>/dev/null)
  printf '%s' "$highest_ref"
}

highest=0
conflicting_ticket=""
current_branch="$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
if [[ "$current_branch" =~ ticket[-/]([0-9]{3}) ]]; then
  current_ticket="project/ticket-${BASH_REMATCH[1]}"
  if is_active_ticket "$current_ticket"; then
    conflicting_ticket="$current_ticket"
  fi
fi
if git rev-parse --git-dir >/dev/null 2>&1; then
  highest="$(refs_highest)"
  if [[ -n "$allocation_state" && -f "$allocation_state" ]]; then
    read -r reserved_highest < "$allocation_state"
    if [[ ! "$reserved_highest" =~ ^[0-9]+$ ]]; then
      echo "GOV-TICKET-LOCK-002: ticket allocation state is invalid." >&2
      exit 4
    fi
    reserved_decimal=$((10#$reserved_highest))
    (( reserved_decimal > highest )) && highest=$reserved_decimal
  fi
fi
if [[ -d project ]]; then
  for dir in project/ticket-*; do
    [[ -d "$dir" ]] || continue
    number="${dir##*-}"
    [[ "$number" =~ ^[0-9]+$ ]] || continue
    decimal=$((10#$number))
    (( decimal > highest )) && highest=$decimal
    if [[ -z "$current_branch" ]] && is_active_ticket "$dir"; then
      active_workstream="$(sed -nE 's/^[[:space:]]*"workstream"[[:space:]]*:[[:space:]]*"([a-z0-9-]+)".*/\1/p' "$dir/intent.json" 2>/dev/null | head -n 1)"
      if [[ -z "$active_workstream" || "$active_workstream" == "unresolved" || "$WORKSTREAM" == "unresolved" || "$active_workstream" == "$WORKSTREAM" ]]; then
        conflicting_ticket="$dir"
      fi
    fi
  done
fi

if [[ -n "$conflicting_ticket" && "$FORCE_NEW" != true ]]; then
  echo "Active ticket conflicts with workstream '$WORKSTREAM': $conflicting_ticket" >&2
  echo "Continue it, or return to the default branch before allocating a distinct workstream." >&2
  exit 3
fi

if [[ "$ALLOCATION_MODE" == "registered" ]]; then
  if [[ -z "$ALLOCATION_KEY" ]]; then
    echo "GOV-TICKET-ALLOCATION-003: registered mode requires --allocation-key from the Supervisor correlation." >&2
    echo "  remediation: retry with the stable task correlation; never invent a local sequence." >&2
    exit 5
  fi
  if ! origin_url="$(git config --get remote.origin.url 2>/dev/null)"; then
    echo "GOV-TICKET-ALLOCATION-003: registered mode requires a canonical origin repository." >&2
    exit 5
  fi
  if ! repository_ref="$(python3 "$ALLOCATION_RUNTIME" repository-ref --url "$origin_url")"; then
    exit 5
  fi
  allocation_arguments=(
    --config "$ALLOCATION_CONFIG"
    --repository-ref "$repository_ref"
    --allocation-key "$ALLOCATION_KEY"
    --title "$TITLE"
    --agent "$AGENT"
    --workstream "$WORKSTREAM"
    --kind "$KIND"
    --priority "$PRIORITY"
    --origin "$ORIGIN"
  )
  if [[ -z "$ALLOCATION_RECEIPT" ]]; then
    echo "GOV-TICKET-ALLOCATION-003: registered allocation receipt is required; submit this request to the configured process URI." >&2
    python3 "$ALLOCATION_RUNTIME" request "${allocation_arguments[@]}"
    exit 5
  fi
  if ! ticket_num="$(python3 "$ALLOCATION_RUNTIME" validate "${allocation_arguments[@]}" --receipt "$ALLOCATION_RECEIPT")"; then
    echo "  remediation: obtain a fresh receipt from the configured process URI for this exact request." >&2
    exit 5
  fi
  next_num=$((10#$ticket_num))
  if (( next_num <= highest )); then
    echo "GOV-TICKET-ALLOCATION-004: registered ticket $ticket_num is already visible in repository state." >&2
    echo "  remediation: continue the existing claim or request a fresh fenced allocation; do not recreate or rename it." >&2
    exit 5
  fi
else
  next_num=$((highest + 1))
  ticket_num="$(printf '%03d' "$next_num")"
fi
ticket_num="$(printf '%03d' "$next_num")"
ticket_id="ticket-$ticket_num"
ticket_dir="project/$ticket_id"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
date_only="${timestamp%%T*}"

if ! mkdir "$ticket_dir" 2>/dev/null; then
  echo "GOV-TICKET-LOCK-003: ticket directory already exists: $ticket_dir" >&2
  exit 4
fi
if [[ -n "$allocation_state" ]]; then
  allocation_state_tmp="$allocation_state.$$"
  printf '%s\n' "$next_num" > "$allocation_state_tmp"
  mv "$allocation_state_tmp" "$allocation_state"
fi

escape_sed() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//&/\\&}"
  value="${value//|/\\|}"
  printf '%s' "$value"
}

render_template() {
  local source="$1"
  local target="$2"
  sed \
    -e "s|{TICKET_ID}|$(escape_sed "$ticket_id")|g" \
    -e "s|{NNN}|$(escape_sed "$ticket_num")|g" \
    -e "s|{SHORT_TITLE}|$(escape_sed "$TITLE")|g" \
    -e "s|{TIMESTAMP}|$(escape_sed "$timestamp")|g" \
    -e "s|{YYYY-MM-DD}|$(escape_sed "$date_only")|g" \
    -e "s|{OWNER_NAME}|unresolved:human|g" \
    -e "s|{PROVIDER}|$(escape_sed "$AGENT")|g" \
    -e "s|{WORKSTREAM}|$(escape_sed "$WORKSTREAM")|g" \
    "$source" > "$target"
}

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

render_json_template() {
  local source="$1"
  local target="$2"
  sed \
    -e "s|{TICKET_ID}|$(escape_sed "$(json_escape "$ticket_id")")|g" \
    -e "s|{NNN}|$(escape_sed "$(json_escape "$ticket_num")")|g" \
    -e "s|{SHORT_TITLE}|$(escape_sed "$(json_escape "$TITLE")")|g" \
    -e "s|{TIMESTAMP}|$(escape_sed "$(json_escape "$timestamp")")|g" \
    -e "s|{YYYY-MM-DD}|$(escape_sed "$(json_escape "$date_only")")|g" \
    -e "s|{PROVIDER}|$(escape_sed "$(json_escape "$AGENT")")|g" \
    -e "s|{WORKSTREAM}|$(escape_sed "$(json_escape "$WORKSTREAM")")|g" \
    -e "s|{KIND}|$(escape_sed "$(json_escape "$KIND")")|g" \
    -e "s|{PRIORITY}|$(escape_sed "$(json_escape "$PRIORITY")")|g" \
    -e "s|{ORIGIN}|$(escape_sed "$(json_escape "$ORIGIN")")|g" \
    "$source" > "$target"
}

if [[ -f template/files/ticket.template.md ]]; then
  render_template template/files/ticket.template.md "$ticket_dir/README.md"
else
  cat > "$ticket_dir/README.md" <<EOF
# Ticket $ticket_num: $TITLE

- **ID**: $ticket_id
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: $date_only

## Goal and scope

To be completed from human-owned input.

## Acceptance criteria

- [ ] AC-01: Scope is approved by a human owner.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
EOF
fi

if [[ -f template/files/intent.template.json ]]; then
  render_json_template template/files/intent.template.json "$ticket_dir/intent.json"
else
  cat > "$ticket_dir/intent.json" <<EOF
{
  "schema": "new-project.intent/v3",
  "ticket": "$ticket_id",
  "summary": "$(json_escape "$TITLE")",
  "workstream": "$WORKSTREAM",
  "classification": {
    "kind": "$KIND",
    "priority": "$PRIORITY",
    "origin": "$ORIGIN"
  },
  "allowedPaths": ["project/$ticket_id/**", "TODO.md", "project/TICKETS.md"],
  "forbiddenPaths": ["project/ticket-*/user-*.md"],
  "stacks": [],
  "dependsOn": [],
  "conflictsWith": [],
  "integrationTicket": null
}
EOF
fi

if [[ -n "$USERS" ]]; then
  echo "warning: --users=$USERS did not create user-* files; human-owned input must come from a human or trusted intake boundary" >&2
fi

if [[ -f project/readme.sh ]]; then
  bash ./project/readme.sh
fi

echo "Successfully scaffolded $ticket_dir for '$TITLE'."
