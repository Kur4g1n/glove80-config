#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Bootstrap Python before invoking the Python-based dependency installer.
if ! command -v python3 >/dev/null 2>&1; then
    if [[ "$(uname -s)" == Darwin ]] && command -v brew >/dev/null 2>&1; then
        brew install python
    else
        echo 'Install Python 3, then run just setup again.' >&2
        exit 1
    fi
fi
exec python3 scripts/tasks.py setup
