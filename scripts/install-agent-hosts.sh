#!/usr/bin/env bash
# Activate the host-agnostic new-project contract in a clone, and optionally
# bootstrap it into another checkout or into user-level LLM host directories.
#
# The file list is not hardcoded here: it is read from the agent host contract
# (governance/agent-hosts.json or .governance/agent-hosts.json) and, when
# bootstrapping a different checkout, from governance/package-manifest.json.

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/install-agent-hosts.sh [options]

  --source DIR    Hub or already-populated checkout (default: this script's repo)
  --target DIR    Git clone that should receive host files and hooksPath
  --user          Also install user-level Cursor / Gemini / Claude pointers
  --check         Report what is missing and exit non-zero; change nothing
  -h, --help      Show this help

With no --target and no --user the current git work tree is activated in place:
host files already delivered by adoption are verified, the hook is made
executable and core.hooksPath is set. Nothing is copied over itself.
EOF
}

SOURCE=""
TARGET=""
USER_INSTALL=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      [[ $# -ge 2 && -n "${2:-}" ]] || { echo "Missing value for --source" >&2; exit 2; }
      SOURCE="$2"; shift 2 ;;
    --target)
      [[ $# -ge 2 && -n "${2:-}" ]] || { echo "Missing value for --target" >&2; exit 2; }
      TARGET="$2"; shift 2 ;;
    --user) USER_INSTALL=true; shift ;;
    --check) CHECK_ONLY=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$SOURCE" ]]; then
  SOURCE="$(cd "$script_dir/.." && pwd)"
fi
SOURCE="$(cd "$SOURCE" && pwd)"

if [[ -z "$TARGET" && "$USER_INSTALL" == false ]]; then
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    TARGET="$(git rev-parse --show-toplevel)"
  else
    echo "No --target and current directory is not a git work tree." >&2
    usage >&2
    exit 2
  fi
fi

contract_path() {
  local root="$1"
  for candidate in "governance/agent-hosts.json" ".governance/agent-hosts.json"; do
    if [[ -f "$root/$candidate" ]]; then
      printf '%s\n' "$root/$candidate"
      return 0
    fi
  done
  echo "Agent host contract not found under $root" >&2
  return 1
}

# Emits "<target-path>\t<is-hook>" lines for every file the contract governs.
contract_targets() {
  python3 - "$1" <<'PY'
import json, sys
contract = json.load(open(sys.argv[1], encoding="utf-8"))
for host in contract["hosts"]:
    print(f"{host['file']}\t0")
print(f"{contract['hook']['path']}\t1")
for runtime_file in contract["hook"]["runtimeFiles"]:
    print(f"{runtime_file}\t0")
PY
}

hooks_path_config() {
  python3 - "$1" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["hook"]["hooksPathConfig"])
PY
}

# Emits "<source>\t<target>\t<executable>" for every file the host contract
# needs in a target checkout: the instruction files, the hook, and the contract
# itself, because activate_in_place reads the contract from the target.
package_host_files() {
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
contract = json.load(open(sys.argv[2], encoding="utf-8"))
contract_source = sys.argv[3]
governed = (
    {host["file"] for host in contract["hosts"]}
    | {contract["hook"]["path"]}
    | set(contract["hook"]["runtimeFiles"])
)
for item in manifest["files"]:
    if item["target"] in governed or item["source"] == contract_source:
        print(f"{item['source']}\t{item['target']}\t{int(bool(item['executable']))}")
PY
}

