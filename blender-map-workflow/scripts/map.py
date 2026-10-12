#!/usr/bin/env python3
"""One entry point for a portable LLM-driven Blender map workflow."""
import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from common import discover_blender, load_config, write_json

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['doctor','prepare','build','verify','run'])
    parser.add_argument('--config',type=Path,default=HERE.parent/'presets'/'united-states.json')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--cache',type=Path)
    parser.add_argument('--blender',help='Path to stable Blender executable (or BLENDER_BIN)')
    parser.add_argument('--offline',action='store_true',help='Never make network requests; require complete checked cache')
    parser.add_argument('--overwrite',action='store_true',help='Back up existing output before regenerating')
    parser.add_argument('--no-render',action='store_true',help='Build editable scene without preview')
    parser.add_argument('--render',action='store_true',help='Render again during saved-file verification')
    args=parser.parse_args()
    if args.stage=='doctor':
        modules=['numpy','PIL','pyproj','rasterio','shapely','shapefile']
        report={'python':sys.version.split()[0],'platform':platform.platform(),
                'libraries':{m:bool(importlib.util.find_spec(m)) for m in modules}}
        try:report['blender'],report['blender_version']=discover_blender(args.blender)
        except RuntimeError as e:report['blender_error']=str(e)
        print(json.dumps(report,indent=2))
        return 0 if all(report['libraries'].values()) and 'blender' in report else 1
    if args.output is None:parser.error('--output is required')
    output=args.output.resolve();config=load_config(args.config)
    if args.stage in ('run','prepare','build') and list(output.glob('*.blend')):
        if not args.overwrite:raise RuntimeError('Output contains a saved scene. Choose a new --output or use --overwrite to create a backup first.')
        backup=output.with_name(output.name+'.backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.copytree(output,backup)
        print('BACKUP',backup,flush=True)
    cache=(args.cache or output.parent/'cache').resolve()
    if args.stage in ('run','prepare'):
        from prepare import prepare
        prepare(args.config,output,cache,args.offline)
    if args.stage=='prepare':return 0
    blender,version=discover_blender(args.blender)
    if args.stage in ('run','build'):
        command=[blender,'--background','--factory-startup','--python-exit-code','1','--python',str(HERE/'build_scene.py'),'--','--output',str(output)]
        if args.no_render:command.append('--no-render')
        run_logged(command,output/'build.log')
    if args.stage in ('run','verify'):
        saved_config=json.loads((output/'project.json').read_text())['config']
        scene_path=output/(saved_config['slug']+'.blend')
        command=[blender,'--background','--factory-startup',str(scene_path),'--python-exit-code','1','--python',str(HERE/'verify_scene.py'),'--','--output',str(output)]
        if args.render:command.append('--render')
        run_logged(command,output/'verify.log')
    # Environment versions are diagnostic evidence, not a claim of cross-platform certification.
    versions={}
    for name in ['numpy','Pillow','pyproj','rasterio','shapely','pyshp']:
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:pass
    write_json(output/'environment.json',{'python':sys.version.split()[0],'platform':platform.platform(),
                                        'blender':version,'libraries':versions})
    print('COMPLETE',output,flush=True)
    return 0


def run_logged(command,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    print('BLENDER_STAGE',Path(command[command.index('--python')+1]).name,flush=True)
    with path.open('w',encoding='utf-8') as log:
        process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if process.returncode:
        lines=path.read_text(errors='replace').splitlines()[-25:]
        raise RuntimeError(f'Blender exited {process.returncode}. See {path}\n'+'\n'.join(lines))
    print('LOG',path,flush=True)


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('ERROR:',e,file=sys.stderr);sys.exit(1)
