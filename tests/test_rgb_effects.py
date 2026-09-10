import hashlib
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class RGBEffectsTests(unittest.TestCase):
    def test_actual_patched_effect_transitions(self):
        source=ROOT/'config/reference/zmk-rgb-underglow.c'
        self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(),(ROOT/'config/reference/README.md').read_text())
        with tempfile.TemporaryDirectory() as directory:
            temp=Path(directory);(temp/'src').mkdir();(temp/'src/rgb_underglow.c').write_bytes(source.read_bytes())
            subprocess.run(['patch','-p1','-i',str(ROOT/'patches/rgb-effect-cycle.patch')],cwd=temp,check=True,capture_output=True)
            patched=(temp/'src/rgb_underglow.c').read_text()
            names=['zmk_rgb_underglow_palette_index','rgb_settings_set','zmk_rgb_underglow_on','zmk_rgb_underglow_transient_on','zmk_rgb_underglow_off','zmk_rgb_underglow_transient_off','zmk_rgb_underglow_calc_effect','zmk_rgb_underglow_select_effect','zmk_rgb_underglow_cycle_effect']
            functions=[]
            for name in names:
                match=re.search(r'(?:static )?(?:int|uint8_t) '+name+r'\([^)]*\) \{',patched)
                self.assertIsNotNone(match,name)
                start=match.start();end=match.end();depth=1
                while depth:
                    depth+=(patched[end]=='{')-(patched[end]=='}');end+=1
                functions.append(patched[start:end])
            enum=re.search(r'enum rgb_underglow_effect \{.*?\};',patched,re.S)[0]
            (temp/'rgb_effect_enum.inc').write_text(enum)
            module=(ROOT/'module/src/behavior_lock_color.c').read_text()
            functions.append(re.search(r'static int palette_color\(.*?\n\}',module,re.S)[0])
            (temp/'rgb_effects.inc').write_text('\n'.join(functions))
            for count in (1,2,3,4,5):
                subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-parameter',f'-DTHEME_COUNT={count}','-I'+str(temp),str(ROOT/'tests/test_rgb_effects.c'),'-o',str(temp/'test')],check=True)
                subprocess.run([str(temp/'test')],check=True)
