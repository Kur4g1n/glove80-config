#!/usr/bin/env python3
"""Validate, generate, and import the personal MoErgo layout. Standard library only."""
import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['Base', 'Cursor', 'Number', 'Magic', 'Symbol']
CONTROLS = {51: 1, 68: 2, 75: 4}
def controls_for(layer):
    return {pos: target for pos, target in CONTROLS.items() if layer not in (2,4) or target == layer}

ROW_ENDS = [10, 22, 34, 46, 64, 80]

def read(path):
    return json.loads(path.read_text())

def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'

def expr(node):
    value = str(node['value'])
    params = node.get('params', [])
    if value == 'Custom':
        return str(params[0]['value'])
    if value.startswith('&'):
        return value + ((' ' + ' '.join(expr(p) for p in params)) if params else '')
    return value + (('(' + ', '.join(expr(p) for p in params) + ')') if params else '')

def validate(layout):
    if layout.get('keyboard') != 'glove80' or layout.get('layer_names') != NAMES:
        raise ValueError('Expected Glove80 layers in order: ' + ', '.join(NAMES))
    if len(layout.get('layers', [])) != 5 or any(len(row) != 80 for row in layout['layers']):
        raise ValueError('Each of the five layers must have exactly 80 keys')
    if layout.get('locale') != 'en-US':
        raise ValueError('This keymap uses the en-US host keycode layout')
    def validate_node(node, top=False):
        if not isinstance(node, dict) or 'value' not in node: raise ValueError('Malformed key binding')
        if not isinstance(node['value'], (int, str)): raise ValueError('Invalid binding value')
        if not isinstance(node.get('params', []), list): raise ValueError('Invalid binding parameters')
        val = str(node['value'])
        if val == 'Custom':
            if len(node.get('params', [])) != 1: raise ValueError('Custom bindings need one expression')
            raw = node['params'][0]['value']
            if not isinstance(raw,str) or not re.fullmatch(r'&(?:im|ish (?:LSHFT|RSHFT)|il LAYER_(?:Cursor|Number|Symbol))',raw):
                raise ValueError('Unsupported custom binding: ' + str(raw))
        else:
            if not re.fullmatch(r'&?[A-Za-z_][A-Za-z_0-9]*|[0-9]+',val): raise ValueError('Invalid token: '+val)
            for param in node.get('params', []): validate_node(param)
        decoration=node.get('decoration',{})
        for name in ('color','background'):
            if name in decoration and not re.fullmatch(r'#[0-9a-fA-F]{6}',decoration[name]):
                raise ValueError('Decoration colors must be six-digit #RRGGBB values')
    for li, layer in enumerate(layout['layers']):
        for key in layer: validate_node(key, True)
        for pos, target in controls_for(li).items():
            if expr(layer[pos]) != '&il LAYER_'+NAMES[target]:
                raise ValueError(f'{NAMES[li]} key {pos} must retain its {NAMES[target]} control')
        for pos in (64,79):
            if expr(layer[pos]) != '&im': raise ValueError('Both Magic keys must remain available on every layer')
    geometry=read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
    for li,side in ((2,'L_'),(4,'R_')):
        for pos,g in enumerate(geometry):
            if not g['label'].startswith(side) or pos in controls_for(li) or pos in (64,79):continue
            expected='&trans' if '_T' in g['label'] else '&none'
            if expr(layout['layers'][li][pos])!=expected:
                raise ValueError(f'{NAMES[li]} {g["label"]}: inactive fingers must be disabled; only thumbs inherit Base')
    base=layout['layers'][0]
    if any(k['value']=='&trans' for k in base):raise ValueError('Base cannot contain transparent keys')
    for shift in ('LSHFT','RSHFT'):
        if not any(expr(k)=='&ish '+shift for k in base):raise ValueError('Base must contain both immediate Shift keys')
    for key in (k for layer in layout['layers'] for k in layer):
        if key['value'] in ('&mt','&lt','&layer','&magic','&tog','&to','&mo','&sk','&sl'):
            raise ValueError('Use the immediate controls; timed/sticky/independent layer behaviors are not supported')
    if any(layout.get(k) for k in ('holdTaps','combos','macros','inputListeners')):
        raise ValueError('Keep generated behaviors in config/behaviors.dtsi; GUI hold-taps/combos/macros are unsupported')

