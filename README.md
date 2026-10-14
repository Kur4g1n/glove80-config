# Glove80 config

ZMK firmware for a [Glove80](https://www.moergo.com/) with an [Enthium](https://github.com/sunaku/glove80-keymaps) base layer, per-layer key colors in a Catppuccin flavor, and English/Russian ([Statica](https://github.com/mohoaz1348-rgb/statica)) typing on macOS with [Karabiner-Elements](https://karabiner-elements.pqrs.org/). The [interactive diagram](docs/index.html) shows every layer and exports a PDF.

Everything is generated from `config/`:

| File | Purpose |
| --- | --- |
| `layout.json` | Layers as ZMK bindings, one array per physical row; optional per-layer role overrides |
| `russian.json` | Cyrillic letter for each Base key |
| `theme.json` | Key roles → Catppuccin colors, symbol groups, flavors |
| `geometry.json` | Key positions for the diagram |
| `behaviors.dtsi` | The few ZMK behaviors the layout refers to (`&magic`, `&lang`, `&bt0`…) |

`just generate` writes `config/glove80.keymap`, `host/` and `docs/layout-data.js`; commit them with the sources.

## Install

```sh
brew install just
just setup        # Homebrew tools, Colima/Docker (Nix runs inside the container)
just install      # Russian input source + Karabiner rule; log out and back in afterwards
just build        # or: just build mocha  (latte, frappe, macchiato, mocha)
just flash        # once per half, see below
```

After `just install`:

1. *System Settings → Keyboard → Text Input*: keep **ABC** and add **Glove80 Russian** (search “Glove80”); remove other sources so Control-Space toggles exactly these two. Turn off *Use Caps Lock to switch to and from ABC*.
2. Install [Karabiner-Elements](https://karabiner-elements.pqrs.org/) and finish its setup prompts, then in *Complex Modifications → Add predefined rule* enable **Glove80: Statica in Russian; laptop keys stay native**.

Build before entering boot mode; a half in boot mode cannot type. To flash, switch a half off, hold **Magic + C3R3** (the `O` key on the left, `D` on the right), switch it on, and copy `build/glove80.uf2` to the volume that appears (`just flash` does this; `just flash-ready` opens Finder for a mouse-only copy). Flash the right half, then the left. The same file contains both halves. [MoErgo flashing guide](https://docs.moergo.com/glove80-user-guide/customizing-key-layout/#loading-new-zmk-firmware-onto-your-glove80).

After the first flash, hold **Magic** and press **Effect** until the keys show their layer colors; the choice is saved on the keyboard. **Magic + C6R4** enters boot mode and **Magic + C6R5** restarts a half. For a factory reset and re-pairing of the halves follow [MoErgo's guide](https://docs.moergo.com/glove80-user-guide/troubleshooting/#configuration-factory-reset-and-re-pairing-left-and-right-halves).

## Layers

Hold a layer key for a momentary layer. **Magic + layer key** locks the layer; pressing the layer key again unlocks it. The Magic key is MoErgo's hold-tap: hold for the Magic layer, tap to show the battery/connection status. Bluetooth profiles and USB are on the Magic layer.

## English and Russian

The language is the macOS input source and nothing else: **ABC** for English, **Glove80 Russian** for Russian. **Cursor → EN / RU** sends Control-Space (*Select the previous input source*). The firmware has no language state and the keyboard has none either; Caps Lock is a normal Caps Lock, also reachable by pressing **both Shifts**.

`host/Glove80.bundle` is Apple's Russian – PC letters with US digits and symbols, so the Glove80's Number and Symbol layers are identical in both languages and no modifier is involved. `host/glove80.json` is one Karabiner rule with per-device manipulators:

- Glove80, Russian source: letters are moved to the Statica positions (`config/russian.json`).
- Glove80, any source: Base keeps its real US keycodes, so English typing needs no software at all (login window included). Because `= - ' , . ; \ /` on Base are Cyrillic letters in Russian, the Number and Symbol layers send those eight symbols as F13–F20/INT1 and the rule turns them back into the symbols; the unused `L_C6R3` key sends a spare for ё. Without Karabiner, only those symbols on the Number/Symbol layers (and ё) are dead.
- Built-in keyboard, Russian source: the seven ЙЦУКЕН letters on punctuation keys, the shifted digit row (`"№;%:?`), `/` and `\` are mapped back to their native characters, so the laptop keeps QWERTY / ЙЦУКЕН unchanged.

Command and Control shortcuts keep their Latin letters in Russian. Inside the Russian keylayout the seven letters that ЙЦУКЕН puts on punctuation keys (х ъ ж э б ю ё) and № live on keypad codes, so a terminal program that switches the keypad to application mode (vim, for example) may read those seven letters as keypad keys. Edit `config/russian.json` to move letters, then `just generate`, `just install` (re-enable the rule in Karabiner), `just build` and `just flash`.
