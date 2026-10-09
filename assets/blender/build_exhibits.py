"""Build the four Huzhou interpretive exhibits in Blender 4.2.

Run: blender --background --python assets/blender/build_exhibits.py -- <project-root>
Every movable Empty stores explosion data in glTF extras. Geometry is authored
in Blender; no Three.js primitives are used for the shipped exhibits.
"""

import bpy
import math
import os
import random
import sys
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from surface_maps import surface_maps
SURFACE_CACHE = {}

ROOT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.getcwd()
MODEL_DIR = os.path.join(ROOT, 'public', 'models')
SOURCE_DIR = os.path.join(ROOT, 'assets', 'blender', 'sources')
PREVIEW_DIR = os.path.join(ROOT, 'assets', 'blender', 'previews')
for folder in (MODEL_DIR, SOURCE_DIR, PREVIEW_DIR):
    os.makedirs(folder, exist_ok=True)

random.seed(24)
texture_cache = {}


def surface_kind(name):
    key = name.lower()
    if 'bamboo' in key: return 'bamboo'
    if 'timber' in key or 'wood' in key: return 'wood'
    if 'glaze' in key or 'celadon' in key: return 'glaze'
    if 'tile' in key or 'roof ceramic' in key: return 'tile'
    if 'stone' in key or 'brick' in key: return 'stone' if 'stone' in key else 'brick'
    if 'silk' in key: return 'silk'
    if 'hair' in key: return 'hair'
    if 'leaf' in key or 'bud' in key: return 'leaf'
    if 'clay' in key: return 'stone'
    return None


def hash2(x, y):
    value = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return value - math.floor(value)


def smooth_noise(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx, sy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = hash2(ix, iy) * (1 - sx) + hash2(ix + 1, iy) * sx
    b = hash2(ix, iy + 1) * (1 - sx) + hash2(ix + 1, iy + 1) * sx
    return a * (1 - sy) + b * sy


def surface_signal(kind, u, v):
    coarse = smooth_noise(u * 9, v * 8)
    fine = smooth_noise(u * 66, v * 65)
    if kind == 'bamboo':
        line = math.sin(2 * math.pi * (u * 46 + 0.10 * math.sin(v * 13)))
        return 0.48 + 0.25 * line + 0.14 * coarse + 0.10 * fine
    if kind == 'wood':
        warped = u * 29 + 0.18 * math.sin(v * 17 + u * 9)
        return 0.48 + 0.23 * math.sin(2 * math.pi * warped) + 0.16 * coarse + 0.10 * fine
    if kind == 'silk' or kind == 'hair':
        return 0.52 + 0.20 * math.sin(2 * math.pi * u * 74) + 0.17 * fine
    if kind == 'glaze':
        # Celadon reads as a continuous fired glaze, not a field of stippled cracks.
        # Broad, low-amplitude kiln variation survives at close range without spots.
        broad = smooth_noise(u * 4.2, v * 4.0)
        return 0.46 + 0.13 * broad + 0.035 * coarse + 0.012 * fine
    if kind == 'leaf':
        return 0.48 + 0.19 * math.sin(v * 24 + u * 7) + 0.19 * coarse + 0.12 * fine
    return 0.40 + 0.34 * coarse + 0.25 * fine


def texture_image(kind, channel, rgb, rough):
    cache_key = (kind, channel, tuple(rgb), rough)
    if cache_key in texture_cache:
        return texture_cache[cache_key]
    key = (kind, tuple(rgb), rough)
    if key not in SURFACE_CACHE:
        SURFACE_CACHE[key] = surface_maps(kind, rgb, rough, 1024)
    pixels = SURFACE_CACHE[key][channel]
    size = pixels.shape[0]
    image = bpy.data.images.new(f'{kind}_{channel}_{len(texture_cache)}', width=size, height=size, alpha=True)
    image.file_format = 'PNG'
    image.colorspace_settings.name = 'sRGB' if channel == 'color' else 'Non-Color'
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    texture_cache[cache_key] = image
    return image


def material(name, rgb, rough=0.7, metallic=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, alpha)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, alpha)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Alpha'].default_value = alpha
    if alpha < 1:
        m.blend_method = 'BLEND'
        m.use_nodes = True
    kind = surface_kind(name)
    if kind == 'glaze':
        p.inputs['Coat Weight'].default_value = 0.28
        p.inputs['Coat Roughness'].default_value = 0.12
        p.inputs['IOR'].default_value = 1.46
    if kind:
        links = m.node_tree.links
        color = m.node_tree.nodes.new('ShaderNodeTexImage')
        color.label = f'{kind} albedo'
        color.image = texture_image(kind, 'color', rgb, rough)
        links.new(color.outputs['Color'], p.inputs['Base Color'])
        texture_rough = m.node_tree.nodes.new('ShaderNodeTexImage')
        texture_rough.label = f'{kind} roughness'
        texture_rough.image = texture_image(kind, 'roughness', rgb, rough)
        links.new(texture_rough.outputs['Color'], p.inputs['Roughness'])
        texture_normal = m.node_tree.nodes.new('ShaderNodeTexImage')
        texture_normal.label = f'{kind} micro normal'
        texture_normal.image = texture_image(kind, 'normal', rgb, rough)
        normal_map = m.node_tree.nodes.new('ShaderNodeNormalMap')
        normal_map.inputs['Strength'].default_value = 0.20 if kind == 'glaze' else 0.55
        links.new(texture_normal.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], p.inputs['Normal'])
    return m


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)


