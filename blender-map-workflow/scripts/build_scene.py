"""Run with Blender --background --factory-startup --python ... -- --output DIR."""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import sample_surface, write_json


def color(value):
    rgb = [int(value.lstrip('#')[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb) + (1,)


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def simple_material(name, value, emission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = color(value)
    shader.inputs['Roughness'].default_value = .82
    shader.inputs['Metallic'].default_value = 0
    if 'Emission Color' in shader.inputs:
        shader.inputs['Emission Color'].default_value = color(value)
        shader.inputs['Emission Strength'].default_value = emission
    return mat


def driver(owner, path, index, target, key, expression='value'):
    curve = owner.driver_add(path) if index is None else owner.driver_add(path, index)
    v = curve.driver.variables.new()
    v.name = 'value'; v.type = 'SINGLE_PROP'
    v.targets[0].id = target; v.targets[0].data_path = '["' + key + '"]'
    curve.driver.expression = expression


def empty(name, target, parent=None):
    obj = bpy.data.objects.new(name, None)
    target.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = .5
    return obj


def mesh_object(name, vertices, faces, target):
    vertices = np.asarray(vertices, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(vertices)); mesh.vertices.foreach_set('co', vertices.ravel())
    mesh.loops.add(faces.size); mesh.loops.foreach_set('vertex_index', faces.ravel())
    mesh.polygons.add(len(faces)); mesh.polygons.foreach_set('loop_start', np.arange(len(faces), dtype=np.int32) * faces.shape[1])
    mesh.polygons.foreach_set('loop_total', np.full(len(faces), faces.shape[1], dtype=np.int32))
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    return obj


def curve_object(name, lines, target, mat, width, parent=None):
    data = bpy.data.curves.new(name, 'CURVE'); data.dimensions = '3D'
    data.resolution_u = 1; data.bevel_depth = width; data.bevel_resolution = 0; data.resolution_v = 0
    for coords in lines:
        if len(coords) < 2:
            continue
        spline = data.splines.new('POLY'); spline.points.add(len(coords) - 1)
        array = np.c_[coords, np.ones(len(coords))].astype(np.float32)
        spline.points.foreach_set('co', array.ravel())
    obj = bpy.data.objects.new(name, data); target.objects.link(obj)
    obj.parent = parent; data.materials.append(mat)
    return obj


def text_object(name, body, position, size, target, mat, camera=None, parent=None):
    data = bpy.data.curves.new(name, 'FONT'); data.body = body
    data.size = size; data.align_x = 'CENTER'; data.align_y = 'CENTER'; data.extrude = 0
    obj = bpy.data.objects.new(name, data); target.objects.link(obj)
    obj.parent = parent; obj.location = position; data.materials.append(mat)
    if camera:
        constraint = obj.constraints.new('COPY_ROTATION'); constraint.target = camera
        constraint.owner_space = 'WORLD'; constraint.target_space = 'WORLD'
    return obj


def terrain_material(panel, config, output):
    mat = bpy.data.materials.new('Relief / ' + panel['id']); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    shader.inputs['Roughness'].default_value = .88
    attr = nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'Elevation_m'
    maximum = config['style']['palette'][-1][0]
    divide = nodes.new('ShaderNodeMath'); divide.operation = 'DIVIDE'; divide.inputs[1].default_value = maximum
    links.new(attr.outputs['Fac'], divide.inputs[0])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation = 'LINEAR'
    entries = config['style']['palette']
    for i, (height, value) in enumerate(entries):
        element = ramp.color_ramp.elements[i] if i < 2 else ramp.color_ramp.elements.new(height / maximum)
        element.position = height / maximum; element.color = color(value)
    links.new(divide.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs['Color'], shader.inputs['Base Color'])
    if config['style'].get('contours'):
        mod = nodes.new('ShaderNodeMath'); mod.operation = 'MODULO'
        mod.inputs[1].default_value = config['style']['contour_interval_m']
        links.new(attr.outputs['Fac'], mod.inputs[0])
        test = nodes.new('ShaderNodeMath'); test.operation = 'LESS_THAN'
        test.inputs[1].default_value = config['style']['contour_interval_m'] * .035
        links.new(mod.outputs[0], test.inputs[0])
        amount = nodes.new('ShaderNodeMath'); amount.operation = 'MULTIPLY'; amount.inputs[1].default_value = .22
        links.new(test.outputs[0], amount.inputs[0])
        mix = nodes.new('ShaderNodeMixRGB'); mix.inputs[2].default_value = color('#493d30')
        links.new(amount.outputs[0], mix.inputs[0]); links.new(ramp.outputs['Color'], mix.inputs[1])
        links.new(mix.outputs[0], shader.inputs['Base Color'])
    image = bpy.data.images.load(str(output / 'assets' / f'{panel["id"]}-normal.png'))
    image.colorspace_settings.name = 'Non-Color'; image.pack()
    image.filepath = f'//assets/{panel["id"]}-normal.png'
    texture = nodes.new('ShaderNodeTexImage'); texture.image = image; texture.extension = 'EXTEND'
    normal = nodes.new('ShaderNodeNormalMap'); normal.space = 'OBJECT'
    links.new(texture.outputs['Color'], normal.inputs['Color']); links.new(normal.outputs['Normal'], shader.inputs['Normal'])
    return mat


def build(output, render=True):
    started = time.perf_counter()
    output = Path(output).resolve()
    project = json.loads((output / 'project.json').read_text())
    config = project['config']
    if bpy.app.version < (4, 5, 0) or any(s in bpy.app.version_string.lower() for s in ('alpha', 'beta', 'candidate')):
        raise RuntimeError('Use a stable Blender release >= 4.5')
    # Intended for factory-startup or a new scene. Never clears an artist's existing scene.
    if bpy.data.filepath or not bpy.app.background:
        raise RuntimeError('Build only in a new background Blender process with --factory-startup; preserve any live artist scene')
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    scene = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    else:
        raise RuntimeError('EEVEE unavailable')
    scene.render.resolution_x = config['render']['width']; scene.render.resolution_y = config['render']['height']
    scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = 'PNG'
    scene.render.use_lock_interface = True; scene.render.film_transparent = False
    if hasattr(scene, 'eevee'):
        for key, value in [('taa_render_samples', config['render']['samples']), ('taa_samples', 16), ('use_raytracing', False)]:
            if hasattr(scene.eevee, key):
                setattr(scene.eevee, key, value)
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.exposure = 0; scene.view_settings.gamma = 1
    scene.world.use_nodes = True
    bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = color('#b8c8c9'); bg.inputs['Strength'].default_value = .65
    terrain_c = collection('01_TERRAIN'); boundary_c = collection('02_BOUNDARIES')
    vectors_c = collection('03_HYDROGRAPHY'); labels_c = collection('04_LABELS')
    water_c = collection('05_OCEAN'); lights_c = collection('06_LIGHTING'); cameras_c = collection('07_CAMERA_RIG')
    layout_c = collection('08_LAYOUT')
    boundary_mat = simple_material('State boundaries', config['style']['boundary'], .25)
    text_mat = simple_material('Labels', config['style']['text'], .7)
    muted_mat = simple_material('Water labels', '#81a6b1', .4)
    # Plain plane keeps ocean cost constant. All meaningful geography remains independent.
    ocean = mesh_object('Ocean', [[-110,-90,-.06],[110,-90,-.06],[110,90,-.06],[-110,90,-.06]], [[0,1,2,3]], water_c)
    ocean.data.materials.append(simple_material('Ocean / matte blue', config['style']['water']))
    rig = empty('CAMERA_RIG', cameras_c); rig.location = config['camera']['target']
    settings = [('Orbit (degrees)', config['camera']['orbit_degrees'], -360, 360),
                ('Tilt (degrees)', config['camera']['tilt_degrees'], 5, 89),
                ('Distance', config['camera']['distance'], 1, 1000),
                ('Focal length (mm)', config['camera']['focal_length_mm'], 15, 200)]
    for key, value, low, high in settings:
        rig[key] = float(value); rig.id_properties_ui(key).update(min=low, max=high, description='Keyframe this control; pan by moving CAMERA_RIG')
    yaw = empty('Rig / Orbit', cameras_c, rig); pitch = empty('Rig / Tilt', cameras_c, yaw); dolly = empty('Rig / Dolly', cameras_c, pitch)
    driver(yaw,'rotation_euler',2,rig,'Orbit (degrees)','value * 0.017453292519943295')
    driver(pitch,'rotation_euler',0,rig,'Tilt (degrees)','-value * 0.017453292519943295')
    driver(dolly,'location',1,rig,'Distance','-value')
    camera_data = bpy.data.cameras.new('Map camera'); camera = bpy.data.objects.new('Map camera', camera_data)
    cameras_c.objects.link(camera); camera.parent = dolly; camera.matrix_parent_inverse = Matrix.Identity(4)
    camera.rotation_euler = (math.pi/2,0,0); camera.data.sensor_fit = 'HORIZONTAL'; camera.data.clip_start = .02; camera.data.clip_end = 1000
    driver(camera.data,'lens',None,rig,'Focal length (mm)'); scene.camera = camera
    report = {'blender': bpy.app.version_string, 'engine': scene.render.engine,
              'gpu_backend': bpy.context.preferences.system.gpu_backend, 'panels': [], 'config_sha256': project['config_sha256']}
    units = config['metres_per_unit']
    for panel in project['panels']:
        data = np.load(output/'assets'/f'{panel["id"]}-terrain.npz')
        elevation, valid = data['elevation'], data['valid']
        h,w = elevation.shape; bounds = panel['bounds']; cx,cy = panel['center']
        root = empty('MAP / ' + panel['title'], terrain_c)
        root.location = (*panel['position'],0); root.scale.x = root.scale.y = panel['scale']
        root.scale.z = panel['scale']; root['Vertical exaggeration'] = float(panel['relief'])
        root.id_properties_ui('Vertical exaggeration').update(min=1, max=200, description='Scale physical DEM elevations and all draped overlays together')
        driver(root,'scale',2,root,'Vertical exaggeration',f'value * {panel["scale"] / panel["relief"]}')
        root['CRS'] = panel['crs']; root['Projected origin (m)'] = panel['center']; root['Metres per unit'] = units
        xx,yy = np.meshgrid(np.linspace(bounds[0],bounds[2],w),np.linspace(bounds[3],bounds[1],h))
        z = np.maximum(np.nan_to_num(elevation),0) / units * panel['relief'] + .035
        vertices = np.stack([(xx-cx)/units,(yy-cy)/units,z],axis=-1).reshape(-1,3)
        grid = np.arange(w*h,dtype=np.int32).reshape(h,w)
        a = grid[:-1,:-1].ravel(); b=a+1; c=a+w; d=c+1
        keep = (valid[:-1,:-1]&valid[:-1,1:]&valid[1:,:-1]&valid[1:,1:]).ravel()
        faces = np.concatenate([np.stack([a,c,b],axis=1)[keep],np.stack([b,c,d],axis=1)[keep]])
        used=np.zeros(w*h,dtype=bool); used[faces.ravel()]=True
        remap=np.cumsum(used,dtype=np.int32)-1
        obj=mesh_object('Terrain / '+panel['title'],vertices[used],remap[faces],terrain_c); obj.parent=root
        obj.data.polygons.foreach_set('use_smooth',np.ones(len(faces),dtype=bool))
        attr=obj.data.attributes.new('Elevation_m','FLOAT','POINT'); attr.data.foreach_set('value',np.nan_to_num(elevation).ravel()[used].astype(np.float32))
        uv = obj.data.uv_layers.new(name='DEM coordinates')
        uu,vv=np.meshgrid(np.linspace(0,1,w),np.linspace(1,0,h))
        texcoords=np.stack([uu,vv],axis=-1).reshape(-1,2)[used]
        uv.data.foreach_set('uv',texcoords[remap[faces].ravel()].astype(np.float32).ravel())
        obj.data.materials.append(terrain_material(panel,config,output))
        obj['Source']='USGS 3DEP; source GeoTIFF retained in assets'
        obj['Display spacing (m)']=panel['mesh_spacing_m']; obj['Relief texture spacing (m)']=panel['source_spacing_m']
        def coords(points,offset=.02,water=False):
            p=np.asarray(points,dtype=float)[:,:2]
            heights=np.zeros(len(p)) if water else np.maximum(np.nan_to_num(sample_surface(elevation,bounds,p[:,0],p[:,1])),0)/units*panel['relief']+.035
            return np.c_[(p[:,0]-cx)/units,(p[:,1]-cy)/units,heights+offset]
        def label_position(point,text,size,water=False):
            # Raise the whole billboard above the highest local terrain under its glyph footprint.
            position=coords([point],.12,water)[0]
            if not water:
                radius=max(size*.6,len(text)*size*.31)*units
                sx,sy=np.meshgrid(np.linspace(point[0]-radius,point[0]+radius,9),np.linspace(point[1]-size*units,point[1]+size*units,5))
                highest=float(np.nanmax(np.maximum(np.nan_to_num(sample_surface(elevation,bounds,sx,sy)),0)))
                position[2]=highest/units*panel['relief']+.24
            return position
        vectors=json.loads((output/'assets'/f'{panel["id"]}-vectors.json').read_text())
        for state in vectors['states']:
            outline=curve_object('Boundary / '+state['name'],[coords(line) for line in state['lines']],boundary_c,boundary_mat,config['style']['boundary_width']/panel['scale'],root)
            outline['Census STATEFP']=state['fips']; outline['Source']='U.S. Census Bureau 2024 cartographic boundaries'
            if panel['id']=='conus' and state['area_m2']>3.8e10:
                label=text_object('State / '+state['name'],state['abbr'],label_position(state['label_xy'],state['abbr'],.32),.32,labels_c,text_mat,camera,root)
        for layer in vectors['additional']:
            mat=simple_material(layer['kind']+' / '+layer['name'],layer['color'],.25)
            if 'triangles' in layer:
                triangles=layer['triangles']
                if triangles:
                    points=np.asarray(triangles).reshape(-1,2)
                    waterbody=mesh_object('Waterbody / '+layer['name'],coords(points,.035),np.arange(len(points)).reshape(-1,3),vectors_c)
                    waterbody.parent=root;waterbody.data.materials.append(mat)
            else:
                river=curve_object('River / '+layer['name'],[coords(line,.04) for line in layer['lines']],vectors_c,mat,layer['width']/panel['scale'],root)
                river['Source']='Imported GeoJSON; attribution in project.json'
        for label in vectors['labels']:
            size=label['size']/panel['scale']
            text_object('Label / '+label['text'],label['text'],label_position(label['xy'],label['text'],size,label.get('water',False)),size,labels_c,muted_mat if label.get('water') else text_mat,camera,root)
        if panel['id']!='conus' and len(project['panels'])>1:
            px,py=panel['position']; panel_width=(bounds[2]-bounds[0])/units*panel['scale']; panel_height=(bounds[3]-bounds[1])/units*panel['scale']
            text_object('Inset / '+panel['id'],panel['title'].upper(),(px,py-panel_height/2-.9,.12),.36,layout_c,text_mat,camera)
            text_object('Inset scale / '+panel['id'],'INSET · INDEPENDENT SCALE',(px,py-panel_height/2-1.4,.12),.18,layout_c,muted_mat,camera)
        report['panels'].append({'id':panel['id'],'vertices':len(obj.data.vertices),'triangles':len(obj.data.polygons),'state_count':len(vectors['states']),
                                 'river_features':sum(v['kind']=='river' for v in vectors['additional']),
                                 'waterbody_features':sum(v['kind']=='waterbody' for v in vectors['additional']),
                                 'source_spacing_m':panel['source_spacing_m'],'mesh_spacing_m':panel['mesh_spacing_m'],'missing_land_fraction':panel['missing_land_fraction']})
        print('BUILT',panel['id'],len(obj.data.vertices),'vertices',flush=True)
    # Large typography is attached to the camera for stable graphic placement.
    depth=12;view_w=depth*36/config['camera']['focal_length_mm'];view_h=view_w*config['render']['height']/config['render']['width']
    title=text_object('Title',config['name'].upper(),(-.45*view_w,.425*view_h,-depth),.34,layout_c,text_mat,parent=camera)
    title.data.align_x='LEFT'
    subtitle=text_object('Subtitle','A STUDY IN RELIEF  /  REAL ELEVATION · EDITABLE GEOGRAPHY',(-.45*view_w,.372*view_h,-depth),.062,layout_c,muted_mat,parent=camera);subtitle.data.align_x='LEFT'
    footer=text_object('Attribution','USGS 3DEP  /  U.S. CENSUS BUREAU 2024    •    STYLIZED ELEVATION COLORS    •    VERTICAL RELIEF EXAGGERATED',(-.45*view_w,-.456*view_h,-depth),.052,layout_c,muted_mat,parent=camera);footer.data.align_x='LEFT'
    sun_data=bpy.data.lights.new('Raking sunlight','SUN');sun_data.energy=2.0;sun_data.angle=math.radians(12)
    sun=bpy.data.objects.new('Raking sunlight',sun_data);lights_c.objects.link(sun);sun.rotation_euler=(math.radians(28),math.radians(-22),math.radians(-25))
    scene['Map attribution']=project['attribution'];scene['Map config SHA256']=project['config_sha256']
    scene['Map units']='Projected metres centered locally; horizontal metres/unit: '+str(units)
    scene['Map palette']=project['palette_type'];scene['Build status']='No prebuilt animation. Keyframe CAMERA_RIG controls.'
    bpy.data.texts.new('START HERE / Map controls').write('Pan by moving CAMERA_RIG; keyframe Orbit, Tilt, Distance and Focal length custom properties.\nChange each MAP root Vertical exaggeration to adjust relief and draped overlays together.\nTerrain elevation attribute stores original metres. State borders, rivers, labels and ocean remain independently editable.\nSource rasters, request URLs, acquisition dates, SHA256 hashes and CRS metadata accompany this scene.\nRelief and palette are stylized. Alaska and Hawaii insets use independent scales; Hawaii includes the main islands.\nNo external add-on, driver handler, GIS library or local archive is needed to open this packed scene.\n')
    bpy.data.texts.new('PROVENANCE / project.json').write(json.dumps(project,indent=2))
    for obj in bpy.context.selected_objects:obj.select_set(False)
    rig.select_set(True);bpy.context.view_layer.objects.active=rig
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.lock_camera=False;area.spaces.active.shading.type='SOLID'
    scene.frame_set(1);bpy.context.view_layer.update()
    (output/'renders').mkdir(exist_ok=True)
    scene.render.filepath=str(output/'renders'/'overview.png')
    if render:
        t=time.perf_counter();bpy.ops.render.render(write_still=True);report['render_seconds']=time.perf_counter()-t
    scene.render.filepath='//renders/overview.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(output/(config['slug']+'.blend')),compress=True)
    report['total_seconds']=time.perf_counter()-started
    report['terrain_vertices']=sum(p['vertices'] for p in report['panels'])
    report['file_bytes']=(output/(config['slug']+'.blend')).stat().st_size
    report['packed_images']=sum(bool(i.packed_file) for i in bpy.data.images)
    write_json(output/'build-report.json',report)
    print('BUILD_COMPLETE',json.dumps(report),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--no-render',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    build(args.output,not args.no_render)
