import bpy, sys, math, mathutils
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x=900; sc.render.resolution_y=1200
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.05,0.09,0.09,1); bg.inputs[1].default_value=0.6
def sun(rot,e,col):
    l=bpy.data.objects.new("S",bpy.data.lights.new("S",'SUN')); l.data.energy=e; l.data.color=col; sc.collection.objects.link(l); l.rotation_euler=rot
sun((math.radians(60),0,math.radians(-140)),4.5,(1,0.82,0.6)); sun((math.radians(70),0,math.radians(40)),1.0,(0.6,0.8,0.85))
cam=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam; cam.data.lens=50
dg=bpy.data.objects["细部_斗栱"]; dg.hide_render=True
for c in dg.children: c.hide_render=True
nodes=[o for o in bpy.data.objects if "explodeDistance" in o]
for mode,amt in (("assembled",0),("exploded",1)):
    for o in nodes: o["_z0"]=o.get("_z0",o.location.z); o.location.z=o["_z0"]+amt*o["explodeDistance"]
    bpy.context.view_layer.update()
    top=max((o.matrix_world@mathutils.Vector(c)).z for o in bpy.data.objects if o.type=='MESH' and not o.hide_render for c in o.bound_box)
    ctr=mathutils.Vector((0,0,top/2)); d=top*1.75
    p=ctr+mathutils.Vector((d*0.55,-d*0.83,top*0.05)); cam.location=p; cam.rotation_euler=(ctr-p).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=out+"_"+mode+".jpg"; sc.render.image_settings.file_format='JPEG'; bpy.ops.render.render(write_still=True)