def part(name, loc=(0, 0, 0), direction=None, distance=0):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.empty_display_size = 0.15
    e.location = loc
    if direction is not None:
        e['explodeDirection'] = list(direction)  # Three.js coordinates, Y up
        e['explodeDistance'] = float(distance)
    return e


def attach(obj, parent, loc=(0, 0, 0), mat=None, bevel=0):
    obj.parent = parent
    obj.location = loc
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('soft machined edge', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        obj.modifiers.new('weighted normals', 'WEIGHTED_NORMAL')
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = len(poly.vertices) > 3
    return obj


def cube(parent, name, loc, size, mat, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(obj, parent, loc, mat, bevel)


def cylinder(parent, name, loc, radius, depth, mat, vertices=24, radius_top=None):
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius_top, depth=depth)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, parent, loc, mat)


def uv_sphere(parent, name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return attach(obj, parent, loc, mat)


def rod(parent, name, a, b, radius, mat, vertices=8):
    va, vb = Vector(a), Vector(b)
    mid = (va + vb) / 2
    obj = cylinder(parent, name, mid, radius, (vb - va).length, mat, vertices)
    obj.rotation_euler = (vb - va).to_track_quat('Z', 'Y').to_euler()
    return obj


def tube(parent, name, points, radius, mat, resolution=2):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)
    for p, co in zip(spline.bezier_points, points):
        p.co = co
        p.handle_left_type = 'AUTO'
        p.handle_right_type = 'AUTO'
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    return attach(obj, parent, mat=mat)


def lathe(parent, name, profile, mat, segments=64):
    verts = []
    faces = []
    for r, z in profile:
        for i in range(segments):
            a = i * 2 * math.pi / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(len(profile) - 1):
        for i in range(segments):
            k = j * segments + i
            n = j * segments + (i + 1) % segments
            faces.append((k, n, n + segments, k + segments))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='Surface UV')
    for polygon in mesh.polygons:
        seam = any(mesh.loops[loop].vertex_index % segments == segments - 1 for loop in polygon.loop_indices)
        for loop in polygon.loop_indices:
            vertex = mesh.loops[loop].vertex_index
            column = vertex % segments
            row = vertex // segments
            u = 1 if seam and column == 0 else column / segments
            uv_layer.data[loop].uv = (u, row / max(1, len(profile) - 1))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return attach(obj, parent, mat=mat)


def ring(parent, name, radius, z, thickness, mat, sides=48):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=thickness,
                                     major_segments=sides, minor_segments=6)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, parent, (0, 0, z), mat)


def oct_point(r, i, offset=math.pi / 8):
    a = i * math.pi / 4 + offset
    return (r * math.cos(a), r * math.sin(a))


def oct_rail(parent, name, r, z, mat, width=0.018):
    for i in range(8):
        a, b = oct_point(r, i), oct_point(r, (i + 1) % 8)
        rod(parent, f'{name} {i + 1}', (a[0], a[1], z), (b[0], b[1], z), width, mat)


