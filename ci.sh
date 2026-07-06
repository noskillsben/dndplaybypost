#!/usr/bin/env bash
# CI entrypoint: backend unit tests always; set CI_FULL=1 to also rebuild the
# docker stack and run frontend tests inside it.
set -euo pipefail
cd "$(dirname "$0")"

make test-backend

if [ "${CI_FULL:-0}" = "1" ]; then
    make rebuild
    make test-frontend
fi

echo "CI passed."
