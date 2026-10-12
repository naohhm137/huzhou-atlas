# Bake the render-time albedo grade into the textures and export web GLBs (tutorial 4.6 / 8.2).
# usage: blender -b feiying.blend -P grade_export.py -- <out_dir>
import bpy, sys, os
import numpy as np

OUT = sys.argv[sys.argv.index("--") + 1:][0]
os.makedirs(OUT, exist_ok=True)

# (saturation, value) — same numbers render_shots.py uses on the shader side.
GRADE = {"A_floor": (1.3, 0.78), "B_top": (1.3, 0.78), "D_base": (1.3, 0.78),
         "F_dougong": (1.3, 0.78), "E_inner": (1.0, 0.92), "C_spire": (1.15, 0.85)}


def grade(img, sat, val):
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    rgb = px[:, :3]
    mx, mn = rgb.max(1), rgb.min(1)
    grey = (mx + mn) / 2.0
    rgb = grey[:, None] + (rgb - grey[:, None]) * sat   # saturation about the midpoint
    px[:, :3] = np.clip(rgb * val, 0.0, 1.0)
    img.pixels.foreach_set(px.ravel())
    img.update()


done = set()
for m in bpy.data.materials:
    key = m.name.replace("_mat", "")
    if key not in GRADE or not m.use_nodes:
        continue
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    link = next((l for l in m.node_tree.links if l.to_node == bsdf and l.to_socket.name == "Base Color"), None)
    if not link or link.from_node.type != 'TEX_IMAGE':
        continue
    img = link.from_node.image
    if img.name in done:
        continue
    grade(img, *GRADE[key])
    img.pack()
    done.add(img.name)
    m.use_backface_culling = False  # cutaway shows the inside of the shell
print("GRADED", sorted(done))


def export(path, tex):
    for img in bpy.data.images:
        if img.size[0] > tex:
            img.scale(tex, tex)
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=False,
        export_extras=True, export_yup=True,
        export_image_format='WEBP', export_image_quality=82,
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14, export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
    )
    print("EXPORTED", path, os.path.getsize(path))


export(os.path.join(OUT, "feiying.glb"), 2048)
export(os.path.join(OUT, "feiying-mobile.glb"), 1024)
