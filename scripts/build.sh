#!/usr/bin/env bash
# Build build/glove80.uf2 (both halves) for the given theme inside the pinned Nix container.
set -euo pipefail
cd "$(dirname "$0")/.."
theme="${1:-}"
mkdir -p build
python3 scripts/glove80.py keymap ${theme:+--theme "$theme"} > build/glove80.keymap
docker build -q -t glove80-zmk . >/dev/null
docker run --rm -v "$PWD:/workspace" -v glove80-nix:/nix -e KEYMAP=/workspace/build/glove80.keymap glove80-zmk
python3 scripts/glove80.py uf2 build/glove80.uf2
