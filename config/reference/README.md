# Layout reference snapshots

These files are provenance and regression fixtures, not build instructions. Generation uses `../layout.json`, `../behaviors.dtsi`, and `../palette.json`. `scripts/seed-layout.py` reconstructs the initial agreed layout for regression tests; it does not overwrite an existing source.

Sunaku files were copied from [v52, commit 7d8c0076308c5649614317fd8c6b53b800c46719](https://github.com/sunaku/glove80-keymaps/tree/7d8c0076308c5649614317fd8c6b53b800c46719). Credit to Sunaku for the Enthium implementation, symbol/number maps, and RGB/diagram palettes.

| Local file | Upstream path | SHA-256 |
| --- | --- | --- |
| `sunaku-v52.json` | `keymap.json` | `feb86b3d79245da53ee2d4716db5dc09f71310f88077e24028a696db307e59f9` |
| `sunaku-number-diagram.json` | `README/number-layer-diagram.json` | `b48316203775864d0204a9d43f2654f6916f9de7ab96fc41bb5499c357180f3d` |
| `sunaku-symbol-diagram.json` | `README/symbol-layer-diagram.json` | `71d4ab61a0b5185ac7e65b851585b2539dc8f4ec9bd7301c76db6a5f4ba2ffa6` |
| `sunaku-cursor-diagram.json` | `README/cursor-layer-diagram.json` | `2b46cb0dadd48ffcfbc540daa35e4116d76283250b643ab58b914043411a8afd` |

Function/media palette: `sunaku-function-diagram.json` from `README/function-layer-diagram.json`, SHA-256 `369b807bd2abc9d7e0433cee805d2ded7ad9ba8e00f878a9dbad453754903553`.

`prototype.json` is the user's revised [MoErgo prototype](https://my.moergo.com/glove80/#/layout/user/f38069dc-cf2d-4a1a-a02b-f1a2bfb33253), exported on 2026-09-10. The initial layout preserves its Base and Cursor positions, replaces the agreed layer controls, and removes its obsolete Cursor exit and scissors decoration.

The current diagram adapts the thumb coordinates published in the inline JavaScript of [Sunaku's interactive diagram](https://sunaku.github.io/moergo-glove80-keyboard.html#layers), inspected on 2026-09-10. Both thumb rows use 25°, 35°, and 45° rotations; the right side is mirrored exactly. `config/info.json` contains the normalized coordinates. The SVG renderer and interactive color legend are local implementations.

The default Macchiato palette translates Sunaku's functional groups into [Catppuccin Macchiato](https://github.com/catppuccin/catppuccin#-palette). `base-colors-before-macchiato.json` preserves the previous personal Base palette and decorations, independently of firmware bindings, for a possible restoration.

RGB effect regression fixture: `zmk-rgb-underglow.c` is `app/src/rgb_underglow.c` at the firmware revision in `firmware.lock.json`, SHA-256 `8b212d21a124c13e2d936e92d58da335ae168eadf344fc0cda9b497761ce9fcc`. It retains the upstream license and is used to compile and test the patched effect transitions.

This project began with MoErgo’s configuration template and draws on the dedicated-key approach of [Matt Sturgeon’s configuration](https://github.com/MattSturgeon/glove80-config). Firmware is pinned to [MoErgo PR36](https://github.com/moergo-sc/zmk/pull/36), `darknao/zmk` revision `db2ba9fcd3dec4c7afcf171f123585a9f8292595`, with its Nix dependencies. Local patches enable layer RGB at startup, synchronize reconnections, and restart or stop the animation timer when cycling between layer colors and the four built-in effects. The immediate-input module uses ZMK’s extra-module support.

Catppuccin Latte, Frappé, Macchiato, and Mocha use the official [Catppuccin palette](https://github.com/catppuccin/palette), version 1.8.0. `catppuccin-colors.json` retains the source hex codes. All four firmware palettes share category assignments; light/dark page styling remains a separate UI preference.

Multi-palette builds pack only the explicitly chosen maps, in the supplied order. Magic’s stock effect command synchronizes the absolute effect index to both halves. The local palette behavior selects its map and matching lock color from that index. The diagram stays Macchiato; its 93% light-mode surface mix also applies to legend swatches.

The optional `qmk` firmware palette uses RGB constants from pinned Sunaku v52. Teal and Sky groups share **Azure (`AZU_RGB`, `#99F5FF`)**, replacing dark teal. Flamingo, Maroon, and Pink groups share Sunaku’s Pink. Yellow, Green, Blue, Lilac, and Red use his original constants; modifiers retain Yellow Shift, Green Control, Cyan Alt, and Magenta Command. Category assignments and bindings stay the same. Each role records its upstream `source_color`; MoErgo decorations use Sunaku-style pastel backgrounds. The interactive map and default build remain Macchiato.

Dual-Shift sends Caps Lock down as soon as both Shift keys are held, and Caps Lock up when either is released. Both Shifts must be released before another chord can trigger Caps Lock. Shift events retain their original timestamps; there is no timer or output queue.
