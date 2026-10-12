# Tutorial step 4.4.2: assemble Lux3D parts into the Feiying pagoda in Blender.
# usage: blender -b -P assemble.py -- <lux3d_dir> <out_blend> <out_glb> <decimate_ratio> <tex_px>
import bpy, sys, os, json, mathutils

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT_BLEND, OUT_GLB = a[0], a[1], a[2]
RATIO, TEX = float(a[3]), int(a[4])

bpy.ops.wm.read_factory_settings(use_empty=True)
SOURCES = {}
scene = bpy.context.scene


def import_part(name):
    """Import one Lux3D GLB, bake transforms, put origin at bottom-centre, return the mesh."""
    before = set(bpy.data.objects)
    std = os.path.join(SRC, "..", "lux3d-std", name + "_glb.glb")
    path = std if os.path.exists(std) else os.path.join(SRC, name + ".glb")
    SOURCES[name] = "G1" if path == std else "G1-Turbo"
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    assert len(meshes) == 1, (name, len(meshes))
    m = meshes[0]
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    m.parent = None
    m.matrix_world = m.matrix_world.copy()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in new:
        if o is not m:
            bpy.data.objects.remove(o)
    if RATIO < 0.999:
        d = m.modifiers.new("dec", 'DECIMATE')
        d.ratio = RATIO
        bpy.ops.object.modifier_apply(modifier=d.name)
    vs = [v.co for v in m.data.vertices]
    mn = mathutils.Vector([min(v[i] for v in vs) for i in range(3)])
    mx = mathutils.Vector([max(v[i] for v in vs) for i in range(3)])
    off = mathutils.Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    m.data.transform(mathutils.Matrix.Translation(-off))
    m.location = (0, 0, 0)
    m.data.name = name + "_mesh"
    for slot in m.material_slots:
        if slot.material:
            slot.material.name = name + "_mat"
    return m, mx - mn


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = 'PLAIN_AXES'
    scene.collection.objects.link(e)
    e.parent = parent
    e.location = loc
    return e


def place(mesh_src, size, node_name, parent, z, width, zscale=0.85, linked=False):
    """Instance (or move) a part under an empty; width = target footprint in metres."""
    node = empty(node_name, parent, (0, 0, z))
    if linked:
        obj = bpy.data.objects.new(node_name + "_geo", mesh_src.data)
        scene.collection.objects.link(obj)
    else:
        obj = mesh_src
        obj.name = node_name + "_geo"
    obj.parent = node
    s = width / max(size.x, size.y)
    obj.scale = (s, s, s * zscale)
    return node, size.z * s * zscale


parts = {n: import_part(n) for n in ["A_floor", "B_top", "C_spire", "D_base", "E_inner", "F_dougong"]}
for m, _ in parts.values():
    if m.users_collection and m.users_collection[0] is not scene.collection:
        for c in m.users_collection:
            c.objects.unlink(m)
        scene.collection.objects.link(m)

# Units: metres, Blender Z-up (glTF exporter converts to Y-up).
root = empty("feiying_tower")
outer = empty("outer_tower", root)
BASE_W = 14.0
OVERLAP = 0.06          # floors sit slightly into the eave below, so no light gap when assembled
floors = []             # (node, height)

# Floor 1: base with 副阶 gallery
m, sz = parts["D_base"]
n, h = place(m, sz, "外塔_01_副阶", outer, 0.0, BASE_W, zscale=0.9)
floors.append((n, h)); z = h * (1 - OVERLAP)

# Floors 2–6: one Lux3D module reused with a gentle taper (逐层收分)
m, sz = parts["A_floor"]
for i, w in enumerate([11.6, 11.0, 10.4, 9.8, 9.2], start=2):
    n, h = place(m, sz, f"外塔_{i:02d}", outer, z, w, linked=(i != 2))
    floors.append((n, h)); z += h * (1 - OVERLAP)

# Floor 7: pyramidal top
m, sz = parts["B_top"]
n, h = place(m, sz, "外塔_07_顶层", outer, z, 8.6)
floors.append((n, h)); z += h * 0.97
body_top = z

# Spire
m, sz = parts["C_spire"]
spire, sh = place(m, sz, "塔刹", root, body_top - 0.1, 1.5, zscale=1.0)
s = (body_top * 0.38) / sz.z
spire.children[0].scale = (s * 0.62, s * 0.62, s)

# Inner stone pagoda: stands on the base, top around floor 4–5
m, sz = parts["E_inner"]
inner_h = body_top * 0.74 - floors[0][1] * 0.25
inner = empty("内塔_石塔", root, (0, 0, floors[0][1] * 0.25))
m.name = "内塔_石塔_geo"; m.parent = inner
s = inner_h / sz.z
m.scale = (s, s, s)

# Dougong close-up exhibit, kept out of the tower footprint and hidden by the site until screen 04
m, sz = parts["F_dougong"]
dg = empty("细部_斗栱", None, (BASE_W * 1.6, 0, 0))
m.name = "细部_斗栱_geo"; m.parent = dg
s = 3.0 / sz.z
m.scale = (s, s, s)

# Explosion metadata (tutorial 4.4.2 step 5 + 5.5.2): origin + direction × distance.
gap = 3.2
for i, (node, _) in enumerate(floors):
    node["explodeDirection"] = [0.0, 0.0, 1.0]
    node["explodeDistance"] = round(i * gap, 3)
spire["explodeDirection"] = [0.0, 0.0, 1.0]
spire["explodeDistance"] = round(len(floors) * gap + 1.0, 3)

# Record initial transforms for asset-index.json (Blender Z-up → glTF Y-up: (x, z, -y)).
bpy.context.view_layer.update()
index = []
for node in [*(f[0] for f in floors), spire, inner, dg]:
    p = node.location
    index.append({
        "node": node.name,
        "parent": node.parent.name if node.parent else None,
        "position": [round(p.x, 4), round(p.z, 4), round(-p.y, 4)],
        "rotation": [0, 0, 0, 1], "scale": [1, 1, 1],
        "explodeDirection": [0, 1, 0] if "explodeDirection" in node else None,
        "explodeDistance": node.get("explodeDistance"),
        "source": next(c.data.name.replace("_mesh", "") for c in node.children),
    })

# Downscale textures for the web build (tutorial 4.6 / 7.5).
for img in bpy.data.images:
    if img.size[0] > TEX:
        img.scale(TEX, TEX)

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.export_scene.gltf(
    filepath=OUT_GLB, export_format='GLB', use_selection=False,
    export_extras=True, export_yup=True, export_apply=False,
    export_image_format='WEBP', export_image_quality=85,
    export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14, export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=12,
)
print("SOURCES", SOURCES)
print("ASSEMBLED", json.dumps({"bodyTop": round(body_top, 3), "spireH": round(body_top * 0.38, 3),
      "innerH": round(inner_h, 3), "floors": [round(h, 3) for _, h in floors]}))
with open(os.path.splitext(OUT_GLB)[0] + ".nodes.json", "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=1)