def prepare_render(name, height, camera_at=(7, -9, 5.3)):
    world = bpy.context.scene.world or bpy.data.worlds.new('studio')
    bpy.context.scene.world = world
    world.color = (0.025, 0.038, 0.035)
    bpy.ops.object.camera_add(location=camera_at)
    camera = bpy.context.object
    camera.name = 'PREVIEW_CAMERA'
    camera.rotation_euler = (Vector((0, 0, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = height
    bpy.context.scene.camera = camera
    for name_light, position, power, color, size in [
        ('warm key', (5, -4, 8), 1250, (1, 0.86, 0.68), 6),
        ('cool fill', (-6, -2, 4), 650, (0.60, 0.77, 0.79), 5),
        ('rim', (-2, 4, 7), 1450, (1, 0.91, 0.76), 4),
    ]:
        bpy.ops.object.light_add(type='AREA', location=position)
        lamp = bpy.context.object
        lamp.name = name_light
        lamp.data.energy = power
        lamp.data.color = color
        lamp.data.shape = 'DISK'
        lamp.data.size = size
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = os.path.join(PREVIEW_DIR, f'{name}.png')
    scene.view_settings.view_transform = 'AgX'
    scene.render.image_settings.color_mode = 'RGBA'
    bpy.ops.render.render(write_still=True)


def export(name, preview_height, camera_at=(7, -9, 5.3)):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE_DIR, f'{name}.blend'))
    # Keep editable curves in the .blend source but bake their bevelled geometry
    # into meshes for the glTF exporter and the browser renderer.
    bpy.ops.object.select_all(action='DESELECT')
    curves = [obj for obj in bpy.data.objects if obj.type == 'CURVE']
    if curves:
        for obj in curves:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.select_all(action='DESELECT')
    # Cameras/lights are not included in exported GLB.
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODEL_DIR, f'{name}.glb'),
                              export_format='GLB', export_extras=True,
                              export_cameras=False, export_lights=False,
                              export_apply=False)
    prepare_render(name, preview_height, camera_at)
    for obj in bpy.data.objects:
        if 'explodeDirection' not in obj:
            continue
        dx, dy, dz = obj['explodeDirection']
        obj.location += Vector((dx, -dz, dy)) * float(obj['explodeDistance'])
    bpy.context.view_layer.update()
    vertices = [obj.matrix_world @ Vector(corner)
                for obj in bpy.data.objects if obj.type == 'MESH'
                for corner in obj.bound_box]
    low = Vector(tuple(min(v[axis] for v in vertices) for axis in range(3)))
    high = Vector(tuple(max(v[axis] for v in vertices) for axis in range(3)))
    center = (low + high) / 2
    camera = bpy.context.scene.camera
    camera.location = center + Vector(camera_at)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = max((high - low).z * 1.3, (high - low).x * 1.5)
    bpy.context.scene.render.filepath = os.path.join(PREVIEW_DIR, f'{name}-expanded.png')
    bpy.ops.render.render(write_still=True)
    print('EXPORTED', name, os.path.getsize(os.path.join(MODEL_DIR, f'{name}.glb')))


