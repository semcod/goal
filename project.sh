#!/usr/bin/env bash
# Safe target-repository entry point for wellmanifest/new-project governance.

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
validator="$repo_root/project/governance-check.sh"

if [[ -x "$validator" && -f "$repo_root/.governance/manifest.json" ]]; then
  "$validator" "$@"
elif [[ ! -f "$repo_root/.governance/manifest.json" ]]; then
  echo "GOV-MANIFEST-001: .governance/manifest.json is not installed in this target repository." >&2
  echo "  remediation: bootstrap the pinned governance package before implementation." >&2
  exit 1
else
  echo "GOV-BOOT-001: project/governance-check.sh is missing or not executable." >&2
  echo "  remediation: restore the wrapper from the pinned governance package." >&2
  exit 1
fi

# Optional analysis tools must be supplied as an explicitly pinned image.
# The governance gate above always runs first and no package is installed on the host.
if [[ -n "${NEW_PROJECT_ANALYSIS_IMAGE:-}" ]]; then
  if [[ ! "$NEW_PROJECT_ANALYSIS_IMAGE" =~ @sha256:[a-f0-9]{64}$ ]]; then
    echo "GOV-STACK-001: NEW_PROJECT_ANALYSIS_IMAGE must be pinned by sha256 digest." >&2
    echo "  remediation: use registry/image@sha256:<64 lowercase hex characters>." >&2
    exit 1
  fi
  command -v docker >/dev/null 2>&1 || {
    echo "GOV-DOCKER-001: docker command is unavailable." >&2
    exit 1
  }
  docker info >/dev/null
  docker run --rm --network none \
    --mount "type=bind,src=$repo_root,dst=/workspace" \
    --workdir /workspace \
    "$NEW_PROJECT_ANALYSIS_IMAGE"
fi
