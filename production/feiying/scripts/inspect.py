import bpy, sys, os, math, mathutils
a=sys.argv[sys.argv.index("--")+1:]; src, out = a[0], a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
bb=[o.matrix_world @ mathutils.Vector(c) for o in meshes for c in o.bound_box]
mn=mathutils.Vector([min(v[i] for v in bb) for i in range(3)]); mx=mathutils.Vector([max(v[i] for v in bb) for i in range(3)])
size=mx-mn; ctr=(mn+mx)/2
tris=sum(len(o.data.polygons) for o in meshes)
mats=sorted({s.material.name for o in meshes for s in o.material_slots if s.material})
imgs=[(i.name,i.size[0],i.size[1]) for i in bpy.data.images]
print("INFO",os.path.basename(src),"objs",len(meshes),"polys",tris,"size",[round(x,3) for x in size],"min",[round(x,3) for x in mn],"mats",mats[:6],"imgs",imgs[:6])
sc=bpy.context.scene; sc.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x=sc.render.resolution_y=768; sc.render.film_transparent=False
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[0].default_value=(0.55,0.56,0.55,1); w.node_tree.nodes['Background'].inputs[1].default_value=1.0
for loc,e in [((3,-4,5),4),((-4,-2,2),1.5)]:
    l=bpy.data.objects.new("L",bpy.data.lights.new("L",'SUN')); l.data.energy=e; sc.collection.objects.link(l); l.rotation_euler=(mathutils.Vector(loc)).to_track_quat('Z','Y').to_euler()
r=max(size)*1.9
cam=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
for name,(az,el) in {"front":(-90,12),"side":(-30,25)}.items():
    p=ctr+mathutils.Vector((r*math.cos(math.radians(el))*math.cos(math.radians(az)), r*math.cos(math.radians(el))*math.sin(math.radians(az)), r*math.sin(math.radians(el))))
    cam.location=p; cam.rotation_euler=(ctr-p).to_track_quat('-Z','Y').to_euler(); cam.data.lens=50
    sc.render.filepath=out+"_"+name+".jpg"; sc.render.image_settings.file_format='JPEG'; bpy.ops.render.render(write_still=True)
