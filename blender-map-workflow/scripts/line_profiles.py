"""Flat cartographic curve strokes; keep geographic paths editable without tubes."""
import bpy


def flat_profile(data, half_width, collection_name='13_LINE_PROFILES'):
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    # One small shared open cross-section for each stroke width.
    name = 'Flat stroke / ' + format(half_width, '.8f')
    profile = bpy.data.objects.get(name)
    if profile is None:
        curve = bpy.data.curves.new(name, 'CURVE')
        curve.dimensions = '2D'; curve.resolution_u = 1
        spline = curve.splines.new('POLY'); spline.points.add(1)
        spline.points[0].co = (-half_width, 0, 0, 1)
        spline.points[1].co = (half_width, 0, 0, 1)
        profile = bpy.data.objects.new(name, curve)
        collection.objects.link(profile)
        profile.hide_render = True; profile.hide_set(True)
    enums = {e.identifier for e in data.bl_rna.properties['bevel_mode'].enum_items}
    if 'OBJECT' not in enums:
        raise RuntimeError('This Blender version lacks object bevel profiles')
    data.bevel_mode = 'OBJECT'; data.bevel_object = profile
    data.twist_mode = 'Z_UP'; data.use_fill_caps = False
    return profile


def is_flat(data):
    p = data.bevel_object
    if data.bevel_mode != 'OBJECT' or p is None or data.twist_mode != 'Z_UP':
        return False
    return (len(p.data.splines) == 1 and len(p.data.splines[0].points) == 2
            and all(abs(v.co.y) < 1e-8 and abs(v.co.z) < 1e-8 for v in p.data.splines[0].points))