def color(layout, palette, layer, pos):
    role=palette['roles'][palette['layers'][layer][pos]]
    deco=layout['layers'][layer][pos].get('decoration',{})
    bg=deco.get('background',role['background'])
    return {'rgb':role['rgb'] if bg.lower()==role['background'].lower() else bg,
            'background':bg,'foreground':deco.get('color',role['foreground'])}

PUNCT = {'N1':('1','!'),'N2':('2','@'),'N3':('3','#'),'N4':('4','$'),'N5':('5','%'),
         'N6':('6','^'),'N7':('7','&'),'N8':('8','*'),'N9':('9','('),'N0':('0',')'),
         'SQT':("'",'"'),'SINGLE_QUOTE':("'",'"'),'GRAVE':('`','~'),'LBKT':('[','{'),
         'RBKT':(']','}'),'MINUS':('-','_'),'EQUAL':('=','+'),'BSLH':('\\','|'),
         'FSLH':('/','?'),'COMMA':(',','<'),'DOT':('.','>'),'SEMI':(';',':')}
LABELS={'SPACE':'Space','ESC':'Esc','RET':'Enter','ENTER':'Enter','BSPC':'⌫','BACKSPACE':'⌫',
        'DEL':'Del','INS':'Ins','TAB':'Tab','LGUI':'⌘','RGUI':'⌘','LCTRL':'Ctrl','RCTRL':'Ctrl',
        'LALT':'Opt','RALT':'Opt','LSHFT':'⇧','RSHFT':'⇧','HOME':'Home','END':'End',
        'PG_UP':'PgUp','PG_DN':'PgDn','LEFT':'←','RIGHT':'→','UP':'↑','DOWN':'↓',
        'CAPS':'Caps','SCROLLLOCK':'Scroll','PSCRN':'PrtSc','PAUSE_BREAK':'Pause',
        'C_MUTE':'Mute','C_VOL_DN':'Vol −','C_VOL_UP':'Vol +','C_BRI_DN':'☀ −','C_BRI_UP':'☀ +',
        'C_PREV':'⏮','C_NEXT':'⏭','C_PP':'⏯','LC(SPACE)':'EN / RU'}
RGB_LABELS={'RGB_SPI':'Speed +','RGB_SPD':'Speed −','RGB_SAI':'Sat +','RGB_SAD':'Sat −',
            'RGB_HUI':'Hue +','RGB_HUD':'Hue −','RGB_BRI':'Light +','RGB_BRD':'Light −',
            'RGB_TOG':'RGB','RGB_EFF':'Effect'}

def legends(key):
    text=expr(key)
    if text in ('&none','&trans'):return ('','')
    if text.startswith('&il '):return (text.split('LAYER_')[1],'')
    if text=='&im':return ('Magic','')
    if text.startswith('&ish '):return ('⇧','')
    if key['value']=='&kp':
        param=key['params'][0]
        if param['value']=='RA':
            return legends({'value':'&kp','params':param['params']})
        if param['value']=='LS':
            code=str(param['params'][0]['value'])
            return (PUNCT[code][1] if code in PUNCT else LABELS.get(code,code),'')
        code=expr(param)
        if re.fullmatch('[A-Z]',code):return (code.lower(),code)
        return PUNCT.get(code,(LABELS.get(code,code),''))
    if key['value']=='&rgb_ug':return (RGB_LABELS[key['params'][0]['value']],'')
    if text=='&bootloader':return ('Boot','')
    if text=='&sys_reset':return ('Reset','')
    if text.startswith('&bt_'):return ('BT '+text[-1],'')
    if text=='&bt BT_CLR':return ('Clear BT','')
    if text=='&bt BT_CLR_ALL':return ('Clear all','')
    if text=='&out OUT_USB':return ('USB','')
    return (text,'')

