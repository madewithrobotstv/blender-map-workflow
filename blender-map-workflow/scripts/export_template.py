"""Export a reviewed packed map template from a saved scene in background Blender.

Run Blender --background INPUT.blend --python export_template.py -- --output DIR.
Keeps geometry, shaders, constraints, drivers, animations and the current shot.
Removes project notes and machine paths; review the audit before redistribution.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import bpy
import numpy as np


REDACT_TERMS = []


def clean(value):
    for term in REDACT_TERMS:
        value = re.sub(re.escape(term), 'Map', value, flags=re.I)
    return value


def blocks():
    seen = set()
    for prop in bpy.data.bl_rna.properties:
        if prop.type != 'COLLECTION':
            continue
        for block in getattr(bpy.data, prop.identifier):
            if isinstance(block, bpy.types.ID) and block.as_pointer() not in seen:
                seen.add(block.as_pointer())
                yield block
                tree = getattr(block, 'node_tree', None)
                if tree and tree.as_pointer() not in seen:
                    seen.add(tree.as_pointer())
                    yield tree


def signature():
    """Appearance-bearing arrays and packed bytes must survive cleanup unchanged."""
    result = {'meshes': {}, 'packed': {}, 'camera': {}, 'material_links': {}}
    for mesh in bpy.data.meshes:
        digest = hashlib.sha256()
        for collection, key, shape, dtype in [(mesh.vertices, 'co', 3, 'f4'),
                                              (mesh.loops, 'vertex_index', 1, 'i4'),
                                              (mesh.polygons, 'loop_total', 1, 'i4')]:
            arr = np.empty(len(collection) * shape, dtype=dtype)
            collection.foreach_get(key, arr)
            digest.update(arr.tobytes())
        result['meshes'][clean(mesh.name)] = digest.hexdigest()
    for image in bpy.data.images:
        if image.packed_file:
            result['packed'][clean(image.name)] = hashlib.sha256(image.packed_file.data).hexdigest()
    for font in bpy.data.fonts:
        if font.packed_file:
            result['packed'][clean(font.name)] = hashlib.sha256(font.packed_file.data).hexdigest()
    for mat in bpy.data.materials:
        if mat.use_nodes:
            result['material_links'][clean(mat.name)] = sorted([[clean(l.from_node.name), l.from_socket.identifier, clean(l.to_node.name), l.to_socket.identifier] for l in mat.node_tree.links])
    camera = bpy.context.scene.camera
    result['camera'] = {'matrix': [list(row) for row in camera.matrix_world],
                        'lens': camera.data.lens, 'aperture': camera.data.dof.aperture_fstop,
                        'frame': bpy.context.scene.frame_current}
    return result


def main(output, font_path=None):
    if not bpy.app.background or not bpy.data.filepath:
        raise RuntimeError('Open an existing saved scene in a separate background process')
    output.mkdir(parents=True, exist_ok=True)
    destination = output / 'north-carolina-detailed.blend'
    if destination.exists():
        raise RuntimeError('Choose a new output folder; export never replaces a template')
    bpy.context.view_layer.update()
    substitution = None
    reference = signature()
    if font_path:
        original_fonts = list(bpy.data.fonts)
        replacement = bpy.data.fonts.load(str(font_path)); replacement.pack()
        for curve in bpy.data.curves:
            if isinstance(curve, bpy.types.TextCurve):
                for key in ('font', 'font_bold', 'font_italic', 'font_bold_italic'):
                    setattr(curve, key, replacement)
        substitution = {'original_families': [f.name for f in original_fonts], 'replacement_family': replacement.name}
        for font in original_fonts:
            bpy.data.fonts.remove(font)
    before = signature()
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)
    # Numeric driver controls survive. Replace all free-form project notes rather
    # than trying to guess whether an old note contains private information.
    for block in blocks():
        if not block.is_property_readonly('name'):
            public_name = clean(block.name)
            if public_name != block.name:
                block.name = 'X' * 60
                block.name = public_name
        for key in list(block.keys()):
            if key == '_RNA_UI' or isinstance(block[key], str):
                del block[key]
        if isinstance(block, bpy.types.NodeTree):
            for node in block.nodes:
                node.name = clean(node.name)
                node.label = clean(node.label)
        for key in block.keys():
            try:
                info = block.id_properties_ui(key).as_dict()
                if info.get('description'):
                    block.id_properties_ui(key).update(description='Map control; see START HERE')
            except (TypeError, KeyError):
                pass
    for action in bpy.data.actions:
        for slot in action.slots:
            name = clean(slot.name_display)
            slot.name_display = 'X' * 60
            slot.name_display = name
    for curve in bpy.data.curves:
        if isinstance(curve, bpy.types.TextCurve):
            curve.body = clean(curve.body)
    for index, image in enumerate(list(bpy.data.images)):
        if image.type in ('RENDER_RESULT', 'COMPOSITING'):
            bpy.data.images.remove(image)
        elif image.source == 'FILE' or image.packed_file:
            if not image.packed_file:
                image.pack()
            public_path = '//packed/' + (Path(image.filepath).name or f'image-{index:02}.png')
            image.filepath = ' ' * 1023
            image.filepath = public_path
            for packed in image.packed_files:
                packed.filepath = ' ' * 1023
                packed.filepath = public_path
    for font in bpy.data.fonts:
        if font.filepath != '<builtin>':
            if not font.packed_file:
                font.pack()
            public_path = '//packed/fonts/' + Path(font.filepath).name
            font.filepath = ' ' * 1023
            font.filepath = public_path
    if bpy.data.libraries or bpy.data.sounds or bpy.data.movieclips:
        raise RuntimeError('Linked libraries/audio/video require a separate redistribution review')
    for scene in bpy.data.scenes:
        scene.render.filepath = ' ' * 1023
        scene.render.filepath = '//renders/overview.png'
        for layer in scene.view_layers:
            layer.use_pass_cryptomatte_object = False
            layer.use_pass_cryptomatte_material = False
        scene['Map attribution'] = 'USGS 3DEP and Annual NLCD 2025; FWS NWI; Census; NC OneMap; NC DEQ. See sources.json.'
        scene['Template version'] = 2
    for screen in bpy.data.screens:
        for area in screen.areas:
            for space in area.spaces:
                if space.type == 'TEXT_EDITOR':
                    space.text = None
                if space.type == 'FILE_BROWSER' and space.params:
                    space.params.directory = b' ' * 1023
                    space.params.directory = b''
                    space.params.filename = ' ' * 255
                    space.params.filename = ''
    bpy.context.preferences.filepaths.save_version = 0
    bpy.data.texts.new('START HERE / Detailed map').write(
        'NORTH CAROLINA / CAPE FEAR DETAILED MAP\n'
        'All terrain/map-ink textures and the public font are packed; no original folder required.\n'
        'Move CAMERA_RIG to pan; use its custom properties to orbit, tilt, dolly and zoom.\n'
        'Move Camera Target | Aim and Focus to aim and pull focus. Camera DOF uses this same target.\n'
        'MAP_DETAIL_CONTROLS: land cover, wetlands, lowland normal strength.\n'
        'Atlantic_Ocean_Surface: ripple strength, color variation, roughness, drift speed.\n'
        'RELIEF_CONTROL_scale_Z: scale Z to adjust terrain and draped overlays together.\n'
        'V2 rivers and state borders are printed terrain ink; raised curves remain hidden in archives.\n'
        'TERRAIN_DEPTH_CONTROLS: shared geometry-node height, relief and channel-depth controls.\n'
        'Coast taper masks blend the terrain into the independent ocean plane.\n'
        'County labels and optional watershed are hidden by default.\n'
        'Existing camera and target keyframes and the stored current shot are retained.\n'
        'This is a fixed NC data snapshot. Changing state requires new geographic data.\n'
        'See detailed-map.md and sources.json in the distributed workflow.\n')
    for license_file in sorted((output / 'licenses').glob('*.txt')):
        bpy.data.texts.new('LICENSE / ' + license_file.stem).write(license_file.read_text())
    after = signature()
    if before != after:
        raise RuntimeError('Cleanup changed geometry, packed assets, or current camera pose')
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True, relative_remap=False)
    manifest = {'schema_version': 1, 'blender': bpy.app.version_string, 'frame': bpy.context.scene.frame_current,
                'template_file': destination.name, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                'file_bytes': destination.stat().st_size, 'appearance_signature': after,
                'collections': {c.name: len(c.objects) for c in bpy.data.collections},
                'terrain_vertices': sum(len(o.data.vertices) for o in bpy.data.collections['01_TERRAIN'].objects if o.type == 'MESH'),
                'packed_images': sum(bool(i.packed_file) for i in bpy.data.images),
                'packed_fonts': sum(bool(f.packed_file) for f in bpy.data.fonts),
                'reference_signature': reference, 'font_substitution': substitution}
    (output / 'template-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('EXPORTED', destination.name, manifest['file_bytes'], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--font', type=Path, help='Optional licensed public replacement for all label fonts')
    p.add_argument('--redact-term', action='append', default=[], help='Project name to replace in exported names/labels; repeat as needed')
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    REDACT_TERMS = a.redact_term
    main(a.output.resolve(), a.font)
