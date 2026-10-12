"""Verify a saved scene in a separate Blender process; optionally render again."""
import argparse
import json
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import sample_surface, sha256, write_json


def verify(output, render=False):
    output=Path(output).resolve()
    project=json.loads((output/'project.json').read_text())
    scene=bpy.context.scene
    checks={}
    def check(name,condition):
        checks[name]=bool(condition)
    check('configuration_matches',scene.get('Map config SHA256')==project['config_sha256'])
    if (output/'config.json').exists():
        check('effective_config_hash_matches',sha256(output/'config.json')==project['config_sha256'])
    check('one_perspective_camera',sum(o.type=='CAMERA' for o in scene.objects)==1 and scene.camera.data.type=='PERSP')
    driver_curves=[]
    for datablock in list(bpy.data.objects)+list(bpy.data.cameras):
        if datablock.animation_data:driver_curves.extend(datablock.animation_data.drivers)
    scene.frame_set(1);bpy.context.view_layer.update()
    check('drivers_valid',len(driver_curves)>=5 and all(f.driver.is_valid for f in driver_curves))
    images=[i for i in bpy.data.images if i.type=='IMAGE' and i.source=='FILE']
    check('all_images_packed',len(images)==len(project['panels']) and all(i.packed_file for i in images))
    check('no_absolute_asset_paths',all(i.filepath.startswith('//') for i in images))
    boundaries=[o for o in bpy.data.collections['02_BOUNDARIES'].objects if o.type=='CURVE']
    expected=[f for p in project['panels'] for f in p['state_fips']]
    check('boundaries_complete',sorted(o.get('Census STATEFP') for o in boundaries)==sorted(expected))
    hydro=bpy.data.collections['03_HYDROGRAPHY'].objects
    vector_checks=True
    for panel in project['panels']:
        vector_file=output/'assets'/f'{panel["id"]}-vectors.json'
        if vector_file.exists():
            items=json.loads(vector_file.read_text())['additional']
            expected_rivers=sum(v['kind']=='river' for v in items)
            expected_lakes=sum(v['kind']=='waterbody' and bool(v.get('triangles')) for v in items)
            actual=[o for o in hydro if o.parent and o.parent.name=='MAP / '+panel['title']]
            vector_checks &= sum(o.type=='CURVE' for o in actual)==expected_rivers and sum(o.type=='MESH' for o in actual)==expected_lakes
    check('imported_vectors_present',vector_checks)
    drape_errors=[]
    for panel in project['panels']:
        grid_path=output/'assets'/f'{panel["id"]}-terrain.npz'
        if not grid_path.exists():continue
        elevation=np.load(grid_path)['elevation'];cx,cy=panel['center'];units=project['config']['metres_per_unit']
        for obj in list(boundaries)+list(hydro):
            if obj.type!='CURVE' or not obj.parent or obj.parent.name!='MAP / '+panel['title']:continue
            offset=.02 if obj in boundaries else .04
            for spline in obj.data.splines:
                data=np.empty(len(spline.points)*4,dtype=np.float32);spline.points.foreach_get('co',data)
                points=data.reshape(-1,4)
                heights=np.maximum(np.nan_to_num(sample_surface(elevation,panel['bounds'],points[:,0].astype(float)*units+cx,points[:,1].astype(float)*units+cy)),0)/units*panel['relief']+.035+offset
                if len(points):drape_errors.append(float(np.max(np.abs(points[:,2]-heights))))
    if drape_errors:check('overlays_match_display_surface',max(drape_errors)<2e-5)
    terrains=[o for o in bpy.data.collections['01_TERRAIN'].objects if o.type=='MESH']
    check('one_terrain_per_panel',len(terrains)==len(project['panels']))
    check('terrain_finite',all(all(math_isfinite(v.co) for v in o.data.vertices) for o in terrains))
    check('physical_elevation_attribute',all('Elevation_m' in o.data.attributes for o in terrains))
    check('triangulated_terrain',all(all(len(p.vertices)==3 for p in o.data.polygons) for o in terrains))
    check('provenance_embedded','PROVENANCE / project.json' in bpy.data.texts)
    check('no_python_frame_handlers',not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post)
    # Verify the terrain transforms and rig survive serialization, including changes to controls.
    rig=bpy.data.objects['CAMERA_RIG'];initial=scene.camera.matrix_world.translation.copy()
    distance=rig['Distance'];rig['Distance']=distance*.8;rig.update_tag();scene.frame_set(2);bpy.context.view_layer.update()
    moved=(scene.camera.matrix_world.translation-initial).length
    rig['Distance']=distance;rig.update_tag();scene.frame_set(1);bpy.context.view_layer.update()
    check('camera_control_moves_camera',moved>1)
    panel_roots=[o for o in bpy.data.objects if o.name.startswith('MAP / ')]
    relief_ok=True
    for root in panel_roots:
        initial_scale=root.scale.z;initial_relief=root['Vertical exaggeration']
        root['Vertical exaggeration']=initial_relief*1.1;root.update_tag();scene.frame_set(2);bpy.context.view_layer.update()
        relief_ok &= abs(root.scale.z-initial_scale*1.1)<1e-5
        root['Vertical exaggeration']=initial_relief;root.update_tag()
    scene.frame_set(1);bpy.context.view_layer.update()
    check('relief_controls_work',relief_ok)
    # Frame bounds are measured from the actual camera projection, not assumed rig settings.
    projection=scene.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=scene.render.resolution_x,y=scene.render.resolution_y)
    xy=[]
    front=True
    for terrain in terrains:
        vertices=np.empty(len(terrain.data.vertices)*3,dtype=np.float32)
        terrain.data.vertices.foreach_get('co',vertices)
        matrix=np.asarray(projection@scene.camera.matrix_world.inverted()@terrain.matrix_world)
        projected=np.c_[vertices.reshape(-1,3),np.ones(len(terrain.data.vertices))]@matrix.T
        front &= bool(np.all(projected[:,3]>0))
        xy.append(projected[:,:2]/projected[:,3,None]*.5+.5)
    xy=np.concatenate(xy)
    check('terrain_inside_camera',front and bool(np.all((xy[:,0]>.015)&(xy[:,0]<.985)&(xy[:,1]>.09)&(xy[:,1]<.88))))
    report={'blender':bpy.app.version_string,'checks':checks,'passed':all(checks.values()),
            'terrain_vertices':sum(len(o.data.vertices) for o in terrains),'boundary_objects':len(boundaries),
            'driver_count':len(driver_curves),'packed_images':len(images),
            'maximum_overlay_drape_error_units':max(drape_errors) if drape_errors else None,
            'terrain_camera_bounds':{'min':xy.min(axis=0).tolist(),'max':xy.max(axis=0).tolist()}}
    if render:
        (output/'renders').mkdir(exist_ok=True)
        scene.render.filepath=str(output/'renders'/'verified.png')
        t=time.perf_counter();bpy.ops.render.render(write_still=True);report['reopened_render_seconds']=time.perf_counter()-t
    write_json(output/'verification-report.json',report)
    print('VERIFICATION',json.dumps(report),flush=True)
    if not report['passed']:
        raise RuntimeError('Saved scene verification failed: '+', '.join(k for k,v in checks.items() if not v))


def math_isfinite(vector):
    import math
    return all(math.isfinite(v) for v in vector)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--render',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    verify(args.output,args.render)