activate_in_place() {
  local dest="$1"
  dest="$(cd "$dest" && pwd)"
  local contract hooks
  contract="$(contract_path "$dest")"
  hooks="$(hooks_path_config "$contract")"
  local missing=()

  while IFS=$'\t' read -r target is_hook; do
    if [[ ! -f "$dest/$target" ]]; then
      missing+=("$target")
      continue
    fi
    if [[ "$is_hook" == "1" && "$CHECK_ONLY" == false ]]; then
      chmod +x "$dest/$target"
    fi
  done < <(contract_targets "$contract")

  if [[ "${#missing[@]}" -gt 0 ]]; then
    printf 'GOV-AGENT-HOST-004: missing host files in %s:\n' "$dest" >&2
    printf '  %s\n' "${missing[@]}" >&2
    echo "  Adopt the current standard package, or bootstrap with --source <hub> --target $dest" >&2
    return 1
  fi

  if [[ "$CHECK_ONLY" == true ]]; then
    local configured; configured="$(git -C "$dest" config --get core.hooksPath || true)"
    if [[ "$configured" != "$hooks" ]]; then
      echo "GOV-AGENT-HOST-006: core.hooksPath is '${configured:-unset}', expected '$hooks'" >&2
      return 1
    fi
    echo "Host contract is active in $dest"
    return 0
  fi

  git -C "$dest" config core.hooksPath "$hooks"
  echo "Activated host contract and core.hooksPath=$hooks in $dest"
}

bootstrap_into() {
  local dest="$1"
  dest="$(cd "$dest" && pwd)"
  if ! git -C "$dest" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "Target is not a git work tree: $dest" >&2
    exit 1
  fi
  local contract
  contract="$(contract_path "$SOURCE")"
  local manifest="$SOURCE/governance/package-manifest.json"
  if [[ ! -f "$manifest" ]]; then
    echo "Source has no governance/package-manifest.json: $SOURCE" >&2
    exit 1
  fi

  while IFS=$'\t' read -r source target executable; do
    if [[ ! -f "$SOURCE/$source" ]]; then
      echo "Source file missing: $SOURCE/$source" >&2
      exit 1
    fi
    if [[ "$CHECK_ONLY" == true ]]; then
      continue
    fi
    mkdir -p "$dest/$(dirname "$target")"
    cp -f "$SOURCE/$source" "$dest/$target"
    if [[ "$executable" == "1" ]]; then
      chmod +x "$dest/$target"
    fi
  done < <(package_host_files "$manifest" "$contract" "${contract#"$SOURCE/"}")

  activate_in_place "$dest"
}

install_user_files() {
  local home="${HOME:-}"
  if [[ -z "$home" || ! -d "$home" ]]; then
    echo "HOME is not a directory; skipping --user" >&2
    return 1
  fi
  if [[ "$CHECK_ONLY" == true ]]; then
    echo "--check does not inspect user-level pointers"
    return 0
  fi
  local rule="$SOURCE/.cursor/rules/new-project-standard.mdc"
  [[ -f "$rule" ]] || { echo "Source file missing: $rule" >&2; return 1; }

  mkdir -p "$home/.cursor/rules" "$home/.gemini" "$home/.claude" "$home/.config/aider"
  cp -f "$rule" "$home/.cursor/rules/new-project-standard.mdc"

  local marker="wellmanifest/new-project host contract"
  for pointer in "$home/.gemini/GEMINI.md" "$home/.claude/CLAUDE.md"; do
    if [[ ! -f "$pointer" ]] || ! grep -Fq "$marker" "$pointer"; then
      cat > "$pointer" <<EOF
# $marker

When the current repository has \`./project/new-ticket.sh\`, follow that
repository's host contract and \`AGENTS.md\`. Allocate tickets only through
that script. Never commit on main or a dirty primary checkout. Run
\`./scripts/install-agent-hosts.sh\` once per clone so the git hook is active.
EOF
    fi
  done
  echo "Installed user-level host pointers under $home/.cursor $home/.gemini $home/.claude"
}

status=0
if [[ -n "$TARGET" ]]; then
  target_abs="$(cd "$TARGET" && pwd)"
  if [[ "$target_abs" == "$SOURCE" ]]; then
    activate_in_place "$target_abs" || status=1
  else
    bootstrap_into "$target_abs" || status=1
  fi
fi
if [[ "$USER_INSTALL" == true ]]; then
  install_user_files || status=1
fi
exit "$status"
