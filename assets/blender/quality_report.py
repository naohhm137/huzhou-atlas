"""Blender background quality report for Huzhou exhibit sources."""
import bpy, json, os, sys
root = sys.argv[-1] if sys.argv and not sys.argv[-1].endswith('.py') else os.getcwd()
report = {"blend": bpy.data.filepath, "objects": 0, "meshes": 0, "named": 0, "movable": 0, "materials": 0, "textures": 0}
for obj in bpy.data.objects:
    report["objects"] += 1
    if obj.type == 'MESH': report["meshes"] += 1
    if obj.name and not obj.name.startswith(('Cube','Cylinder','Sphere','Torus','Cone','Plane')): report["named"] += 1
    if 'explodeDirection' in obj.keys() and 'explodeDistance' in obj.keys(): report["movable"] += 1
report["materials"] = len(bpy.data.materials)
report["textures"] = len(bpy.data.images)
out = os.path.join(root, 'docs', 'blend-quality-report.json')
with open(out, 'w', encoding='utf-8') as f: json.dump(report, f, ensure_ascii=False, indent=2)
print(json.dumps(report, ensure_ascii=False))
