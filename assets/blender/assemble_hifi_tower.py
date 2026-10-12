"""Assemble the Lux3D hero with the semantic Blender tower scene.

Run with Blender 4.2 in background mode. The exported GLB keeps the
procedural semantic groups for scroll decomposition and stores the Lux3D
hero as a separate collection for the first and last screens.
"""
import bpy
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SOURCE_BLEND = os.path.join(ROOT, 'assets', 'blender', 'sources', 'tower.blend')
LUX_GLTF = os.path.join(ROOT, 'public', 'models', 'tower-lux3d.glb')
OUT_BLEND = os.path.join(ROOT, 'assets', 'blender', 'sources', 'tower-hifi.blend')
OUT_GLTF = os.path.join(ROOT, 'public', 'models', 'tower-hifi.glb')

bpy.ops.wm.open_mainfile(filepath=SOURCE_BLEND)

# Keep the semantic Blender scene intact as the animated decomposition base.
for obj in bpy.context.scene.objects:
    obj.select_set(False)

hero_collection = bpy.data.collections.get('lux3d_hero') or bpy.data.collections.new('lux3d_hero')
if hero_collection.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(hero_collection)

before = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=LUX_GLTF)
hero_objects = [obj for obj in bpy.context.scene.objects if obj not in before]
for obj in hero_objects:
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    hero_collection.objects.link(obj)
    obj.name = f'lux3d_hero__{obj.name}'
    obj['screenRole'] = 'hero-surface'
    obj['source'] = 'Aholo Lux3D G1-Turbo'

# The hero is used for the cover/detail/return screens. The semantic scene is
# retained for the exploded structural screens and remains the editable source.
hero_collection['screenRoles'] = ['cover', 'surface', 'return']
hero_collection['semanticFallback'] = 'tower procedural Blender groups'

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=OUT_GLTF, export_format='GLB', use_selection=False, export_apply=True)
print(f'ASSEMBLED {OUT_BLEND}')
print(f'EXPORTED {OUT_GLTF}')
