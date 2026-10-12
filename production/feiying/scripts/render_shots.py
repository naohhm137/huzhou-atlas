# Cinematic Blender renders of the assembled pagoda, one per design screen.
# Look follows design/design-spec.md: ink-teal night, warm low key from back-left (rim + haze glow),
# cool fill, AgX tone mapping.
# usage: blender -b feiying.blend -P render_shots.py -- <outdir> [samples] [width] [only_shot_prefix]
import bpy, sys, math, mathutils

V = mathutils.Vector
args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
SAMPLES = int(args[1]) if len(args) > 1 else 160
WIDTH = int(args[2]) if len(args) > 2 else 1920
ONLY = args[3] if len(args) > 3 else ""

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 4.0
sc.cycles.transparent_max_bounces = 16
try:
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'CUDA'
    p.get_devices()
    for d in p.devices:
        d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print("gpu", e)
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = 0.3
sc.render.resolution_x = WIDTH
sc.render.resolution_y = WIDTH * 9 // 16
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 92

# --- Material grade: Lux3D standard albedo reads pale/pink under warm light. Deepen and saturate.
for m in bpy.data.materials:
    if not m.use_nodes or not m.name.endswith("_mat"):
        continue
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    link = next((l for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Base Color"), None)
    if not link:
        continue
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = 1.0 if m.name.startswith("E_inner") else 1.3
    hsv.inputs["Value"].default_value = 0.92 if m.name.startswith("E_inner") else 0.78
    nt.links.new(link.from_socket, hsv.inputs["Color"])
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])

