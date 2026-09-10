import contextlib
import io
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import tasks

def uf2(family,index=0,total=1):
    block=bytearray(512)
    struct.pack_into('<8I',block,0,0x0A324655,0x9E5D5157,0x2000,0x26000+index*256,256,index,total,family)
    struct.pack_into('<I',block,508,0x0AB16F30)
    return bytes(block)

class BuildToolsTests(unittest.TestCase):
    def test_mouse_preparation_validates_before_opening_finder(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(tasks,'ROOT',Path(directory)),patch.object(tasks.platform,'system',return_value='Darwin'),patch.object(tasks,'run') as run:
            root=Path(directory);(root/'build').mkdir();image=root/'build/glove80.uf2'
            with self.assertRaises(RuntimeError):tasks.flash_ready()
            run.assert_not_called()
            image.write_bytes(uf2(0x9807B007)+uf2(0x9808B007))
            with contextlib.redirect_stdout(io.StringIO()):tasks.flash_ready()
            self.assertEqual([c.args[0] for c in run.call_args_list],[['open','/Volumes'],['open','-R',str(image)]])
            self.assertEqual(image.read_bytes(),uf2(0x9807B007)+uf2(0x9808B007))
    def test_uf2_families_and_completeness(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.uf2'
            good=uf2(0x9807B007)+uf2(0x9808B007)
            path.write_bytes(good);self.assertEqual(tasks.validate_uf2(path),good)
            for bad in (b'',good[:-1],uf2(0xADA52840),uf2(0x9807B007,0,2),uf2(0x9807B007)*2,bytes(512)):
                path.write_bytes(bad)
                with self.assertRaises(RuntimeError):tasks.validate_uf2(path)
    def test_flash_requires_explicit_glove80_volume_and_combined_image(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(tasks,'ROOT',Path(directory)):
            root=Path(directory);(root/'build').mkdir();mount=root/'selected volume';mount.mkdir()
            image=root/'build/glove80.uf2';image.write_bytes(uf2(0x9807B007)+uf2(0x9808B007))
            with self.assertRaises(RuntimeError):tasks.flash(mount,True)
            (mount/'INFO_UF2.TXT').write_text('Model: Glove80\n')
            with contextlib.redirect_stdout(io.StringIO()):tasks.flash(mount,True)
            self.assertFalse((mount/'glove80.uf2').exists())
            # Exercise copying only into this isolated temporary fixture.
            with contextlib.redirect_stdout(io.StringIO()):tasks.flash(mount)
            self.assertEqual((mount/'glove80.uf2').read_bytes(),image.read_bytes())
            image.write_bytes(uf2(0x9807B007))
            with self.assertRaises(RuntimeError):tasks.flash(mount,True)
