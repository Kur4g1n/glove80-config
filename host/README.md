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
2. Install [AutoHotkey v2](https://www.autohotkey.com/), for example with `winget install --id AutoHotkey.AutoHotkey --exact --source winget --scope user`. Download release ZIPs for [AutoHotInterception](https://github.com/evilC/AutoHotInterception/releases) and the [Interception driver](https://github.com/oblitum/Interception/releases); AHI's source-code ZIP does not contain all the compiled dependencies. In an **administrator PowerShell**, change to the driver's `command line installer` folder and run `./install-interception.exe /install`. **Restart Windows before running Monitor.** Installing the files alone does not load the driver.
3. Assemble a permanent AHI working folder, for example `%LOCALAPPDATA%\Programs\Glove80`, following AHI's [installation guide](https://github.com/evilC/AutoHotInterception#setup). Copy the release's **AHK v2** contents there, copy `Common\Lib\AutoHotInterception.dll` into its `Lib` folder, and copy the driver's `library\x86` and `library\x64` folders into `Lib`. The required files are:

   ```text
   Glove80/
     Monitor.ahk
     Lib/
       AutoHotInterception.ahk
       AutoHotInterception.dll
       CLR.ahk
       x86/interception.dll
       x64/interception.dll
   ```

4. Copy this repository's `host\windows\Glove80.ahk`, `layout.tsv`, and `settings.ini.example` into that working folder. For a first installation, copy `settings.ini.example` to `settings.ini`. Back up existing helper files before updating and preserve your `settings.ini`. **No Python, just, Docker, or firmware build is needed to copy the supplied host files.** Alternatively, with Python installed, run the following from a native Windows terminal in the repository:

   ```powershell
   $env:PYTHONUTF8 = '1'
   python scripts/tasks.py install --directory "C:\path\to\Glove80"
   ```

   UTF-8 mode is needed for the Russian source files on Windows installations whose default Python encoding is not UTF-8. The environment variable also reaches the generator subprocess. If just is installed, `just install "C:\path\to\Glove80"` uses the same installer; set `PYTHONUTF8` there too. The installer copies the files, backs up changed files, and preserves existing settings. WSL is detected as Linux; use native Windows for this step.
5. Open `Monitor.ahk` from the working folder with AutoHotkey v2. Identify the Glove80 row and select **only that keyboard's checkbox**, then press a few physical Glove80 keys and confirm its ID appears in the event list. Simulated typing does not verify this connection. USB is a useful fallback if Bluetooth is absent; connect the left half and select USB on the keyboard. Close Monitor after testing.
6. Configure the verified keyboard in `settings.ini`:

   - If Monitor shows nonzero VID/PID, enter those values and leave `Handle=` empty.
   - **Bluetooth may show `0x0000, 0x0000` despite receiving events.** Use that row's **Handle Copy** button and paste the exact result after `Handle=` instead. A nonempty Handle takes precedence over VID/PID. Do not copy another keyboard's handle, use zero IDs as a wildcard, or substitute IDs from Device Manager: Interception may parse them differently. Use the Copy button rather than transcribing accessibility text, which can double the `&` characters for display.

   USB and Bluetooth can have different handles/IDs. This configuration selects one connection; identify and update it if you change transport. The script looks up the matching device again every second after reconnecting, rather than saving Monitor's temporary numeric device ID.
7. Run `Glove80.ahk` with AutoHotkey v2. It runs in the tray, so **no application window is expected**. It maps only the selected keyboard, reads the focused text editor's input language, and waits if that keyboard is disconnected. Test English and Russian text, Shift, punctuation, thumb shortcuts, and a reconnect. Include Notepad and a browser in the language test. Only after these checks pass, enable startup as described below.

### Opening the helper and enabling startup

The repository's installer **does not create Start menu or desktop shortcuts**, and neither does copying the files. Open `Monitor.ahk` or `Glove80.ahk` directly from your working folder. If double-click opens an editor or the wrong interpreter, use AutoHotkey v2 explicitly. For a per-user installation, an example PowerShell command is:

```powershell
& "$env:LOCALAPPDATA\Programs\AutoHotkey\v2\AutoHotkey64.exe" "$env:LOCALAPPDATA\Programs\Glove80\Glove80.ahk"
```

Replace the script name with `Monitor.ahk` for Monitor. Adjust both paths to your actual installation; an all-users AutoHotkey install may be under Program Files.

For a convenient shortcut, use **Desktop → New → Shortcut**. Set its target to the quoted AutoHotkey v2 executable followed by the quoted full script path, and name it **Start Glove80** or **Glove80 Device Monitor**. Only shortcuts you create will appear on the desktop or in the Start menu.

After testing, copy the **Start Glove80** shortcut into **Win-R → `shell:startup`**. It starts at the current user's sign-in, not immediately when copied. Do not put Monitor in startup. To stop the helper, right-click its AutoHotkey tray icon and choose **Exit**; remove the startup shortcut to disable future automatic launches.

### Language switching and troubleshooting

The default `SwapThumbs=1` maps Glove80's **left Command ↔ left Ctrl**, and **right Command → right Ctrl**. Thus the Command thumb positions become the usual Windows Ctrl shortcut positions, and the old left Ctrl position becomes Win. Set `SwapThumbs=0` to retain the Mac modifier arrangement. The map shows these default Windows labels when viewed on Windows.

With `SwapThumbs=1`, **Cursor → EN / RU** becomes Win-Space and cycles Windows input sources. Keep only US English and Russian enabled for a two-language cycle. With `SwapThumbs=0`, the key sends Control-Space; use Win-Space manually instead.

If the Windows language indicator changes but Notepad keeps typing in the old language, update the installed `Glove80.ahk` and restart the helper. Modern Notepad can host its editor on a different thread from its main window. The helper uses [GetGUIThreadInfo](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getguithreadinfo) to find the focused editor before querying its keyboard layout; older copies queried only the main window. The Windows indicator changing alone does not verify the helper's language detection.

AHI must detect physical events from the selected connection in Monitor; Bluetooth support is device/driver-dependent. Bluetooth input and English/Russian switching, including the Notepad fix, were verified on one Windows PC with AutoHotkey 2.0.27, AutoHotInterception 0.9.2, and Interception 1.0.1. This does not establish compatibility with every Bluetooth driver. Interception has a [known reconnect/hibernate limitation](https://github.com/evilC/AutoHotInterception#known-issues): repeated reconnects can exhaust keyboard IDs and require a reboot. English keys use normal scan-code down/up events, including held keys and the Number/Symbol output bank; Russian text still uses Windows Unicode input. Select English for gameplay. Earlier helper versions injected English as Unicode too, which caused Genshin Impact to ignore letters while recognizing thumb keys. Updating and restarting the helper resolved that issue on the tested PC. For elevated applications, run the helper at the same elevation.

To remove the setup, exit the helper and remove its startup shortcut. Run `./install-interception.exe /uninstall` from the driver's installer folder in an administrator PowerShell, then restart. AutoHotkey can be removed through Windows Installed apps if nothing else uses it. Use the standard firmware when continuing without the bilingual helper.

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

## Games

Select English before gameplay and test movement while holding and releasing keys, combinations with Shift/Ctrl, and in-game text chat separately. Games can bind physical key positions instead of displayed letters, so an Enthium layout may require rebinding controls.

- **Windows:** use the current helper. English preserves normal scan-code events and the thumb swap; the former Unicode-only English output was incompatible with Genshin Impact on the tested PC. Russian text remains Unicode-based and is not intended for gameplay controls.
- **macOS:** choose **Glove80 English**. Ordinary English letters retain the firmware's native key identities; the generated Karabiner Statica letter rules are restricted to **Glove80 RussianPC**. English uses a native keyboard layout, not text injection. The dedicated language-switch chord and reserved F13–F15 signals are still handled by Karabiner. The Number/Symbol bank uses Option, which a game may also treat as a modifier.
- **Linux:** choose the English group of the device-specific XKB layout. It maps native key events to US symbols rather than injecting text. The Number/Symbol bank uses the right-Alt level selector; handling of that modifier and device-specific configuration depends on the compositor and game.

Automated checks cover English mapping identities, macOS Russian-only letter rules, and Linux English symbols. These checks are not macOS/Linux gameplay tests or a guarantee for every game. If a game rejects a remapped/virtual keyboard, use the standard firmware with a stock US input layout and disable the helper for that device through its normal settings.

## Layout source

[Statica-orto-thumb](https://github.com/mohoaz1348-rgb/statica/tree/6a3e1a50fddfda463757d758e1c2437296224ef4), by mohoaz1348-rgb, supplies the Russian arrangement. The Glove80 adaptation keeps Cursor in place and в on the right thumb, with the letter and punctuation changes listed above.

Edit `config/russian.json` and run `just generate` to update the map and host files. After changing positions, regenerate the device-specific Karabiner rule and recopy `layout.tsv` to the Windows helper. Keep the standard MoErgo source in `config/layout.json`; bilingual firmware is derived from it.

For updates, rerun `just install` if the input layouts or icons changed, replace the existing Glove80 rule with its regenerated version, then build and flash both halves using the [installation guide](../README.md#flash-both-halves). Copying a rule into `assets/complex_modifications` alone does not update a rule already enabled in Karabiner.
