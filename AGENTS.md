# Notes for agents

- Principles: KISS, macOS only, minimal docs. README = overview + usage; this file = only what the code cannot tell you.
- Language = macOS input source only (`&lang` is Control-Space). No language state in the firmware. Karabiner tells the Glove80 from the built-in keyboard with `is_built_in_keyboard`, so no vendor/product IDs.
- The Russian keylayout keeps US digits/symbols on purpose: that is what makes the Number/Symbol layers language-independent. Native laptop symbols come from Karabiner, not from the layout.
- Base always sends real US keycodes (English must work at the login window without Karabiner). Where Base holds a Cyrillic letter on a punctuation key, the *other* layers send a spare keycode (`SPARE` in `scripts/glove80.py`) for that symbol and Karabiner maps it back in both languages. Inside the Russian keylayout the extra letters sit on keypad codes (`HOST_SPARE`): macOS types text from keypad codes but never from F-key codes, whatever the keylayout says.
- Firmware is pinned in `Dockerfile` to darknao's MoErgo ZMK branch because stock MoErgo/upstream ZMK has no `zmk,underglow-layer`; `&ug`, `&rgb_ug RGB_STATUS` and `CONFIG_EXPERIMENTAL_RGB_LAYER` come from it. No patches, no custom module: the layer-color effect is selected once on the keyboard and saved.
- Firmware cannot be built here without Docker; `just check` is the gate, CI builds.
