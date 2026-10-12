# Web export for one Lux3D exhibit: bakes the render_item.py look (albedo grade, roughness floor,
# glass, lit windows) into the textures, gives the Nanxun river its own material, normalises scale.
# usage: blender -b -P export_item.py -- <glb> <out_glb> <item_id> <decimate_ratio> <tex_px>
import bpy, sys, os, math, mathutils
import numpy as np

V = mathutils.Vector
a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, ITEM, RATIO, TEX = a[0], a[1], a[2], float(a[3]), int(a[4])

# Same numbers as render_item.py SPECS.
LOOK = {"brush": "studio", "loom": "studio", "tea": "studio", "yishang": "dusk", "dongwu": "dusk", "nanxun": "dusk"}[ITEM]
ROUGH = {"brush": 0.5, "loom": 0.55, "tea": 0.16, "yishang": 0.6, "dongwu": 0.12, "nanxun": 0.6}[ITEM]
SAT, VAL = {"dongwu": (1.0, 1.0)}.get(ITEM, (1.3, 0.8) if LOOK == "dusk" else (1.15, 0.9))
GAMMA = 1.18
SIZE = 6.0  # largest dimension in metres on the web, matching the old exhibit scale

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
for o in list(bpy.context.scene.objects):
    if o is not obj: bpy.data.objects.remove(o)
obj.parent = None
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = obj.data
co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
mn, mx = co.min(0), co.max(0); s = 1.0 / float((mx - mn).max())
me.transform(mathutils.Matrix.Scale(s, 4) @ mathutils.Matrix.Translation(-V(((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]))))
dims = (mx - mn) * s
obj.name = me.name = f"{ITEM}_lux3d"

mat = obj.material_slots[0].material
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
base_img = next(l.from_node for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Base Color").image
mr_img = next(n.image for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image is not base_img)


def to_lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
def ramp(x, a_, b_): return np.clip((x - a_) / (b_ - a_), 0, 1)


def pixels(img):
    p = np.empty(img.size[0] * img.size[1] * 4, np.float32); img.pixels.foreach_get(p); return p.reshape(-1, 4)


def hsv(c):
    v = c.max(1); mn_ = c.min(1); d = v - mn_
    s_ = np.where(v > 1e-6, d / np.maximum(v, 1e-6), 0)
    r, g, b = c[:, 0], c[:, 1], c[:, 2]; dd = np.maximum(d, 1e-6)
    h = np.where(v == r, (g - b) / dd % 6, np.where(v == g, (b - r) / dd + 2, (r - g) / dd + 4)) / 6
    return np.where(d > 1e-6, h, 0), s_, v


px = pixels(base_img); orig = to_lin(px[:, :3])
# Blender Hue/Saturation (HSV saturation × SAT, value × VAL) then Gamma, in scene-linear.
vmax = orig.max(1, keepdims=True)
graded = np.clip(vmax - (vmax - orig) * SAT, 0, None) * VAL
graded = np.power(np.clip(graded, 0, None), GAMMA)
mrp = pixels(mr_img)
mrp[:, 1] = np.maximum(mrp[:, 1], ROUGH)  # glTF: G = roughness, B = metallic

if False:  # disabled: darkening the curtain wall turned the real blue glass black
    h, s_, _ = hsv(orig)
    m = ramp(h, 0.47, 0.53) * ramp(h, 0.72, 0.66) * ramp(s_, 0.18, 0.3)
    # Lighter than the Cycles shader: without GI the web glass otherwise renders nearly black.
    glass = graded * 0.75 + np.array([0.02, 0.05, 0.08]) * 0.25
    graded = graded * (1 - m[:, None]) + glass * m[:, None]
    mrp[:, 1] = mrp[:, 1] * (1 - m) + 0.14 * m
    mrp[:, 2] = mrp[:, 2] * (1 - m) + 0.3 * m

px[:, :3] = to_srgb(graded)
base_img.pixels.foreach_set(px.ravel()); base_img.update(); base_img.pack()
mr_img.pixels.foreach_set(mrp.ravel()); mr_img.update(); mr_img.pack()

if ITEM in ("yishang", "nanxun"):  # bright warm pixels (lit windows, lanterns) → emissive texture
    m = ramp(graded[:, 0] - graded[:, 2], 0.3, 0.6) * ramp(graded[:, 0], 0.65, 0.9)
    em = np.zeros_like(px); em[:, :3] = to_srgb(graded * m[:, None]); em[:, 3] = 1
    w_, h_ = base_img.size
    em_img = bpy.data.images.new(f"{ITEM}_emissive", w_, h_); em_img.pixels.foreach_set(em.ravel()); em_img.pack()
    node = nt.nodes.new("ShaderNodeTexImage"); node.image = em_img
    uv = next(l.from_socket for l in nt.links if l.to_node.type == 'TEX_IMAGE' and l.to_socket.name == "Vector") if any(
        l.to_node.type == 'TEX_IMAGE' and l.to_socket.name == "Vector" for l in nt.links) else None
    if uv: nt.links.new(uv, node.inputs["Vector"])
    nt.links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 3.0

if ITEM == "nanxun":  # river: largest horizontal surface in the lower half → its own dark reflective material
    n = len(me.polygons)
    nrm = np.empty(n * 3, np.float32); me.polygons.foreach_get("normal", nrm); nrm = nrm.reshape(-1, 3)
    cen = np.empty(n * 3, np.float32); me.polygons.foreach_get("center", cen); cen = cen.reshape(-1, 3)
    ar = np.empty(n, np.float32); me.polygons.foreach_get("area", ar)
    sel = (nrm[:, 2] > 0.97) & (cen[:, 2] < dims[2] * 0.5) & (cen[:, 2] > dims[2] * 0.01)
    hist, edges = np.histogram(cen[sel, 2], bins=120, weights=ar[sel]); k = int(np.argmax(hist))
    wz = float((edges[k] + edges[k + 1]) / 2)
    water = bpy.data.materials.new("nanxun_water"); water.use_nodes = True
    wb = water.node_tree.nodes["Principled BSDF"]
    wb.inputs["Base Color"].default_value = (0.01, 0.025, 0.024, 1); wb.inputs["Roughness"].default_value = 0.05
    me.materials.append(water)
    idx = np.where((nrm[:, 2] > 0.95) & (np.abs(cen[:, 2] - wz) < dims[2] * 0.02))[0]
    mi = np.zeros(n, np.int32); me.polygons.foreach_get("material_index", mi); mi[idx] = 1; me.polygons.foreach_set("material_index", mi)
    print("WATER faces", len(idx), "at", round(wz, 4))

if RATIO < 0.999:
    d = obj.modifiers.new("dec", 'DECIMATE'); d.ratio = RATIO
    bpy.ops.object.modifier_apply(modifier=d.name)
me.transform(mathutils.Matrix.Scale(SIZE, 4))
for img in bpy.data.images:
    if img.size[0] > TEX: img.scale(TEX, TEX)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=OUT, export_format='GLB', use_selection=False, export_yup=True,
    export_image_format='WEBP', export_image_quality=82,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14, export_draco_normal_quantization=10, export_draco_texcoord_quantization=12,
)
print("EXPORTED", ITEM, os.path.getsize(OUT), "faces", len(me.polygons), "dims", [round(float(v) * SIZE, 2) for v in dims])
