"""Configure or verify the packed NC detailed template in background Blender."""
import argparse
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import sha256, write_json
from export_template import signature, blocks


def audit():
    findings = []
    forbidden = ('/users/', '/home/', '/applications/', 'c:\\users\\')
    strings = []
    for block in blocks():
        strings.append((block.name, block.name))
        for prop in block.bl_rna.properties:
            if prop.type == 'STRING':
                value = getattr(block, prop.identifier, '')
                if isinstance(value, str):
                    strings.append((block.name + '.' + prop.identifier, value))
        for key, value in block.items():
            if isinstance(value, str):
                strings.append((block.name + '.' + key, value))
        if isinstance(block, bpy.types.Text):
            strings.append((block.name, block.as_string()))
        if isinstance(block, bpy.types.NodeTree):
            for node in block.nodes:
                strings.extend([(block.name + '.node', node.name), (block.name + '.label', node.label)])
    for image in bpy.data.images:
        for packed in image.packed_files:
            strings.append((image.name + '.packed_filepath', packed.filepath))
    for owner, value in strings:
        if any(word in value.lower() for word in forbidden):
            findings.append(owner)  # Do not print the private value in a shareable report.
    external = []
    for seq in (bpy.data.images, bpy.data.fonts):
        for item in seq:
            if getattr(item, 'source', '') == 'FILE' or isinstance(item, bpy.types.VectorFont):
                if getattr(item, 'filepath', '') not in ('', '<builtin>') and not item.packed_file:
                    external.append(item.name)
    return {'inspected_strings': len(strings), 'private_reference_fields': findings,
            'unpacked_assets': external, 'linked_libraries': len(bpy.data.libraries),
            'passed': not findings and not external and not bpy.data.libraries}


def verify(output, render=False):
    project = json.loads((output / 'project.json').read_text())
    manifest = project['template_manifest']
    scene = bpy.context.scene
    scene.frame_set(project['config']['frame'])
    bpy.context.view_layer.update()
    camera = scene.camera
    target = bpy.data.objects.get('Camera Target | Aim and Focus')
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
    check('configuration_matches', scene.get('Map config SHA256') == project['config_sha256'])
    check('template_origin_matches', scene.get('Template SHA256') == manifest['sha256'])
    check('one_perspective_camera', len(bpy.data.cameras) == 1 and camera.data.type == 'PERSP')
    check('aim_and_focus_share_target', target is not None and camera.data.dof.focus_object == target and any(c.type == 'DAMPED_TRACK' and c.target == target for c in camera.constraints))
    check('dof_matches_config', camera.data.dof.use_dof == project['config']['dof']['enabled'] and abs(camera.data.dof.aperture_fstop - project['config']['dof']['aperture']) < 1e-5)
    archives = [c for c in bpy.data.collections if c.name.startswith('Archive | raised')]
    check('raised_river_boundary_archives_hidden',len(archives)==2 and all(c.hide_render or all(o.hide_render for o in c.objects) for c in archives))
    check('printed_ink_masks_packed',len([i for i in bpy.data.images if i.name.startswith('Map ink |') and i.packed_file])==4)
    check('coast_taper_masks_packed',len([i for i in bpy.data.images if i.name.startswith('Coast taper |') and i.packed_file])==3)
    check('terrain_depth_controls_present','TERRAIN_DEPTH_CONTROLS' in bpy.data.objects)
    check('collection_counts_match', all(n in bpy.data.collections and len(bpy.data.collections[n].objects) == v for n, v in manifest['collections'].items()))
    current = signature()
    check('exact_geometry_matches', current['meshes'] == manifest['appearance_signature']['meshes'])
    if 'material_links' in manifest['appearance_signature']:
        check('material_connections_match',current['material_links']==manifest['appearance_signature']['material_links'])
    check('packed_assets_match', current['packed'] == manifest['appearance_signature']['packed'])
    check('packed_image_count_matches', sum(bool(i.packed_file) for i in bpy.data.images) == manifest['packed_images'])
    check('packed_font_count_matches', sum(bool(f.packed_file) for f in bpy.data.fonts) == manifest['packed_fonts'])
    check('no_frame_handlers', not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post)
    drivers = []
    for block in blocks():
        if getattr(block, 'animation_data', None):
            drivers.extend(block.animation_data.drivers)
    check('drivers_valid', bool(drivers) and all(c.driver.is_valid for c in drivers))
    ocean = bpy.data.objects['Atlantic_Ocean_Surface']
    wave = next(n for n in ocean.data.materials[0].node_tree.nodes if n.type == 'TEX_WAVE')
    frame = scene.frame_current
    scene.frame_set(1); bpy.context.view_layer.update()
    start_phase = wave.inputs['Phase Offset'].default_value
    scene.frame_set(25); bpy.context.view_layer.update()
    delta = wave.inputs['Phase Offset'].default_value - start_phase
    expected = 24 * scene.render.fps_base / scene.render.fps * ocean['Drift speed']
    check('ocean_drift_follows_frame_rate', abs(delta - expected) < 1e-5)
    scene.frame_set(frame); bpy.context.view_layer.update()
    check('camera_and_target_animation_retained', camera.animation_data is not None and camera.animation_data.action is not None and (project['config'].get('target_location') is not None or (target.animation_data is not None and target.animation_data.action is not None)))

    original = target.location.copy()
    target.location.x += .25
    target.update_tag(); bpy.context.view_layer.update()
    direction = -(camera.matrix_world.to_quaternion() @ Vector((0, 0, 1)))
    to_target = (target.matrix_world.translation - camera.matrix_world.translation).normalized()
    check('moving_null_aims_camera', direction.dot(to_target) > .9999)
    target.location = original; target.update_tag(); bpy.context.view_layer.update()
    privacy = audit()
    check('portable_asset_audit', privacy['passed'])
    report = {'blender': bpy.app.version_string, 'checks': checks, 'passed': all(checks.values()),
              'terrain_vertices': manifest['terrain_vertices'], 'privacy': privacy,
              'frame': scene.frame_current, 'driver_count': len(drivers)}
    if render:
        scene.render.filepath = str(output / 'renders' / 'verified.png')
        start = time.perf_counter(); bpy.ops.render.render(write_still=True)
        report['reopened_render_seconds'] = time.perf_counter() - start
    write_json(output / 'verification-report.json', report)
    print('VERIFICATION', json.dumps(report), flush=True)
    if not report['passed']:
        raise RuntimeError('Detailed verification failed: ' + ', '.join(k for k, v in checks.items() if not v))


