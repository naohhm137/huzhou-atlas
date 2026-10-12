# Cinematic Blender renders for one Lux3D exhibit (single mesh, no part split).
# Framing is fitted to the model's real bounds; close-ups aim at a located feature.
# usage: blender -b -P render_item.py -- <glb> <out_prefix> <item_id> [samples] [width] [baked]
import bpy, sys, math, mathutils
import numpy as np

V = mathutils.Vector
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, ITEM = a[0], a[1], a[2]
SAMPLES = int(a[3]) if len(a) > 3 else 128
WIDTH = int(a[4]) if len(a) > 4 else 1920
# 'baked': the source is a web GLB from export_item.py whose textures already carry the look.
BAKED = len(a) > 5 and a[5] == 'baked'

# az: camera direction around Z (−90 = the Lux3D "front", which matches the reference image).
# el: elevation in degrees. fit: frame margin (1 = bounding sphere just fits). Close-ups use
# `focus` (a located feature) and `span` (visible size in model units) instead of fit.
SPECS = {
    "brush":   dict(look="studio", rough=0.5,  shots=[dict(az=-100, el=22, fit=0.9),
                                                      dict(az=-120, el=16, focus="lowest", span=0.32, fstop=2.8)]),
    "loom":    dict(look="studio", rough=0.55, shots=[dict(az=-115, el=18, fit=1.0),
                                                      dict(az=-95, el=26, focus="front-mid", span=0.5, fstop=4.0)]),
    "tea":     dict(look="studio", rough=0.16, shots=[dict(az=-105, el=28, fit=0.66),
                                                      dict(az=-95, el=55, focus="top", span=0.55, fstop=4.0)]),
    "yishang": dict(look="dusk",   rough=0.6,  shots=[dict(az=-115, el=34, fit=0.66),
                                                      dict(az=-100, el=18, focus="center", span=0.6, fstop=8.0)]),
    "dongwu":  dict(look="day",    rough=0.12, sat=1.0, val=1.0, noglow=True, shots=[dict(az=-110, el=14, fit=0.66),
                                                      dict(az=-125, el=4, focus="center", span=0.95)]),
    "nanxun":  dict(look="dusk",   rough=0.6,  water=True,
                                               shots=[dict(az=-105, el=32, fit=0.66),
                                                      dict(az=-150, el=14, focus="center", span=0.65, fstop=8.0)]),
}
spec = SPECS[ITEM]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in sc.objects if o.type == 'MESH']
for o in sc.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:
    o.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