def themed(layout,palette,name=None):
    """Apply a theme without losing explicit MoErgo decoration overrides."""
    name=name or palette.get('default_theme','macchiato')
    themes=palette.get('themes',{'macchiato':{'name':'Catppuccin Macchiato'}})
    if name not in themes:raise ValueError('Unknown key theme: '+str(name))
    profile=themes[name]
    result=copy.deepcopy(layout);colors=copy.deepcopy(palette)
    colors['roles'].update(profile.get('roles',{}))
    colors['layers']=copy.deepcopy(profile.get('layers',palette['layers']))
    for li,row in enumerate(result['layers']):
        for pos,key in enumerate(row):
            old=palette['roles'][palette['layers'][li][pos]]
            new=colors['roles'][colors['layers'][li][pos]]
            deco=key.setdefault('decoration',{})
            for field,role_field in [('background','background'),('color','foreground')]:
                if field not in deco or deco[field].lower()==old[role_field].lower():deco[field]=new[role_field]
    return result,colors

def outputs(layout,palette,theme=None,profile='standard'):
    from languages import profile_layout
    theme=theme or palette.get('default_theme','macchiato')
    layout,palette=themed(layout,palette,theme)
    layout=profile_layout(layout,profile)
    validate(layout)
    behavior=(ROOT/'config/behaviors.dtsi').read_text().replace(
        'PALETTE_LAYER_LOCKED',palette['roles']['layer.locked']['rgb'].replace('#','0x'))
    lines=['/* Generated by just generate. Edit config/layout.json and config/palette.json. */',
           '/ {', '    underglow-layer {', '        compatible = "zmk,underglow-layer";']
    for li,name in enumerate(NAMES):
        lines += [f'        {name.lower()}_rgb {{',f'            layer-id = <{li}>;',
                  '            bindings = <']
        bindings=[]
        for pos in range(80):
            rgb=color(layout,palette,li,pos)['rgb'].replace('#','0x')
            bindings.append(f'&lkcolor {CONTROLS[pos]} {rgb}' if pos in controls_for(li) else f'&ug {rgb}')
        start=0
        for end in ROW_ENDS:
            lines.append('                '+'  '.join(bindings[start:end]));start=end
        lines += ['            >;','        };']
    lines += ['    };','};','']
    tree='\n'.join(lines)
    exported=copy.deepcopy(layout)
    exported['custom_defined_behaviors']=behavior
    exported['custom_devicetree']=tree
    headers=['behaviors.dtsi','dt-bindings/zmk/keys.h','dt-bindings/zmk/bt.h',
             'dt-bindings/zmk/outputs.h','dt-bindings/zmk/rgb.h']
    keymap=['/* Generated by just generate. Do not edit. */']
    keymap += [f'#include <{h}>' for h in headers]
    keymap += [f'#define LAYER_{name} {i}' for i,name in enumerate(NAMES)]
    keymap += ['/ {',behavior,'    keymap {','        compatible = "zmk,keymap";']
    for li,name in enumerate(NAMES):
        keymap += [f'        {name.lower()}_layer {{',f'            label = "{name}";','            bindings = <']
        start=0
        for end in ROW_ENDS:
            keymap.append('                '+'  '.join(expr(k) for k in layout['layers'][li][start:end]));start=end
        keymap += ['            >;','        };']
    keymap += ['    };','};',tree]
    info=read(ROOT/'config/info.json')['layouts']['LAYOUT']['layout']
    corners=[]
    for g in info:
        cx,cy=g['x']+.5,g['y']+.5;r=math.radians(g.get('r',0))
        corners.extend((cx+x*math.cos(r)-y*math.sin(r),cy+x*math.sin(r)+y*math.cos(r)) for x,y in ((-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)))
    xs,ys=zip(*corners)
    diagram={'names':NAMES,'geometry':info,'controls':CONTROLS,'magic':[64,79],'layers':[],
             'theme':palette['theme'],'roles':copy.deepcopy(palette['roles']),
             'viewBox':[min(xs)-.3,min(ys)-.3,max(xs)-min(xs)+.6,max(ys)-min(ys)+.65]}
    for li,layer in enumerate(layout['layers']):
        keys=[]
        for pos,key in enumerate(layer):
            transparent=key['value']=='&trans'
            effective=layout['layers'][0][pos] if transparent else key
            label,shifted=legends(effective)
            label=effective.get('decoration',{}).get('label',label)
            if expr(effective).startswith('&ish '):label='⇧'
            actual=color(layout,palette,li,pos)
            role_id=palette['layers'][li][pos];role=palette['roles'][role_id]
            if any(actual[field]!=role[field] for field in ('background','foreground')):
                role_id+='.'+actual['background'][1:]+actual['foreground'][1:]
                diagram['roles'][role_id]={**role,**actual,'label':role['label']+' · '+actual['background'],
                                           'color_name':'Custom'}
            keys.append(dict(label=label,shifted=shifted,binding=expr(effective),role=role_id,
                             target=controls_for(li).get(pos,3 if pos in (64,79) else None),
                             transparent=transparent,**actual))
        diagram['layers'].append(keys)
    diagram['defaultTheme']=theme
    return {'config/glove80.keymap':'\n'.join(keymap).rstrip()+'\n','config/keymap.json':dump(exported),
            'docs/layout-data.js':'// Generated by just generate.\nwindow.GLOVE80 = '+json.dumps(diagram,ensure_ascii=False).replace('<','\\u003c')+';\n'}

