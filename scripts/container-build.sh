#!/usr/bin/env bash
set -euo pipefail
cd /workspace
if [[ "$(git -C /opt/zmk rev-parse HEAD)" != db2ba9fcd3dec4c7afcf171f123585a9f8292595 ]]; then
  echo 'Firmware revision does not match the lock.' >&2
  exit 1
fi
IFS=',' read -ra palettes <<< "${KEY_THEME:-macchiato}"
for palette in "${palettes[@]}"; do
  case "$palette" in qmk|latte|frappe|macchiato|mocha) ;; *) echo 'Unknown key theme' >&2; exit 1 ;; esac
done
palette_build_key="${KEY_THEME:-macchiato}"
palette_build_key="${palette_build_key//,/-}"
profile="${BUILD_PROFILE:-standard}"
case "$profile" in standard|bilingual) ;; *) echo 'Unknown build profile' >&2; exit 1 ;; esac
nix-build config --arg keymapFile "/workspace/.cache/build-config/${profile}/${palette_build_key}/glove80.keymap" -o /tmp/glove80-result --show-trace
mkdir -p build
cp --remove-destination /tmp/glove80-result/* build/
cp ".cache/build-config/${profile}/${palette_build_key}/keymap.json" build/keymap.json
printf '%s\n' "${KEY_THEME:-macchiato}" > build/key-theme.txt
printf '%s\n' "$profile" > build/profile.txt
mkdir -p "build/$profile"
cp --remove-destination build/*.uf2 build/*.config build/keymap.json build/key-theme.txt build/profile.txt "build/$profile/"
chmod u+w build/*
if [[ -n "${HOST_UID:-}" && -n "${HOST_GID:-}" ]]; then
  chown -R "$HOST_UID:$HOST_GID" build
fi
