#!/usr/bin/env python3
"""Build the original personal layout from pinned references (not run by generate)."""
import copy
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def binding(value, *params):
    return {'value': value, **({'params': [{'value': p} for p in params]} if params else {})}

def seed():
    source = json.loads((ROOT / 'config/reference/sunaku-v52.json').read_text())
    layout = json.loads((ROOT / 'config/reference/prototype.json').read_text())
    rgb_source = source['custom_devicetree']
    rgb_values = dict(re.findall(r'#define (\w+)_RGB (0x[\dA-Fa-f]+)', rgb_source))
    rgb_values['___'] = '0x000000'
    roles = {}
    color_layers = []
    layers = layout['layers']
    controls = {67: 2, 68: 1, 75: 4}
    info = json.loads((ROOT / 'config/info.json').read_text())['layouts']['LAYOUT']['layout']
    def add_role(name, rgb, background):
        roles[name] = {'rgb': rgb, 'background': background, 'foreground': '#20232a'}
        return name
    basic = {
        'blank': ('#000000', '#29333b'), 'alpha': ('#ffffff', '#edf0f2'),
        'digit': ('#ffd900', '#fff3e0'), 'function': ('#ff80bf', '#fce4ec'),
        'edit': ('#ff7c4d', '#ffccbc'), 'shift': ('#ffff00', '#fff59d'),
        'ctrl': ('#00ff00', '#c8e6c9'), 'alt': ('#00ffff', '#b2ebf2'),
        'cmd': ('#ff00ff', '#f3c6f1'), 'layer': ('#6b1fce', '#d1c4e9'),
        'navigation': ('#99f5ff', '#e0f2f1'), 'media': ('#ff80bf', '#fce4ec'),
        'connection': ('#00ff80', '#dcedc8'), 'lighting': ('#ffd900', '#ffecb3'),
        'danger': ('#ff0000', '#ffcdd2'), 'lock': ('#ffff00', '#fff59d')}
    for name, (rgb, bg) in basic.items(): add_role(name, rgb, bg)
    roles['blank']['foreground'] = '#ced6dc'
    # Cursor functions keep Sunaku's color when moved. New media/brightness
    # positions take their colors from his Function layer.
    cursor_colors = {}
    cursor_screen = {'COR':'#ffccbc','AZU':'#e0f2f1','BLU':'#e0f2f1','CHU':'#e8f5e9'}
    for name in ('Cursor','Function'):
        tokens = re.search(r'\b'+name+r'\s*\{\s*bindings\s*=\s*<(.*?)>', rgb_source, re.S)[1].split()
        for key, token in zip(source['layers'][source['layer_names'].index(name)], tokens):
            if key['value'] == 'Custom':
                raw = key['params'][0]['value']
                if raw not in ('&kp _HOME','&kp _END'): continue
                code = raw.split()[1]
            elif key['value'] == '&kp':
                code = str(key.get('params',[{}])[0].get('value',''))
            else: continue
            if token not in cursor_screen: continue
            role = 'cursor.'+token.lower()
            add_role(role, '#'+rgb_values[token][2:].lower(), cursor_screen[token])
            cursor_colors.setdefault(code.removeprefix('_'),role)
    screen = {
        'Number': {'GDN':'#fff3e0','GOL':'#fff3e0','TEA':'#e0f2f1','SPG':'#e8f5e9','___':'#29333b'},
        'Symbol': {'COR':'#c5cae9','PNK':'#ffcdd2','AZU':'#bbdefb','CHU':'#c8e6c9',
                   'PUR':'#d1c4e9','GDN':'#ffecb3','SPG':'#dcedc8','BLU':'#c5cae9','___':'#29333b'}}
    upstream_colors = {}
    for name in ('Number', 'Symbol'):
        tokens = re.search(r'\b'+name+r'\s*\{\s*bindings\s*=\s*<(.*?)>', rgb_source, re.S)[1].split()
        assert len(tokens) == 80
        upstream_colors[name] = []
        for token in tokens:
            role = name.lower()+'.'+token.lower()
            rgb = '#'+rgb_values[token][2:].lower()
            add_role(role, rgb, screen[name].get(token, '#d7ccc8'))
            upstream_colors[name].append(role)
    # Sunaku's Symbol map contains a colored blank and one special '..' macro.
    # Both are copied as colors; the Magic corner overrides the macro itself.
    for name, index, side in [('Number',2,'R_'),('Symbol',4,'L_')]:
        src = source['layers'][source['layer_names'].index(name)]
        layers[index] = [copy.deepcopy(src[p]) if info[p]['label'].startswith(side)
                         else binding('&trans') for p in range(80)]
    layers[1][54] = binding('&trans') # old Cursor exit was now the dedicated Ctrl key
    for layer in layers:
        for key in layer: key.pop('decoration', None)
    layers[0][52] = binding('Custom', '&ish LSHFT')
    layers[0][57] = binding('Custom', '&ish RSHFT')
    for layer in layers:
        for pos,target in controls.items(): layer[pos] = binding('Custom', f'&il LAYER_{layout["layer_names"][target]}')
        for pos in (64,79): layer[pos] = binding('Custom', '&im')
    # Ordinary firmware-owned behaviors remain readable in MoErgo.
    for key in layers[3]:
        if key['value'] == '&reset': key['value'] = '&sys_reset'
    # Base punctuation takes its symbol-layer family, using unshifted codes.
    punct = {'SQT':'symbol.pnk','GRAVE':'symbol.pnk','LBKT':'symbol.azu','RBKT':'symbol.azu',
             'BSLH':'symbol.pur','EQUAL':'symbol.spg','MINUS':'symbol.spg',
             'COMMA':'symbol.chu','DOT':'symbol.chu','SEMI':'symbol.chu','FSLH':'symbol.gdn'}
    def base_role(key):
        if key['value'] in ('&none','&trans'): return 'blank'
        text = str(key)
        if key['value'] == 'Custom': return 'shift' if '&ish' in text else 'layer'
        code = str(key.get('params',[{}])[0].get('value',''))
        if re.fullmatch(r'F\d+',code):return 'function'
        if re.fullmatch(r'N\d',code):return 'digit'
        if len(code)==1 and code.isalpha():return 'alpha'
        if code.endswith('GUI'):return 'cmd'
        if code.endswith('CTRL'):return 'ctrl'
        if code.endswith('ALT'):return 'alt'
        return punct.get(code,'edit')
    for li,layer in enumerate(layers):
        colors=[]
        for pos,key in enumerate(layer):
            if pos in controls or pos in (64,79): role='layer'
            elif li==0:role=base_role(key)
            elif key['value']=='&trans':role=color_layers[0][pos]
            elif li in (2,4):role=upstream_colors[layout['layer_names'][li]][pos]
            elif key['value']=='&none':role='blank'
            elif li==3:
                role='lighting' if key['value']=='&rgb_ug' else 'danger' if key['value'] in ('&bootloader','&sys_reset') else 'connection'
            else:
                code=key.get('params',[{}])[0].get('value','')
                role=cursor_colors.get(code,'lock' if code in ('CAPS','SCROLLLOCK') else 'edit')
            colors.append(role)
        color_layers.append(colors)
    layout.update(title='Qr4g1n · Enthium v14', uuid='', parent_uuid='f38069dc-cf2d-4a1a-a02b-f1a2bfb33253',
                  notes='', tags=['Enthium','v14','macOS'], date=1789046400,
                  custom_defined_behaviors='',custom_devicetree='',
                  config_parameters=[{'paramName':'EXPERIMENTAL_RGB_LAYER','value':'y'}])
    for li,layer in enumerate(layers):
        for pos,key in enumerate(layer):
            role=roles[color_layers[li][pos]]
            key['decoration']={'color':role['foreground'],'background':role['background']}
            if key['value']=='Custom':
                raw=key['params'][0]['value']
                label='Shift' if '&ish' in raw else 'Magic' if raw=='&im' else raw.split('LAYER_')[1]
                key['decoration']['label']=label
    return layout, {'roles':roles, 'layers':color_layers}

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path,help='Output directory for a fresh seed; existing files are never overwritten')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    layout,palette=seed()
    for name,value in [('layout.json',layout),('palette.json',palette)]:
        with (args.output/name).open('x') as f: f.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