def generate(check=False):
    from languages import diagram_languages, host_outputs
    source=read(ROOT/'config/layout.json')
    content=outputs(source,read(ROOT/'config/palette.json'))
    prefix='// Generated by just generate.\nwindow.GLOVE80 = '
    diagram=json.loads(content['docs/layout-data.js'][len(prefix):-2])
    diagram['languages']=diagram_languages(diagram,source)
    content['docs/layout-data.js']=prefix+json.dumps(diagram,ensure_ascii=False).replace('<','\\u003c')+';\n'
    content.update(host_outputs(source))
    stale=[]
    for name,value in content.items():
        path=ROOT/name
        if check:
            if not path.exists() or (path.read_bytes() if isinstance(value,bytes) else path.read_text())!=value:stale.append(name)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(value,bytes): path.write_bytes(value)
            else: path.write_text(value)
    if stale:raise ValueError('Generated files are stale: '+', '.join(stale)+'; run just generate')
    return content

def selected_themes(palette,selection):
    names=[name.strip() for name in selection.split(',')]
    if not names or any(name not in palette['themes'] for name in names):
        raise ValueError('Choose comma-separated palettes: '+', '.join(palette['themes']))
    if len(set(names))!=len(names):raise ValueError('Choose each palette only once')
    return names

def build_outputs(source,palette,selection,profile='standard'):
    names=selected_themes(palette,selection)
    result=outputs(source,palette,names[0],profile)
    if len(names)==1:return result
    packed=[]
    for name in names:
        themed_source,colors=themed(source,palette,name)
        packed += [color(themed_source,colors,li,pos)['rgb'].replace('#','0x') for li in range(5) for pos in range(80)]
        packed.append(colors['roles']['layer.locked']['rgb'].replace('#','0x'))
    node=['/ {','    behaviors {','        palette_rgb: palette_rgb {',
          '            compatible = "personal,palette-color"; #binding-cells = <2>;',
          f'            theme-count = <{len(names)}>;', '            colors = <']
    for pos in range(0,len(packed),10):node.append('                '+' '.join(packed[pos:pos+10]))
    node += ['            >;','        };','    };','};','']
    export=json.loads(result['config/keymap.json']);tree=export['custom_devicetree']
    position=iter(range(400))
    def binding(match):
        index=next(position);li,pos=divmod(index,80)
        return f'&palette_rgb {index} {controls_for(li).get(pos,0)}'
    bank_tree=re.sub(r'&(?:ug 0x[0-9a-fA-F]+|lkcolor [0-9]+ 0x[0-9a-fA-F]+)',binding,tree)
    result['config/glove80.keymap']=result['config/glove80.keymap'].replace(tree,'\n'.join(node)+bank_tree)
    # The editable MoErgo export shows the first palette; banks are build-only.
    return result

