#!/usr/bin/env python3
"""Generate the ZMK keymap, the macOS keylayout and the diagram data from config/.

    glove80.py generate            write config/glove80.keymap, host/, docs/layout-data.js
    glove80.py check               validate config/ and fail if generated files are stale
    glove80.py keymap [--theme t]  print the keymap for a theme
    glove80.py uf2 FILE            validate a Glove80 UF2 file
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROWS = [10, 12, 12, 12, 18, 16]

# ZMK keycode: (character, shifted character, macOS virtual keycode).
US = {}
for code, mac in zip('ASDFHGZXCVBQWERYTOUIPLJKNM', [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 31, 32, 34, 35, 37, 38, 40, 45, 46]):
    US[code] = (code.lower(), code, mac)
for digit, shifted, mac in zip('1234567890', '!@#$%^&*()', [18, 19, 20, 21, 23, 22, 26, 28, 25, 29]):
    US['N' + digit] = (digit, shifted, mac)
for code, pair, mac in [('MINUS', '-_', 27), ('EQUAL', '=+', 24), ('LBKT', '[{', 33), ('RBKT', ']}', 30),
                        ('BSLH', '\\|', 42), ('SEMI', ';:', 41), ('SQT', '\'"', 39), ('GRAVE', '`~', 50),
                        ('COMMA', ',<', 43), ('DOT', '.>', 47), ('FSLH', '/?', 44)]:
    US[code] = (pair[0], pair[1], mac)
KARABINER = {'MINUS': 'hyphen', 'EQUAL': 'equal_sign', 'LBKT': 'open_bracket', 'RBKT': 'close_bracket', 'BSLH': 'backslash',
             'SEMI': 'semicolon', 'SQT': 'quote', 'GRAVE': 'grave_accent_and_tilde', 'COMMA': 'comma', 'DOT': 'period', 'FSLH': 'slash',
             'INT1': 'international1', **{f'F{n}': f'f{n}' for n in range(13, 21)}}
# Keycodes that mean nothing in stock macOS layouts. The Base layer sends them at positions that hold a Cyrillic
# letter on a punctuation key, and the Russian keylayout uses them for the seven ЙЦУКЕН letters on punctuation keys.
SPARE = [('F13', 105), ('F14', 107), ('F15', 113), ('F16', 106), ('F17', 64), ('F18', 79), ('F19', 80), ('F20', 90), ('INT1', 94)]
# Apple's Russian – PC letter positions; the laptop keeps them.
NATIVE = dict(zip('QWERTYUIOP', 'йцукенгшщз'), **dict(zip('ASDFGHJKL', 'фывапролд')), **dict(zip('ZXCVBNM', 'ячсмить')),
              LBKT='х', RBKT='ъ', SEMI='ж', SQT='э', COMMA='б', DOT='ю', GRAVE='ё')
NATIVE_SPARE = dict(zip(['LBKT', 'RBKT', 'SEMI', 'SQT', 'COMMA', 'DOT', 'GRAVE'], SPARE))
NUMERO = SPARE[7]  # № for the laptop's Shift-3
# Laptop keys whose Russian – PC symbol lives on another US key: (shift held?, key) -> (key, shift?).
NATIVE_SYMBOLS = {(True, 'N2'): ('SQT', True), (True, 'N3'): (NUMERO[0], False), (True, 'N4'): ('SEMI', False), (True, 'N6'): ('SEMI', True),
                  (True, 'N7'): ('FSLH', True), (False, 'FSLH'): ('DOT', False), (True, 'FSLH'): ('COMMA', False), (True, 'BSLH'): ('FSLH', False)}
# Non-text keys every macOS keylayout defines (same characters as Apple's U.S. layout).
FIXED = {36: '\r', 48: '\t', 49: ' ', 51: '\b', 53: '\x1b', 76: '\x03', 117: '\x7f', 114: '',
         123: '', 124: '', 125: '', 126: '', 115: '', 119: '', 116: '', 121: ''}
FIXED.update({mac: chr(0xf704 + i) for i, mac in enumerate([122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111])})

LABELS = {'SPACE': 'Space', 'ESC': 'Esc', 'RET': 'Enter', 'BSPC': '⌫', 'DEL': 'Del', 'INS': 'Ins', 'TAB': 'Tab',
          'LGUI': '⌘', 'RGUI': '⌘', 'LCTRL': 'Ctrl', 'RCTRL': 'Ctrl', 'LALT': '⌥', 'RALT': '⌥', 'LSHFT': '⇧', 'RSHFT': '⇧',
          'HOME': 'Home', 'END': 'End', 'PG_UP': 'PgUp', 'PG_DN': 'PgDn', 'LEFT': '←', 'RIGHT': '→', 'UP': '↑', 'DOWN': '↓',
          'PSCRN': 'PrtSc', 'SCROLLLOCK': 'Scroll', 'PAUSE_BREAK': 'Pause', 'C_MUTE': 'Mute', 'C_VOL_DN': 'Vol −',
          'C_VOL_UP': 'Vol +', 'C_BRI_DN': '☀ −', 'C_BRI_UP': '☀ +', 'C_PREV': '⏮', 'C_NEXT': '⏭', 'C_PP': '⏯',
          'RGB_SPI': 'Speed +', 'RGB_SPD': 'Speed −', 'RGB_SAI': 'Sat +', 'RGB_SAD': 'Sat −', 'RGB_HUI': 'Hue +',
          'RGB_HUD': 'Hue −', 'RGB_BRI': 'Light +', 'RGB_BRD': 'Light −', 'RGB_TOG': 'RGB', 'RGB_EFF': 'Effect',
          'BT_CLR': 'Clear BT', 'BT_CLR_ALL': 'Clear all', 'OUT_USB': 'USB', '&bootloader': 'Boot', '&sys_reset': 'Reset',
          '&caps_word': 'Caps', '&lang': 'EN / RU', '&bt0': 'BT 0', '&bt1': 'BT 1', '&bt2': 'BT 2', '&bt3': 'BT 3'}
ROLES = [('&kp [LR]GUI', 'cmd'), ('&kp [LR]CTRL', 'ctrl'), ('&kp [LR]ALT', 'alt'), ('&kp [LR]SHFT', 'shift'), ('&caps_word', 'shift'),
         ('&kp (LS\\()?[A-Z]\\)?', 'alpha'), ('&kp N[0-9]', 'digit'), ('&kp F([1-9]|1[0-2])', 'function'),
         ('&kp (SPACE|TAB|RET)', 'space'), ('&kp (ESC|BSPC|DEL)', 'edit'), ('&kp (INS|HOME|END|PG_UP|PG_DN|LEFT|RIGHT|UP|DOWN)', 'navigation'),
         ('&kp (C_|PSCRN|SCROLLLOCK|PAUSE).*', 'media'), ('&kp .*', 'symbol'), ('&(mo|tog|magic) .*', 'layer'), ('&lang', 'lang'),
         ('&(bt|out).*', 'bluetooth'), ('&rgb_ug .*', 'rgb'), ('&(bootloader|sys_reset)', 'system'), ('&none', 'blank')]


def read(name):
    return json.loads((ROOT / 'config' / name).read_text())


def flat(rows):
    return [key for row in rows for key in row]


class Layout:
    def __init__(self):
        self.source = read('layout.json')
        self.geometry = read('geometry.json')
        self.russian = read('russian.json')
        self.theme = read('theme.json')
        self.names = list(self.source['layers'])
        self.layers = {name: flat(rows) for name, rows in self.source['layers'].items()}
        self.labels = [g['label'] for g in self.geometry]
        self.validate()
        self.spares = {}  # position -> (ZMK keycode, macOS keycode) replacing US punctuation on Base
        pool = iter(SPARE)
        for pos in self.russian_positions():
            if not re.fullmatch('&kp [A-Z]', self.layers['Base'][pos]):
                self.spares[pos] = next(pool, None) or self.fail('Too many Russian letters on non-letter keys; the spare keycode pool is exhausted')

    def fail(self, message):
        raise ValueError(message)

    def validate(self):
        if len(self.labels) != 80 or len(set(self.labels)) != 80:
            self.fail('geometry.json must list 80 distinct keys')
        for name, rows in self.source['layers'].items():
            if [len(row) for row in rows] != ROWS:
                self.fail(f'Layer {name}: rows must have {ROWS} keys')
        if '&trans' in self.layers[self.names[0]]:
            self.fail('The first layer cannot contain &trans')
        for name, keys in self.layers.items():
            for key in keys:
                for target in re.findall(r'LAYER_(\w+)', key):
                    if target not in self.names:
                        self.fail(f'Layer {name}: unknown layer {target} in {key}')
        chars = list(self.russian['keys'].values())
        if len(set(chars)) != len(chars):
            self.fail('russian.json assigns the same character twice')
        for label in self.russian['keys']:
            if label not in self.labels:
                self.fail('russian.json: unknown key ' + label)
            key = self.layers['Base'][self.labels.index(label)]
            if key != '&none' and not (key.startswith('&kp ') and key[4:] in US):
                self.fail(f'russian.json: {label} must hold a plain US key or &none on Base, not {key}')

    def russian_positions(self):
        return [self.labels.index(label) for label in self.russian['keys']]

    def firmware_key(self, name, pos):
        key = self.layers[name][pos]
        if name == self.names[0] and pos in self.spares:
            return '&kp ' + self.spares[pos][0]
        return key

    def role(self, name, pos):
        key = self.layers[name][pos]
        if key == '&trans':
            return self.role(self.names[0], pos)
        return next(role for pattern, role in ROLES if re.fullmatch(pattern, key))

    def colors(self, flavor):
        palette = self.theme['flavors'][flavor]
        return {role: palette[color] if color else None for role, (color, label) in self.theme['roles'].items()}

    # ---- outputs -------------------------------------------------------------------

    def keymap(self, flavor=None):
        colors = self.colors(flavor or self.theme['default'])
        lines = ['/* Generated by `just generate` from config/. Do not edit. */', '#include <behaviors.dtsi>']
        lines += [f'#include <dt-bindings/zmk/{h}.h>' for h in ('keys', 'bt', 'outputs', 'rgb')]
        lines += [f'#define LAYER_{name} {i}' for i, name in enumerate(self.names)]
        lines += ['/ {', (ROOT / 'config/behaviors.dtsi').read_text().rstrip(), '    keymap {', '        compatible = "zmk,keymap";']
        for name in self.names:
            lines += [f'        {name.lower()}_layer {{', f'            label = "{name}";', '            bindings = <']
            lines += self.rows([self.firmware_key(name, pos) for pos in range(80)])
            lines += ['            >;', '        };']
        shifts = [pos for pos, key in enumerate(self.layers[self.names[0]]) if key in ('&kp LSHFT', '&kp RSHFT')]
        lines += ['    };', '    combos {', '        compatible = "zmk,combos";',
                  f'        caps {{ key-positions = <{" ".join(map(str, shifts))}>; bindings = <&kp CAPS>; layers = <0>; }};',
                  '    };', '    underglow-layer {', '        compatible = "zmk,underglow-layer";']
        for i, name in enumerate(self.names):
            lines += [f'        {name.lower()}_rgb {{', f'            layer-id = <{i}>;', '            bindings = <']
            lines += self.rows(['&ug 0x' + (colors[self.role(name, pos)] or '#000000')[1:] for pos in range(80)])
            lines += ['            >;', '        };']
        lines += ['    };', '};', '']
        return '\n'.join(lines)

    @staticmethod
    def rows(keys):
        start, lines = 0, []
        for n in ROWS:
            lines.append('                ' + '  '.join(keys[start:start + n]))
            start += n
        return lines

    def russian_table(self):
        """macOS keycode -> (character, shifted) of the Glove80 Russian input source: ЙЦУКЕН letters, US everything else."""
        table = {}
        for code, (char, shifted, mac) in US.items():
            if code in NATIVE_SPARE:
                table[NATIVE_SPARE[code][1]] = (NATIVE[code], NATIVE[code].upper())
                table[mac] = (char, shifted)
            elif code in NATIVE:
                table[mac] = (NATIVE[code], NATIVE[code].upper())
            else:
                table[mac] = (char, shifted)
        table[NUMERO[1]] = ('№', '№')
        return table

    def keylayout(self):
        table = self.russian_table()
        latin = {mac: char for char, _, mac in US.values()}
        control = {mac: chr(ord(char.upper()) - 64) for mac, char in latin.items() if char.isalpha()}
        def caps(shift):
            return {mac: pair[shift != pair[0].isalpha()] for mac, pair in table.items()}
        maps = [('', {m: p[0] for m, p in table.items()}), ('anyShift', {m: p[1] for m, p in table.items()}),
                ('caps', caps(False)), ('anyShift caps', caps(True)),
                ('command anyShift? anyOption? anyControl? caps?', latin), ('anyControl anyShift? anyOption? caps?', {**latin, **control})]
        def escaped(value):
            return ''.join(f'&#x{ord(c):04x};' if ord(c) < 32 else c.replace('&', '&amp;').replace('<', '&lt;').replace('"', '&quot;') for c in value)
        lines = ['<?xml version="1.1" encoding="UTF-8"?>',
                 '<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',
                 '<!-- Generated by `just generate` from config/. -->',
                 '<keyboard group="126" id="-28081" name="Glove80 Russian" maxout="1">',
                 '<layouts><layout first="0" last="255" mapSet="maps" modifiers="modifiers"/></layouts>',
                 '<modifierMap id="modifiers" defaultIndex="0">']
        lines += [f'<keyMapSelect mapIndex="{i}"><modifier keys="{mods}"/></keyMapSelect>' for i, (mods, _) in enumerate(maps)]
        lines += ['</modifierMap>', '<keyMapSet id="maps">']
        for i, (_, values) in enumerate(maps):
            lines.append(f'<keyMap index="{i}">')
            lines += [f'<key code="{mac}" output="{escaped(out)}"/>' for mac, out in sorted({**FIXED, **values}.items())]
            lines.append('</keyMap>')
        return '\n'.join(lines + ['</keyMapSet>', '</keyboard>', ''])

    def bundle_plist(self):
        import plistlib
        return plistlib.dumps({'CFBundleIdentifier': 'org.glove80.keyboardlayout.glove80', 'CFBundleName': 'Glove80', 'CFBundleVersion': '4',
                               'KLInfo_Glove80 Russian': {'TISInputSourceID': 'org.glove80.inputmethod.Russian', 'TISIntendedLanguage': 'ru'}},
                              sort_keys=False).decode()

    def karabiner(self):
        """Per-device rules: Glove80 letters follow Statica in Russian; the laptop keeps ЙЦУКЕН; spare keycodes get their meaning."""
        def name(code):
            return KARABINER.get(code, code[1:] if re.fullmatch('N[0-9]', code) else code.lower())
        def rule(src, dst, conditions, shift=None, to_shift=False):
            modifiers = {'optional': ['shift', 'caps_lock'] if shift is None else ['caps_lock']}
            if shift:
                modifiers['mandatory'] = ['shift']
            return {'type': 'basic', 'from': {'key_code': src, 'modifiers': modifiers},
                    'to': [{'key_code': dst, **({'modifiers': ['shift']} if to_shift else {})}], 'conditions': conditions}
        russian = {'type': 'input_source_if', 'input_sources': [{'input_source_id': '^org\\.glove80\\.inputmethod\\.Russian$'}]}
        english = {**russian, 'type': 'input_source_unless'}
        glove80 = {'type': 'device_unless', 'identifiers': [{'is_built_in_keyboard': True}]}
        laptop = {**glove80, 'type': 'device_if'}
        where = {char: name(NATIVE_SPARE[code][0] if code in NATIVE_SPARE else code) for code, char in NATIVE.items()}
        where.update({',': 'comma', '.': 'period'})
        rules = []
        for pos, char in zip(self.russian_positions(), self.russian['keys'].values()):
            rules.append(rule(name(self.firmware_key('Base', pos)[4:]), where[char] if char else 'vk_none', [glove80, russian]))
        for pos, (spare, _) in self.spares.items():
            key = self.layers['Base'][pos]
            rules.append(rule(name(spare), name(key[4:]) if key != '&none' else 'vk_none', [glove80, english]))
        for code, (spare, _) in NATIVE_SPARE.items():
            rules.append(rule(name(code), name(spare), [laptop, russian]))
        for (shift, code), (target, to_shift) in NATIVE_SYMBOLS.items():
            rules.append(rule(name(code), name(target), [laptop, russian], shift=shift, to_shift=to_shift))
        return json.dumps({'title': 'Glove80', 'rules': [{'description': 'Glove80: Statica in Russian; laptop keys stay native', 'manipulators': rules}]},
                          ensure_ascii=False, indent=1) + '\n'

    def legend(self, key):
        if key in ('&none', '&trans'):
            return ('', '')
        if key in LABELS:
            return (LABELS[key], '')
        if m := re.fullmatch(r'&kp LS\((\w+)\)', key):
            return (US[m[1]][1] if m[1] in US else LABELS.get(m[1], m[1]), '')
        if m := re.fullmatch(r'&kp (\w+)', key):
            return US[m[1]][:2] if m[1] in US else (LABELS.get(m[1], m[1]), '')
        if m := re.fullmatch(r'&(mo|tog|magic) LAYER_(\w+).*', key):
            return (m[2], '')
        if m := re.fullmatch(r'&\w+ (\w+).*', key):
            return (LABELS.get(m[1], m[1]), '')
        return (key, '')

    def diagram(self):
        layers = []
        for name in self.names:
            keys = []
            for pos, key in enumerate(self.layers[name]):
                source = self.layers['Base'][pos] if key == '&trans' else key
                label, shifted = self.legend(source)
                entry = {'label': label, 'shift': shifted, 'role': self.role(name, pos)}
                if key == '&trans':
                    entry['inherited'] = True
                if m := re.fullmatch(r'&(mo|tog|magic) LAYER_(\w+).*', source):
                    entry['layer'] = m[2]
                    entry['lock'] = m[1] == 'tog'
                if name == self.names[0] and self.labels[pos] in self.russian['keys']:
                    char = self.russian['keys'][self.labels[pos]]
                    entry['ru'] = char
                    entry['ruShift'] = char.upper() if char.isalpha() else next(s for c, s, _ in US.values() if c == char)
                keys.append(entry)
            layers.append({'name': name, 'keys': keys})
        return {'name': self.source['name'], 'russian': self.russian['name'], 'rows': ROWS, 'geometry': self.geometry,
                'layers': layers, 'roles': {role: label for role, (_, label) in self.theme['roles'].items()},
                'colors': {flavor: self.colors(flavor) for flavor in self.theme['flavors']},
                'flavors': self.theme['flavors'], 'default': self.theme['default']}

    def outputs(self):
        bundle = 'host/Glove80.bundle/Contents/'
        return {'config/glove80.keymap': self.keymap(), bundle + 'Info.plist': self.bundle_plist(),
                bundle + 'Resources/Glove80 Russian.keylayout': self.keylayout(), 'host/glove80.json': self.karabiner(),
                'docs/layout-data.js': 'window.GLOVE80 = ' + json.dumps(self.diagram(), ensure_ascii=False).replace('<', '\\u003c') + ';\n'}


def uf2(path):
    data = Path(path).read_bytes()
    halves = {}
    if not data or len(data) % 512:
        raise ValueError(f'{path} is not a complete UF2 file')
    for offset in range(0, len(data), 512):
        magic0, magic1, flags, _, _, index, total, family = struct.unpack_from('<8I', data, offset)
        if (magic0, magic1) != (0x0A324655, 0x9E5D5157) or not flags & 0x2000 or family not in (0x9807B007, 0x9808B007):
            raise ValueError(f'{path} is not Glove80 firmware')
        halves.setdefault(family, (total, set()))[1].add(index)
    if len(halves) != 2 or any(len(indices) != total for total, indices in halves.values()):
        raise ValueError(f'{path} must contain every block of both halves')
    print(f'{path}: {len(data):,} bytes, both halves')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=['generate', 'check', 'keymap', 'uf2'])
    parser.add_argument('file', nargs='?')
    parser.add_argument('--theme')
    args = parser.parse_args()
    try:
        if args.command == 'uf2':
            return uf2(args.file or parser.error('uf2 needs a file'))
        layout = Layout()
        if args.command == 'keymap':
            return print(layout.keymap(args.theme), end='')
        stale = []
        for name, content in layout.outputs().items():
            path = ROOT / name
            if args.command == 'check':
                if not path.exists() or path.read_text() != content:
                    stale.append(name)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        if stale:
            raise ValueError('Stale generated files, run `just generate`: ' + ', '.join(stale))
        print(f'{args.command}: {len(layout.names)} layers, {len(layout.russian["keys"])} Russian keys, {len(layout.spares)} spare keycodes')
    except (ValueError, KeyError, StopIteration, OSError) as error:
        sys.exit(f'Error: {error}')


if __name__ == '__main__':
    main()