def brush():
    reset()
    bamboo = material('aged amber bamboo', (0.55, 0.38, 0.21), 0.6)
    bamboo_dark = material('bamboo end grain', (0.28, 0.18, 0.10), 0.88)
    bamboo_light = material('bamboo highlight', (0.7, 0.52, 0.29), 0.62)
    cord = material('linen binding', (0.65, 0.55, 0.35), 0.92)
    hair = material('purple rabbit hair', (0.20, 0.15, 0.12), 0.96)
    hair_light = material('pale blended hair', (0.72, 0.65, 0.52), 0.93)
    root = part('湖笔_总成')
    shaft = part('竹笔杆', (0, 0, 0.61), (0, 1, 0), 0.18)
    shaft.parent = root
    cylinder(shaft, '细长竹管', (0, 0, 0), 0.091, 3.40, bamboo, 48, radius_top=0.086)
    for z in (-1.62, 0.56, 1.60):
        ring(shaft, '竹管天然节痕', 0.090, z, 0.007, bamboo_dark)
        ring(shaft, '节痕亮边', 0.091, z + 0.016, 0.003, bamboo_light)
    # A slightly offset, natural growth scar breaks the silhouette's axial symmetry.
    # This is interpretive bamboo morphology, not a claimed inscription or relic mark.
    scar = uv_sphere(shaft, '竹节自然生长痕', (0.017, -0.086, 0.56),
                     (0.028, 0.0045, 0.042), bamboo_dark)
    scar.rotation_euler[2] = -0.34
    for i in range(9):
        z = -1.08 + i * 0.255
        a = -1.18 + i * 0.23
        r = 0.0908
        uv_sphere(shaft, '竹皮细斑', (r * math.cos(a), r * math.sin(a), z),
                  (0.0025, 0.0018, 0.013 + (i % 3) * 0.002),
                  bamboo_dark if i % 3 == 0 else bamboo_light)
    # Subtle longitudinal grain, not metal decoration.
    for i in range(12):
        a = i * 2 * math.pi / 12
        r = 0.0905
        tube(shaft, '竹纤维浅纹', [(r * math.cos(a), r * math.sin(a), -1.44),
                                (r * math.cos(a + 0.035), r * math.sin(a + 0.035), 0),
                                (r * math.cos(a + 0.015), r * math.sin(a + 0.015), 1.47)],
             0.0008, bamboo_light, 1)
    socket = part('嵌接管口', (0, 0, -1.12), (0, -1, 0), 0.30)
    socket.parent = root
    cylinder(socket, '竹口套接', (0, 0, 0), 0.10, 0.22, bamboo_dark, 40, radius_top=0.085)
    ring(socket, '管口内沿', 0.102, -0.1, 0.009, bamboo_light)
    binding = part('毫根结头', (0, 0, -1.30), (0, -1, 0), 0.35)
    binding.parent = root
    cylinder(binding, '捆扎毫根', (0, 0, 0), 0.105, 0.2, cord, 40, radius_top=0.09)
    for i in range(7):
        ring(binding, '丝线绕扎', 0.105 - i * 0.0015, -0.075 + i * 0.026, 0.004, bamboo_dark)
    tip = part('笔锋_一整束', (0, 0, -1.60), (0, -1, 0), 0.67)
    tip.parent = root
    # One continuous, tapering lan-rui brush head. Fibres are geometry inside ONE movable part.
    lathe(tip, '兰蕊毫束芯', [(0.06, 0.18), (0.105, 0.11), (0.145, -0.12),
                            (0.13, -0.32), (0.10, -0.48), (0.055, -0.67),
                            (0.002, -0.88)], hair, 48)
    for i in range(360):
        a = i * 2.399963
        r = 0.114 * math.sqrt((i + 0.5) / 360)
        x, y = r * math.cos(a), r * math.sin(a)
        blend = i % 7 == 0
        tube(tip, '一束笔锋中的单根毫', [(x * 0.58, y * 0.58, 0.18),
             (x * 1.12, y * 1.12, -0.06), (x, y, -0.30),
             (x * 0.68, y * 0.68, -0.52), (x * 0.14, y * 0.14, -0.76),
             (0, 0, -0.91 + random.uniform(-0.025, 0.02))],
             0.0015 if blend else 0.0011, hair_light if blend else hair, 1)
    export('brush', 6.9, (6.3, -8, 4))