def build(output, render=True):
    project = json.loads((output / 'project.json').read_text())
    config = project['config']
    scene = bpy.context.scene
    scene.frame_set(config['frame']); bpy.context.view_layer.update()
    # None means preserve the exact stored pose at the selected frame.
    rig = bpy.data.objects['CAMERA_RIG']
    for key, value in config.get('rig', {}).items():
        # An explicit control edit overrides its own keys, not unrelated animation.
        if rig.animation_data and rig.animation_data.action:
            raise RuntimeError('Rig is keyed; edit its action explicitly instead of overriding controls')
        rig[key] = float(value)
    if config.get('target_location') is not None:
        target = bpy.data.objects['Camera Target | Aim and Focus']
        if target.animation_data:
            target.animation_data.action = None
        target.location = config['target_location']
    camera = scene.camera
    camera.data.dof.use_dof = config['dof']['enabled']
    camera.data.dof.aperture_fstop = config['dof']['aperture']
    detail = bpy.data.objects['MAP_DETAIL_CONTROLS']
    for key, value in config['detail'].items():
        detail[key] = float(value)
    ocean = bpy.data.objects['Atlantic_Ocean_Surface']
    for key, value in config['ocean'].items():
        ocean[key] = float(value)
    for obj in (rig, detail, ocean):
        obj.update_tag()
    scene.render.resolution_x = config['render']['width']
    scene.render.resolution_y = config['render']['height']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.use_stamp = False
    scene.render.use_lock_interface = True
    if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = config['render']['samples']
    scene['Map config SHA256'] = project['config_sha256']
    scene['Template SHA256'] = project['template_manifest']['sha256']
    bpy.context.view_layer.update()
    scene.render.filepath = '//renders/overview.png'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / (config['slug'] + '.blend')), compress=True, relative_remap=False)
    start = time.perf_counter()
    if render:
        scene.render.filepath = str(output / 'renders' / 'overview.png')
        bpy.ops.render.render(write_still=True)
    write_json(output / 'build-report.json', {'mode': 'detailed-template', 'blender': bpy.app.version_string,
               'template_sha256': project['template_manifest']['sha256'], 'frame': scene.frame_current,
               'render_seconds': time.perf_counter() - start if render else None,
               'terrain_vertices': project['template_manifest']['terrain_vertices']})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--verify', action='store_true')
    p.add_argument('--no-render', action='store_true')
    p.add_argument('--render', action='store_true')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if a.verify:
        verify(a.output.resolve(), a.render)
    else:
        build(a.output.resolve(), not a.no_render)
