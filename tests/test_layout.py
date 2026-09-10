import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import layout as generator
spec=importlib.util.spec_from_file_location('seed',ROOT/'scripts/seed-layout.py')
seed=importlib.util.module_from_spec(spec);spec.loader.exec_module(seed)

class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout=generator.read(ROOT/'config/layout.json')
        cls.palette=generator.read(ROOT/'config/palette.json')
        cls.upstream=generator.read(ROOT/'config/reference/sunaku-v52.json')
    def test_schema_and_generated_artifacts(self):
        generator.validate(self.layout);generator.generate(check=True)
        self.assertEqual([len(x) for x in self.layout['layers']],[80]*5)
    def test_relocated_controls_and_inactive_halves(self):
        base=self.layout['layers'][0]
        self.assertEqual(generator.CONTROLS,{51:1,68:2,75:4})
        self.assertEqual([generator.expr(base[p]) for p in (65,66,67)],['&none','&kp BSLH','&kp FSLH'])
        geometry=generator.read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
        for li,side in ((2,'L_'),(4,'R_')):
            self.assertEqual(sum(k['value']=='&trans' for k in self.layout['layers'][li]),6)
            for pos,g in enumerate(geometry):
                if not g['label'].startswith(side) or pos in {*generator.controls_for(li),64,79}:continue
                key=self.layout['layers'][li][pos]
                if '_T' in g['label']:
                    self.assertEqual(key['value'],'&trans')
                    self.assertEqual(generator.color(self.layout,self.palette,li,pos),generator.color(self.layout,self.palette,0,pos))
                else:
                    self.assertEqual(key['value'],'&none')
                    self.assertEqual(generator.color(self.layout,self.palette,li,pos)['rgb'],'#000000')
    def test_seed_preserves_revised_prototype(self):
        initial,_=seed.seed()
        prototype=generator.read(ROOT/'config/reference/prototype.json')
        for p in range(80):
            if p not in {52,57,64,67,68,75,79}:
                self.assertEqual(generator.expr(initial['layers'][0][p]),generator.expr(prototype['layers'][0][p]))
        self.assertEqual(generator.expr(initial['layers'][1][54]),'&trans')
        self.assertFalse(any('icon' in k.get('decoration',{}) for layer in initial['layers'] for k in layer))
    def test_reference_enthium(self):
        initial,_=seed.seed()
        reference=self.upstream['layers'][0]
        for p in list(range(23,33))+list(range(34,46))+list(range(47,52))+list(range(58,63)):
            want=generator.expr(reference[p])
            if reference[p]['value']=='Custom':
                import re
                want='&kp '+re.search(r'\(([A-Z]+),',want)[1]
            self.assertEqual(generator.expr(initial['layers'][0][p]),want)
        self.assertEqual(generator.expr(initial['layers'][0][74]),'&kp R')
    def test_upstream_active_halves(self):
        initial,palette=seed.seed()
        geometry=generator.read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
        for name,li,side in [('Number',2,'R_'),('Symbol',4,'L_')]:
            source=self.upstream['layers'][self.upstream['layer_names'].index(name)]
            for pos in range(80):
                if pos in {64,67,68,75,79}:continue
                wanted=generator.expr(source[pos]) if geometry[pos]['label'].startswith(side) else '&trans'
                self.assertEqual(generator.expr(initial['layers'][li][pos]),wanted,(name,pos))
    def test_current_active_halves_restore_all_sunaku_keys(self):
        geometry=generator.read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
        for li,name,side in [(2,'Number','R_'),(4,'Symbol','L_')]:
            upstream=self.upstream['layers'][self.upstream['layer_names'].index(name)]
            for pos,g in enumerate(geometry):
                if g['label'].startswith(side) and pos not in (64,79):
                    self.assertEqual(generator.expr(self.layout['layers'][li][pos]),generator.expr(upstream[pos]),(name,pos))
            controls=[p for p,k in enumerate(self.layout['layers'][li]) if generator.expr(k).startswith('&il')]
            self.assertEqual(controls,list(generator.controls_for(li)))
        diagram=json.loads(generator.outputs(self.layout,self.palette)['docs/layout-data.js'].split('window.GLOVE80 = ',1)[1].removesuffix(';\n'))
        self.assertIsNone(diagram['layers'][4][51]['target'])
        self.assertIsNone(diagram['layers'][2][75]['target'])
        self.assertEqual(generator.legends({'value':'&kp','params':[{'value':'A'}]}),('a','A'))
        self.assertEqual(generator.legends({'value':'&kp','params':[{'value':'LS','params':[{'value':'A'}]}]}),('A',''))

    def test_round_trip_and_edits(self):
        exported=json.loads(generator.outputs(self.layout,self.palette)['config/keymap.json'])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'layout.json';path.write_text(generator.dump(exported))
            imported,palette=generator.imported(path)
            self.assertEqual(imported,self.layout);self.assertEqual(palette,self.palette)
            exported['layers'][0][24]['params'][0]['value']='Z'
            exported['layers'][0][24]['decoration'].update(label='Test <key>',background='#123456',color='#ffffff')
            path.write_text(generator.dump(exported));imported,palette=generator.imported(path)
            out=generator.outputs(imported,palette)
            self.assertIn('&kp Z',out['config/glove80.keymap'])
            self.assertIn('&ug 0x123456',out['config/glove80.keymap'])
            self.assertIn('Test \\u003ckey>',out['docs/layout-data.js'])
            diagram=json.loads(out['docs/layout-data.js'].split('window.GLOVE80 = ',1)[1].removesuffix(';\n'))
            self.assertEqual(diagram['roles'][diagram['layers'][0][24]['role']]['background'],'#123456')
            self.assertEqual(json.loads(out['config/keymap.json'])['layers'][0][24],exported['layers'][0][24])
    def test_theme_exports_round_trip_and_keep_bindings(self):
        exports={name:generator.outputs(self.layout,self.palette,name) for name in self.palette['themes']}
        self.assertEqual(self.palette['default_theme'],'macchiato')
        self.assertNotEqual(exports['latte']['config/glove80.keymap'],exports['macchiato']['config/glove80.keymap'])
        for name,out in exports.items():
            exported=json.loads(out['config/keymap.json'])
            self.assertEqual([[generator.expr(k) for k in row] for row in exported['layers']],
                             [[generator.expr(k) for k in row] for row in self.layout['layers']])
            with tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'layout.json';path.write_text(generator.dump(exported))
                imported,palette=generator.imported(path)
                self.assertEqual(imported,self.layout);self.assertEqual(palette,self.palette)
                # Explicit decorations survive a palette round trip.
                exported['layers'][0][24]['decoration'].update(label='Custom Y',background='#123456')
                path.write_text(generator.dump(exported));imported,palette=generator.imported(path)
                again=json.loads(generator.outputs(imported,palette,name)['config/keymap.json'])
                self.assertEqual(again['layers'][0][24],exported['layers'][0][24])
        with self.assertRaises(ValueError):generator.outputs(self.layout,self.palette,'missing')

    def test_selected_palette_banks(self):
        import re
        for names in ('qmk,macchiato','macchiato,mocha','latte,frappe,mocha','mocha,latte,frappe,macchiato','qmk,mocha,latte,frappe,macchiato'):
            selected=names.split(',');result=generator.build_outputs(self.layout,self.palette,names)
            keymap=result['config/glove80.keymap']
            self.assertIn(f'theme-count = <{len(selected)}>;',keymap)
            packed=re.search(r'colors = <(.*?)>;',keymap,re.S)[1].split()
            self.assertEqual(len(packed),401*len(selected))
            for index,name in enumerate(selected):
                source,colors=generator.themed(self.layout,self.palette,name)
                expected=[generator.color(source,colors,li,p)['rgb'].replace('#','0x') for li in range(5) for p in range(80)]
                expected.append(colors['roles']['layer.locked']['rgb'].replace('#','0x'))
                self.assertEqual(packed[index*401:(index+1)*401],expected)
            bindings=re.findall(r'&palette_rgb (\d+) (\d+)',keymap)
            self.assertEqual(len(bindings),400)
            for pos,(index,target) in enumerate(bindings):
                self.assertEqual(int(index),pos)
                self.assertEqual(int(target),generator.controls_for(pos//80).get(pos%80,0))
            self.assertEqual(result['config/keymap.json'],generator.outputs(self.layout,self.palette,selected[0])['config/keymap.json'])
        for selection in ('unknown','all','macchiato,macchiato','mocha,','../mocha',''):
            with self.assertRaises(ValueError):generator.build_outputs(self.layout,self.palette,selection)

    def test_reject_invalid_import(self):
        for kind in ('short','layers','locale','control','timed','inactive'):
            d=copy.deepcopy(self.layout)
            if kind=='short':d['layers'][0].pop()
            elif kind=='layers':d['layer_names'].reverse()
            elif kind=='locale':d['locale']='de-DE'
            elif kind=='control':d['layers'][0][68]={'value':'&none'}
            elif kind=='inactive':d['layers'][2][24]={'value':'&trans'}
            else:d['layers'][0][24]={'value':'&lt','params':[{'value':1},{'value':'Y'}]}
            with self.assertRaises(ValueError):generator.validate(d)
    def test_firmware_versions(self):
        lock=generator.read(ROOT/'firmware.lock.json')
        self.assertIn(lock['revision'],(ROOT/'Dockerfile').read_text())
        self.assertIn('CONFIG_EXPERIMENTAL_RGB_LAYER=y',(ROOT/'config/glove80.conf').read_text())
    def test_native_input(self):
        with tempfile.TemporaryDirectory() as temp:
            for test in ['test_input','test_adapter']:
                cmd=['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-function','-Wno-unused-const-variable',
                     '-I'+str(ROOT/'module/include'),'-I'+str(ROOT/'tests/stubs'),str(ROOT/'module/src/personal_input.c'),str(ROOT/'tests'/f'{test}.c'),'-o',str(Path(temp)/test)]
                subprocess.run(cmd,check=True);subprocess.run([str(Path(temp)/test)],check=True)

if __name__=='__main__':unittest.main()
