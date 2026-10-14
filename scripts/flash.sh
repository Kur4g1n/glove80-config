#!/usr/bin/env bash
# Copy build/glove80.uf2 to whichever Glove80 bootloader volume is mounted (right half first, then left).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/glove80.py uf2 build/glove80.uf2
for volume in /Volumes/GLV80RHBOOT /Volumes/GLV80LHBOOT; do
  if [[ -f "$volume/INFO_UF2.TXT" ]]; then
    cp -X build/glove80.uf2 "$volume/" && echo "Flashed $volume"; exit 0
  fi
done
echo 'No Glove80 bootloader volume is mounted. Hold Magic + C3R3 (O or D) while switching a half on, then retry.' >&2
exit 1
