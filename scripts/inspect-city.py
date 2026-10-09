"""Read-only bounds diagnostics; run with Blender and a .blend argument."""
import bpy
import sys
from mathutils import Vector

path = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=path)
bpy.context.view_layer.update()
records = []
for obj in bpy.data.objects:
    if obj.type not in ('MESH', 'CURVE', 'FONT'): continue
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lo = tuple(min(p[i] for p in corners) for i in range(3))
    hi = tuple(max(p[i] for p in corners) for i in range(3))
    records.append((obj.name, lo, hi))
for axis in range(3):
    print('AXIS', axis, 'MIN', min(records, key=lambda r:r[1][axis]), 'MAX', max(records, key=lambda r:r[2][axis]))
print('OBJECTS', len(records))
if bpy.context.scene.camera:
    print('CAMERA', bpy.context.scene.camera.location[:])
