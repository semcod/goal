#!/usr/bin/env bash
# Universal ticket scaffolder for target System X repositories.

set -euo pipefail

TITLE="New Task Ticket"
USERS=""
AGENT="antigravity"
WORKSTREAM=""
FORCE_NEW=false

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
  -w, --workstream ID    Required workstream declared in the governance manifest
  -u, --users IDS        Compatibility input only; human files are not created
  -k, --kind KIND        Work kind; default SERVICE
  -p, --priority P       Work priority; default P2
  -o, --origin ORIGIN    Work origin; default health
      --force-new        Create a new ticket despite an unfinished ticket
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
    --force-new)
      FORCE_NEW=true
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

if [[ -z "$WORKSTREAM" ]]; then
  echo "Workstream is required; choose an id declared in .governance/manifest.json" >&2
  exit 2
fi

WORKSTREAM="$(printf '%s' "$WORKSTREAM" | tr '[:upper:]' '[:lower:]')"
if [[ ! "$WORKSTREAM" =~ ^[a-z0-9][a-z0-9-]*$ ]]; then
  echo "Workstream id must match [a-z0-9][a-z0-9-]*" >&2
  exit 2
fi

is_active_ticket() {
  local readme="$1/README.md"
  [[ -f "$readme" ]] && grep -Eiq '^-[[:space:]]+\*\*Status\*\*:[[:space:]]*IN_PROGRESS([[:space:]]|$)' "$readme"
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
if git rev-parse --git-dir >/dev/null 2>&1 \
  && git remote get-url origin >/dev/null 2>&1; then
  if ! git fetch --prune origin '+refs/heads/*:refs/remotes/origin/*' >/dev/null 2>&1; then
    echo "GOV-TICKET-LOCK-004: remote ticket refs could not be refreshed safely." >&2
    echo "  remediation: restore origin connectivity and retry; do not allocate a number from stale refs." >&2
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
    if is_active_ticket "$dir"; then
      active_workstream="$(sed -nE 's/^[[:space:]]*"workstream"[[:space:]]*:[[:space:]]*"([a-z0-9-]+)".*/\1/p' "$dir/intent.json" 2>/dev/null | head -n 1)"
      if [[ -z "$active_workstream" || "$active_workstream" == "unresolved" || "$WORKSTREAM" == "unresolved" || "$active_workstream" == "$WORKSTREAM" ]]; then
        conflicting_ticket="$dir"
      fi
    fi
  done
fi

if [[ -n "$conflicting_ticket" && "$FORCE_NEW" != true ]]; then
  echo "Active ticket conflicts with workstream '$WORKSTREAM': $conflicting_ticket" >&2
  echo "Continue it, choose a distinct declared workstream, close/cancel it, or use --force-new after an explicit human decision." >&2
  exit 3
fi

next_num=$((highest + 1))
ticket_num="$(printf '%03d' "$next_num")"
ticket_id="ticket-$ticket_num"
ticket_dir="project/$ticket_id"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
date_only="${timestamp%%T*}"
agent_file="ai-$AGENT.md"
agent_log="ai-$AGENT-logs.txt"

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

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [$agent_file]($agent_file)
EOF
fi

if [[ -f template/files/preprompt.template.md ]]; then
  render_template template/files/preprompt.template.md "$ticket_dir/preprompt.md"
else
  cat > "$ticket_dir/preprompt.md" <<EOF
# Ticket preprompt

- **Task ID**: $ticket_id
- **Task title**: $TITLE
- **Created**: $timestamp

Keep executable implementation outside this governance/evidence directory.
Read a human-owned user-*.md file only when one exists.
The request to execute this work creates SESSION_EXECUTION_AUTHORIZATION;
proceed within the recorded intent without a redundant confirmation prompt.
Require new authority for destructive action, secrets, external coordination,
material objective expansion and trusted merge approval.
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

if [[ -f template/files/agent-participant.template.md ]]; then
  render_template template/files/agent-participant.template.md "$ticket_dir/$agent_file"
else
  cat > "$ticket_dir/$agent_file" <<EOF
---
participant-id: agent:$AGENT
participant: $AGENT
role: agent
ticket: $ticket_id
---
# Participant: $AGENT (AI agent)

## Understanding

To be completed after reading human-owned input and the ticket preprompt.

## Execution plan

1. Validate the ticket scope and acceptance evidence before implementation.

## Actual changes

- Initialized the bounded ticket and recorded SESSION_EXECUTION_AUTHORIZATION
  from the request to execute this work.

## Blockers

- None inside the recorded intent; proceed without a second confirmation.
- New authority remains required for destructive action, secret access, new
  external coordination, material objective expansion and trusted merge.
EOF
fi

: > "$ticket_dir/$agent_log"

cat > "$ticket_dir/changelog.md" <<EOF
# Ticket Changelog ($ticket_id)

## [0.1.0] - $date_only

- Initial governance scaffold created.
- No human participant identity or content was generated.
EOF

if [[ -n "$USERS" ]]; then
  echo "warning: --users=$USERS did not create user-* files; human-owned input must come from a human or trusted intake boundary" >&2
fi

if [[ -f project/readme.sh ]]; then
  bash ./project/readme.sh
fi

echo "Successfully scaffolded $ticket_dir for '$TITLE'."