def imported(path):
    incoming=read(path)
    if 'bilingual-generated' in incoming.get('tags',[]):
        raise ValueError('Import the standard MoErgo export; bilingual bindings are generated from config/russian.json')
    old=read(ROOT/'config/layout.json')
    palette=read(ROOT/'config/palette.json')
    original_roles=copy.deepcopy(palette['layers'])
    original_theme_layers={name:copy.deepcopy(profile['layers']) for name,profile in palette.get('themes',{}).items() if 'layers' in profile}
    # Identify the exported theme from its generated custom blocks, then normalize
    # unchanged theme decorations back to the canonical source palette.
    candidates=[]
    for name in palette.get('themes',{'macchiato':{}}):
        exported=json.loads(outputs(old,palette,name)['config/keymap.json'])
        if all(incoming.get(f,'') in ('',exported[f]) for f in ('custom_defined_behaviors','custom_devicetree')):
            candidates.append(name)
    if not candidates:raise ValueError('Custom behavior or RGB definitions were changed; edit repository sources instead')
    theme=palette.get('default_theme','macchiato') if palette.get('default_theme','macchiato') in candidates else candidates[0]
    themed_old,themed_palette=themed(old,palette,theme)
    for field in ('custom_defined_behaviors','custom_devicetree'):incoming[field]=''
    validate(incoming)
    for li,row in enumerate(incoming['layers']):
        for pos,key in enumerate(row):
            matches=[p for p,k in enumerate(themed_old['layers'][li]) if expr(k)==expr(key) and k.get('decoration')==key.get('decoration')]
            match=pos if pos in matches or not matches else matches[0]
            if matches:
                palette['layers'][li][pos]=original_roles[li][match]
                for name,profile in palette.get('themes',{}).items():
                    if 'layers' in profile:
                        # Read the original matrix, not entries changed earlier in this import.
                        original=original_theme_layers[name]
                        profile['layers'][li][pos]=original[li][match]
            before=themed_palette['roles'][themed_palette['layers'][li][match]]
            after=palette['roles'][palette['layers'][li][pos]]
            for field,role_field in [('background','background'),('color','foreground')]:
                deco=key.get('decoration',{})
                if deco.get(field,'').lower()==before[role_field].lower():deco[field]=after[role_field]
    return incoming,palette

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['generate','check','import'])
    parser.add_argument('file',nargs='?',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='import':
            if args.file is None:parser.error('import requires a JSON file')
            new,palette=imported(args.file)
            # Validate all derived artifacts before replacing the source.
            outputs(new,palette)
            from languages import host_outputs
            host_outputs(new)
            (ROOT/'config/layout.json').write_text(dump(new))
            (ROOT/'config/palette.json').write_text(dump(palette))
        generate(check=args.command=='check')
        print('Layout '+('checked' if args.command=='check' else 'generated')+': 5 layers × 80 keys')
    except (ValueError,KeyError,TypeError,IndexError,OSError) as error:
        print('Layout error: '+str(error),file=sys.stderr);sys.exit(1)
