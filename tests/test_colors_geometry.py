import hashlib
import json
import math
import re
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import layout

class ColorGeometryTests(unittest.TestCase):
    def test_current_macchiato_palette_and_layer_feedback(self):
        source=layout.read(ROOT/'config/layout.json');palette=layout.read(ROOT/'config/palette.json')
        theme=palette['theme']['colors']
        for li,layer in enumerate(source['layers']):
            for pos,key in enumerate(layer):
                role=palette['roles'][palette['layers'][li][pos]]
                self.assertIn(role['background'],theme.values())
                self.assertTrue(role['label']);self.assertTrue(role['color_name'])
                if key['value']=='&none':self.assertEqual(role['rgb'],'#000000')
                def luminance(color):
                    channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
                    linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in channels]
                    return sum(c*w for c,w in zip(linear,(.2126,.7152,.0722)))
                fg,bg=sorted((luminance(role['foreground']),luminance(role['background'])))
                self.assertGreaterEqual((bg+.05)/(fg+.05),4.5)
            for pos,target in {**layout.controls_for(li),64:3,79:3}.items():
                self.assertEqual(layout.color(source,palette,li,pos)['rgb'],theme['pink' if li==target else 'mauve'])
        for pos,tone in [(24,'teal'),(11,'yellow'),(0,'flamingo'),(67,'green'),(69,'blue'),(55,'blue'),(72,'blue'),(70,'red'),(73,'red')]:
            self.assertEqual(layout.color(source,palette,0,pos)['rgb'],theme[tone])
        for pos in (15,27,39,67):self.assertEqual(layout.expr(source['layers'][1][pos]),'&none')
        keymap=layout.outputs(source,palette,'macchiato')['config/glove80.keymap']
        self.assertIn('locked-color = <'+theme['red'].replace('#','0x')+'>',keymap)
    def test_reference_checksums(self):
        notes=(ROOT/'config/reference/README.md').read_text()
        for path in (ROOT/'config/reference').glob('sunaku-*.json'):
            self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(),notes,path.name)
    def test_active_half_rgb_and_diagram_palettes(self):
        import test_layout
        original,palette=test_layout.seed.seed()
        upstream=layout.read(ROOT/'config/reference/sunaku-v52.json')['custom_devicetree']
        definitions=dict(re.findall(r'#define (\w+)_RGB (0x[\dA-Fa-f]+)',upstream));definitions['___']='0x000000'
        geometry=layout.read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
        for li,name,side in [(2,'Number','R_'),(4,'Symbol','L_')]:
            tokens=re.search(r'\b'+name+r'\s*\{\s*bindings\s*=\s*<(.*?)>',upstream,re.S)[1].split()
            diagram=layout.read(ROOT/f'config/reference/sunaku-{name.lower()}-diagram.json')
            backgrounds={item['c'].lower() for row in diagram if isinstance(row,list) for item in row if isinstance(item,dict) and 'c' in item}
            for pos,g in enumerate(geometry):
                if pos in {64,67,68,75,79} or not g['label'].startswith(side):continue
                actual=layout.color(original,palette,li,pos)
                self.assertEqual(actual['rgb'].lower(),definitions[tokens[pos]].replace('0x','#').lower())
                if tokens[pos]!='___':self.assertIn(actual['background'].lower(),backgrounds)
        for pos,key in enumerate(original['layers'][1]):
            code=key.get('params',[{}])[0].get('value')
            if code in ('HOME','END','PG_UP','PG_DN','LEFT','RIGHT','UP','DOWN'):
                self.assertEqual(layout.color(original,palette,1,pos)['rgb'],'#99f5ff')
    def test_all_catppuccin_flavors_match_official_colors(self):
        source=layout.read(ROOT/'config/layout.json');palette=layout.read(ROOT/'config/palette.json')
        reference=layout.read(ROOT/'config/reference/catppuccin-colors.json')['colors']
        for name,expected in reference.items():
            themed,colors=layout.themed(source,palette,name)
            self.assertEqual(colors['layers'],palette['layers'])
            for role in {r for row in colors['layers'] for r in row}|{'layer.active','layer.locked'}:
                actual=colors['roles'][role];tone=actual['color_name'].lower()
                self.assertEqual(actual['rgb'],'#000000' if tone=='unlit' else expected[tone],(name,role))

    def test_qmk_uses_pinned_sunaku_colors_and_light_azure(self):
        source=layout.read(ROOT/'config/layout.json');palette=layout.read(ROOT/'config/palette.json')
        themed,colors=layout.themed(source,palette,'qmk')
        upstream=layout.read(ROOT/'config/reference/sunaku-v52.json')['custom_devicetree']
        constants={key:value.replace('0x','#').lower() for key,value in re.findall(r'#define (\w+_RGB) (0x[\dA-Fa-f]+)',upstream)}
        self.assertEqual(colors['layers'],palette['layers'])
        used={role for row in colors['layers'] for role in row}|{'layer.active','layer.locked'}
        for name in used:
            role=colors['roles'][name]
            self.assertEqual(role['rgb'],constants[role['source_color']],name)
            if palette['roles'][name]['color_name'] in ('Teal','Sky') and name!='alt':
                self.assertEqual(role['rgb'],'#99f5ff',name)
        for role,token in {'shift':'YLW_RGB','ctrl':'GRN_RGB','alt':'CYN_RGB','cmd':'MAJ_RGB','function':'PNK_RGB'}.items():
            self.assertEqual(colors['roles'][role]['rgb'],constants[token])
        self.assertNotIn('#008080',{colors['roles'][name]['rgb'] for name in used})
        self.assertEqual(palette['default_theme'],'macchiato')

    def test_geometry_has_80_distinct_nonoverlapping_key_faces(self):
        geometry=layout.read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
        self.assertEqual(len({g['label'] for g in geometry}),80)
        by_label={g['label']:g for g in geometry}
        for i,angle in enumerate((25,35,45,25,35,45),1):
            left,right=by_label[f'L_T{i}'],by_label[f'R_T{i}']
            self.assertEqual((left['r'],right['r']),(angle,-angle))
            self.assertEqual(left['y'],right['y'])
            self.assertAlmostEqual(left['x']+right['x'],18.25,places=5)
        polygons=[]
        for g in geometry:
            x,y=g['x'],g['y'];cx,cy=g.get('rx',x+.5),g.get('ry',y+.5);r=math.radians(g.get('r',0))
            polygons.append([(cx+(px-cx)*math.cos(r)-(py-cy)*math.sin(r),cy+(px-cx)*math.sin(r)+(py-cy)*math.cos(r)) for px,py in [(x+.035,y+.035),(x+.965,y+.035),(x+.965,y+.965),(x+.035,y+.965)]])
        def separate(a,b):
            for p in (a,b):
                for i in range(4):
                    dx=p[(i+1)%4][0]-p[i][0];dy=p[(i+1)%4][1]-p[i][1]
                    aa=[x*-dy+y*dx for x,y in a];bb=[x*-dy+y*dx for x,y in b]
                    if max(aa)<=min(bb) or max(bb)<=min(aa):return True
            return False
        for i,a in enumerate(polygons):
            for j in range(i):self.assertTrue(separate(a,polygons[j]),f'Keys {i} and {j} overlap')
