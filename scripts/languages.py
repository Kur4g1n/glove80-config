"""Bilingual firmware and host maps, derived from the same physical layout."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ('standard', 'bilingual')
# ZMK name: macOS virtual key code, Windows set-1 scan code, Karabiner name, XKB name.
KEYS = {}
for name, mac, scan, xkb in [
    ('A',0,30,'AC01'),('S',1,31,'AC02'),('D',2,32,'AC03'),('F',3,33,'AC04'),
    ('H',4,35,'AC06'),('G',5,34,'AC05'),('Z',6,44,'AB01'),('X',7,45,'AB02'),
    ('C',8,46,'AB03'),('V',9,47,'AB04'),('B',11,48,'AB05'),('Q',12,16,'AD01'),
    ('W',13,17,'AD02'),('E',14,18,'AD03'),('R',15,19,'AD04'),('Y',16,21,'AD06'),
    ('T',17,20,'AD05'),('O',31,24,'AD09'),('U',32,22,'AD07'),('I',34,23,'AD08'),
    ('P',35,25,'AD10'),('L',37,38,'AC09'),('J',38,36,'AC07'),('K',40,37,'AC08'),
    ('N',45,49,'AB06'),('M',46,50,'AB07')]:
    KEYS[name] = (mac,scan,name.lower(),xkb)
for number, mac in zip('1234567890',[18,19,20,21,23,22,26,28,25,29]):
    KEYS['N'+number]=(mac, 11 if number=='0' else int(number)+1, number, 'AE'+('10' if number=='0' else '0'+number))
for name,mac,scan,karabiner,xkb in [
    ('MINUS',27,12,'hyphen','AE11'),('EQUAL',24,13,'equal_sign','AE12'),
    ('LBKT',33,26,'open_bracket','AD11'),('RBKT',30,27,'close_bracket','AD12'),
    ('BSLH',42,43,'backslash','BKSL'),('SEMI',41,39,'semicolon','AC10'),
    ('SQT',39,40,'quote','AC11'),('GRAVE',50,41,'grave_accent_and_tilde','TLDE'),
    ('COMMA',43,51,'comma','AB08'),('DOT',47,52,'period','AB09'),('FSLH',44,53,'slash','AB10'),
    ('F13',105,100,'f13','FK13'),('F14',107,101,'f14','FK14'),('F15',113,102,'f15','FK15')]:
    KEYS[name]=(mac,scan,karabiner,xkb)

def config():
    return json.loads((ROOT/'config/russian.json').read_text())

def positions():
    return [g['label'] for g in json.loads((ROOT/'config/info.json').read_text())['layouts']['LAYOUT']['layout']]

def us_pairs():
    from layout import PUNCT
    return {**PUNCT, **{chr(n):(chr(n+32),chr(n)) for n in range(65,91)}}

def native_russian():
    """Russian PC / Windows ЙЦУКЕН; laptop keys keep these normal mappings."""
    result=us_pairs()
    for codes,letters in [
        ('Q W E R T Y U I O P LBKT RBKT','йцукенгшщзхъ'),
        ('A S D F G H J K L SEMI SQT','фывапролджэ'),
        ('Z X C V B N M COMMA DOT','ячсмитьбю'),('GRAVE','ё')]:
        result.update({code:(letter,letter.upper()) for code,letter in zip(codes.split(),letters)})
    for code,shifted in zip(['N'+c for c in '1234567890'],'!"№;%:?*()'):
        result[code]=(result[code][0],shifted)
    result['FSLH']=('.',','); result['BSLH']=('\\','/')
    return result

def profile_layout(source, profile):
    if profile not in PROFILES: raise ValueError('Choose build profile: '+', '.join(PROFILES))
    result=copy.deepcopy(source)
    if profile=='standard': return result
    result['tags']=[*result.get('tags',[]),'bilingual-generated']
    labels=positions(); conf=config()
    for label,code in conf['extra_keys'].items():
        pos=labels.index(label)
        if source['layers'][0][pos]['value']!='&none':
            raise ValueError(f'Bilingual extra letter needs an unused Base key at {label}')
        result['layers'][0][pos]={'value':'&kp','params':[{'value':code}]}
    # Right Alt is an output-bank marker. Existing left Alt remains a modifier.
    for li in (2,4):
        for key in result['layers'][li]:
            if key['value']!='&kp': continue
            param=key['params'][0]; code=param
            if code['value']=='LS': code=code['params'][0]
            if code['value'] in us_pairs():
                key['params']=[{'value':'RA','params':[param]}]
    return result

def base_pairs(source, language):
    from layout import expr, legends
    conf=config(); pairs={}
    physical=profile_layout(source,'bilingual')['layers'][0]
    for label,key in zip(positions(),physical):
        if key['value']!='&kp': continue
        code=expr(key['params'][0])
        if code not in KEYS: continue
        pair=us_pairs().get(code,('',''))
        if language=='ru' and label in conf['base']:
            char=conf['base'][label]
            pair=russian_pair(char)
        if code in pairs and pairs[code]!=pair: raise ValueError('Different text assigned to the same Base keycode: '+code)
        pairs[code]=pair
    return pairs

def russian_pair(char):
    if char.isalpha(): return (char,char.upper())
    if not char: return ('','')
    return next(pair for pair in us_pairs().values() if pair[0]==char)

def diagram_languages(diagram, source):
    from layout import legends
    conf=config(); result={}
    for language in ('en','ru'):
        layers=copy.deepcopy(diagram['layers'])
        for li,row in enumerate(layers):
            for pos,key in enumerate(row):
                if li!=0 and not key['transparent']: continue
                label=positions()[pos]
                if language=='ru' and label in conf['base']:
                    char=conf['base'][label]
                    key['label']=char
                    key['shifted']=russian_pair(char)[1]
                    key['binding']='Russian '+char if char else '&none'
                    role='alpha' if char.isalpha() else source_role(diagram, bool(char))
                    if role in diagram['roles']:
                        key.update({field:diagram['roles'][role][field] for field in ('rgb','background','foreground')})
                        key['role']=role
                # Extra keys are deliberately blank in the English diagram.
        result[language]={'name':'Enthium v14' if language=='en' else conf['name'],'layers':layers}
    return result

def source_role(diagram, punctuation):
    return diagram['layers'][0][67 if punctuation else 65]['role']

def karabiner(source, devices):
    if not devices or any(set(d)!={'vendor_id','product_id'} or any(not isinstance(v,int) or not 0<=v<=65535 for v in d.values()) for d in devices):
        raise ValueError('Specify exact Glove80 vendor/product IDs; wildcards are not allowed')
    native=native_russian(); ascii_pairs=us_pairs(); rules=[]
    condition={'type':'device_if','identifiers':devices}
    ru={'type':'input_source_if','input_sources':[{'input_source_id':r'^org\.glove80\.inputmethod\.RussianPC$'}]}
    # The dedicated Cursor key sends Control-Space. Choose the exact pair,
    # independent of macOS's recent-input-source history or the ABC fallback.
    for target,current in [('English',ru),('RussianPC',{**ru,'type':'input_source_unless'})]:
        rules.append({'type':'basic',
                      'from':{'key_code':'spacebar','modifiers':{'mandatory':['left_control'],'optional':['caps_lock']}},
                      'to':[{'select_input_source':{'input_source_id':r'^org\.glove80\.inputmethod\.'+target+'$'},'repeat':False}],
                      'conditions':[condition,current]})
    for code,pair in base_pairs(source,'ru').items():
        if pair==('',''): target={'key_code':'vk_none'}
        elif pair in native.values():
            dest=next(k for k,v in native.items() if v==pair)
            target={'key_code':KEYS[dest][2]}
        else:
            dest=next(k for k,v in ascii_pairs.items() if v==pair)
            target={'key_code':KEYS[dest][2],'modifiers':['right_option']}
        rules.append({'type':'basic','from':{'key_code':KEYS[code][2], 'modifiers':{'optional':['shift','caps_lock']}},
                      'to':[target], 'conditions':[condition,ru]})
    # Suppress the retired F14/F15 signals too while older firmware is installed.
    for code in ('F13','F14','F15'):
        rules.append({'type':'basic','from':{'key_code':KEYS[code][2],'modifiers':{'optional':['any']}},
                      'to':[{'key_code':'vk_none'}],'conditions':[condition]})
    return {'title':'Glove80 bilingual','rules':[{'description':'Glove80: Statica in Russian; laptop keys stay native','manipulators':rules}]}

def xml_keylayout(language):
    """Two native laptop maps; right Option provides the firmware's US bank."""
    from xml.sax.saxutils import escape
    ordinary=us_pairs() if language=='en' else native_russian()
    maps=[]
    for bank in (ordinary,us_pairs()):
        for shift,caps in ((False,False),(True,False),(False,True),(True,True)):
            values={KEYS[code][0]:pair[int(shift ^ (caps and pair[0].isalpha()))] for code,pair in bank.items() if code in KEYS}
            values.update({36:'\r',48:'\t',49:' ',51:'\b',53:'\x1b',76:'\r',117:'\x7f',
                           123:'\uf702',124:'\uf703',125:'\uf701',126:'\uf700',115:'\uf729',119:'\uf72b',116:'\uf72c',121:'\uf72d'})
            maps.append(values)
    # Command shortcuts always retain the US key identities emitted by Enthium.
    for shift in (False,True):
        maps.append({**maps[0],**{KEYS[k][0]:v[int(shift)] for k,v in us_pairs().items() if k in KEYS}})
    maps.append({**maps[0],**{KEYS[chr(n)][0]:chr(n-64) for n in range(65,91)}})
    modifiers=['', 'anyShift', 'caps', 'anyShift caps',
               'anyOption', 'anyOption anyShift', 'anyOption caps', 'anyOption anyShift caps',
               'command anyOption? caps?', 'command anyShift anyOption? caps?',
               'anyControl anyShift? anyOption? command? caps?']
    name='English' if language=='en' else 'RussianPC'
    def escaped(value):
        return ''.join(f'&#x{ord(c):04x};' if ord(c)<32 else escape(c,{'"':'&quot;'}) for c in value)
    lines=['<?xml version="1.1" encoding="UTF-8"?>',
           '<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',
           f'<keyboard group="126" id="{-28080 if language=="en" else -28081}" name="Glove80 {name}" maxout="1">',
           '<layouts><layout first="0" last="255" mapSet="maps" modifiers="modifiers"/></layouts>',
           '<modifierMap id="modifiers" defaultIndex="0">']
    lines += [f'<keyMapSelect mapIndex="{i}"><modifier keys="{v}"/></keyMapSelect>' for i,v in enumerate(modifiers)]
    lines += ['</modifierMap>','<keyMapSet id="maps">']
    for i,values in enumerate(maps):
        lines.append(f'<keyMap index="{i}">')
        lines += [f'<key code="{code}" output="{escaped(value)}"/>' for code,value in sorted(values.items())]
        lines.append('</keyMap>')
    return '\n'.join(lines+['</keyMapSet>','</keyboard>',''])

