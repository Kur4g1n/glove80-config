# Glove80 installation

[Open the interactive keyboard map](https://kur4g1n.github.io/glove80-config/) — explore all five layers, preview English/Russian and Shift legends, and export a PDF.

## Install

On macOS, install [Homebrew](https://brew.sh), then run from this repository:

```sh
brew install just
just setup
just doctor
```

Setup installs missing tools and prepares Docker with Colima. Nix runs inside the container. If a C compiler is missing, run `xcode-select --install`. On Linux/WSL, install `just`, Docker, Python 3, Node.js, and a C compiler first.

## Build

```sh
just check
just build                 # Macchiato
# just build macchiato,mocha # Choose palettes in cycle order
just build-bilingual       # English + Statica; requires the host setup below
just docs
```

View the Macchiato map [online](https://kur4g1n.github.io/glove80-config/), or run `just docs` and open [localhost:8000](http://127.0.0.1:8000) for a local preview. GitHub Pages publishes `docs/` from `main`; commit regenerated documentation after `just generate` to update the online map. Choose firmware palettes from `qmk`, `latte`, `frappe`, `macchiato`, and `mocha`, separated by commas. The first is the default. **Magic → Effect** cycles through the chosen palettes, solid, breathing, spectrum, and swirl, then returns to the first palette. Saved effect preferences survive restarts. `qmk` uses Sunaku’s RGB colors with light Azure (`#99F5FF`) replacing dark teal; use `just build qmk` or mix it with other palettes.

Both halves and the combined `build/glove80.uf2` are generated. `build/key-theme.txt` records the chosen palettes; `build/keymap.json` shows the first palette in MoErgo. Build locally: MoErgo's online builder cannot include the custom module.

Each build also saves a copy in `build/standard/` or `build/bilingual/`. The top-level UF2 is always the **last build**; check `build/profile.txt` before flashing. Both commands accept the same palette choices.

## English and Russian

The standard build works with a US English input layout. The bilingual build adds an adapted [Statica thumb layout](https://github.com/mohoaz1348-rgb/statica/tree/6a3e1a50fddfda463757d758e1c2437296224ef4), with **в** on the right thumb, all 33 Russian letters, and shared Number/Symbol output. The map's **EN/RU** button previews both languages, including Shift and PDF export; it does not switch the computer's language.

Install the host setup **before flashing the bilingual build**:

| System | Setup | Laptop keyboard |
| --- | --- | --- |
| macOS | [Karabiner + supplied input layouts](host/README.md#macos) | QWERTY / Russian PC (ЙЦУКЕН); Glove80-only rules activate with Russian |
| Windows | [AutoHotkey + AutoHotInterception](host/README.md#windows) | Standard English / Russian; automatic Glove80 mapping and Ctrl/Win thumb swap |
| Linux | [Device-specific XKB layouts](host/README.md#linux) | Existing layout stays assigned to the laptop |

`just install` detects the host OS and installs its bilingual support files; Windows requires the prepared AutoHotInterception directory as an argument. The guides cover permissions, language switching, flag icons, reconnects, startup, and removal. No host software is installed by `just setup`. The Russian positions live in `config/russian.json`; `just generate` also regenerates host maps.

Finish building **before entering boot mode**. To prepare for flashing with only a mouse on macOS:

```sh
just flash-ready
```

This opens Finder at the firmware file and mounted volumes. On other systems, open those locations in the file manager.

## Flash both halves

Connect a USB **data** cable directly to the half being flashed. Start with the **right half**, then repeat for the **left**, using the same combined UF2.

1. Switch the half off. Hold its two boot keys below while switching it on.
2. Release the keys when its boot volume appears.
3. Using the mouse, copy `build/glove80.uf2` onto that volume. Wait for copying to finish and the volume to disappear.

| Half | Hold at power-on | Boot volume |
| --- | --- | --- |
| Left | `L_C6R6` + `L_C3R3` (Magic + O in this layout) | `GLV80LHBOOT` |
| Right | `R_C6R6` + `R_C3R3` (Magic + D in this layout) | `GLV80RHBOOT` |

`C6` is the outermost column; rows count from the top. These physical boot keys work regardless of the installed layout. Once installed, **Magic + C6R4** also enters boot mode on that half.

A half in boot mode cannot type. If already there, use the prepared Finder windows to copy firmware with the mouse. To exit without flashing, switch it off and on without holding keys. After flashing, turn both halves on and connect USB to the **left** half for typing. [MoErgo's flashing guide](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/#loading-new-zmk-firmware-onto-your-glove80).

With another keyboard available, `just flash /Volumes/GLV80RHBOOT` copies to an explicitly selected boot volume; repeat with `/Volumes/GLV80LHBOOT` for the left half.

## Restart and reset

**Restart:** switch the half off and on, or press **Magic + C6R5**. Saved settings remain intact.

**Reset settings and pair the halves:** switch both off. Hold `L_C6R6` + `L_C3R2` (Magic + 3), switch the left half on, hold for **5 seconds**, then switch it off. Repeat on the right with `R_C6R6` + `R_C3R2` (Magic + 8). Turn both on together, check both respond, and leave them on for **at least one minute**. This clears saved preferences and Bluetooth pairings, retaining the firmware. [MoErgo's reset guide](https://docs.moergo.com/glove80-user-guide/troubleshooting/#configuration-factory-reset-and-re-pairing-left-and-right-halves).

For Bluetooth, select a green **BT 0–BT 3** key on Magic and pair “Glove80” in the computer's Bluetooth settings. Forget any old pairing after a reset. For USB, connect the left half and select **USB** on Magic.