def loom():
    reset()
    oak = material('warm carved timber', (0.42, 0.27, 0.14), 0.78)
    dark = material('dark mortise wood', (0.18, 0.115, 0.075), 0.86)
    edge = material('worked wood edge', (0.59, 0.39, 0.22), 0.68)
    silk = material('Jili silk ivory', (0.88, 0.77, 0.55), 0.48)
    silk2 = material('silk shadow', (0.64, 0.50, 0.31), 0.55)
    brass = material('bronze pins', (0.56, 0.43, 0.22), 0.38, 0.55)
    root = part('双林水平织机_总成')
    frame = part('机架木构', (0, 0, 0), (0, -1, 0), 0.40); frame.parent = root
    for x in (-1.56, 1.56):
        for y in (-1.38, 1.38):
            cube(frame, '榫卯立柱', (x, y, -0.20), (0.14, 0.14, 2.07), oak, 0.016)
            cube(frame, '柱脚', (x, y, -1.20), (0.23, 0.22, 0.10), dark)
            uv_sphere(frame, '木柱顶销', (x, y, 0.87), (0.08, 0.08, 0.035), brass)
        for z in (-0.83, 0.42):
            cube(frame, '纵向梁', (x, 0, z), (0.12, 3.02, 0.13), edge)
    for y in (-1.40, 1.40):
        for z in (-0.82, 0.42):
            cube(frame, '横向榫梁', (0, y, z), (3.3, 0.13, 0.12), oak)
    # Distinct winding axes and pedals.
    for name, y, dy in [('经轴_送经', -1.32, -1), ('卷布轴_成绫', 1.32, 1)]:
        group = part(name, (0, y, -0.24), (0, 0, dy), 0.68); group.parent = root
        rod(group, '木制轴心', (-1.42, 0, 0), (1.42, 0, 0), 0.155, oak, 24)
        for x in (-1.44, 1.44):
            obj = cylinder(group, '轴端挡板', (x, 0, 0), 0.245, 0.055, dark, 32)
            obj.rotation_euler[1] = math.pi / 2
            for k in range(8):
                a = k * math.pi / 4
                uv_sphere(group, '轴端铜钉', (x + (0.029 if x > 0 else -0.029),
                          0.19 * math.cos(a), 0.19 * math.sin(a)), (0.013, 0.013, 0.013), brass)
    for i in range(2):
        y = -0.42 + i * 0.22
        g = part(f'综框{i + 1}', (0, y, 0.22 + i * 0.17), (0, 1, (-1)**i * 0.3), 0.66); g.parent = root
        for z in (-0.28, 0.28): cube(g, '综框横木', (0, 0, z), (3.02, 0.07, 0.07), dark)
        for x in (-1.47, 1.47): cube(g, '综框竖木', (x, 0, 0), (0.07, 0.08, 0.64), dark)
        for k in range(48):
            x = (k - 23.5) * 0.059
            rod(g, '独立综丝', (x, 0, -0.25), (x, 0, 0.25), 0.0024, silk2, 5)
    reed = part('筘_密排打纬', (0, 0.47, 0.12), (0, 1, 0.4), 0.75); reed.parent = root
    for z in (-0.33, 0.33): cube(reed, '筘框横木', (0, 0, z), (3.05, 0.09, 0.08), dark)
    for i in range(97):
        x = (i - 48) * 0.029
        rod(reed, '筘齿', (x, 0, -0.29), (x, 0, 0.29), 0.0022, brass, 4)
    # Ninety-six warp threads, each a distinct named curve; opening is alternating.
    for group_index in range(8):
        g = part(f'经丝组{group_index + 1}', (0, 0, 0.06),
                 ((group_index - 3.5) * 0.16, 0.1, 0.35), 0.42)
        g.parent = root
        for i in range(12):
            index = group_index * 12 + i
            x = (index - 47.5) * 0.029
            rise = 0.065 if index % 2 else -0.055
            tube(g, f'经丝{index + 1:03d}', [(x, -1.31, -0.12),
                 (x, -0.53, rise), (x, 0.28, rise), (x, 1.31, -0.12)],
                 0.004, silk2 if index % 11 == 0 else silk, 1)
    weft = part('纬丝_逐根穿梭', (0, 0.63, 0.065), (0, 1, 0.25), 0.50); weft.parent = root
    for row in range(30):
        y = 0.61 + row * 0.025
        points = [(-1.39 + i * 0.029, y,
                   0.022 if (i + row) % 2 else 0.077) for i in range(97)]
        tube(weft, f'纬丝{row + 1:02d}', points, 0.0037, silk if row % 7 else silk2, 1)
    shuttle = part('木梭_纡管', (0.1, 0.20, -0.06), (1, 0.35, 0.45), 0.95); shuttle.parent = root
    uv_sphere(shuttle, '梭身', (0, 0, 0), (0.55, 0.16, 0.09), oak)
    cube(shuttle, '梭心凹槽', (0, 0, 0.07), (0.52, 0.07, 0.025), dark, 0.01)
    rod(shuttle, '纡管', (-0.23, 0, 0.10), (0.23, 0, 0.10), 0.035, silk2, 12)
    for x in (-0.4, 0.4): uv_sphere(shuttle, '梭尖', (x, 0, 0), (0.18, 0.10, 0.055), edge)
    cloth = part('成绫织物', (0, 0.95, 0.055), (0, 0.4, 0.45), 0.55); cloth.parent = root
    for i in range(96):
        x = (i - 47.5) * 0.029
        rod(cloth, f'织物经线{i:03d}', (x, -0.31, 0), (x, 0.31, 0), 0.0038, silk, 4)
    for j in range(22):
        y = (j - 10.5) * 0.029
        rod(cloth, f'织物纬线{j:02d}', (-1.39, y, 0.004), (1.39, y, 0.004), 0.0038, silk2 if j % 8 == 0 else silk, 4)
    export('loom', 6.6, (6.6, -8.5, 5.5))