# --- World: dark ink-teal overhead, faint warm glow near the horizon.
w = bpy.data.worlds.new("night")
sc.world = w
w.use_nodes = True
nt = w.node_tree
bg = nt.nodes['Background']
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.05
mr.inputs["From Max"].default_value = 0.55
mix = nt.nodes.new("ShaderNodeMix")
mix.data_type = 'RGBA'
mix.inputs[6].default_value = (0.06, 0.04, 0.026, 1)  # A: horizon warm
mix.inputs[7].default_value = (0.008, 0.024, 0.026, 1)  # B: zenith ink-teal
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
nt.links.new(mix.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0

# --- Ground haze in a bounded box (a world volume is infinite in Cycles and swallows sunlight).
# Density fades with height so there is no visible box edge.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 10))
haze = bpy.context.active_object
haze.name = "haze_volume"
haze.scale = (300, 300, 20)
hm = bpy.data.materials.new("haze")
hm.use_nodes = True
hn = hm.node_tree
hn.nodes.remove(hn.nodes['Principled BSDF'])
vol = hn.nodes.new('ShaderNodeVolumePrincipled')
vol.inputs['Color'].default_value = (0.86, 0.9, 0.9, 1)
vol.inputs['Anisotropy'].default_value = 0.6
htc = hn.nodes.new("ShaderNodeTexCoord")
hsep = hn.nodes.new("ShaderNodeSeparateXYZ")
hmr = hn.nodes.new("ShaderNodeMapRange")
hmr.inputs["From Min"].default_value = -0.5
hmr.inputs["From Max"].default_value = 0.5
hmr.inputs["To Min"].default_value = 0.0012
hmr.inputs["To Max"].default_value = 0.0
hn.links.new(htc.outputs["Object"], hsep.inputs[0])
hn.links.new(hsep.outputs["Z"], hmr.inputs["Value"])
hn.links.new(hmr.outputs["Result"], vol.inputs["Density"])
hn.links.new(vol.outputs[0], hn.nodes['Material Output'].inputs['Volume'])
haze.data.materials.append(hm)


def sun(pos, target, energy, color, angle=2.0):
    l = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    l.data.energy = energy
    l.data.color = color
    l.data.angle = math.radians(angle)
    sc.collection.objects.link(l)
    l.location = pos
    l.rotation_euler = (V(target) - V(pos)).to_track_quat('-Z', 'Y').to_euler()
    return l


key = sun((-55, 40, 18), (0, 0, 14), 7.0, (1.0, 0.68, 0.40), 1.5)   # warm, low, back-left: rim + haze glow
front = sun((-30, -60, 30), (0, 0, 14), 2.4, (1.0, 0.80, 0.60), 4)  # warm front so the facade reads
fill = sun((50, -30, 40), (0, 0, 14), 0.6, (0.55, 0.75, 0.9), 15)   # cool fill

bpy.ops.mesh.primitive_circle_add(vertices=96, radius=80, fill_type='NGON', location=(0, 0, -0.02))
ground = bpy.context.active_object
gm = bpy.data.materials.new("ground")
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.018, 0.022, 0.021, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
ground.data.materials.append(gm)

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.clip_end = 1000
sc.collection.objects.link(cam)
sc.camera = cam

nodes = [o for o in bpy.data.objects if "explodeDistance" in o]
z0 = {o.name: o.location.z for o in nodes}
detail = bpy.data.objects["细部_斗栱"]


# Render-only architectural cutaway done in the shader (a mesh boolean flips these
# non-manifold Lux3D shells inside-out). Two vertical planes through the tower axis bound
# a 90° wedge on the camera side; fragments inside both half-spaces become transparent and
# backfaces seen through the cut are shaded as dark timber. Mirrors three.js clipIntersection.
CUT = {}
for m in bpy.data.materials:
    if not (m.use_nodes and m.name.split("_mat")[0] in ("A_floor", "B_top", "D_base")):
        continue
    t = m.node_tree
    out = t.nodes["Material Output"]
    surf = next(l for l in t.links if l.to_node == out and l.to_socket.name == "Surface")
    src = surf.from_socket
    geo = t.nodes.new("ShaderNodeNewGeometry")
    n1 = t.nodes.new("ShaderNodeCombineXYZ"); n2 = t.nodes.new("ShaderNodeCombineXYZ")
    d1 = t.nodes.new("ShaderNodeVectorMath"); d1.operation = 'DOT_PRODUCT'
    d2 = t.nodes.new("ShaderNodeVectorMath"); d2.operation = 'DOT_PRODUCT'
    t.links.new(geo.outputs["Position"], d1.inputs[0]); t.links.new(n1.outputs[0], d1.inputs[1])
    t.links.new(geo.outputs["Position"], d2.inputs[0]); t.links.new(n2.outputs[0], d2.inputs[1])
    g1 = t.nodes.new("ShaderNodeMath"); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = 0.0
    g2 = t.nodes.new("ShaderNodeMath"); g2.operation = 'GREATER_THAN'; g2.inputs[1].default_value = 0.0
    t.links.new(d1.outputs["Value"], g1.inputs[0]); t.links.new(d2.outputs["Value"], g2.inputs[0])
    both = t.nodes.new("ShaderNodeMath"); both.operation = 'MULTIPLY'
    t.links.new(g1.outputs[0], both.inputs[0]); t.links.new(g2.outputs[0], both.inputs[1])
    en = t.nodes.new("ShaderNodeValue"); en.outputs[0].default_value = 0.0
    mask = t.nodes.new("ShaderNodeMath"); mask.operation = 'MULTIPLY'
    t.links.new(both.outputs[0], mask.inputs[0]); t.links.new(en.outputs[0], mask.inputs[1])
    dark = t.nodes.new("ShaderNodeBsdfPrincipled")
    dark.inputs["Base Color"].default_value = (0.06, 0.018, 0.01, 1); dark.inputs["Roughness"].default_value = 0.8
    back = t.nodes.new("ShaderNodeMixShader")
    t.links.new(geo.outputs["Backfacing"], back.inputs[0]); t.links.new(src, back.inputs[1]); t.links.new(dark.outputs[0], back.inputs[2])
    hole = t.nodes.new("ShaderNodeBsdfTransparent")
    mx = t.nodes.new("ShaderNodeMixShader")
    t.links.new(mask.outputs[0], mx.inputs[0]); t.links.new(back.outputs[0], mx.inputs[1]); t.links.new(hole.outputs[0], mx.inputs[2])
    t.links.new(mx.outputs[0], out.inputs["Surface"])
    CUT[m.name] = (n1, n2, en)


def cutaway(on, yaw_deg=-60):
    """Open the 90° wedge centred on yaw_deg (direction from tower axis towards the camera)."""
    a, b = math.radians(yaw_deg - 45), math.radians(yaw_deg + 45)
    for n1, n2, en in CUT.values():
        # plane normals: rotate each edge direction 90° towards the wedge interior
        n1.inputs[0].default_value, n1.inputs[1].default_value = -math.sin(a), math.cos(a)
        n2.inputs[0].default_value, n2.inputs[1].default_value = math.sin(b), -math.cos(b)
        en.outputs[0].default_value = 1.0 if on else 0.0

def explode(amount):
    for o in nodes:
        o.location.z = z0[o.name] + amount * o["explodeDistance"]


def show(prefixes):
    for o in bpy.data.objects:
        if o.type == 'MESH' and o is not ground and o is not haze:
            o.hide_render = not any(o.name.startswith(p) for p in prefixes)
    ground.hide_render = "细部_斗栱" in prefixes


def shot(name, target, pos, lens, dof=None, shift_x=0.0, clip_start=0.1):
    if ONLY and not name.startswith(ONLY):
        return
    cam.location = pos
    cam.rotation_euler = (V(target) - V(pos)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.shift_x = shift_x
    cam.data.clip_start = clip_start
    cam.data.dof.use_dof = dof is not None
    if dof:
        cam.data.dof.focus_distance = (V(target) - V(pos)).length
        cam.data.dof.aperture_fstop = dof
    sc.render.filepath = f"{OUT}/{name}.jpg"
    bpy.ops.render.render(write_still=True)


TOWER = ["外塔", "塔刹", "内塔"]
show(TOWER); explode(0); cutaway(False)
# 01 cover: whole pagoda centred, ~80% of frame height, slight low angle
shot("01_初见", (0, 0, 20), (10, -58, 4), 32)
# 02 body: 3/4 low angle from front-left, tower on the right
shot("02_塔身", (0, 0, 22), (-16, -34, 2), 24, shift_x=-0.2)
# 03 tower-in-tower: floors lifted apart AND the camera-side wedge opened, so the stone pagoda shows
explode(0.55); cutaway(True, yaw_deg=-75)
shot("03_塔中塔", (0, 0, 28), (12, -82, 10), 34, shift_x=-0.12)
explode(0)
# 05 stone pagoda: looking up through the cutaway
cutaway(True, yaw_deg=-70)
shot("05_石塔", (0, 0, 14), (4.5, -13, 2.0), 20, dof=8.0, shift_x=-0.18)
cutaway(False)
# 06 closing: whole pagoda again, tower on the left
shot("06_守护", (0, 0, 19), (-14, -60, 4), 34, shift_x=0.2)
# 04 dougong close-up, separate exhibit node
show(["细部_斗栱"])
key.rotation_euler = (V((detail.location.x, 0, 1.5)) - V((detail.location.x - 20, 15, 4))).to_track_quat('-Z', 'Y').to_euler()
shot("04_斗栱", (detail.location.x, 0, 1.9), (detail.location.x + 3.0, -4.2, 0.0), 38, dof=4.0, shift_x=-0.15)
