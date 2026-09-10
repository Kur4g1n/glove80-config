# Bilingual keyboard setup

Build with `just build-bilingual` (or `just build-bilingual macchiato,qmk`). Install the matching setup below before flashing. Use the standard build on computers without this setup.

Only Glove80 receives the Statica mapping. The laptop keeps QWERTY/ЙЦУКЕН even while Glove80 is connected, so disconnecting does not require an input-layout reset. Select English or Russian normally; the website's EN/RU button only changes the diagram.

Number and Symbol keep their US output in either language. The Russian Base has **ф** at `L_C6R4`, **щ** at `R_C6R4`, and **ё** at `L_C6R3`. Its adjacent `L_C4R6` / `L_C3R6` keys type **, .** (Shift: **< >**); English keeps **\\ /** there. The former ф/щ positions are blank. The extra ё key uses F13 internally and produces nothing in English.

**Cursor → R_C1R5 (EN / RU)** switches language. The website's EN/RU button only previews the map; it does not change the computer's input source.

## macOS

1. Install [Karabiner-Elements](https://karabiner-elements.pqrs.org/), open **Karabiner-Elements** (not just EventViewer), and complete its **Setup** checklist. For version 16, enable **Karabiner-Elements Non-Privileged Agents v2** and **Karabiner-Elements Privileged Daemons v2** under **System Settings → General → Login Items & Extensions**, then follow Setup's Accessibility and Driver Extension prompts. See the [required macOS settings](https://karabiner-elements.pqrs.org/docs/manual/misc/required-macos-settings/). An empty EventViewer **Devices** tab can mean these services are not running; complete Setup before looking for device IDs. [Ukelele](https://software.sil.org/ukelele/) is optional for editing the supplied input layouts.
2. From the repository, install the input-layout bundle:

   ```sh
   just install
   ```

   This copies the bundle and verifies both layouts with macOS's native loader. Existing files are backed up. It requires Apple's command line tools (`xcode-select --install`). A successful check does **not** mean System Settings has refreshed its input-source list.
3. **Log out and back in after installing**, then open **System Settings → Keyboard → Text Input → Edit → +**. Add **Glove80 English 🇬🇧** under English and **Glove80 RussianPC 🇷🇺** under Russian (or search for “Glove80”). The flags are input-menu icons; the names stay unchanged. Select these for daily English/Russian use. Keep **ABC** as a fallback while testing; Glove80 English already preserves QWERTY on the laptop. Disable the Caps Lock language-switch option if using the firmware's dual-Shift Caps behavior.

   On the laptop, Control-Space toggles the two most recently used sources. If it switches ABC ↔ Glove80 English, choose **Glove80 English**, then **Glove80 RussianPC** from the menu bar once. Control-Option-Space cycles through all enabled sources. With the Glove80 rule enabled, its **Cursor → EN / RU** key (or left Ctrl-Space) selects the exact Glove80 English/Russian pair and skips ABC.

   If upgrading an early installation that never appeared, run `just install` and log out again **after** that command. The corrected bundle includes Apple's keyboard-layout document declaration and updated bundle metadata. Reopening Settings or restarting the input-menu process alone may leave the old session list in place.
4. In **Karabiner-EventViewer → Devices**, find Glove80's vendor and product IDs. Generate its rule, replacing `VENDOR_ID:PRODUCT_ID` with those numbers (decimal or `0x` hexadecimal):

   ```sh
   python3 scripts/languages.py --device VENDOR_ID:PRODUCT_ID
   mkdir -p "$HOME/.config/karabiner/assets/complex_modifications"
   cp host/macos/glove80.json "$HOME/.config/karabiner/assets/complex_modifications/"
   ```

   If Bluetooth reports different IDs, repeat `--device VENDOR_ID:PRODUCT_ID` in the same command for that connection. Use IDs observed from Glove80 only.
5. In **Karabiner → Complex Modifications → Add predefined rule**, enable **Glove80: Statica in Russian; laptop keys stay native**. Enable device modification for Glove80. The generated conditions never match the built-in keyboard. Karabiner runs at login and applies the same rules when the device reconnects.

The input layouts retain ordinary laptop QWERTY/ЙЦУКЕН typing. Option is reserved for the US output bank, so native Option accent/dead-key entry is replaced. Command shortcuts keep US key identities. Statica activates only for the supplied Russian source; choosing Apple's stock Russian source will not activate it. Mac thumb positions remain as shown in the map.

To remove: disable the Glove80 rule, select the original input sources, remove the two Glove80 sources in Settings, and remove `Glove80.bundle`. Use the standard firmware if continuing without the host setup.

## Windows

1. Keep Windows' standard **English (United States)** and **Russian** keyboard layouts. Switch using Win-Space. No custom keyboard-layout DLL is required.
2. Install [AutoHotkey v2](https://www.autohotkey.com/). Download [AutoHotInterception](https://github.com/evilC/AutoHotInterception/releases) and the [Interception driver](https://github.com/oblitum/Interception/releases). Follow AHI's [installation guide](https://github.com/evilC/AutoHotInterception#setup): install the driver from an administrator terminal with `install-interception.exe /install`, restart, and assemble the **AHK v2** folder with its `Lib` directory and the required DLLs.
3. Run AHI's `Monitor.ahk` and identify Glove80's VID/PID. Verify it sees events from that connection; start with USB. From a native Windows terminal in this repository, run `just install "C:\path\to\AutoHotInterception\AHK v2"` (install [just](https://github.com/casey/just#installation) and [Python](https://www.python.org/downloads/windows/) first). This copies the helper and mapping files into the prepared folder. WSL is detected as Linux; use PowerShell for Windows host installation.
4. Enter Glove80's VID/PID in the installed `settings.ini`, then run `Glove80.ahk`. The script intercepts only that device, reads the foreground application's English/Russian input language, and sends the corresponding text immediately. The laptop is never intercepted. It waits while Glove80 is absent and checks for reconnection every second.
5. Test English, Russian, punctuation, shortcuts, and unplug/reconnect. To start automatically, place a shortcut to `Glove80.ahk` in the folder opened by **Win-R → `shell:startup`**. To stop, right-click its tray icon and choose **Exit**; remove the startup shortcut to disable automatic launch.

The default `SwapThumbs=1` maps Glove80's **left Command ↔ left Ctrl**, and **right Command → right Ctrl**. Thus the Command thumb positions become the usual Windows Ctrl shortcut positions, and the old left Ctrl position becomes Win. Set `SwapThumbs=0` to retain the Mac modifier arrangement. The map shows these default Windows labels when viewed on Windows.

With `SwapThumbs=1`, **Cursor → EN / RU** becomes Win-Space and cycles Windows input sources. Keep only US English and Russian enabled for a two-language cycle. With `SwapThumbs=0`, the key sends Control-Space; use Win-Space manually instead.

AHI must detect the selected connection in Monitor; Bluetooth support is device/driver-dependent. Its driver has a [known reconnect/hibernate limitation](https://github.com/evilC/AutoHotInterception#known-issues): repeated reconnects can exhaust keyboard IDs and require a reboot. Ordinary text uses Windows Unicode input; applications that require raw keyboard events may need the standard build. For elevated applications, run the helper at the same elevation. The script has not been hardware-tested on Windows.

## Linux

The generated [XKB](https://xkbcommon.org/doc/current/user-configuration.html) definitions can be assigned to Glove80 independently. Install them in the user XKB directory:

```sh
just install
```

For **Sway**, get Glove80's identifier using `swaymsg -t get_inputs`, then add a device-specific block (replace the example identifier) to the Sway configuration:

```text
input "VENDOR:PRODUCT:Glove80" {
    xkb_layout "glove80,glove80"
    xkb_variant "en,ru"
    xkb_options "grp:ctrl_space_toggle"
}
```

Reload Sway. Control-Space or **Cursor → EN / RU** switches Glove80's English/Russian groups. Add another exact device block if Bluetooth uses a different identifier. Leave the laptop's input block unchanged. See [Sway's input configuration](https://man.archlinux.org/man/sway-input.5.en).

GNOME, KDE, and X11 have different device-layout configuration paths; the Sway block is not portable to them. Do not apply this layout globally if the laptop must retain its existing layout. Remove the device block to undo the setup. Linux modifier placement remains the firmware's arrangement.

## Layout source

[Statica-orto-thumb](https://github.com/mohoaz1348-rgb/statica/tree/6a3e1a50fddfda463757d758e1c2437296224ef4), by mohoaz1348-rgb, supplies the Russian arrangement. The Glove80 adaptation keeps Cursor in place and в on the right thumb, with the letter and punctuation changes listed above.

Edit `config/russian.json` and run `just generate` to update the map and host files. After changing positions, regenerate the device-specific Karabiner rule and recopy `layout.tsv` to the Windows helper. Keep the standard MoErgo source in `config/layout.json`; bilingual firmware is derived from it.

For updates, rerun `just install` if the input layouts or icons changed, replace the existing Glove80 rule with its regenerated version, then build and flash both halves using the [installation guide](../README.md#flash-both-halves). Copying a rule into `assets/complex_modifications` alone does not update a rule already enabled in Karabiner.