pts = [o.matrix_world @ V(c) for o in meshes for c in o.bound_box]
mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
size = mx - mn; s = 1.0 / max(size)
for o in meshes:
    o.data.transform(mathutils.Matrix.Translation(-V(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))
    o.data.transform(mathutils.Matrix.Scale(s, 4))
dims = size * s
center = V((0, 0, dims.z / 2))
radius = dims.length / 2
verts = np.array([v.co[:] for o in meshes for v in o.data.vertices], dtype=np.float32)


def water_level():
    """Height of the largest horizontal surface in the lower half, weighted by face area."""
    zs, ws = [], []
    for o in meshes:
        n = len(o.data.polygons)
        nrm = np.empty(n * 3, np.float32); o.data.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
        cen = np.empty(n * 3, np.float32); o.data.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
        ar = np.empty(n, np.float32); o.data.polygons.foreach_get("area", ar)
        sel = (nrm[:, 2] > 0.97) & (cen[:, 2] < dims.z * 0.5) & (cen[:, 2] > dims.z * 0.01)
        zs.append(cen[sel, 2]); ws.append(ar[sel])
    z, w_ = np.concatenate(zs), np.concatenate(ws)
    if len(z) < 50: return None
    hist, edges = np.histogram(z, bins=120, weights=w_)
    k = int(np.argmax(hist)); return float((edges[k] + edges[k + 1]) / 2)


WATER_Z = water_level() if spec.get("water") else None
print("WATER_Z", WATER_Z)


def feature(kind):
    if kind == "center":
        return center
    if kind == "top":
        return V((0, 0, dims.z * 0.85))
    if kind == "lowest":  # e.g. the brush tip
        k = max(50, len(verts) // 60)
        return V(verts[np.argsort(verts[:, 2])[:k]].mean(0))
    if kind == "front-mid":
        return V((0, dims.y * -0.15, dims.z * 0.45))
    return center


# --- render settings
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
try:
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'CUDA'; p.get_devices()
    for d in p.devices: d.use = True
    sc.cycles.device = 'GPU'
except Exception as e:
    print("gpu", e)
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = 0.2
sc.render.resolution_x = WIDTH; sc.render.resolution_y = WIDTH * 9 // 16
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 92

# --- world + lights: the same rig as the approved Feiying renders (production/feiying/scripts/render_shots.py)
w = bpy.data.worlds.new("night"); sc.world = w; w.use_nodes = True; nt = w.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.55
mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
mix.inputs[6].default_value = (0.16, 0.10, 0.06, 1) if spec["look"] == "dusk" else (0.06, 0.04, 0.026, 1)  # dusk: something warm for glass and water to reflect
mix.inputs[7].default_value = (0.008, 0.024, 0.026, 1)
if spec["look"] == "day":  # Dongwu: its blue curtain wall only reads blue under a daylight sky (as in the reference photo)
    mix.inputs[6].default_value = (0.55, 0.68, 0.85, 1); mix.inputs[7].default_value = (0.10, 0.25, 0.62, 1)
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
nt.links.new(mr.outputs["Result"], mix.inputs["Factor"]); nt.links.new(mix.outputs[2], nt.nodes["Background"].inputs["Color"])
nt.nodes["Background"].inputs["Strength"].default_value = 1.0


def sun(pos, energy, color, angle):
    l = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    l.data.energy = energy; l.data.color = color; l.data.angle = math.radians(angle)
    sc.collection.objects.link(l)
    l.rotation_euler = (V((0, 0, 0)) - V(pos)).to_track_quat('-Z', 'Y').to_euler()


if spec["look"] == "day":
    sun((-30, -60, 50), 4.5, (1.0, 0.96, 0.9), 1.0)   # high white sun, front-left
    sun((50, 30, 30), 0.8, (0.7, 0.82, 1.0), 10)      # sky-blue fill
    sc.view_settings.exposure = 0.0
else:
    sun((-55, 40, 18), 7.0, (1.0, 0.68, 0.40), 1.5)   # warm, low, back-left: rim
    sun((-30, -60, 30), 2.4, (1.0, 0.80, 0.60), 4)    # warm front so the surface reads
    sun((50, -30, 40), 0.6, (0.55, 0.75, 0.9), 15)    # cool fill
    sc.view_settings.exposure = 0.3

# --- dark, fully rough floor (no hot spot)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.0005))
floor = bpy.context.active_object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fb = fm.node_tree.nodes["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.008, 0.011, 0.011, 1); fb.inputs["Roughness"].default_value = 1.0
fb.inputs["Specular IOR Level"].default_value = 0.1
floor.data.materials.append(fm)

# --- material tweaks on the Lux3D PBR material
for m in ([] if BAKED else bpy.data.materials):
    if not m.use_nodes or m is fm: continue
    t = m.node_tree; bsdf = t.nodes.get("Principled BSDF")
    if not bsdf: continue
    # roughness floor: Lux3D maps read plastic-glossy under area lights
    rl = next((l for l in t.links if l.to_node == bsdf and l.to_socket.name == "Roughness"), None)
    if rl:
        mx_ = t.nodes.new("ShaderNodeMath"); mx_.operation = 'MAXIMUM'; mx_.inputs[1].default_value = spec["rough"]
        t.links.new(rl.from_socket, mx_.inputs[0]); t.links.new(mx_.outputs[0], bsdf.inputs["Roughness"])
    bl = next((l for l in t.links if l.to_node == bsdf and l.to_socket.name == "Base Color"), None)
    if not bl: continue
    base = bl.from_socket
    grade = t.nodes.new("ShaderNodeHueSaturation")
    sat, val = (1.3, 0.8) if spec["look"] == "dusk" else (1.15, 0.9)
    if spec["look"] == "day": sat, val = 1.0, 1.0
    sat, val = spec.get("sat", sat), spec.get("val", val)
    grade.inputs["Saturation"].default_value = sat; grade.inputs["Value"].default_value = val
    gam = t.nodes.new("ShaderNodeGamma"); gam.inputs["Gamma"].default_value = 1.18
    t.links.new(base, grade.inputs["Color"]); t.links.new(grade.outputs["Color"], gam.inputs["Color"])
    t.links.new(gam.outputs["Color"], bsdf.inputs["Base Color"])
    base = gam.outputs["Color"]
    if spec["look"] == "dusk" and not spec.get("noglow"):
        # bright warm pixels (lit windows, lanterns) glow
        sepc = t.nodes.new("ShaderNodeSeparateColor"); t.links.new(base, sepc.inputs[0])
        warm = t.nodes.new("ShaderNodeMath"); warm.operation = 'SUBTRACT'
        t.links.new(sepc.outputs[0], warm.inputs[0]); t.links.new(sepc.outputs[2], warm.inputs[1])
        wm = t.nodes.new("ShaderNodeMapRange"); wm.inputs["From Min"].default_value = 0.3; wm.inputs["From Max"].default_value = 0.6
        t.links.new(warm.outputs[0], wm.inputs["Value"])
        bm = t.nodes.new("ShaderNodeMapRange"); bm.inputs["From Min"].default_value = 0.65; bm.inputs["From Max"].default_value = 0.9
        t.links.new(sepc.outputs[0], bm.inputs["Value"])
        both = t.nodes.new("ShaderNodeMath"); both.operation = 'MULTIPLY'
        t.links.new(wm.outputs["Result"], both.inputs[0]); t.links.new(bm.outputs["Result"], both.inputs[1])
        gain = t.nodes.new("ShaderNodeMath"); gain.operation = 'MULTIPLY'; gain.inputs[1].default_value = 6.0
        t.links.new(both.outputs[0], gain.inputs[0])
        t.links.new(base, bsdf.inputs["Emission Color"]); t.links.new(gain.outputs[0], bsdf.inputs["Emission Strength"])
    if spec.get("glass"):
        # blue curtain wall → dark, mirror-like glass that picks up the dusk horizon
        hsv2 = t.nodes.new("ShaderNodeSeparateColor"); hsv2.mode = 'HSV'; t.links.new(bl.from_socket, hsv2.inputs[0])
        hue = t.nodes.new("ShaderNodeMapRange"); hue.inputs["From Min"].default_value = 0.47; hue.inputs["From Max"].default_value = 0.53
        t.links.new(hsv2.outputs[0], hue.inputs["Value"])
        hue2 = t.nodes.new("ShaderNodeMapRange"); hue2.inputs["From Min"].default_value = 0.72; hue2.inputs["From Max"].default_value = 0.66
        t.links.new(hsv2.outputs[0], hue2.inputs["Value"])
        sat2 = t.nodes.new("ShaderNodeMapRange"); sat2.inputs["From Min"].default_value = 0.18; sat2.inputs["From Max"].default_value = 0.3
        t.links.new(hsv2.outputs[1], sat2.inputs["Value"])
        g1 = t.nodes.new("ShaderNodeMath"); g1.operation = 'MULTIPLY'; t.links.new(hue.outputs["Result"], g1.inputs[0]); t.links.new(hue2.outputs["Result"], g1.inputs[1])
        gm = t.nodes.new("ShaderNodeMath"); gm.operation = 'MULTIPLY'; t.links.new(g1.outputs[0], gm.inputs[0]); t.links.new(sat2.outputs["Result"], gm.inputs[1])
        glass = t.nodes.new("ShaderNodeBsdfPrincipled")
        gdark = t.nodes.new("ShaderNodeMix"); gdark.data_type = 'RGBA'; gdark.inputs[0].default_value = 0.55
        t.links.new(base, gdark.inputs[6]); gdark.inputs[7].default_value = (0.01, 0.025, 0.04, 1)
        t.links.new(gdark.outputs[2], glass.inputs["Base Color"])
        glass.inputs["Metallic"].default_value = 0.6; glass.inputs["Roughness"].default_value = 0.06
        out = t.nodes["Material Output"]
        sl = next(l for l in t.links if l.to_node == out and l.to_socket.name == "Surface")
        gmix = t.nodes.new("ShaderNodeMixShader")
        t.links.new(gm.outputs[0], gmix.inputs[0]); t.links.new(sl.from_socket, gmix.inputs[1]); t.links.new(glass.outputs[0], gmix.inputs[2])
        t.links.new(gmix.outputs[0], out.inputs["Surface"])
    if spec.get("water") and WATER_Z is not None:
        # low, upward-facing, desaturated pixels are the river: make them dark and mirror-like
        geo = t.nodes.new("ShaderNodeNewGeometry"); sxyz = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(geo.outputs["Normal"], sxyz.inputs[0])
        up = t.nodes.new("ShaderNodeMapRange"); up.inputs["From Min"].default_value = 0.92; up.inputs["From Max"].default_value = 0.98
        t.links.new(sxyz.outputs["Z"], up.inputs["Value"])
        pz = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(geo.outputs["Position"], pz.inputs[0])
        low = t.nodes.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = dims.z * 0.035; low.inputs["From Max"].default_value = dims.z * 0.012
        dz = t.nodes.new("ShaderNodeMath"); dz.operation = 'SUBTRACT'; dz.inputs[1].default_value = WATER_Z
        t.links.new(pz.outputs["Z"], dz.inputs[0])
        adz = t.nodes.new("ShaderNodeMath"); adz.operation = 'ABSOLUTE'; t.links.new(dz.outputs[0], adz.inputs[0])
        t.links.new(adz.outputs[0], low.inputs["Value"])
        hsv = t.nodes.new("ShaderNodeSeparateColor"); hsv.mode = 'HSV'; t.links.new(base, hsv.inputs[0])
        grey = t.nodes.new("ShaderNodeMapRange"); grey.inputs["From Min"].default_value = 0.45; grey.inputs["From Max"].default_value = 0.3
        t.links.new(hsv.outputs[1], grey.inputs["Value"])
        m1 = t.nodes.new("ShaderNodeMath"); m1.operation = 'MULTIPLY'; t.links.new(up.outputs["Result"], m1.inputs[0]); t.links.new(low.outputs["Result"], m1.inputs[1])
        mask = m1
        water = t.nodes.new("ShaderNodeBsdfPrincipled")
        water.inputs["Base Color"].default_value = (0.01, 0.025, 0.024, 1); water.inputs["Roughness"].default_value = 0.04
        noise = t.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 260; noise.inputs["Detail"].default_value = 4
        bump = t.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
        t.links.new(noise.outputs["Fac"], bump.inputs["Height"]); t.links.new(bump.outputs["Normal"], water.inputs["Normal"])
        out = t.nodes["Material Output"]
        sl = next(l for l in t.links if l.to_node == out and l.to_socket.name == "Surface")
        mixs = t.nodes.new("ShaderNodeMixShader")
        t.links.new(mask.outputs[0], mixs.inputs[0]); t.links.new(sl.from_socket, mixs.inputs[1]); t.links.new(water.outputs[0], mixs.inputs[2])
        t.links.new(mixs.outputs[0], out.inputs["Surface"])

# --- cameras fitted to the real bounds
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.clip_start = 0.002; cam.data.clip_end = 200; cam.data.sensor_fit = 'HORIZONTAL'; cam.data.sensor_width = 36
for i, sh in enumerate(spec["shots"], 1):
    az, el = math.radians(sh["az"]), math.radians(sh["el"])
    direction = V((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    lens = 50
    vfov = 2 * math.atan(36 * 9 / 16 / 2 / lens)
    if "focus" in sh:
        tgt = feature(sh["focus"]); dist = (sh["span"] / 2) / math.tan(vfov / 2)
    else:
        tgt = center; dist = radius * sh["fit"] / math.sin(vfov / 2)
    cam.location = tgt + direction * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    cam.data.dof.use_dof = "fstop" in sh
    if "fstop" in sh:
        cam.data.dof.focus_distance = dist; cam.data.dof.aperture_fstop = sh["fstop"]
    sc.render.filepath = f"{OUT}_{i}.jpg"
    bpy.ops.render.render(write_still=True)
print("RENDERED", ITEM, [round(v, 3) for v in dims])
