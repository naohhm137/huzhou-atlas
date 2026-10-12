import bpy, sys, math, mathutils
V=mathutils.Vector
out=sys.argv[sys.argv.index("--")+1:][0]
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=96; sc.cycles.use_denoising=True
try:
    p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='CUDA'; p.get_devices()
    for d in p.devices: d.use=True
    sc.cycles.device='GPU'
except Exception as e: print("gpu",e)
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=0.6
sc.render.resolution_x=1280; sc.render.resolution_y=720
w=bpy.data.worlds.new("w"); sc.world=w; w.use_nodes=True; bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.10,0.16,0.17,1); bg.inputs[1].default_value=1.4
def light(pos,target,e,col,ang=3):
    l=bpy.data.objects.new("S",bpy.data.lights.new("S",'SUN')); l.data.energy=e; l.data.color=col; l.data.angle=math.radians(ang)
    sc.collection.objects.link(l); l.location=pos; l.rotation_euler=(V(target)-V(pos)).to_track_quat('-Z','Y').to_euler()
light((-40,-45,45),(0,0,15),6.0,(1,0.78,0.52))      # warm key from front-left, low-ish
light((40,35,25),(0,0,15),3.0,(1,0.85,0.65),1)      # warm rim from back-right
light((45,-20,10),(0,0,15),0.8,(0.55,0.75,0.9),12)  # cool fill
cam=bpy.data.objects.new("C",bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera=cam
def shot(name,target,pos,lens):
    cam.location=pos; cam.rotation_euler=(V(target)-V(pos)).to_track_quat('-Z','Y').to_euler(); cam.data.lens=lens
    sc.render.filepath=out+"/"+name+".jpg"; sc.render.image_settings.file_format='JPEG'; bpy.ops.render.render(write_still=True)
def show(names):
    for o in bpy.data.objects:
        if o.type=='MESH': o.hide_render = not any(o.name.startswith(n) for n in names)
dg=bpy.data.objects["细部_斗栱"]; dgx=dg.location.x
nodes=[o for o in bpy.data.objects if "explodeDistance" in o]; z0={o.name:o.location.z for o in nodes}
tower=["外塔","塔刹","内塔"]
show(tower); shot("1_全貌",(0,0,20),(38,-72,12),35)
shot("2_楼层近景",(0,0,15),(9,-17,13),35)
for o in nodes: o.location.z=z0[o.name]+o["explodeDistance"]
shot("3_拆层",(0,0,27),(52,-98,20),35)
for o in nodes: o.location.z=z0[o.name]
show(["外塔_01","内塔"]); shot("4_内石塔",(0,0,11),(8,-17,6),35)
show(["细部_斗栱"]); shot("5_斗栱",(dgx,0,1.5),(dgx+3.2,-4.6,0.6),40)
