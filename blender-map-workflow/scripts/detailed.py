"""Network-free orchestration of the checked, packed NC scene template."""
import json
import math
import re
from datetime import datetime
from pathlib import Path

from common import discover_blender, sha256, write_json
from template_assets import assemble

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / 'templates'


def validate(config):
    unknown = set(config) - {'schema_version', 'mode', 'name', 'slug', 'frame', 'rig', 'target_location', 'dof', 'detail', 'ocean', 'render'}
    if unknown:
        raise ValueError('Unsupported detailed configuration fields: ' + ', '.join(sorted(unknown)))
    if config.get('schema_version') != 1 or config.get('mode') != 'detailed-template':
        raise ValueError('Expected schema_version 1 and detailed-template mode')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', config.get('slug', '')):
        raise ValueError('Invalid output slug')
    if not isinstance(config['frame'], int):
        raise ValueError('frame must be an integer')
    for key in ('width', 'height', 'samples'):
        if not isinstance(config['render'][key], int) or config['render'][key] <= 0:
            raise ValueError('Render dimensions and samples must be positive integers')
    if not isinstance(config['dof']['enabled'], bool) or not 0.1 <= config['dof']['aperture'] <= 128:
        raise ValueError('DOF requires a boolean enabled and aperture in [0.1,128]')
    limits = {'detail': {'Land cover amount': (0, 1), 'Wetland amount': (0, 1), 'Lowland relief boost': (0, 2)},
              'ocean': {'Ripple strength': (0, 1), 'Color variation': (0, 1), 'Water roughness': (.1, .8), 'Drift speed': (0, 1)},
              'rig': {'Orbit (degrees)': (-360, 360), 'Tilt (degrees)': (5, 89), 'Distance': (1, 1000), 'Focal length (mm)': (15, 200)}}
    for group, props in limits.items():
        for key, value in config.get(group, {}).items():
            if key not in props or not isinstance(value, (int, float)) or not math.isfinite(value) or not props[key][0] <= value <= props[key][1]:
                raise ValueError('Invalid control: ' + key)
    target = config.get('target_location')
    if target is not None and (len(target) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in target)):
        raise ValueError('target_location must contain three finite map coordinates')


def run(args):
    from map import run_logged
    output = args.output.resolve()
    if args.stage == 'verify':
        project = json.loads((output / 'project.json').read_text())
        config = project['config']
    else:
        config = json.loads(args.config.read_text())
        validate(config)
        if args.stage == 'prepare':
            raise ValueError('Detailed mode is already prepared; use run or build')
        if list(output.glob('*.blend')):
            if not args.overwrite:
                raise RuntimeError('Output contains a scene. Choose a new directory or --overwrite for a backup.')
            import shutil
            backup = output.with_name(output.name + '.backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            shutil.copytree(output, backup)
        template, manifest = assemble(TEMPLATES, (args.cache or output.parent / 'cache').resolve())
        output.mkdir(parents=True, exist_ok=True)
        (output / 'renders').mkdir(exist_ok=True)
        write_json(output / 'config.json', config)
        project = {'config': config, 'config_sha256': sha256(output / 'config.json'),
                   'template_manifest': manifest, 'sources': json.loads((TEMPLATES / 'sources.json').read_text())}
        write_json(output / 'project.json', project)
    blender, version = discover_blender(args.blender)
    # This scene uses 5.2 compositor APIs. Do not imply compatibility with older versions.
    import re
    match = re.search(r'Blender (\d+)\.(\d+)', version)
    if not match or tuple(map(int, match.groups())) < (5, 2):
        raise RuntimeError('The detailed template requires stable Blender >= 5.2; tested on 5.2.2 LTS')
    if args.stage in ('build', 'run'):
        cmd = [blender, '--background', '--factory-startup', str(template), '--python-exit-code', '1', '--python', str(HERE / 'detailed_scene.py'), '--', '--output', str(output)]
        if args.no_render:
            cmd.append('--no-render')
        run_logged(cmd, output / 'build.log')
    if args.stage in ('verify', 'run'):
        cmd = [blender, '--background', '--factory-startup', str(output / (config['slug'] + '.blend')), '--python-exit-code', '1', '--python', str(HERE / 'detailed_scene.py'), '--', '--output', str(output), '--verify']
        if args.render:
            cmd.append('--render')
        run_logged(cmd, output / 'verify.log')
    print('COMPLETE', output, flush=True)
    return 0
