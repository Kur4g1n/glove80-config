#!/usr/bin/env bash
# Install the build tools with Homebrew and start the Docker runtime (Colima).
set -euo pipefail
command -v brew >/dev/null || { echo 'Install Homebrew first: https://brew.sh' >&2; exit 1; }
brew install just python docker colima
docker info >/dev/null 2>&1 || colima start --cpu 4 --memory 8
docker info >/dev/null
echo 'Ready: just build'
