# Input menu icons

`english.icns` and `russian.icns` are the canonical icons copied into the generated macOS bundle. Each contains legacy 16-pixel (`is32`/`s8mk`) and 32-pixel (`il32`/`l8mk`) RGB/mask pairs. The 32-pixel image supports Retina menus.

The original PNG-only `icp4`/`icp5` representations decoded as noise in macOS IconServices. The corrected small images were resampled from the clean 128-pixel originals and encoded as legacy RGB/mask pairs, then visually verified through `GetIconRefFromIconFamilyPtr` and `NSImage(iconRef:)`. A large image preview alone does not catch this bug.

Preserve the legacy representations when editing these files. [Chromium’s icon documentation](https://chromium.googlesource.com/chromium/src/+/142.0.7444.59/docs/mac/icons.md) describes the same compatibility issue and tools for this format.

Run `just generate`, then `just install` after updating icons. Log out and back in to refresh cached input-menu icons. No firmware rebuild or flashing is needed.
