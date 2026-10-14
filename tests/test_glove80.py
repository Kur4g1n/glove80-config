import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import glove80

LAYOUT = glove80.Layout()
RUSSIAN = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'


def keymaps(keylayout):
    """modifier string -> {mac keycode: output} from the generated XML."""
    root = ET.fromstring(re.sub(r'&#x00([0-9a-f]{2});', lambda m: chr(int(m[1], 16)) if int(m[1], 16) > 31 else '', keylayout).replace('version="1.1"', 'version="1.0"'))
    selects = {int(s.get('mapIndex')): s.find('modifier').get('keys') for s in root.iter('keyMapSelect')}
    return {selects[int(m.get('index'))]: {int(k.get('code')): k.get('output') for k in m} for m in root.iter('keyMap')}


class Firmware(unittest.TestCase):
    def test_every_layer_has_80_keys_and_colors(self):
        keymap = LAYOUT.keymap()
        for name in LAYOUT.names:
            self.assertIn(f'{name.lower()}_layer', keymap)
        self.assertEqual(keymap.count('&ug 0x'), 80 * len(LAYOUT.names))

    def test_language_switch_and_double_shift_caps(self):
        keymap = LAYOUT.keymap()
        self.assertIn('bindings = <&kp LC(SPACE)>', keymap)
        self.assertRegex(keymap, r'caps \{ key-positions = <52 57>; bindings = <&kp CAPS>;')

    def test_themes_change_colors(self):
        self.assertNotEqual(LAYOUT.keymap('latte'), LAYOUT.keymap('mocha'))

    def test_spare_keycodes_replace_punctuation_on_base_only(self):
        base = [LAYOUT.firmware_key('Base', pos) for pos in range(80)]
        for pos, (code, _) in LAYOUT.spares.items():
            self.assertEqual(base[pos], '&kp ' + code)
        other = [LAYOUT.firmware_key(name, pos) for name in LAYOUT.names[1:] for pos in range(80)]
        self.assertFalse(any(key[4:] in dict(glove80.SPARE) for key in other if key.startswith('&kp ')))

    def test_uf2_rejects_garbage(self):
        path = Path(__file__).with_name('garbage.uf2')
        path.write_bytes(b'\0' * 1024)
        try:
            with self.assertRaises(ValueError):
                glove80.uf2(path)
        finally:
            path.unlink()


class Host(unittest.TestCase):
    maps = keymaps(LAYOUT.keylayout())
    rules = json.loads(LAYOUT.karabiner())['rules'][0]['manipulators']

    def test_russian_source_has_every_letter_once_and_us_symbols(self):
        self.assertEqual(sorted(v for v in self.maps[''].values() if 'а' <= v <= 'я' or v == 'ё'), sorted(RUSSIAN))
        for mods in ('anyShift', 'caps'):
            self.assertEqual(sorted(v for v in self.maps[mods].values() if 'А' <= v <= 'Я' or v == 'Ё'), sorted(RUSSIAN.upper()))
        for char, shifted, mac in glove80.US.values():
            if not char.isalpha() and mac not in {m for _, m in glove80.NATIVE_SPARE.values()}:
                self.assertEqual((self.maps[''][mac], self.maps['anyShift'][mac]), (char, shifted))
        self.assertEqual(self.maps[''][glove80.NUMERO[1]], '№')

    def test_shortcuts_keep_latin_in_russian(self):
        for mods, values in self.maps.items():
            if mods.startswith('command') or mods.startswith('anyControl'):
                self.assertFalse(any('а' <= v.lower() <= 'я' or v.lower() == 'ё' for v in values.values()), mods)

    def glove80_in_russian(self, source):
        """What the Glove80's keycode becomes on the Russian source, as a character."""
        rule = next(r for r in self.rules if r['from']['key_code'] == source and r['conditions'][0]['type'] == 'device_unless' and r['conditions'][1]['type'] == 'input_source_if')
        mac = {glove80.KARABINER.get(c, c.lower()): m for c, (_, _, m) in glove80.US.items()}
        mac.update({glove80.KARABINER[c]: m for c, m in glove80.SPARE + glove80.HOST_SPARE})
        return self.maps[''][mac[rule['to'][0]['key_code']]]

    def test_glove80_types_statica_in_russian(self):
        for pos, char in zip(LAYOUT.russian_positions(), LAYOUT.russian['keys'].values()):
            code = LAYOUT.firmware_key('Base', pos)[4:]
            self.assertEqual(self.glove80_in_russian(glove80.KARABINER.get(code, code.lower())), char, code)

    def test_glove80_spares_type_english_punctuation(self):
        for pos, (spare, _) in LAYOUT.spares.items():
            rule = next(r for r in self.rules if r['from']['key_code'] == glove80.KARABINER[spare] and r['conditions'][1]['type'] == 'input_source_unless')
            key = LAYOUT.layers['Base'][pos]
            self.assertEqual(rule['to'][0]['key_code'], glove80.KARABINER[key[4:]] if key != '&none' else 'vk_none')

    def test_laptop_rules_only_touch_the_built_in_keyboard(self):
        laptop = [r for r in self.rules if r['conditions'][0]['type'] == 'device_if']
        self.assertEqual(len(laptop), len(glove80.NATIVE_SPARE) + len(glove80.NATIVE_SYMBOLS))
        self.assertTrue(all(r['conditions'][0]['identifiers'] == [{'is_built_in_keyboard': True}] for r in laptop))


class Diagram(unittest.TestCase):
    data = LAYOUT.diagram()

    def test_russian_legends_only_on_base_and_inherited_keys(self):
        en, ru = self.data['languages']['en']['layers'], self.data['languages']['ru']['layers']
        self.assertEqual(sum(a['label'] != b['label'] for a, b in zip(en[0], ru[0])), len(LAYOUT.russian['keys']))
        for li in range(1, len(en)):
            for a, b in zip(en[li], ru[li]):
                self.assertTrue(a['transparent'] or a['label'] == b['label'])

    def test_layer_keys_point_at_existing_layers(self):
        targets = {k['target'] for layer in self.data['layers'] for k in layer if k['target'] is not None}
        self.assertTrue(targets <= set(range(len(LAYOUT.names))))
        self.assertIn('layer.locked', self.data['roles'])


if __name__ == '__main__':
    unittest.main()