def xkb_symbols(source):
    """Per-device XKB maps, with ASCII on levels 3/4 for Number/Symbol."""
    def sym(char): return f'U{ord(char):04X}' if char else 'NoSymbol'
    lines=['// Generated. Use only on Glove80, not as a global replacement.']
    for lang in ('en','ru'):
        lines += [f'partial alphanumeric_keys xkb_symbols "{lang}" {{', '    include "us(basic)"',
                  '    include "level3(ralt_switch)"',f'    name[Group1] = "Glove80 {lang}";']
        for code,pair in base_pairs(source,lang).items():
            levels=(*pair,*us_pairs().get(code,('','')))
            kind='FOUR_LEVEL_ALPHABETIC' if pair[0].isalpha() else 'FOUR_LEVEL'
            lines.append(f'    key <{KEYS[code][3]}> {{ type[Group1]="{kind}", [ '+', '.join(map(sym,levels))+' ] };')
        lines += ['};','']
    return '\n'.join(lines)

def flag_icon(language):
    """Use verified legacy RGB/mask icons for the macOS input menu."""
    name={'en':'english','ru':'russian'}[language]
    return (ROOT/'config/icons'/f'{name}.icns').read_bytes()


def host_outputs(source):
    import plistlib
    ascii_pairs=us_pairs()
    # A TSV keeps the Windows runtime dependency-free beyond AutoHotInterception.
    rows=['; scan\ten\ten_shift\tru\tru_shift\tbank\tbank_shift']
    ru=base_pairs(source,'ru')
    for code,en in base_pairs(source,'en').items():
        pair=ru[code]; bank=ascii_pairs.get(code,('',''))
        # Encode Unicode scalars, avoiding escaping and locale-dependent file reads.
        values=[str(ord(c)) if c else '0' for c in (*en,*pair,*bank)]
        rows.append('\t'.join([str(KEYS[code][1]),*values]))
    # macOS discovers layout bundles by the .keyboardlayout. identifier component.
    # Keep the per-layout input source IDs stable for the Karabiner conditions.
    bundle={'CFBundleIdentifier':'org.glove80.keyboardlayout.personal','CFBundleName':'Glove80',
            'CFBundleVersion':'3','CFBundlePackageType':'BNDL',
            'KLInfo_Glove80 English':{'TISInputSourceID':'org.glove80.inputmethod.English','TISIntendedLanguage':'en','TISIconIsTemplate':False},
            'KLInfo_Glove80 RussianPC':{'TISInputSourceID':'org.glove80.inputmethod.RussianPC','TISIntendedLanguage':'ru','TISIconIsTemplate':False}}
    result={'host/windows/layout.tsv':'\n'.join(rows)+'\n', 'host/linux/glove80':xkb_symbols(source),
            'host/macos/Glove80.bundle/Contents/Info.plist':plistlib.dumps(bundle).decode()}
    for lang,name in [('en','English'),('ru','RussianPC')]:
        result[f'host/macos/Glove80.bundle/Contents/Resources/Glove80 {name}.keylayout']=xml_keylayout(lang)
        result[f'host/macos/Glove80.bundle/Contents/Resources/Glove80 {name}.icns']=flag_icon(lang)
    return result

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Generate device-specific Glove80 host rules without changing OS settings.')
    parser.add_argument('--device',action='append',required=True,help='Glove80 vendor:product, decimal or 0x-prefixed; repeat for USB/Bluetooth')
    parser.add_argument('--output',type=Path,default=ROOT/'host/macos/glove80.json')
    args=parser.parse_args()
    try:
        devices=[]
        for value in args.device:
            vendor,product=value.split(':')
            devices.append({'vendor_id':int(vendor,0),'product_id':int(product,0)})
        source=json.loads((ROOT/'config/layout.json').read_text())
        result=karabiner(source,devices)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(args.output)
    except (ValueError,OSError) as error: parser.exit(1,str(error)+'\n')
