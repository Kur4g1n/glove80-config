import copy
import json
import plistlib
import re
import struct
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import languages as lang
import layout

class LanguageTests(unittest.TestCase):
    def test_flag_icons_include_legacy_small_and_retina_images(self):
        for language in ('en','ru'):
            icon=lang.flag_icon(language)
            magic,length=struct.unpack_from('>4sI',icon)
            self.assertEqual(magic,b'icns')
            self.assertEqual(length,len(icon))
            records={}
            offset=8
            while offset<len(icon):
                kind,size=struct.unpack_from('>4sI',icon,offset)
                self.assertGreater(size,8)
                self.assertLessEqual(offset+size,len(icon))
                records[kind]=icon[offset+8:offset+size]
                offset+=size
            self.assertEqual(offset,len(icon))
            # Input Menu needs the legacy RGB/mask pairs at 16 and 32 pixels.
            self.assertEqual(set(records),{b'is32',b's8mk',b'il32',b'l8mk'})
            for size,kind,mask in [(16,b'is32',b's8mk'),(32,b'il32',b'l8mk')]:
                self.assertEqual(len(records[mask]),size*size)
                encoded=iter(records[kind]);rgb=bytearray()
                for count in encoded:
                    if count<128:rgb.extend(next(encoded) for _ in range(count+1))
                    else:rgb.extend([next(encoded)]*(count-125))
                self.assertEqual(len(rgb),3*size*size)
                self.assertEqual(records[mask][0],0)
                center=(size//2)*size+size//2
                color=tuple(rgb[channel*size*size+center] for channel in range(3))
                if language=='en':self.assertGreater(color[0],color[2])
                else:self.assertGreater(color[2],color[0])


    @classmethod
    def setUpClass(cls):
        cls.source=layout.read(ROOT/'config/layout.json')
        cls.palette=layout.read(ROOT/'config/palette.json')

    def test_standard_unchanged_and_bilingual_preserves_controls(self):
        before=copy.deepcopy(self.source)
        self.assertEqual(lang.profile_layout(self.source,'standard'),self.source)
        bilingual=lang.profile_layout(self.source,'bilingual')
        layout.validate(bilingual)
        self.assertEqual(self.source,before)
        for li,row in enumerate(bilingual['layers']):
            self.assertEqual(len(row),80)
            for pos,key in enumerate(row):
                original=self.source['layers'][li][pos]
                if li==0 and lang.positions()[pos] in lang.config()['extra_keys']:
                    self.assertEqual(original['value'],'&none')
                elif key!=original:
                    self.assertIn(li,(2,4))
                    self.assertEqual(key['params'][0]['value'],'RA')
                    self.assertEqual(key['params'][0]['params'],original['params'])
                if pos in {*layout.controls_for(li),64,79}:
                    self.assertEqual(key,original)
        # A bilingual palette bank must retain its encoded bindings too.
        built=layout.build_outputs(self.source,self.palette,'macchiato,qmk','bilingual')
        self.assertIn('&kp RA(LS(N9))',built['config/glove80.keymap'])
        self.assertIn('theme-count = <2>',built['config/glove80.keymap'])

    def test_all_33_letters_and_thumb_adaptation(self):
        pairs=lang.base_pairs(self.source,'ru')
        letters=[v[0] for v in pairs.values() if re.fullmatch('[а-яё]',v[0])]
        self.assertEqual(len(letters),33)
        self.assertEqual(set(letters),set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя'))
        self.assertEqual(pairs['R'],('в','В'))
        self.assertEqual(pairs['F13'],('ё','Ё'))
        self.assertEqual(pairs['W'],('щ','Щ'))
        self.assertEqual(pairs['B'],('ф','Ф'))
        self.assertEqual(pairs['BSLH'],(',','<'))
        self.assertEqual(pairs['FSLH'],('.','>'))
        self.assertNotIn('F14',pairs)
        self.assertNotIn('F15',pairs)

    def test_mac_rules_are_device_scoped_and_ignore_shortcuts_and_output_bank(self):
        devices=[{'vendor_id':0x1234,'product_id':0x5678}]
        rules=lang.karabiner(self.source,devices)['rules'][0]['manipulators']
        desired=lang.base_pairs(self.source,'ru')
        native=lang.native_russian()
        reverse={v[2]:k for k,v in lang.KEYS.items()}
        for rule in rules:
            self.assertEqual(rule['conditions'][0],{'type':'device_if','identifiers':devices})
            if 'select_input_source' in rule['to'][0]:continue
            if len(rule['conditions'])==1:continue
            self.assertEqual(rule['from']['modifiers']['optional'],['shift','caps_lock'])
            target=rule['to'][0]
            pair=('','') if target['key_code']=='vk_none' else (lang.us_pairs() if target.get('modifiers') else native)[reverse[target['key_code']]]
            self.assertEqual(pair,desired[reverse[rule['from']['key_code']]])
        for bad in ([],[{}],[{'vendor_id':-1,'product_id':1}]):
            with self.assertRaises(ValueError):lang.karabiner(self.source,bad)

    def test_cursor_switch_selects_exact_language_pair(self):
        key=self.source['layers'][1][lang.positions().index('R_C1R5')]
        self.assertEqual(layout.expr(key),'&kp LC(SPACE)')
        self.assertEqual(layout.legends(key),('EN / RU',''))
        rules=lang.karabiner(self.source,[{'vendor_id':1,'product_id':2}])['rules'][0]['manipulators'][:2]
        for rule,target,condition in zip(rules,('English','RussianPC'),('input_source_if','input_source_unless')):
            self.assertEqual(rule['from'],{'key_code':'spacebar','modifiers':{'mandatory':['left_control'],'optional':['caps_lock']}})
            self.assertEqual(rule['conditions'][1]['type'],condition)
            self.assertEqual(rule['to'],[{'select_input_source':{'input_source_id':r'^org\.glove80\.inputmethod\.'+target+'$'},'repeat':False}])

    def test_mac_laptop_maps_caps_shortcuts_and_shared_ascii_bank(self):
        outputs=lang.host_outputs(self.source)
        info=plistlib.loads(outputs['host/macos/Glove80.bundle/Contents/Info.plist'].encode())
        self.assertIn('.keyboardlayout.',info['CFBundleIdentifier'])
        for language,name in [('en','English'),('ru','RussianPC')]:
            xml=outputs[f'host/macos/Glove80.bundle/Contents/Resources/Glove80 {name}.keylayout']
            self.assertIn('<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',xml)
            # Apple's .keylayout format uses XML 1.1 control references. Expat
            # is XML 1.0 only; substitute those references for structural parsing.
            safe=re.sub(r'&#x00(?:0[0-8bcef]|1[0-9a-f]);','',xml)
            root=ET.fromstring(safe)
            self.assertIn('KLInfo_'+root.attrib['name'],info)
            icon=outputs[f'host/macos/Glove80.bundle/Contents/Resources/{root.attrib["name"]}.icns']
            self.assertTrue(icon.startswith(b'icns'))
            self.assertFalse(info['KLInfo_'+root.attrib['name']]['TISIconIsTemplate'])
            maps={int(m.attrib['index']):{int(k.attrib['code']):k.attrib['output'] for k in m} for m in root.findall('.//keyMap')}
            expected=lang.us_pairs() if language=='en' else lang.native_russian()
            for code,pair in expected.items():
                if code not in lang.KEYS:continue
                mac=lang.KEYS[code][0]
                for i,(shift,caps) in enumerate([(0,0),(1,0),(0,1),(1,1)]):
                    self.assertEqual(maps[i][mac],pair[shift ^ (caps and pair[0].isalpha())])
                    ascii_pair=lang.us_pairs()[code]
                    self.assertEqual(maps[i+4][mac],ascii_pair[shift ^ (caps and ascii_pair[0].isalpha())])
                self.assertEqual(maps[8][mac],lang.us_pairs()[code][0])
            self.assertEqual(maps[0][0],'a' if language=='en' else 'ф')
            self.assertEqual(maps[0][12],'q' if language=='en' else 'й')

    def test_windows_table_matches_firmware_and_preserves_number_letters(self):
        table=lang.host_outputs(self.source)['host/windows/layout.tsv']
        actual={int(row.split('\t')[0]):[chr(int(c)) if int(c) else '' for c in row.split('\t')[1:]] for row in table.splitlines() if not row.startswith(';')}
        en=lang.base_pairs(self.source,'en');ru=lang.base_pairs(self.source,'ru')
        for code,pair in en.items():
            self.assertEqual(actual[lang.KEYS[code][1]],list((*pair,*ru[code],*lang.us_pairs().get(code,('','')))))
        for code in ('G','J','K'):
            self.assertEqual(actual[lang.KEYS[code][1]][4:],[code.lower(),code])
        self.assertEqual(actual[lang.KEYS['F13'][1]][:2],['',''])

    def test_language_diagram_has_matching_letters_and_unchanged_symbol_layer(self):
        generated=layout.generate(check=True)['docs/layout-data.js']
        data=json.loads(generated.split('window.GLOVE80 = ',1)[1][:-2])
        en=data['languages']['en']['layers'];ru=data['languages']['ru']['layers']
        self.assertEqual(en,data['layers'])
        for label,char in lang.config()['base'].items():
            key=ru[0][lang.positions().index(label)]
            self.assertEqual(key['label'],char)
            if char.isalpha():
                self.assertEqual(key['shifted'],char.upper())
                self.assertEqual(key['role'],'alpha')
        for li in (2,4):
            for pos,key in enumerate(en[li]):
                if not key['transparent']:self.assertEqual(key,ru[li][pos])

if __name__=='__main__':unittest.main()
