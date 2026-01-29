#!/usr/bin/env bash
set -euo pipefail

docker build -t goal-integration-matrix -f integration/Dockerfile .
docker run --rm goal-integration-matrix