def leaf_mesh(parent, name, loc, angle, size, green, vein):
    length, width = size
    verts = []
    faces = []
    across = (-1, -0.5, 0, 0.5, 1)
    for row in range(17):
        t = row / 16
        y = (t - 0.52) * length
        breadth = width * max(0.03, math.sin(math.pi * t) ** 0.8)
        for u in across:
            x = u * breadth * (1 + 0.055 * math.sin(t * 18 + angle * 3))
            z = 0.012 + 0.075 * t + 0.015 * math.sin(math.pi * t) - 0.020 * abs(u)
            verts.append((x, y, z))
    for row in range(16):
        for col in range(4):
            a = row * 5 + col
            faces.append((a, a + 1, a + 6, a + 5))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name='Leaf UV')
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop in polygon.loop_indices:
            vertex = mesh.loops[loop].vertex_index
            uv_layer.data[loop].uv = ((vertex % 5) / 4, (vertex // 5) / 16)
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ob)
    attach(ob, parent, loc, green)
    subdivision = ob.modifiers.new('叶面连续曲率', 'SUBSURF')
    subdivision.levels = 1
    subdivision.render_levels = 1
    thickness = ob.modifiers.new('真实薄叶厚度', 'SOLIDIFY')
    thickness.thickness = 0.0012
    ob.rotation_euler[2] = angle
    ca, sa = math.cos(angle), math.sin(angle)
    def at(x, y, z):
        return (loc[0] + x * ca - y * sa, loc[1] + x * sa + y * ca, loc[2] + z)
    tube(parent, '清晰中脉', [at(0, -length * 0.47, 0.017), at(0, 0, 0.067),
                             at(0, length * 0.43, 0.088)], 0.0029, vein, 1)
    for side in (-1, 1):
        for j in range(3):
            y = -length * 0.18 + j * length * 0.18
            tube(parent, '可见侧脉', [at(0, y + 0.03, 0.045),
                 at(side * width * (0.62 + j * 0.08), y, 0.046)], 0.002, vein, 1)
    return ob


def tea():
    reset()
    glaze = material('Yue celadon glaze', (0.38, 0.55, 0.46), 0.22)
    glaze_light = material('celadon glazed lip', (0.55, 0.69, 0.58), 0.19)
    foot = material('exposed pale clay foot', (0.73, 0.67, 0.55), 0.85)
    liquor = material('clear golden tea liquor', (0.25, 0.17, 0.025), 0.27, alpha=0.62)
    surface = material('tea surface amber', (0.32, 0.23, 0.035), 0.26, alpha=0.67)
    green = material('steeped purple-shoot leaf', (0.095, 0.205, 0.055), 0.75)
    green2 = material('young tea bud', (0.155, 0.285, 0.072), 0.70)
    vein = material('leaf vein', (0.25, 0.37, 0.11), 0.75)
    root = part('紫笋茶与越窑盏_总成')
    saucer = part('盏托_宽折沿与圈足', (0, 0, -0.88), (0, -1, 0), 0.75); saucer.parent = root
    lathe(saucer, '盏托一体成形', [(0.52, -0.20), (0.62, -0.20), (0.62, -0.09),
         (0.58, -0.05), (0.74, 0.00), (1.05, 0.03), (1.32, 0.21),
         (1.35, 0.26), (1.31, 0.285), (1.00, 0.12), (0.72, 0.10),
         (0.51, 0.06), (0.0, 0.06)], glaze, 96)
    ring(saucer, '托盘口沿亮线', 1.327, 0.266, 0.013, glaze_light, 96)
    ring(saucer, '托盘底足露胎', 0.57, -0.19, 0.023, foot, 72)
    bowl = part('茶盏_深腹内壁与圈足', (0, 0, -0.13), (0, 1, 0), 0.34); bowl.parent = root
    lathe(bowl, '茶盏陶瓷连续体', [(0.33, -0.47), (0.45, -0.47), (0.47, -0.37),
         (0.58, -0.29), (0.73, -0.05), (0.89, 0.30), (0.985, 0.52),
         (1.00, 0.55), (0.965, 0.575), (0.930, 0.54), (0.81, 0.23),
         (0.64, -0.09), (0.51, -0.32), (0.39, -0.37), (0, -0.37)], glaze, 96)
    ring(bowl, '青釉薄口沿', 0.979, 0.551, 0.021, glaze_light, 96)
    ring(bowl, '茶盏圈足露胎', 0.402, -0.469, 0.021, foot, 72)
    # The shallow translucent lens reads as liquid when lifted out. A full
    # conforming volume looked like a second ceramic bowl in the exploded view.
    tea_part = part('茶汤_透明液体体积', (0, 0, -0.13), (0, 1, 0), 1.28); tea_part.parent = root
    lathe(tea_part, '茶汤透亮浅层', [(0, 0.215), (0.60, 0.218), (0.76, 0.24),
          (0.80, 0.264), (0.78, 0.285)], liquor, 72)
    cylinder(tea_part, '澄黄液面', (0, 0, 0.279), 0.785, 0.01, surface, 96)
    ring(tea_part, '清晰液面弯月边界', 0.788, 0.285, 0.009, glaze_light, 96)
    # Each bud is a distinct part; leaves are above the liquid, not fused into it.
    for i in range(7):
        a = i * 2.399963
        r = 0.11 + (i % 3) * 0.19
        g = part(f'芽叶{i + 1}_一芽二叶', (r * math.cos(a), r * math.sin(a), 0.16),
                 (math.cos(a) * 0.9, 2.0, math.sin(a) * 0.9), 1.9 + i * 0.07)
        g.parent = root
        leaf_mesh(g, '舒展茶叶', (-0.045, 0, 0.02), a - 0.28, (0.36 + i % 3 * 0.03, 0.12),
                  green if i % 2 else green2, vein)
        leaf_mesh(g, '另一片舒展茶叶', (0.05, 0.01, 0.005), a + 0.34,
                  (0.28 + i % 2 * 0.03, 0.10), green2 if i % 2 else green, vein)
        bud = uv_sphere(g, '紫笋芽尖', (0.015, -0.01, 0.10), (0.018, 0.016, 0.075), green2)
        bud.rotation_euler[1] = -0.32
        tube(g, '茶梗', [(0, 0, -0.04), (0.01, -0.01, 0.05), (0.015, -0.01, 0.13)], 0.004, vein)
    export('tea', 4.3, (5.5, -7.8, 4.9))


def tower():
    reset()
    brick = material('weathered warm brick', (0.40, 0.255, 0.205), 0.91)
    brick2 = material('brick sunlight', (0.51, 0.35, 0.27), 0.88)
    timber = material('deep red timber', (0.255, 0.145, 0.115), 0.76)
    timber_dark = material('blackened carved timber', (0.11, 0.075, 0.055), 0.82)
    tile = material('slate roof ceramic', (0.12, 0.16, 0.17), 0.67)
    tile_hi = material('tile ridge glint', (0.175, 0.225, 0.23), 0.62)
    stone = material('pale inner carved stone', (0.65, 0.62, 0.53), 0.94)
    stone_dark = material('stone niche shadow', (0.29, 0.29, 0.25), 0.96)
    gold = material('aged bronze finial', (0.58, 0.42, 0.20), 0.49, 0.42)
    root = part('飞英塔_七外五内总成')
    foundation = part('八角塔基', (0, 0, -2.45), (0, -1, 0), 0.35); foundation.parent = root
    cylinder(foundation, '石塔基下层', (0, 0, -0.08), 1.04, 0.16, stone_dark, 8, 0.97)
    cylinder(foundation, '塔基莲座台阶', (0, 0, 0.05), 1.0, 0.09, stone, 8)
    for r, z in ((1.0, 0.1), (0.92, 0.14)):
        oct_rail(foundation, '塔基线脚', r, z, stone, 0.018)
    inner_base = part('内塔须弥座_莲瓣', (0, 0, -2.16), (0.55, 0, 0), 0.50); inner_base.parent = root
    cylinder(inner_base, '须弥座束腰', (0, 0, 0), 0.48, 0.18, stone, 8, 0.40)
    for i in range(32):
        a = i * 2 * math.pi / 32
        uv_sphere(inner_base, '石刻莲瓣', (0.50 * math.cos(a), 0.50 * math.sin(a), 0.06),
                  (0.07, 0.023, 0.09), stone)
    # Smaller five-level stone tower physically inside the seven-level shell.
    for level in range(5):
        z = -1.96 + level * 0.35
        r = 0.41 - level * 0.032
        group = part(f'内塔石层{level + 1}', (0, 0, z),
                     (0.08 * (-1)**level, 0.45, 0.15), 0.36 + level * 0.07)
        group.parent = root
        cylinder(group, '石层八角壁', (0, 0, 0), r, 0.25, stone, 8, r * 0.87)
        cylinder(group, '仿木石檐', (0, 0, 0.16), r * 1.18, 0.09, stone_dark, 8, r * 0.78)
        oct_rail(group, '石檐刻线', r * 1.12, 0.12, stone, 0.012)
        for face in range(8):
            a = face * math.pi / 4 + math.pi / 8
            x, y = r * 0.87 * math.cos(a), r * 0.87 * math.sin(a)
            niche = cube(group, '佛龛暗口', (x, y, 0.015), (r * 0.29, 0.012, 0.13), stone_dark, 0.004)
            niche.rotation_euler[2] = a + math.pi / 2
            if face % 2 == level % 2:
                uv_sphere(group, '佛龛浮雕', (x * 1.03, y * 1.03, 0.005),
                          (0.025, 0.02, 0.054), stone)
    # Outer shell deliberately leaves two front bays open as an explanatory cutaway.
    for level in range(7):
        z = -1.86 + level * 0.61
        r = 0.95 - level * 0.055
        wall = part(f'外塔楼层{level + 1}', (0, 0, z),
                    (1, 0.06 + level * 0.015, 0), 0.95 + level * 0.06)
        wall.parent = root
        oct_rail(wall, '楼层腰枋', r * 0.85, -0.24, timber_dark, 0.026)
        oct_rail(wall, '楼层上枋', r * 0.85, 0.25, timber, 0.031)
        for face in range(8):
            a = face * math.pi / 4 + math.pi / 8
            x, y = oct_point(r * 0.84, face)
            # Front faces toward viewer (negative Y) remain open for the stone tower.
            if y > -r * 0.54:
                panel = cube(wall, '青砖墙与窗格', (x, y, 0.01), (r * 0.53, 0.045, 0.30),
                             brick2 if face % 2 else brick, 0.01)
                panel.rotation_euler[2] = a + math.pi / 2
                for bar in (-0.16, 0, 0.16):
                    tangent = Vector((-math.sin(a), math.cos(a), 0))
                    pos = Vector((x, y, 0)) + tangent * r * bar
                    rod(wall, '窗棂', (pos.x, pos.y, -0.14),
                        (pos.x, pos.y, 0.15), 0.009, timber_dark, 6)
            corner = oct_point(r * 0.91, face, 0)
            rod(wall, '朱漆角柱', (corner[0], corner[1], -0.28),
                (corner[0], corner[1], 0.25), 0.030, timber, 8)
        for radius, y_z in ((r * 0.87, -0.24), (r * 0.98, -0.10)):
            oct_rail(wall, '回廊栏杆', radius, y_z, timber_dark, 0.015)
        # Three-tier bracket sets in all eight bays, each arm still geometrically present.
        for face in range(8):
            a = face * math.pi / 4 + math.pi / 8
            for step in range(3):
                rad = r * (0.77 + step * 0.10)
                x, y = rad * math.cos(a), rad * math.sin(a)
                arm = cube(wall, '斗拱_层叠拱臂', (x, y, 0.04 + step * 0.05),
                           (0.08 + step * 0.065, 0.14 + step * 0.04, 0.035),
                           timber if step < 2 else timber_dark, 0.006)
                arm.rotation_euler[2] = a
                cube(wall, '斗拱_方斗', (x, y, 0.065 + step * 0.05),
                     (0.045, 0.045, 0.04), timber_dark, 0.004)
        roof = part(f'外塔飞檐{level + 1}', (0, 0, z + 0.34),
                    (-1, 0.08 + level * 0.015, 0), 0.90 + level * 0.055)
        roof.parent = root
        cylinder(roof, '八角坡瓦面', (0, 0, -0.035), r * 1.22, 0.20, tile, 8, r * 0.66)
        cylinder(roof, '脊部小坡', (0, 0, 0.085), r * 0.78, 0.055, tile_hi, 8, r * 0.64)
        oct_rail(roof, '檐口线脚', r * 1.22, -0.13, tile_hi, 0.019)
        for face in range(8):
            a = face * math.pi / 4 + math.pi / 8
            c, s = math.cos(a), math.sin(a)
            tube(roof, '翘角瓦脊', [(r * 0.61 * c, r * 0.61 * s, 0.11),
                 (r * 1.1 * c, r * 1.1 * s, -0.08),
                 (r * 1.25 * c, r * 1.25 * s, 0.01)], 0.018, tile_hi)
            # Muted rows of cylindrical tiles; the roof should read as fired
            # ceramics, not as a bright wireframe at close zoom.
            for j in range(1, 8):
                angle = a + (j - 4) * math.pi / 38
                c2, s2 = math.cos(angle), math.sin(angle)
                tube(roof, '逐道筒瓦', [(r * 0.72 * c2, r * 0.72 * s2, 0.07),
                      (r * 1.03 * c2, r * 1.03 * s2, -0.035),
                      (r * 1.18 * c2, r * 1.18 * s2, -0.12)],
                     0.0035, tile_hi, 1)
    finial = part('塔刹_宝珠相轮', (0, 0, 2.46), (0, 1, 0), 0.55); finial.parent = root
    cylinder(finial, '刹杆', (0, 0, 0.25), 0.026, 0.75, gold, 16)
    for i in range(7):
        ring(finial, '层层相轮', 0.125 - i * 0.010, 0.02 + i * 0.082, 0.018, gold, 32)
    uv_sphere(finial, '塔刹宝珠', (0, 0, 0.75), (0.075, 0.075, 0.11), gold)
    export('tower', 7.1, (7.0, -10.5, 6.2))


makers = {'brush': brush, 'loom': loom, 'tea': tea, 'tower': tower}
selected = os.environ.get('EXHIBIT_ONLY')
if selected and selected not in makers:
    raise ValueError(f'Unknown EXHIBIT_ONLY: {selected}')
for key, maker in makers.items():
    if not selected or selected == key:
        maker()
