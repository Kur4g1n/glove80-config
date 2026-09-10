#!/usr/bin/env python3
"""Portable entry points for just. No Python packages required."""
import argparse
import functools
import http.server
import json
import os
import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'glove80-personal:locked'

def run(args, **kwargs):
    print('+ ' + ' '.join(str(x) for x in args), flush=True)
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)

def docker():
    if not shutil.which('docker'):raise RuntimeError('Docker is missing. Run just setup.')
    candidates=[['docker']]
    if platform.system()=='Darwin' and not os.environ.get('DOCKER_CONTEXT') and not os.environ.get('DOCKER_HOST'):
        candidates.append(['docker','--context','colima'])
    for cmd in candidates:
        if subprocess.run(cmd+['info','--format','{{.ServerVersion}}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return cmd
    raise RuntimeError('Docker is not running. Run just setup, or start your Docker daemon.')

def setup():
    if platform.system()=='Darwin':
        if not shutil.which('brew'):raise RuntimeError('Install Homebrew from https://brew.sh, then run brew install just and just setup.')
        missing=[package for command,package in [('python3','python'),('node','node'),('docker','docker'),('colima','colima')] if not shutil.which(command)]
        if missing:run(['brew','install',*missing])
        # Reuse Docker Desktop or an existing daemon; start Colima only if needed.
        try:docker()
        except RuntimeError:run(['colima','start','--cpu','4','--memory','8'])
    for command in ('python3','cc'):
        if not shutil.which(command):raise RuntimeError(f'{command} is missing. Install the compiler/Python for your operating system.')
    doctor()
    run(docker()+['build','-t',IMAGE,'.'])
    run(docker()+['run','--rm','-v','glove80-nix-store:/nix','--entrypoint','bash',IMAGE,
                  '-c','nix-shell /opt/zmk -A zmk --run true'])

def doctor():
    lock=json.loads((ROOT/'firmware.lock.json').read_text())
    for name in ('just','python3','node','cc','docker'):
        location=shutil.which(name)
        if not location:raise RuntimeError(name+' is missing')
        print(f'{name}: {location}')
    cmd=docker()
    run(cmd+['info','--format','Docker {{.ServerVersion}} ({{.OSType}}/{{.Architecture}})'])
    if lock['revision'] not in (ROOT/'Dockerfile').read_text():raise RuntimeError('Dockerfile firmware revision differs from firmware.lock.json')
    if lock['container'] not in (ROOT/'Dockerfile').read_text():raise RuntimeError('Container image differs from firmware.lock.json')
    print('Firmware: '+lock['revision']+' (PR36 with checked local RGB patch)')

def build(theme="macchiato",profile="standard"):
    import layout
    source=layout.read(ROOT/'config/layout.json');palette=layout.read(ROOT/'config/palette.json')
    names=layout.selected_themes(palette,theme)
    theme=','.join(names)
    generated=layout.build_outputs(source,palette,theme,profile)
    selected=ROOT/'.cache/build-config'/profile/'-'.join(names)
    selected.mkdir(parents=True,exist_ok=True)
    (selected/'glove80.keymap').write_text(generated['config/glove80.keymap'])
    (selected/'keymap.json').write_text(generated['config/keymap.json'])
    run([sys.executable,'scripts/layout.py','generate'])
    cmd=docker()
    run(cmd+['build','-t',IMAGE,'.'])
    run(cmd+['run','--rm','-v',str(ROOT)+':/workspace','-v','glove80-nix-store:/nix',
             '-e',f'KEY_THEME={theme}','-e',f'BUILD_PROFILE={profile}',
             '-e',f'HOST_UID={os.getuid()}','-e',f'HOST_GID={os.getgid()}',IMAGE])
    for name in ('glove80-left.uf2','glove80-right.uf2','glove80.uf2'):
        path=ROOT/'build'/name;validate_uf2(path);print(f'{path} ({path.stat().st_size:,} bytes)')

def validate_uf2(path):
    data=path.read_bytes()
    if not data or len(data)%512:raise RuntimeError('Firmware is not a complete UF2 file: '+str(path))
    segments = {}
    for offset in range(0,len(data),512):
        a,b,flags,address,size,index,total,family=struct.unpack_from('<8I',data,offset)
        if (a,b)!=(0x0A324655,0x9E5D5157) or struct.unpack_from('<I',data,offset+508)[0]!=0x0AB16F30:
            raise RuntimeError('Invalid UF2 block magic')
        # Glove80 uses a different family ID per half, not generic nRF52840.
        if not flags&0x2000 or family not in (0x9807B007,0x9808B007) or not 0<size<=476 or not total or index>=total:
            raise RuntimeError('UF2 is not valid Glove80 firmware')
        expected,indices=segments.setdefault(family,(total,set()))
        if expected!=total or index in indices:raise RuntimeError('Inconsistent or duplicate UF2 blocks')
        indices.add(index)
    if any(len(indices)!=total for total,indices in segments.values()):
        raise RuntimeError('UF2 is missing firmware blocks')
    return data

def combined_firmware():
    source=ROOT/'build/glove80.uf2'
    if not source.is_file():raise RuntimeError('Firmware is missing. Run just build before entering bootloader mode.')
    data=validate_uf2(source)
    if {struct.unpack_from('<I',data,i+28)[0] for i in range(0,len(data),512)}!={0x9807B007,0x9808B007}:
        raise RuntimeError('The combined UF2 must contain firmware for both Glove80 halves')
    return source

def flash_ready():
    source=combined_firmware()
    if platform.system()!='Darwin':
        raise RuntimeError('Finder preparation is macOS-only. Open build/glove80.uf2 in your file manager and copy it to the boot volume.')
    run(['open','/Volumes'])
    run(['open','-R',str(source)])
    print('Finder is ready. Enter bootloader mode, then drag glove80.uf2 onto the selected Glove80 boot volume. Repeat for the other half.')

def flash(mount,dry_run=False):
    volume=mount.expanduser().resolve()
    info=volume/'INFO_UF2.TXT'
    if not volume.is_dir() or not info.is_file() or 'glove80' not in info.read_text(errors='replace').lower():
        raise RuntimeError('The selected directory is not a Glove80 UF2 bootloader volume (INFO_UF2.TXT).')
    source=combined_firmware()
    destination=volume/'glove80.uf2'
    if dry_run:print(f'Validated: would copy {source} to {destination}');return
    with source.open('rb') as src,destination.open('wb') as dst:
        shutil.copyfileobj(src,dst);dst.flush();os.fsync(dst.fileno())
    print('Firmware copied. Repeat for the other half; the bootloader may eject automatically.')

def install_macos():
    if platform.system()!='Darwin':
        raise RuntimeError('This command installs macOS input layouts. See host/README.md for other systems.')
    if not shutil.which('swift'):
        raise RuntimeError('Install Apple command line tools with xcode-select --install, then retry.')
    run([sys.executable,'scripts/layout.py','generate'])
    source=ROOT/'host/macos/Glove80.bundle'
    target=Path.home()/'Library/Keyboard Layouts/Glove80.bundle'
    if target.exists():
        import tempfile
        backup=Path(tempfile.mkdtemp(prefix='glove80-layout-backup-'))/'Glove80.bundle'
        shutil.copytree(target,backup)
        print('Previous bundle backed up to '+str(backup),flush=True)
    shutil.copytree(source,target,dirs_exist_ok=True)
    # copytree preserves source directory timestamps; mark this as a new install.
    os.utime(target,None)
    os.utime(target.parent,None)
    run(['swift',str(ROOT/'scripts/register-macos.swift'),str(target)])
    print('Installed and validated. Log out and back in so macOS refreshes its input-source list.')
    print('Then open System Settings → Keyboard → Text Input → Edit → + and add Glove80 English and Glove80 RussianPC.')

def install(directory=''):
    system=platform.system()
    if system=='Darwin':
        if directory: raise ValueError('macOS uses ~/Library/Keyboard Layouts; omit the directory argument.')
        install_macos()
        return
    if system=='Windows':
        if not directory: raise ValueError('Run just install "C:\\path\\to\\AutoHotInterception\\AHK v2" after preparing AHI. See host/README.md.')
        target=Path(directory).expanduser().resolve()
        if not (target/'Lib/AutoHotInterception.ahk').is_file():
            raise ValueError('Choose the prepared AHI v2 folder containing Lib/AutoHotInterception.ahk.')
        files=['Glove80.ahk','layout.tsv','settings.ini.example']
        sources=[ROOT/'host/windows'/name for name in files]
        destinations=[target/name for name in files]
    elif system=='Linux':
        if directory: raise ValueError('Linux uses the user XKB directory; omit the directory argument.')
        sources=[ROOT/'host/linux/glove80']
        destinations=[Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'xkb/symbols/glove80']
    else: raise RuntimeError('Unsupported host OS: '+system)
    run([sys.executable,'scripts/layout.py','generate'])
    for source,target in zip(sources,destinations):
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=source.read_bytes():
            import tempfile
            backup=Path(tempfile.mkdtemp(prefix='glove80-host-backup-'))/target.name
            shutil.copyfile(target,backup)
            print('Previous file backed up to '+str(backup))
        shutil.copyfile(source,target)
        print('Installed '+str(target))
    if system=='Windows':
        settings=destinations[0].parent/'settings.ini'
        if not settings.exists(): shutil.copyfile(destinations[-1],settings)
        print('Set Glove80 VID/PID in settings.ini, then run Glove80.ahk. Existing settings are preserved.')
    else: print('Assign the XKB layout to Glove80 in the compositor configuration; see host/README.md. No global layout was changed.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for cmd in ('setup','doctor','check','flash-ready'):sub.add_parser(cmd)
    installer=sub.add_parser('install');installer.add_argument('--directory',default='')
    builder=sub.add_parser('build');builder.add_argument('--theme',default='macchiato',help='One palette or an ordered comma-separated list')
    builder.add_argument('--profile',choices=['standard','bilingual'],default='standard')
    docs=sub.add_parser('docs');docs.add_argument('--port',type=int,default=8000)
    fl=sub.add_parser('flash');fl.add_argument('mount',type=Path);fl.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    if args.command=='setup':setup()
    elif args.command=='doctor':doctor()
    elif args.command=='build':build(args.theme,args.profile)
    elif args.command=='flash-ready':flash_ready()
    elif args.command=='install':install(args.directory)
    elif args.command=='check':
        run([sys.executable,'scripts/layout.py','check'])
        run([sys.executable,'-m','unittest','discover','-s','tests','-v'])
        run(['node','tests/test_diagram.cjs'])
    elif args.command=='flash':flash(args.mount,args.dry_run)
    elif args.command=='docs':
        run([sys.executable,'scripts/layout.py','generate'])
        handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(ROOT/'docs'))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',args.port),handler)
        print(f'Layout: http://127.0.0.1:{args.port} (Ctrl-C to stop)',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.server_close()

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr);sys.exit(1)
