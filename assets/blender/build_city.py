"""Blender 4.2: four interpretive, photo-informed Huzhou city miniatures.

Run: blender --background --python assets/blender/build_city.py -- <project-root>
Set CITY_ONLY=yishang|dongwu|longemont|nanxun to rebuild one scene.
All geometry and materials are authored in Blender. Movable Empties carry glTF extras.
"""

import bpy
import bmesh
import math
import os
import random
import re
import sys
from mathutils import Vector, Quaternion

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from architectural_geometry import ellipsoid_sector, clipped_rectangle
from surface_maps import surface_maps

TEXTURE_CACHE = {}

ROOT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.getcwd()
SOURCES = os.path.join(ROOT, 'assets', 'blender', 'sources')
PREVIEWS = os.path.join(ROOT, 'assets', 'blender', 'previews')
MODELS = os.path.join(ROOT, 'public', 'models')
for folder in (SOURCES, PREVIEWS, MODELS):
    os.makedirs(folder, exist_ok=True)
random.seed(2810)
PHOTO_MATS = {}


def noise(x, y):
    n = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return n - math.floor(n)


def surface(kind, u, v):
    coarse = noise(math.floor(u * 24), math.floor(v * 24))
    fine = noise(math.floor(u * 111), math.floor(v * 97))
    if kind == 'stone': return 0.52 + 0.22 * coarse + 0.13 * fine
    if kind == 'wood': return 0.5 + 0.22 * math.sin(u * 115 + 2 * math.sin(v * 11)) + 0.11 * fine
    if kind == 'tile': return 0.48 + 0.21 * math.sin(u * 49) + 0.15 * coarse
    if kind == 'glass': return 0.52 + 0.17 * coarse + 0.055 * fine
    if kind == 'water': return 0.48 + 0.2 * math.sin(v * 72 + u * 13) + 0.11 * fine
    return 0.48 + 0.12 * coarse + 0.08 * fine


def texture(kind, channel, rgb, rough):
    key = (kind, tuple(rgb), rough)
    if key not in TEXTURE_CACHE:
        TEXTURE_CACHE[key] = surface_maps(kind, rgb, rough, 1024)
    pixels = TEXTURE_CACHE[key][channel]
    size = pixels.shape[0]
    image = bpy.data.images.new(f'{kind}_{channel}_{len(bpy.data.images)}', width=size, height=size, alpha=True)
    image.file_format = 'PNG'
    image.colorspace_settings.name = 'sRGB' if channel == 'color' else 'Non-Color'
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    return image


def mat(name, rgb, rough=0.7, metallic=0, kind=None, glow=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    if glow:
        p.inputs['Emission Color'].default_value = (*rgb, 1)
        p.inputs['Emission Strength'].default_value = glow
    if kind:
        links = m.node_tree.links
        c = m.node_tree.nodes.new('ShaderNodeTexImage')
        c.image = texture(kind, 'color', rgb, rough)
        links.new(c.outputs['Color'], p.inputs['Base Color'])
        r = m.node_tree.nodes.new('ShaderNodeTexImage')
        r.image = texture(kind, 'roughness', rgb, rough)
        links.new(r.outputs['Color'], p.inputs['Roughness'])
        n = m.node_tree.nodes.new('ShaderNodeTexImage')
        n.image = texture(kind, 'normal', rgb, rough)
        nm = m.node_tree.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = 0.34 if kind == 'glass' else 0.65
        links.new(n.outputs['Color'], nm.inputs['Color'])
        links.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m


def image_mat(name, path, rough=0.48):
    """Embed a credited sRGB storefront crop in one near-field facade plane."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = rough
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB'
    image.pack()
    texture_node = nodes.new('ShaderNodeTexImage')
    texture_node.image = image
    texture_node.interpolation = 'Linear'
    links.new(texture_node.outputs['Color'], bsdf.inputs['Base Color'])
    return m


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for material in list(bpy.data.materials): bpy.data.materials.remove(material)
    for image in list(bpy.data.images): bpy.data.images.remove(image)


def part(name, parent=None, direction=None, distance=0):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.empty_display_size = 0.08
    if parent: o.parent = parent
    if direction is not None:
        o['explodeDirection'] = list(direction)  # x, y-up, z-toward-camera in Three.js
        o['explodeDistance'] = float(distance)
    return o


def finish(obj, parent, name, xyz, material, bevel=0):
    obj.name = name
    obj.parent = parent
    obj.location = xyz
    obj.data.materials.append(material)
    if bevel:
        m = obj.modifiers.new('edge softness', 'BEVEL')
        m.width = bevel
        m.segments = 2
        obj.modifiers.new('weighted normals', 'WEIGHTED_NORMAL')
    # Architectural planes must stay planar; smoothing all cube faces created
    # large, warped-looking highlights on walls and glass.
    for face in obj.data.polygons: face.use_smooth = obj.name.startswith(('骑', '白马', '狮', '逐粒', '河边'))
    return obj


def box(parent, name, xyz, size, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, parent, name, xyz, material, bevel)


def frustum(parent, name, xyz, height, bottom_w, bottom_d, top_w, top_d, material, bevel=0):
    """A tapered architectural bay with real sloped side faces.

    The city references rely on tapered tower shafts and stepped crowns.  A
    stack of these frusta reads much closer to the photographed buildings than
    a single cube, while remaining a lightweight, independently movable GLB
    part for the scroll explosion.
    """
    mesh = bpy.data.meshes.new(name + '_mesh')
    z0, z1 = -height / 2, height / 2
    # The developer's landscape plan and photos show clipped tower corners.
    lower=clipped_rectangle(bottom_w,bottom_d,min(bottom_w,bottom_d)*0.095)
    upper=clipped_rectangle(top_w,top_d,min(top_w,top_d)*0.095)
    verts=[(x,y,z0) for x,y in lower]+[(x,y,z1) for x,y in upper]
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]
    faces.extend((i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, parent, name, xyz, material, bevel)


def ball(parent, name, xyz, scale, material, segments=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(6, segments // 2), radius=1)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj = finish(o, parent, name, xyz, material)
    for face in obj.data.polygons: face.use_smooth = True
    return obj


def cyl(parent, name, xyz, radius, depth, material, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = finish(bpy.context.object, parent, name, xyz, material, 0.004)
    for face in obj.data.polygons: face.use_smooth = len(face.vertices) == 4
    return obj


def line(parent, name, points, radius, material, resolution=2):
    curve = bpy.data.curves.new(name, 'CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    spline = curve.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points): point.co = (*xyz, 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    return obj


def panel(parent, name, verts, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], [tuple(range(len(verts)))])
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.data.materials.append(material)
    return o


def tiled_slope(parent, name, x, y, z, half, length, height, sign, material):
    """Batched curved overlapping clay tiles, running DOWN the roof slope.

    Tile rows in the earlier model ran along the ridge. Here each tile has a
    curved cross-section, an overlapping lip, and separate physical joints.
    Dimensions are visual estimates, not heritage survey measurements.
    """
    verts, faces = [], []
    columns = max(8, round(length / 0.09))
    courses = max(4, round(half / 0.17))
    dy = length / columns
    step = half / courses
    for col in range(columns):
        cy = y - length / 2 + (col + 0.5) * dy
        for row in range(courses):
            start = max(0, row * step - 0.014)
            end = min(half + 0.018, (row + 1) * step)
            base = len(verts)
            for t in (start, end):
                for j in range(7):
                    yy = cy + (j / 6 - 0.5) * dy * 1.02
                    zz = z + height * (1 - min(t, half) / half)
                    # Barrel crown and the slightly raised lower edge are geometry.
                    zz += 0.011 + 0.023 * math.sin(math.pi * j / 6)
                    zz += 0.008 if t == end else 0
                    verts.append((x + sign * t, yy, zz))
            for j in range(6):
                q = (base+j,base+j+1,base+j+8,base+j+7)
                faces.append(tuple(reversed(q)) if sign > 0 else q)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    for face in mesh.polygons: face.use_smooth = True
    return obj


def gable(parent, name, x, y, z, width, length, height, tiles, ridge):
    roof = part(name, parent)
    half = width / 2
    for sign in (-1, 1):
        roof_points = [(x, y - length / 2, z + height),
             (x + sign * half, y - length / 2, z),
             (x + sign * half, y + length / 2, z),
             (x, y + length / 2, z + height)]
        panel(roof, '倾斜瓦面', roof_points if sign > 0 else list(reversed(roof_points)), tiles)
        tiled_slope(roof, '逐行筒瓦_实体曲面错列瓦片', x, y, z, half, length, height, sign, ridge)
        # The eave exposes real rafter ends and hanging tile tips.
        for j in range(max(8, round(length / 0.13))):
            yy = y-length/2+(j+0.5)*length/max(8, round(length/0.13))
            box(roof,'檐口逐根椽木',(x+sign*(half-0.12),yy,z-0.035),(0.27,0.045,0.055),ridge,0.006)
    line(roof, '正脊', [(x, y - length / 2 - 0.04, z + height + 0.015),
                         (x, y + length / 2 + 0.04, z + height + 0.015)], 0.027, ridge)
    for yy in (y - length / 2, y + length / 2):
        line(roof, '檐口', [(x - half, yy, z), (x, yy, z + height), (x + half, yy, z)], 0.024, ridge)
    return roof


def lantern(parent, xyz, red, gold):
    x, y, z = xyz
    line(parent, '挂灯细绳', [(x, y, z + 0.19), (x, y, z + 0.39)], 0.008, gold, 1)
    ball(parent, '绢面红灯笼', xyz, (0.105, 0.105, 0.15), red, 12)
    cyl(parent, '灯笼上箍', (x, y, z + 0.15), 0.046, 0.025, gold, 12)
    cyl(parent, '灯笼下箍', (x, y, z - 0.15), 0.046, 0.025, gold, 12)
    line(parent, '灯穗', [(x, y, z - 0.16), (x, y, z - 0.30)], 0.01, gold, 1)


def storefront(parent, x, y, side, mats, variant):
    wall, timber, warm, dark, tile, tile_hi, red, gold = mats
    sign = 1 if side == 'right' else -1
    group = part(f'{side}店面_{variant}', parent)
    box(group, '粉墙店身', (x, y, 0.93), (1.36, 1.72, 1.84), wall, 0.015)
    front = x - sign * 0.70
    box(group, '临街深木檐廊', (front, y, 1.17), (0.09, 1.72, 1.26), dark, 0.01)
    for yy in (y - 0.69, y - 0.23, y + 0.23, y + 0.69):
        box(group, '立柱及门樘', (front - sign * 0.065, yy, 0.68), (0.065, 0.052, 1.26), timber, 0.006)
    for zz in (0.37, 0.97, 1.43):
        box(group, '横向窗棂', (front - sign * 0.09, y, zz), (0.05, 1.44, 0.037), timber, 0.003)
    for yy in (y - 0.48, y - 0.12, y + 0.25, y + 0.56):
        box(group, '透光窗格', (front - sign * 0.102, yy, 0.71), (0.014, 0.22, 0.41), warm)
    box(group, '二层木窗带', (front - sign * 0.075, y, 1.61), (0.05, 1.48, 0.37), dark)
    for yy in (y - 0.55, y - 0.18, y + 0.18, y + 0.55):
        box(group, '二层窗格竖梃', (front - sign * 0.107, yy, 1.61), (0.025, 0.035, 0.35), timber)
    back = x + sign * 0.71
    box(group, '外侧连续木窗', (back, y, 1.56), (0.045, 1.49, 0.49), dark)
    for yy in (y - 0.60, y - 0.30, y, y + 0.30, y + 0.60):
        box(group, '外侧细木立梃', (back + sign * 0.04, yy, 1.56), (0.025, 0.031, 0.50), timber)
    for zz in (1.38, 1.74):
        box(group, '外侧细木横档', (back + sign * 0.04, y, zz), (0.026, 1.50, 0.032), timber)
    box(group, '外侧檐下木门', (back + sign * 0.018, y, 0.48), (0.04, 0.70, 0.9), dark)
    for yy in (y - 0.25, y, y + 0.25):
        box(group, '外侧木门棂', (back + sign * 0.052, yy, 0.49), (0.022, 0.027, 0.83), timber)
    for yy in (y - 0.67, y + 0.67):
        box(group, '建筑端面檐下框', (x, yy, 1.01), (1.22, 0.027, 1.45), timber)
    box(group, '檐下灯槽', (front - sign * 0.10, y, 1.32), (0.045, 1.42, 0.025), gold)
    gable(group, '分件_黛瓦坡顶', x, y, 1.87, 1.73, 1.94, 0.40, tile, tile_hi)
    return group


def build_yishang():
    clear()
    stone = mat('旧石板细纹', (0.42, 0.43, 0.40), 0.87, kind='stone')
    wall = mat('灰白墙', (0.61, 0.57, 0.49), 0.88, kind='stone')
    wood = mat('深棕木构', (0.25, 0.16, 0.11), 0.7, kind='wood')
    dark = mat('檐下阴影', (0.10, 0.13, 0.13), 0.8, kind='wood')
    warm = mat('店内暖光', (0.88, 0.68, 0.37), 0.31, glow=0.55)
    tile = mat('青灰旧瓦', (0.18, 0.23, 0.23), 0.88, kind='tile')
    tile_hi = mat('瓦垄与正脊', (0.24, 0.29, 0.27), 0.79, kind='tile')
    red = mat('红绢灯面', (0.68, 0.13, 0.08), 0.47, kind='cloth', glow=0.2)
    gold = mat('灯架铜环', (0.74, 0.49, 0.20), 0.32, 0.55)
    root = part('衣裳街_解释性微缩')
    road = part('石板街道', root, (0, -1, 0), 0.95)
    box(road, '石板街基', (0, 0, -0.18), (6.25, 7.9, 0.28), stone, 0.07)
    for row in range(23):
        yy = -3.7 + row * 0.33
        for col in range(13):
            xx = -2.88 + col * 0.47 + (0.19 if row % 2 else 0)
            if xx > 2.95: continue
            z = -0.025 + 0.008 * random.random()
            box(road, '错缝青石铺地', (xx, yy, z), (0.44, 0.30, 0.04), stone, 0.004)
    for x in (-1.20, 1.20):
        box(road, '街边排水沟', (x, 0, -0.001), (0.055, 7.6, 0.018), dark)
    left = part('左侧店面', root, (-1, 0, 0), 1.25)
    right = part('右侧店面', root, (1, 0, 0), 1.25)
    roofs = part('屋檐檐顶', root, (0, 1, 0), 0.9)
    lights = part('悬挂灯笼', root, (0, 1, 0), 1.25)
    mats = (wall, wood, warm, dark, tile, tile_hi, red, gold)
    for side, parent, x in [('left', left, -2.15), ('right', right, 2.15)]:
        for i, y in enumerate((-2.55, -0.55, 1.45)):
            building = storefront(parent, x, y, side, mats, i)
            # The roof Empty is a separate explanatory layer in the browser.
            for child in list(building.children):
                if child.name.startswith('分件_黛瓦坡顶'):
                    world = child.matrix_world.copy()
                    child.parent = roofs
                    child.matrix_world = world
            inner = x + (0.88 if side == 'left' else -0.88)
            lantern(lights, (inner, y - 0.52, 1.40), red, gold)
            lantern(lights, (inner, y + 0.52, 1.40), red, gold)
    export('yishang', (8.5, -10.5, 7.2), 10.6)


def tower_grille(parent, x, y, bottom, width, depth, height, floor_count, metal, glass, shadow):
    box(parent, '蓝灰镜面幕墙体', (x, y, bottom + height / 2), (width, depth, height), glass, 0.025)
    for i in range(1, floor_count):
        z = bottom + height * i / floor_count
        box(parent, '逐层金属横梃', (x, y - depth / 2 - 0.009, z), (width + 0.035, 0.02, 0.013), metal)
        box(parent, '背面水平檐线', (x, y + depth / 2 + 0.009, z), (width + 0.035, 0.02, 0.013), shadow)
        box(parent, '侧面水平层线', (x + width / 2 + 0.012, y, z), (0.018, depth + 0.02, 0.013), metal)
    for i in range(13):
        xx = x - width / 2 + i * width / 12
        box(parent, '连续玻璃竖梃', (xx, y - depth / 2 - 0.015, bottom + height / 2), (0.018, 0.025, height), metal)
    for i in range(8):
        yy = y - depth / 2 + i * depth / 7
        box(parent, '转角幕墙竖梃', (x + width / 2 + 0.009, yy, bottom + height / 2), (0.021, 0.018, height), metal)


def build_dongwu():
    clear()
    stone = mat('道路浅石', (0.43, 0.45, 0.44), 0.82, kind='stone')
    podium = mat('商业裙楼砂岩', (0.56, 0.43, 0.34), 0.79, kind='stone')
    glass = mat('反光蓝玻璃', (0.26, 0.57, 0.73), 0.16, 0.3, kind='glass')
    glass_deep = mat('退台深蓝玻璃', (0.14, 0.36, 0.51), 0.18, 0.38, kind='glass')
    metal = mat('银色幕墙框架', (0.54, 0.73, 0.78), 0.24, 0.77)
    shadow = mat('楼层阴影带', (0.14, 0.23, 0.27), 0.46, 0.24)
    green = mat('街角绿植', (0.17, 0.33, 0.19), 0.92, kind='leaf')
    root = part('东吴双塔_解释性微缩')
    ground = part('街区地面', root, (0, -1, 0), 0.65)
    box(ground, '城市街区切片', (0, 0, -0.13), (7.0, 4.55, 0.24), stone, 0.07)
    for i in range(9):
        xx = -3.0 + i * 0.75
        ball(ground, '树冠', (xx, -2.08, 0.35), (0.18, 0.16, 0.25), green)
        cyl(ground, '行道树干', (xx, -2.08, 0.11), 0.026, 0.25, podium, 8)
    base = part('商业基座', root, (0, -0.6, 0), 0.85)
    box(base, '层层退进的砂岩裙楼', (0, 0.18, 0.66), (5.75, 3.38, 1.22), podium, 0.055)
    box(base, '裙楼蓝玻璃带', (0, -1.535, 0.94), (5.77, 0.05, 0.19), glass_deep)
    box(base, '裙楼底层门窗', (0, -1.53, 0.37), (5.4, 0.04, 0.34), glass_deep)
    for i in range(22):
        x = -2.62 + i * 0.25
        box(base, '裙楼细密立柱', (x, -1.57, 0.41), (0.015, 0.022, 0.46), metal)
    for z in (0.15, 0.69, 1.24):
        box(base, '商业基座挑檐', (0, -1.57, z), (5.84, 0.12, 0.043), shadow)
    low = part('西侧矮塔', root, (-1, 0, 0), 1.35)
    tall = part('东侧高塔', root, (1, 0, 0), 1.65)
    crown = part('双塔冠部与天线', root, (0, 1, 0), 0.9)
    tower_grille(low, -1.25, 0.35, 1.27, 1.55, 1.55, 3.55, 26, metal, glass_deep, shadow)
    tower_grille(tall, 1.10, 0.1, 1.27, 1.83, 1.83, 5.24, 39, metal, glass, shadow)
    box(low, '矮塔斜切肩部', (-1.25, 0.36, 4.97), (1.28, 1.46, 0.22), glass, 0.012)
    box(tall, '高塔中段退台', (1.1, 0.1, 4.49), (1.98, 1.94, 0.12), shadow, 0.01)
    box(crown, '矮塔冠部', (-1.25, 0.35, 5.11), (1.42, 1.45, 0.17), glass_deep)
    box(crown, '高塔冠部', (1.1, 0.1, 6.59), (1.63, 1.65, 0.16), glass_deep)
    cyl(crown, '双塔细天线_高', (1.1, 0.1, 6.94), 0.019, 0.55, metal, 10)
    cyl(crown, '双塔细天线_低', (-1.25, 0.35, 5.34), 0.014, 0.32, metal, 10)
    export('dongwu', (8.2, -13, 7.5), 10.0)


def arch_segment(parent, name, r0, r1, a0, a1, depth, material):
    verts = []
    for yy in (-depth / 2, depth / 2):
        for radius, angle in ((r0, a0), (r1, a0), (r1, a1), (r0, a1)):
            verts.append((radius * math.cos(angle), yy, 0.77 + radius * math.sin(angle)))
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    o = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(o)
    o.parent = parent
    o.data.materials.append(material)
    return o


def mounted_horse(parent, name, x, y, z, facing, horse_white, shadows, bridle, rider_coat, rider_skin, gold):
    """Photo-led relief of the entrance's two distinct rearing horse groups."""
    horse = part(name,parent,(facing,0,1),0.62)
    horse['evidence'] = 'front visible in 2023 Wikimedia photograph; back inferred'
    # A rear-heavy, rearing horse, made of connected sculptural masses rather
    # than the symbolic flat silhouette used in the rejected first version.
    chest=ball(horse,'白马胸腹',(x,y,z+0.86),(0.33,0.24,0.46),horse_white,32)
    chest.rotation_euler.y=facing*0.40
    ball(horse,'白马臀部',(x-facing*0.37,y,z+0.55),(0.27,0.23,0.29),horse_white,24)
    line(horse,'后腿关节之一',[(x-facing*0.52,y,z+0.51),(x-facing*0.64,y,z+0.22),
                             (x-facing*0.55,y,z+0.07)],0.085,horse_white,3)
    line(horse,'后腿关节之二',[(x-facing*0.29,y,z+0.49),(x-facing*0.32,y,z+0.19),
                             (x-facing*0.16,y,z+0.08)],0.082,horse_white,3)
    line(horse,'扬起前腿之一',[(x+facing*0.23,y,z+0.76),(x+facing*0.48,y,z+0.62),
                            (x+facing*0.61,y,z+0.80)],0.075,horse_white,3)
    line(horse,'扬起前腿之二',[(x+facing*0.36,y,z+0.66),(x+facing*0.63,y,z+0.52),
                            (x+facing*0.75,y,z+0.67)],0.071,horse_white,3)
    line(horse,'拱起马颈',[(x+facing*0.25,y,z+0.94),(x+facing*0.39,y,z+1.17),
                         (x+facing*0.53,y,z+1.30)],0.13,horse_white,3)
    ball(horse,'马头颊部',(x+facing*0.58,y,z+1.36),(0.20,0.15,0.19),horse_white,24)
    ball(horse,'鼻口吻部',(x+facing*0.74,y,z+1.27),(0.15,0.13,0.09),horse_white,20)
    for dx in (-0.08,0.10):
        line(horse,'双耳',[(x+facing*0.55+dx,y,z+1.50),(x+facing*0.55+dx,y,z+1.67)],
             0.026,horse_white,2)
    for yy in (y-0.145,y+0.145):
        ball(horse,'玻璃眼珠',(x+facing*0.63,yy,z+1.40),(0.025,0.008,0.020),shadows,12)
    line(horse,'雕塑尾鬃',[(x-facing*0.60,y,z+0.72),(x-facing*0.85,y,z+0.55),
                         (x-facing*0.96,y,z+0.30)],0.07,horse_white,3)
    for i in range(9):
        xx=x+facing*(0.39+i*0.021)
        line(horse,'逐缕雕刻马鬃',[(xx,y,z+1.32-i*0.018),(xx-facing*0.06,y,z+1.20-i*0.018)],
             0.014,shadows,1)
    line(horse,'马具金色辔绳',[(x+facing*0.65,y-0.17,z+1.42),
                             (x+facing*0.46,y-0.20,z+1.13),(x+facing*0.08,y-0.24,z+0.96)],
         0.010,bridle,1)
    ball(horse,'装饰马鞍',(x-facing*0.07,y,z+1.05),(0.28,0.25,0.12),bridle,20)
    rider = part('骑士人物_胸甲与礼帽',horse)
    ball(rider,'骑士靴与腿',(x-facing*0.10,y-0.22,z+0.84),(0.20,0.075,0.25),rider_coat,18)
    ball(rider,'骑士上身',(x-facing*0.14,y,z+1.38),(0.20,0.16,0.33),rider_coat,20)
    ball(rider,'骑士头部',(x-facing*0.16,y,z+1.81),(0.12,0.11,0.14),rider_skin,20)
    cyl(rider,'高礼帽帽身',(x-facing*0.16,y,z+2.02),0.125,0.23,rider_coat,20)
    cyl(rider,'高礼帽帽檐',(x-facing*0.16,y,z+1.91),0.18,0.025,shadows,20)
    line(rider,'骑士缰绳手臂',[(x-facing*0.02,y-0.02,z+1.55),
             (x+facing*0.15,y-0.13,z+1.36),(x+facing*0.45,y-0.15,z+1.31)],0.060,rider_coat,2)
    line(rider,'骑士举起的另一只手',[(x-facing*0.18,y+0.04,z+1.54),
             (x-facing*0.40,y+0.05,z+1.80),(x-facing*0.50,y+0.05,z+1.93)],0.055,rider_coat,2)
    ball(rider,'骑士手套',(x-facing*0.50,y+0.05,z+1.93),(0.08,0.06,0.07),rider_skin,12)
    box(horse,'骑马雕塑台座',(x,y,z+0.02),(1.82,0.88,0.11),gold,0.055)
    return horse


def build_longemont():
    clear()
    paving = mat('环形广场彩色铺地', (0.29, 0.39, 0.49), 0.69, kind='stone')
    red = mat('马戏红色涂装', (0.75, 0.15, 0.13), 0.38, kind='paint')
    blue = mat('马戏深蓝涂装', (0.10, 0.32, 0.58), 0.37, kind='paint')
    purple = mat('穹棚紫红色饰面', (0.35, 0.14, 0.27), 0.54, kind='cloth')
    gold = mat('金色拱肋饰边', (0.96, 0.58, 0.17), 0.3, 0.54)
    warm = mat('暖光灯珠', (1.0, 0.75, 0.35), 0.2, glow=1.1)
    glass = mat('入口深色玻璃', (0.07, 0.14, 0.22), 0.15, 0.25, kind='glass')
    masonry = mat('门廊装饰结构', (0.50, 0.18, 0.23), 0.58, kind='stone')
    midnight = mat('拱内深蓝背景', (0.035, 0.10, 0.16), 0.56, kind='glass')
    root = part('龙之梦国际马戏城_照片参照外观重现')
    plaza = part('环形广场', root, (0, -1, 0), 0.8)
    # The old 7.8-deep front plaza ended at y=3.2 although the hall ends at
    # y=9.6. One continuous ground now supports the entire venue footprint.
    box(plaza, '完整场馆地坪_彩绘前场', (0, 2.7, -0.12), (16.4, 15.8, 0.23), paving, 0.04)
    for radius in (1.3, 2.2, 3.2):
        pts = [(radius * math.cos(i * math.pi / 36), -1.35 + radius * math.sin(i * math.pi / 36), 0.013) for i in range(73)]
        line(plaza, '广场弧形嵌条', pts, 0.021, gold, 1)
    hall = part('宽椭圆场馆外墙与窗带', root, (0, 1, 0), 0.65)
    roof_gold=part('紫金曲面屋盖_紫黄扁椭圆穹顶穹棚',root,(0,1,0),1.8)
    yellow=mat('穹顶黄色扇区',(0.94,0.70,0.085),0.45,kind='paint')
    pale=mat('圆弧外墙浅黄色',(0.73,0.61,0.37),0.79,kind='stone')
    # High-angle project photograph (21audio, 2022-08-15): the roof is a
    # broad, flattened ellipsoid, almost twice the width of the entrance.
    # These are image-derived proportions, not surveyed engineering sizes.
    rx,ry,roof_h,cy,base_z=7.4,5.0,2.6,4.6,2.3
    hall['evidence']='2022 high-angle exterior; 2023 entrance photograph'
    for sector in range(32):
        a0=sector*math.pi*2/32; a1=(sector+1)*math.pi*2/32
        material=purple if abs(math.cos((a0+a1)/2))<0.70 else yellow
        verts,faces=ellipsoid_sector(rx,ry,roof_h,a0,a1,6,24)
        mesh=bpy.data.meshes.new('穹顶曲面分瓣')
        mesh.from_pydata([(x,y+cy,z+base_z) for x,y,z in verts],[],faces); mesh.update()
        obj=bpy.data.objects.new('穹顶分色曲面_%02d'%sector,mesh)
        bpy.context.collection.objects.link(obj); obj.parent=roof_gold; obj.data.materials.append(material)
        for polygon in mesh.polygons: polygon.use_smooth=True
        # Narrow raised seams follow the real ribbed roof surface.
        for sub in range(6):
            a=a0+(a1-a0)*sub/6
            pts=[((rx+0.005)*math.cos(t*math.pi/60)*math.cos(a),
                  cy+(ry+0.005)*math.cos(t*math.pi/60)*math.sin(a),
                  base_z+(roof_h+0.005)*math.sin(t*math.pi/60)) for t in range(30)]
            line(roof_gold,'穹顶细密竖向屋面接缝',pts,0.008,material,1)
        # Independently visible outer wall, window panels and cornices.
        count=6
        for sub in range(count):
            b0=a0+(a1-a0)*sub/count; b1=a0+(a1-a0)*(sub+1)/count
            pts=[(rx*math.cos(b0),cy+ry*math.sin(b0),0.10),
                 (rx*math.cos(b1),cy+ry*math.sin(b1),0.10),
                 (rx*math.cos(b1),cy+ry*math.sin(b1),base_z),
                 (rx*math.cos(b0),cy+ry*math.sin(b0),base_z)]
            panel(hall,'环形场馆浅色外墙',pts,pale)
            for zz in (0.56,1.28,1.96):
                win=[((rx+0.018)*math.cos(b),cy+(ry+0.018)*math.sin(b),z)
                     for b,z in [(b0+0.004,zz),(b1-0.004,zz),(b1-0.004,zz+0.28),(b0+0.004,zz+0.28)]]
                panel(hall,'环形外墙三层窗带',win,glass)
            line(hall,'场馆外墙逐段竖框',[(rx*math.cos(b0),cy+ry*math.sin(b0),0.18),
                 (rx*math.cos(b0),cy+ry*math.sin(b0),base_z)],0.015,pale,1)
    for z in (0.18,0.96,1.69,2.25):
        pts=[((rx+0.05)*math.cos(i*math.pi/96),cy+(ry+0.05)*math.sin(i*math.pi/96),z) for i in range(193)]
        line(hall,'场馆环形挑檐与窗间带',pts,0.045,pale,1)
    # Small crown and the visible star emblems, mapped onto the dome rather
    # than floating on a vertical half-circle.
    cyl(roof_gold,'穹顶顶部小冠部',(0,cy,base_z+roof_h+0.055),0.64,0.11,gold,48)
    for angle in (-1.48,-2.4,-0.58,1.3):
        lat=0.61
        pos=Vector((rx*math.cos(lat)*math.cos(angle),cy+ry*math.cos(lat)*math.sin(angle),base_z+roof_h*math.sin(lat)))
        normal=Vector((pos.x/(rx*rx),(pos.y-cy)/(ry*ry),(pos.z-base_z)/(roof_h*roof_h))).normalized()
        tangent=Vector((-math.sin(angle),math.cos(angle),0)).normalized()
        up=normal.cross(tangent).normalized()
        contour=[pos+normal*0.022]
        for j in range(10):
            a=math.pi/2+j*math.pi/5; radius=0.19 if j%2==0 else 0.075
            contour.append(pos+normal*0.022+tangent*(radius*math.cos(a))+up*(radius*math.sin(a)))
        mesh=bpy.data.meshes.new('穹顶五角星浮饰')
        mesh.from_pydata([p[:] for p in contour],[],[(0,j+1,(j+1)%10+1) for j in range(10)]); mesh.update()
        obj=bpy.data.objects.new('穹顶星纹',mesh); bpy.context.collection.objects.link(obj)
        obj.parent=roof_gold; obj.data.materials.append(gold)
    # Simplified visible gold dragon outlines are fitted onto the roof's
    # front surface. They are decorative observations, not a claimed exact
    # restoration of the painted artwork or a hidden structural system.
    motif=part('分件_屋盖可见龙纹',roof_gold)
    def roof_point(xx,zz):
        q=max(0.004,1-(xx/rx)**2-((zz-base_z)/roof_h)**2)
        return (xx,cy-ry*math.sqrt(q)-0.012,zz+0.006)
    for rr in (0.64,0.78,0.92):
        pts=[roof_point(-4.05+rr*math.cos(a),3.42+rr*0.58*math.sin(a))
             for a in [i*math.pi*2/80 for i in range(81)]]
        line(motif,'左侧盘龙金色轮廓',pts,0.021,gold,2)
    dragon_paths=[
        [(-4.48,3.70),(-4.12,3.86),(-3.85,3.82),(-3.76,3.63),(-4.05,3.51),(-4.23,3.41)],
        [(-4.13,3.86),(-4.35,4.14),(-4.15,4.19),(-3.91,3.98)],
        [(-3.86,3.83),(-3.58,4.18),(-3.45,4.09),(-3.60,3.86)],
        [(-4.74,3.45),(-5.12,3.35),(-5.23,3.12),(-4.94,3.01)],
        [(4.94,3.05),(4.60,3.16),(4.47,3.44),(4.16,3.57),(3.84,3.54),(3.73,3.32),(4.09,3.22)],
        [(4.12,3.55),(3.98,3.86),(3.40,4.11),(3.07,4.34),(2.88,4.56)],
        [(3.75,3.67),(3.40,3.79),(3.16,3.99),(2.96,4.17),(2.51,4.32)],
        [(4.45,3.45),(4.82,3.73),(5.00,3.75)],
        [(4.91,3.07),(5.44,2.88),(5.74,2.59),(5.55,2.42)],
    ]
    for path in dragon_paths: line(motif,'屋盖金色龙纹枝线',[roof_point(x,z) for x,z in path],0.024,gold,2)
    arc_face = [(0, -0.36, 0.77)] + [(3.12 * math.cos(i * math.pi / 40), -0.36,
                0.77 + 3.12 * math.sin(i * math.pi / 40)) for i in range(41)]
    panel(hall, '深色拱内玻璃立面', arc_face, midnight)
    for i in range(1, 15):
        a = i * math.pi / 15
        line(hall, '拱内放射饰条', [(0, -0.38, 0.77),
             (2.97 * math.cos(a), -0.38, 0.77 + 2.97 * math.sin(a))], 0.008, gold, 1)
    for x in (-2.0, 2.0):
        box(hall, '两翼菱形饰面', (x, -0.39, 1.12), (0.5, 0.025, 0.52), masonry, 0.015)
        ball(hall, '星形浮饰', (x, -0.44, 1.12), (0.11, 0.025, 0.11), gold, 10)
    doorway = part('中央门廊', root, (0, 0, 1), 0.83)
    box(doorway, '入口玻璃幕门', (0, -0.78, 0.96), (2.45, 0.07, 1.62), glass)
    for xx in (-1.24, -0.62, 0, 0.62, 1.24):
        box(doorway, '玻璃门金色竖樘', (xx, -0.83, 0.98), (0.045, 0.045, 1.64), gold)
    for z in (0.18, 1.78):
        box(doorway, '门廊横框', (0, -0.84, z), (2.53, 0.085, 0.065), gold)
    box(doorway, '拱内招牌底板', (0, -0.89, 2.12), (2.7, 0.11, 0.35), masonry, 0.025)
    for i in range(17):
        xx = -1.25 + i * 0.156
        ball(doorway, '入口灯泡', (xx, -0.97, 2.09), (0.025, 0.025, 0.025), warm, 8)
    arch = part('红蓝分段拱环', root, (0, 1, 0), 1.0)
    arch_segment(arch, '内圈金色拱肋', 3.22, 3.31, 0, math.pi, 0.39, gold)
    for i in range(48):
        a0, a1 = i * math.pi / 48, (i + 1) * math.pi / 48
        arch_segment(arch, '红蓝交替拱环', 3.31, 3.84, a0, a1, 0.46, red if i % 2 else blue)
    arch_segment(arch, '外圈金边', 3.84, 3.92, 0, math.pi, 0.49, gold)
    bulbs = part('拱环逐粒灯带', root, (0, 0, 1), 1.2)
    for radius in (3.24, 3.87):
        for i in range(97):
            a = i * math.pi / 96
            ball(bulbs, '逐粒灯珠', (radius * math.cos(a), -0.28,
                 0.77 + radius * math.sin(a)), (0.021, 0.021, 0.021), warm, 8)
    for xx in (-3.82, 3.82):
        box(arch, '拱脚基座', (xx, 0, 0.43), (0.42, 0.65, 0.85), red, 0.025)
    # The photograph shows several nested painted bands, not one abstract arch.
    arch_segment(arch,'拱内红色同心带',2.76,2.86,0,math.pi,0.34,red)
    arch_segment(arch,'拱内蓝色同心带',2.88,3.01,0,math.pi,0.35,blue)
    arch_segment(arch,'拱内金色分界带',3.03,3.075,0,math.pi,0.35,gold)
    for i in range(36):
        angle = i*math.pi/36
        arch_segment(arch,'外沿黄色连续三角纹',3.87,3.97,angle,angle+math.pi/80,0.51,gold)
    # The curving bi-lingual sign is modelled as real raised glyph geometry.
    font_path='C:\\Windows\\Fonts\\simhei.ttf'
    font=bpy.data.fonts.load(font_path) if os.path.exists(font_path) else None
    cn=part('分件_中文弧形招牌',root,(0,1,0),0.72)
    en=part('分件_英文弧形招牌',root,(0,1,0),0.73)
    badge = arch_segment(cn,'双语招牌紫色弧形飘带',2.60,3.00,math.pi*0.31,math.pi*0.69,0.075,purple)
    badge.location.y=-0.61
    for angle in (math.pi*0.31, math.pi*0.69):
        sx=2.80*math.cos(angle); sz=0.77+2.80*math.sin(angle)
        sign=1 if sx>0 else -1
        panel(cn,'招牌两端燕尾飘带',[(sx,-0.66,sz+0.18),(sx+sign*0.44,-0.66,sz+0.11),
            (sx+sign*0.23,-0.66,sz-0.10),(sx+sign*0.50,-0.66,sz-0.27),
            (sx,-0.66,sz-0.25)],purple)
    cn_text='龙之梦国际马戏城'
    for i,glyph in enumerate(cn_text):
        a=math.pi*(0.66-0.32*i/(len(cn_text)-1))
        letter=text_object(cn,'中文弧形招牌_'+glyph,glyph,
                    (2.83*math.cos(a),-0.67,0.77+2.83*math.sin(a)),0.22,gold,'y',font)
        letter.rotation_mode='QUATERNION'
        letter.rotation_quaternion=Quaternion((0,1,0),math.pi/2-a)@Quaternion((1,0,0),math.pi/2)
    en_text='INTERNATIONAL CIRCUS'
    for i,glyph in enumerate(en_text):
        a=math.pi*(0.66-0.32*i/(len(en_text)-1))
        letter=text_object(en,'英文弧形招牌_'+str(i),glyph,
                    (2.54*math.cos(a),-0.675,0.77+2.54*math.sin(a)),0.095,gold,'y')
        letter.rotation_mode='QUATERNION'
        letter.rotation_quaternion=Quaternion((0,1,0),math.pi/2-a)@Quaternion((1,0,0),math.pi/2)
    # In the reference the dotted light trails run radially down each blue
    # stripe, not just around the inner/outer rim.
    lamp_colors=[mat('彩灯红',(1,0.08,0.035),0.25,glow=2.0),
                 mat('彩灯青',(0.02,0.8,0.66),0.25,glow=2.0),
                 mat('彩灯蓝',(0.1,0.25,1),0.25,glow=2.0),warm]
    for i in range(1,48,2):
        angle=(i+0.5)*math.pi/48
        for j in range(9):
            radius=3.34+j*0.055
            ball(bulbs,'放射彩灯逐粒灯珠',(radius*math.cos(angle),-0.29,0.77+radius*math.sin(angle)),
                (0.014,0.014,0.014),lamp_colors[j%4],12)
    # The actual entrance has a circular lion emblem above the glass doors.
    crest=part('分件_狮徽与门廊装饰',root,(0,0,1),0.8)
    ball(crest,'狮徽蓝金圆盘',(0,-0.98,1.36),(0.39,0.045,0.39),blue,32)
    for i in range(14):
        a=i*math.pi*2/14
        ball(crest,'狮徽鬃毛浮雕',(0.28*math.cos(a),-1.025,1.36+0.28*math.sin(a)),
             (0.105,0.037,0.115),gold,10)
    ball(crest,'狮徽脸部浮雕',(0,-1.051,1.36),(0.22,0.04,0.21),gold,18)
    for xx in (-0.09,0.09): ball(crest,'狮眼',(xx,-1.098,1.41),(0.026,0.008,0.024),midnight,10)
    for xx in (-2.50,2.50):
        box(crest,'两翼星形墙面',(xx,-0.45,1.37),(0.55,0.06,0.60),blue,0.02)
        ball(crest,'星徽',(xx,-0.49,1.37),(0.14,0.02,0.14),gold,10)
    # The two visible sculpture groups have opposite poses and stay separate.
    white_horse=mat('骑白马雕塑釉白',(0.78,0.80,0.77),0.40,kind='stone')
    shade=mat('马鬃与眼部深影',(0.11,0.12,0.13),0.64)
    coat=mat('马戏骑士深蓝礼服',(0.11,0.17,0.27),0.68,kind='cloth')
    skin=mat('骑士面部彩饰',(0.72,0.50,0.36),0.58)
    mounted_horse(root,'左骑马雕塑',-2.62,-0.57,0.07,1,white_horse,shade,gold,coat,skin,gold)
    mounted_horse(root,'右骑马雕塑',2.62,-0.57,0.07,-1,white_horse,shade,gold,coat,skin,gold)
    # All paving rings sit on the plaza rather than floating off its edge.
    export('longemont', (2.0, -22.0, 7.3), 18.0)


def house(parent, roof_parent, x, y, side, mats, index):
    wall, timber, glass, tile, ridge, stone, red, gold = mats
    sign = 1 if side == 'right' else -1
    group = part(f'{side}临水屋身_{index}', parent)
    box(group, '粉墙黛瓦民居墙身', (x, y, 1.11), (1.7, 2.0, 2.03), wall, 0.015)
    front = x - sign * 0.86
    box(group, '临水木格窗暗底', (front, y, 1.41), (0.045, 1.70, 0.8), glass)
    for yy in (y - 0.7, y - 0.35, y, y + 0.35, y + 0.7):
        box(group, '木格窗立梃', (front - sign * 0.04, yy, 1.42), (0.03, 0.027, 0.82), timber)
    for z in (1.1, 1.48, 1.82):
        box(group, '木格窗横档', (front - sign * 0.04, y, z), (0.03, 1.73, 0.034), timber)
    for yy in (y - 0.82, y + 0.82):
        box(group, '廊柱', (front - sign * 0.21, yy, 0.65), (0.08, 0.08, 1.25), timber, 0.005)
    box(group, '廊下横梁', (front - sign * 0.21, y, 1.25), (0.08, 1.80, 0.09), timber)
    for yy in (y - 0.58, y - 0.14, y + 0.30, y + 0.74):
        box(group, '临河矮栏柱', (front - sign * 0.40, yy, 0.34), (0.065, 0.065, 0.61), timber)
    box(group, '临河栏杆', (front - sign * 0.40, y, 0.61), (0.07, 1.86, 0.055), timber)
    back = x + sign * 0.86
    box(group, '背街木窗暗底', (back, y, 1.48), (0.044, 1.52, 0.61), glass)
    for yy in (y - 0.61, y - 0.30, y, y + 0.30, y + 0.61):
        box(group, '背街木格竖梃', (back + sign * 0.044, yy, 1.48), (0.024, 0.027, 0.64), timber)
    for zz in (1.24, 1.70):
        box(group, '背街木格横档', (back + sign * 0.044, y, zz), (0.023, 1.54, 0.03), timber)
    for yy in (y - 0.76, y + 0.76):
        box(group, '背街短檐支柱', (back + sign * 0.18, yy, 0.53), (0.063, 0.063, 1.05), timber)
    box(group, '背街廊檐', (back + sign * 0.18, y, 1.08), (0.09, 1.65, 0.06), timber)
    gable(roof_parent, '青瓦民居屋顶', x, y, 2.14, 2.09, 2.20, 0.46, tile, ridge)
    if index % 2 == 0: lantern(group, (front - sign * 0.25, y - 0.55, 1.02), red, gold)
    return group


def build_nanxun():
    clear()
    stone = mat('河岸旧石', (0.48, 0.46, 0.40), 0.89, kind='stone')
    wall = mat('斑驳白墙', (0.69, 0.66, 0.58), 0.91, kind='stone')
    timber = mat('临河旧木', (0.19, 0.14, 0.11), 0.77, kind='wood')
    glass = mat('暗窗', (0.10, 0.15, 0.15), 0.28, 0.1, kind='glass')
    tile = mat('南浔青瓦', (0.20, 0.23, 0.22), 0.86, kind='tile')
    ridge = mat('屋脊与筒瓦', (0.27, 0.29, 0.26), 0.75, kind='tile')
    water = mat('暮色河面', (0.24, 0.32, 0.29), 0.16, 0.15, kind='water')
    red = mat('檐下朱灯', (0.58, 0.12, 0.09), 0.5, glow=0.17)
    gold = mat('黄铜灯架', (0.69, 0.47, 0.20), 0.42, 0.45)
    root = part('南浔河巷_解释性微缩')
    canal = part('河道水面', root, (0, -1, 0), 0.75)
    box(canal, '深色河床', (0, 0, -0.24), (3.4, 7.6, 0.25), stone, 0.04)
    vertices = []
    faces = []
    nx, ny = 22, 48
    for iy in range(ny + 1):
        y = -3.75 + 7.5 * iy / ny
        for ix in range(nx + 1):
            x = -1.65 + 3.3 * ix / nx
            z = -0.035 + 0.012 * math.sin(17 * y + 4 * x) + 0.006 * math.sin(33 * y - 7 * x)
            vertices.append((x, y, z))
    for iy in range(ny):
        for ix in range(nx):
            a = iy * (nx + 1) + ix
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new('独立起伏水面')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('有水纹的河面', mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = canal
    obj.data.materials.append(water)
    for face in obj.data.polygons: face.use_smooth = True
    ripple = mat('细微倒影水纹', (0.53, 0.57, 0.49), 0.28, 0.05)
    for i in range(32):
        yy = -3.45 + i * 0.21
        cx = 0.9 * math.sin(i * 1.73)
        width = 0.16 + (i % 5) * 0.065
        line(canal, '水面离散反光', [(cx - width, yy, -0.008),
             (cx, yy + 0.016, -0.004), (cx + width, yy - 0.008, -0.005)],
             0.003, ripple, 1)
    bank = part('两岸岸基', root, (0, -1, 0), 1.15)
    left = part('左岸屋身', root, (-1, 0, 0), 1.08)
    right = part('右岸屋身', root, (1, 0, 0), 1.08)
    roofs = part('两岸黛瓦屋顶', root, (0, 1, 0), 1.0)
    mats = (wall, timber, glass, tile, ridge, stone, red, gold)
    for side, parent, x in [('left', left, -2.75), ('right', right, 2.75)]:
        sign = 1 if side == 'right' else -1
        box(bank, '临水石基', (x, 0, 0.09), (2.05, 7.53, 0.25), stone, 0.018)
        box(bank, '沿河石驳岸', (x - sign * 1.03, 0, -0.035), (0.14, 7.52, 0.34), stone, 0.008)
        for i, y in enumerate((-2.54, -0.10, 2.34)):
            house(parent, roofs, x, y, side, mats, i)
        for yy in (-3.45, -1.15, 1.15, 3.45):
            box(bank, '河岸系船石桩', (x - sign * 1.05, yy, 0.17), (0.14, 0.15, 0.43), stone, 0.01)
    for j in range(5):
        yy = -2.73 + j * 0.23
        box(bank, '下河埠石阶', (-1.72 - j * 0.08, yy, 0.08 - j * 0.034), (0.55, 0.21, 0.12), stone, 0.006)
    export('nanxun', (8.0, -10.5, 6.8), 10.4)


def text_object(parent, name, message, xyz, size, material, front='y', font=None):
    """Make raised geometry, rather than a browser-dependent floating label."""
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = message
    curve.size = size
    curve.extrude = 0.002
    curve.bevel_depth = 0.001
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    if font: curve.font = font
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = xyz
    if front == 'y': obj.rotation_euler[0] = math.pi / 2
    else: obj.rotation_euler = (math.pi / 2, 0, -math.pi / 2 if front == 'x-negative' else math.pi / 2)
    obj.data.materials.append(material)
    return obj


def windows(parent, name, center, width, depth, z0, height, floors, bays, face, glass_mats, metal, top_scale=1):
    """One mesh per facade; thousands of individually shaded panes without thousands of draw calls."""
    x, y = center
    verts, faces, colors = [], [], []
    inset = 0.017
    def point(u, zz):
        scale = 1 + (top_scale-1) * (zz-z0) / height
        u *= 0.81  # Main flat planes end at the clipped corners.
        if face in ('front', 'back'):
            return (x+u*width*scale, y+(-1 if face=='front' else 1)*(depth*scale/2+inset), zz)
        return (x+(-1 if face=='left' else 1)*(width*scale/2+inset), y+u*depth*scale, zz)
    def facing(quad):
        return list(reversed(quad)) if face in ('back','left') else quad
    for row in range(floors):
        for col in range(bays):
            zlo = z0 + (row + 0.06) * height / floors
            zhi = z0 + (row + 0.94) * height / floors
            ulo, uhi = (col+0.035)/bays-0.5, (col+0.965)/bays-0.5
            quad = facing([point(ulo,zlo),point(uhi,zlo),point(uhi,zhi),point(ulo,zhi)])
            start = len(verts)
            verts.extend(quad)
            faces.append((start, start + 1, start + 2, start + 3))
            # Broad reflected-sky patches read as glass; per-cell alternation
            # looked like a checkerboard and obscured the photographed facade.
            colors.append(int(noise(col // 3 + (0 if face == 'front' else 17), row // 5) * len(glass_mats)) % len(glass_mats))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    for material in glass_mats: mesh.materials.append(material)
    for poly, index in zip(mesh.polygons, colors): poly.material_index = index
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    # The structural grid is a joined mesh too, avoiding one object per mullion.
    grid_verts, grid_faces = [], []
    def strip(u0, u1, zl, zh):
        base = len(grid_verts)
        grid_verts.extend(facing([point(u0,zl),point(u1,zl),point(u1,zh),point(u0,zh)]))
        grid_faces.append((base,base+1,base+2,base+3))
    for col in range(bays + 1):
        u = col / bays - 0.5
        thickness = 0.0022
        strip(u-thickness,u+thickness,z0,z0+height)
    for row in range(floors + 1):
        zz = z0 + row * height / floors
        strip(-0.5,0.5,zz-0.0025,zz+0.0025)
    grid = bpy.data.meshes.new(name + '_龙骨')
    grid.from_pydata(grid_verts, [], grid_faces)
    grid.update()
    frame = bpy.data.objects.new(name + '_龙骨', grid)
    bpy.context.collection.objects.link(frame)
    frame.parent = parent
    frame.data.materials.append(metal)

    # Glazed diagonal corner faces bridge the four flat curtain walls.
    if face=='front':
        clip=min(width,depth)*0.095
        for sx in (-1,1):
            for sy in (-1,1):
                verts,faces=[],[]
                for row in range(floors):
                    lower=z0+(row+0.025)*height/floors
                    upper=z0+(row+0.975)*height/floors
                    quad=[]
                    for endpoint,zz in [(0,lower),(1,lower),(1,upper),(0,upper)]:
                        s=1+(top_scale-1)*(zz-z0)/height
                        xx=x+sx*(width/2-(clip if endpoint==0 else 0))*s
                        yy=y+sy*(depth/2-(0 if endpoint==0 else clip))*s
                        quad.append((xx+sx*inset*0.7,yy+sy*inset*0.7,zz))
                    if sx*sy<0: quad.reverse()
                    start=len(verts); verts.extend(quad); faces.append(tuple(start+i for i in range(4)))
                mesh=bpy.data.meshes.new('切角幕墙'); mesh.from_pydata(verts,[],faces); mesh.update()
                bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
                obj=bpy.data.objects.new('切角对角玻璃面',mesh); bpy.context.collection.objects.link(obj)
                obj.parent=parent; obj.data.materials.append(glass_mats[1])


def build_dongwu_v2():
    clear()
    road = mat('街区灰石', (0.39, 0.42, 0.42), 0.9, kind='stone')
    sandstone = mat('裙楼暖棕石材', (0.46, 0.32, 0.26), 0.84, kind='stone')
    sandstone_light = mat('裙楼浅棕分层', (0.61, 0.45, 0.36), 0.79, kind='stone')
    metal = mat('银灰密网幕墙龙骨', (0.38, 0.48, 0.53), 0.36, 0.51)
    white = mat('照片中的浅色折线', (0.57, 0.66, 0.68), 0.42, 0.46)
    dark = mat('深色设备层', (0.075, 0.18, 0.24), 0.42, 0.25)
    panes = [mat('蓝青玻璃_%02d' % i, color, 0.24 + i * 0.011, 0.13, kind='glass')
             for i, color in enumerate([(0.17,0.31,0.39),(0.19,0.34,0.43),(0.16,0.29,0.37),
                                        (0.22,0.36,0.44),(0.15,0.27,0.35),(0.20,0.35,0.42)])]
    root = part('东吴国际广场_实景参照重建')
    ground = part('街区与道路', root, (0,-1,0), 0.7)
    box(ground, '城市地坪', (0,0,-0.13), (7.6,5.0,0.24), road, 0.045)
    for i in range(16):
        box(ground, '人行道浅色铺装', (-3.45+i*0.46,-2.2,0.005), (0.43,0.48,0.025), sandstone_light, 0.003)
    base = part('六层商业裙楼', root, (0,-0.8,0), 0.9)
    # Split podium wings leave a real open slot; rounded XY corners are
    # physical curves, not a bevel on one solid block across both towers.
    curved = part('裙楼弧形转角_分段立面', base, (0,0,1), 0.28)
    for xmin,xmax,ymax in [(-3.30,-0.30,2.12),(0.30,3.55,1.92)]:
        ymin,r=-1.67,0.48
        outline=[]
        for cx,cy,start in [(xmax-r,ymax-r,0),(xmin+r,ymax-r,90),
                            (xmin+r,ymin+r,180),(xmax-r,ymin+r,270)]:
            for step in range(13):
                angle=math.radians(start+step*90/12)
                outline.append((cx+r*math.cos(angle),cy+r*math.sin(angle)))
        count=len(outline)
        verts=[(x,y,z) for z in (0.015,1.31) for x,y in outline]
        faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]
        faces.extend((j,(j+1)%count,(j+1)%count+count,j+count) for j in range(count))
        mesh=bpy.data.meshes.new('裙房弧形实体'); mesh.from_pydata(verts,[],faces); mesh.update()
        obj=bpy.data.objects.new('银泰六层商业裙楼分翼',mesh); bpy.context.collection.objects.link(obj)
        obj.parent=base; obj.data.materials.append(sandstone)
        for z in (0.24,0.49,0.74,0.99,1.24):
            line(curved,'裙楼弧形逐层石材收边',[(x,y,z) for x,y in outline+[outline[0]]],0.016,sandstone_light,2)
            for j in range(count):
                a,b=outline[j],outline[(j+1)%count]
                mid=Vector(((a[0]+b[0])/2,(a[1]+b[1])/2,0))
                n=Vector((b[1]-a[1],a[0]-b[0],0)).normalized()*0.005
                panel(curved,'裙楼曲面玻璃分格',[(a[0]+n.x,a[1]+n.y,z+0.04),
                    (b[0]+n.x,b[1]+n.y,z+0.04),(b[0]+n.x,b[1]+n.y,z+0.18),
                    (a[0]+n.x,a[1]+n.y,z+0.18)],panes[2])
    passage=part('塔间开敞通道_低平台',root,(0,-1,0),0.35)
    box(passage,'塔间开敞石铺平台',(0,0.15,0.02),(0.58,3.67,0.055),road,0.005)
    box(base, '裙楼东侧外扩体量', (3.18,0.03,0.53), (0.75,3.12,1.02), sandstone, 0.04)
    for z in (0.24,0.49,0.74,0.99,1.24):
        for x,w in [(-1.8,2.03),(1.92,2.27)]:
            box(base, '六层间浅石檐线', (x,-1.68,z), (w,0.08,0.032), sandstone_light, 0.006)
            box(base, '裙楼连续蓝玻璃窗带', (x,-1.715,z+0.10), (w,0.025,0.12), panes[2])
    for i in range(29):
        xx = -2.95+i*0.21
        box(base, '底层门窗竖框', (xx,-1.75,0.115), (0.015,0.021,0.19), metal)
    # The western tower recedes in the near-view photograph. Both keep their
    # documented 288 m nominal height; depth and perspective create the gap.
    for x,y,w,d in [(-1.43,1.18,1.72,1.67),(1.28,0.12,1.85,1.73)]:
        tower = part(('西塔' if x < 0 else '东塔') + '_288米主量体', root,
                     (-1 if x < 0 else 1,0,0), 1.6)
        tower['officialHeightMetres'] = 288
        tower['referenceView'] = 'Commons near/far; developer height'
        # Photo silhouette: the previous miniature was too squat. Stretch
        # above the podium datum, leaving both documented-height towers equal.
        tower.scale.z=1.62
        tower.location.z=1.31*(1-1.62)
        body = part('蓝玻璃幕墙主体', tower)
        z0, top = 1.31, 6.55
        # The reference photographs show a shaft that tightens into a
        # shoulder and then a smaller stepped crown.  Keep those changes as
        # separate Blender parts so the exploded view explains the silhouette
        # instead of presenting a generic rectangular tower.
        frustum(body, '双塔蓝玻璃锥台主楼', (x, y, 3.295), 3.97, w, d, w * 0.965, d * 0.965, panes[1], 0.008)
        frustum(body, '双塔退台肩部', (x, y, 5.615), 0.67, w * 0.965, d * 0.965, w * 0.86, d * 0.86, panes[3], 0.008)
        skin = part('分件_幕墙面板与龙骨', tower, (0,0,1), 0.55)
        for face in ('front','back','left','right'):
            windows(skin, '逐格反射玻璃_'+face, (x,y), w,d,z0,3.97,48,21,face,panes,metal,0.965)
            windows(skin, '肩部分格玻璃_'+face, (x,y), w*0.965,d*0.965,5.28,0.67,8,21,face,panes,metal,0.86/0.965)
        devices = part('分件_深色设备层', tower, (0,1,0), 0.65)
        for z in (3.05,4.74):
            for face in ('front','back'):
                yy = y + (-d/2-0.034 if face == 'front' else d/2+0.034)
                box(devices,'深色设备层水平带', (x,yy,z), (w+0.06,0.04,0.095),dark)
            for side in (-1,1):
                box(devices,'侧面设备层水平带', (x+side*(w/2+0.034),y,z), (0.04,d+0.08,0.095),dark)
        marks = part('分件_幕墙折线斜纹', tower, (0,0,1), 0.72)
        yy = y-d/2-0.06
        # In the near photograph the broad front facade is mostly plain;
        # the distinctive pale chevrons run down the angled side faces.
        for side in (-1,1):
            side_x = x+side*(w/2+0.05)
            for zz in (1.68,3.29,4.50):
                line(marks,'幕墙折线斜纹',[(side_x,y-d*0.45,zz+0.06),
                    (side_x,y+d*0.03,zz+0.72),(side_x,y+d*0.45,zz+0.15)],0.018,white,1)
        # Thin vertical corner fins are visible in both supplied viewpoints.
        for sx in (-1, 1):
            line(marks, '塔角连续竖向收边', [(x + sx * w * 0.47, yy - 0.015, z0),
                                            (x + sx * w * 0.41, yy - 0.015, top)], 0.016, white, 1)
        side_x = x-w/2-0.045
        line(marks,'侧面折线接续',[(side_x,y-d*0.42,2.03),(side_x,y+d*0.30,2.86),
                                  (side_x,y+d*0.43,3.02)],0.015,white,1)
        crown = part('分件_退台塔冠', tower, (0,1,0), 0.8)
        frustum(crown,'退台塔冠玻璃上段',(x,y,6.25),0.60,w*0.86,d*0.86,w*0.77,d*0.78,panes[3],0.008)
        for face in ('front','back','left','right'):
            windows(crown,'冠部分格玻璃_'+face,(x,y),w*0.86,d*0.86,5.95,0.60,7,19,face,panes,metal,0.77/0.86)
        box(crown,'退台塔冠切角顶板',(x,y,6.58),(w*0.68,d*0.72,0.085),metal,0.024)
        cyl(crown,'顶部细桅杆',(x,y,6.92),0.018,0.70,white,12)
        # Small service-door and parapet marks keep the crown readable when
        # the user rotates to the rear, without inventing an interior plan.
        box(crown,'塔冠设备检修门',(x, y-d*0.40, 6.34),(w*0.28,0.022,0.16),dark,0.008)
    font_path='C:\\Windows\\Fonts\\simhei.ttf'
    font=bpy.data.fonts.load(font_path) if os.path.exists(font_path) else None
    sign=part('银泰百货_裙楼标识',base,(0,0,1),0.55)
    text_object(sign,'银泰百货招牌','银泰百货',(0.22,-1.85,1.34),0.20,white,'y',font)
    export('dongwu', (7.2,-12.8,7.5), 10.7)


def street_building(parent, roofs, lights, spec, mats, font):
    """A distinct 2022/2023 street-front volume with its own evidence marker."""
    side, index, x, y, width, depth, height, mode, sign_text = spec
    wall, timber, charcoal, glass, glow, tiles, ridge, red, brass, white = mats
    inward = 1 if side == 'left' else -1
    facade = x + inward * depth / 2
    group = part('%s%02d_逐栋街屋' % (side,index), parent, (-inward,0,(index-3)*0.15),0.12+index*0.025)
    group['referenceBuildingId'] = 'YISHANG_%s_%02d' % (side.upper(),index)
    group['facadeWidth'] = width
    group['evidence'] = 'photo-visible-front; rear interpretive'
    body_mat = timber if mode in ('wood','shopdark') else wall
    outer=x-inward*depth/2
    # Shell walls, floor slabs and recessed openings replace solid shop
    # blocks. The first shop's corner display is visible in the anchor photo.
    box(group,'逐栋后墙',(outer,y,height/2),(0.10,width,height),body_mat,0.01)
    for end in (-1,1):
        if index==1 and end==-1: continue
        box(group,'逐栋侧墙',(x,y+end*(width/2-0.035),height/2),(depth,0.07,height),body_mat,0.008)
    for floor_z in (0.08,height*0.58,height-0.06):
        box(group,'店面分层楼板',(x,y,floor_z),(depth,width,0.08),timber,0.005)
    box(group,'上层临街窗间墙',(facade,y,height*0.87),(0.075,width,height*0.24),body_mat,0.01)
    # The upper floor is continuous sash glazing on some shops and inset plaster on others.
    if mode == 'rounded':
        box(group,'照片中圆角近代楼外檐',(facade,y,height*0.75),
            (0.17,width*1.03,height*0.48),charcoal,0.08)
    if index==1:
        corner_y=y-width/2-0.012
        corner=part('分件_照片中转角店面_%s'%side,group,(0,0,1),0.30)
        box(corner,'转角橱窗玻璃',(x,corner_y,height*0.29),(depth,0.035,height*0.49),glass)
        for panel_i in range(5):
            xx=x-depth/2+panel_i*depth/4
            box(corner,'转角玻璃逐框',(xx,corner_y-0.021,height*0.28),(0.026,0.028,height*0.54),timber,0.003)
        box(corner,'转角发光店招',(x,corner_y-0.055,height*0.53),(depth*1.01,0.08,0.34),white if side=='right' else charcoal,0.02)
        text_object(corner,'转角照片店招_'+sign_text,sign_text,(x,corner_y-0.10,height*0.53),
             min(0.19,depth/max(4,len(sign_text))*1.55),red if side=='right' else glow,'y',font)
        for j in range(3):
            xx=x-depth*0.30+j*depth*0.30
            box(corner,'转角二层玻璃窗',(xx,corner_y,height*0.78),(depth*0.26,0.04,height*0.28),glass)
            for offset in (-0.14,0.14):
                box(corner,'转角二层木窗框',(xx+offset*depth,corner_y-0.03,height*0.78),(0.024,0.03,height*0.29),timber,0.003)
        box(group,'转角店内后景灯墙',(outer+inward*0.09,y,height*0.24),(0.04,width*0.91,height*0.42),glow,0.002)
    for j in range(3 if width > 1.2 else 2):
        yy = y-width/2+(j+0.5)*width/(3 if width > 1.2 else 2)
        box(group,'二层独立窗洞',(facade+inward*0.028,yy,height*0.77),
            (0.035,width/(3 if width>1.2 else 2)*0.77,height*0.29),glass)
        for offset in (-0.38,0,0.38):
            box(group,'二层窗梃',(facade+inward*0.048,yy+offset*width/3,height*0.77),
                (0.019,0.018,height*0.30),timber)
        box(group,'二层横窗档',(facade+inward*0.053,yy,height*0.78),
            (0.018,width/(3 if width>1.2 else 2)*0.77,0.022),timber)
    box(group,'一层店内透光玻璃',(facade+inward*0.03,y,height*0.29),
        (0.04,width*0.87,height*0.47), glass)
    for j in range(5):
        yy = y-width*0.43+j*width*0.215
        box(group,'店门与玻璃竖框',(facade+inward*0.055,yy,height*0.27),
            (0.024,0.026,height*0.52),timber)
    box(group,'檐廊出挑木梁',(facade+inward*0.16,y,height*0.56),
        (0.36,width*1.035,0.085),timber,0.015)
    # The supplied night reference shows a layered contemporary storefront:
    # a recessed glowing window, a dark rain hood, then a thin warm edge light.
    # Keep each layer as a real mesh so the exploded view explains the facade.
    awning = part('分件_照片门头雨棚与光槽_%s%02d' % (side,index), group, (inward,0,0), 0.18)
    box(awning,'门头暖白线性灯',(facade+inward*0.265,y,height*0.595),
        (0.022,width*0.90,0.025),glow,0.002)
    box(awning,'门头深色雨棚',(facade+inward*0.19,y,height*0.625),
        (0.16,width*1.02,0.08),charcoal,0.012)
    for yy in (y-width*0.45, y-width*0.15, y+width*0.15, y+width*0.45):
        box(awning,'雨棚逐根檐条',(facade+inward*0.285,yy,height*0.66),
            (0.12,0.025,0.035),timber,0.003)
    box(awning,'橱窗内透光层',(facade+inward*0.09,y,height*0.30),
        (0.014,width*0.72,height*0.35),glow,0.001)
    if side == 'left' and index == 1 and PHOTO_MATS:
        upper = box(awning,'照片校正_茉莉酸奶二层窗带',
                    (facade+inward*0.115,y,height*0.79),
                    (0.018,width*0.92,height*0.34),PHOTO_MATS['upper'],0.003)
        sign_photo = box(awning,'照片校正_茉莉酸奶门头',
                         (facade+inward*0.285,y,height*0.48),
                         (0.025,width*0.98,height*0.20),PHOTO_MATS['sign'],0.003)
        display = box(awning,'照片校正_茉莉酸奶展示柜',
                      (facade+inward*0.13,y-width*0.12,height*0.26),
                      (0.018,width*0.42,height*0.22),PHOTO_MATS['display'],0.002)
        for obj in (upper, sign_photo, display):
            obj['photographicSurface'] = True
            obj['photoSource'] = '源義信 2023-07-08 衣裳街 · CC BY-SA 4.0'
    box(group,'沿街招牌底板',(facade+inward*0.20,y,height*0.48),
        (0.06,width*0.98,height*0.19),charcoal if mode in ('wood','rounded') else white,0.01)
    if sign_text and not (side == 'left' and index == 1):
        # Raised lettering is supported by the Blender source and converted into GLB meshes.
        text_object(group,'逐栋发光招牌_'+sign_text,sign_text,
                    (facade+inward*0.255,y,height*0.48),min(0.19,width/max(4,len(sign_text))*1.65),
                    glow if mode!='shopdark' else red,'x' if side=='left' else 'x-negative',font)
    # Separate panes, muntins, door handles, signbox lips and the soffit from
    # the wall. The frame is a readable layer in the exploded scene.
    facade_parts = part('分件_门窗灯箱与檐廊_%s%02d' % (side,index),group,(inward,0,0),0.24)
    for child in list(group.children):
        if child == facade_parts: continue
        if any(word in child.name for word in ('窗','店门','招牌','出挑木梁')):
            child.parent = facade_parts
    for yy in (y-width*0.40,y+width*0.40):
        # Raised panelled jambs and a physical brass pull sit in front of the glazing.
        for zz in (height*0.08,height*0.53):
            box(facade_parts,'店门框榫卯压边',(facade+inward*0.07,yy,zz),
                (0.06,0.11,0.025),timber,0.003)
        line(facade_parts,'店门黄铜门把手',[(facade+inward*0.091,yy,0.49),
             (facade+inward*0.13,yy,0.49),(facade+inward*0.13,yy,0.64),
             (facade+inward*0.091,yy,0.64)],0.009,brass,2)
    for zz in (height*0.385,height*0.57):
        box(facade_parts,'灯箱上下收边',(facade+inward*0.238,y,zz),
            (0.014,width*0.99,0.014),brass,0.002)
    if mode in ('rounded','wood'):
        box(facade_parts,'檐下连续暖光灯槽',(facade+inward*0.26,y,height*0.58),
            (0.018,width*0.99,0.015),glow)
    # Recessed display counters are visible through the lower openings.
    box(facade_parts,'店内橱窗台面',(facade-inward*0.08,y,height*0.16),
        (0.26,width*0.79,0.06),charcoal,0.008)
    box(facade_parts,'橱窗内暖光背景',(facade+inward*0.076,y,height*0.30),
        (0.009,width*0.63,height*0.27),glow)
    # Fine wall skirting and rainwater details remain geometrical at close range.
    for zz in (0.065,0.125):
        box(group,'旧砖墙脚压边',(facade+inward*0.021,y,zz),(0.028,width,0.018),charcoal,0.002)
    pipe_y=y+width*0.46
    line(group,'檐下落水管',[(facade+inward*0.052,pipe_y,height*0.94),
        (facade+inward*0.084,pipe_y,height*0.91),(facade+inward*0.084,pipe_y,0.06)],0.018,charcoal,2)
    # Per-building street furniture and lantern spacing follows the irregular facades.
    for yy in (y-width*0.39,y+width*0.39):
        box(group,'店面木柱',(facade+inward*0.23,yy,height*0.28),
            (0.075,0.068,height*0.55),timber,0.008)
        if mode in ('wood','shopdark'):
            lantern(lights,(facade+inward*0.20,yy,height*0.64),red,brass)
    if mode in ('wood','shopdark'):
        for j in range(4):
            yy = y-width*0.35+j*width*0.23
            line(group,'照片中的深木檐廊细部',[(facade+inward*0.19,yy,height*0.56),
                 (facade+inward*0.31,yy,height*0.69)],0.012,timber,1)
    if mode in ('rounded','modern'):
        box(roofs,'平屋顶女儿墙',(x,y,height+0.07),(depth*1.02,width*1.03,0.17),charcoal,0.04)
        for j in range(3):
            box(roofs,'近代楼顶逐级檐线',(facade-inward*0.02,y,height+0.17+j*0.038),
                (0.08,width*1.025,0.021),ridge)
    else:
        roof = gable(roofs,'逐栋灰瓦屋顶',x,y,height,depth+0.21,width+0.15,
              0.22+0.06*(index%3),tiles,ridge)
        roof['explodeDirection']=[0,1,0]
        roof['explodeDistance']=0.06*index
    # Full side and rear surfaces remain three-dimensional, but are marked inferred.
    outer = x-inward*depth/2
    box(group,'背立面窄木窗',(outer-inward*0.022,y,height*0.70),
        (0.044,width*0.52,height*0.24),glass)
    for j in range(4):
        box(group,'背立面窗棂',(outer-inward*0.046,y-width*0.23+j*width*0.15,height*0.70),
            (0.02,0.018,height*0.24),timber)
    return group


def build_yishang_v2():
    clear()
    stone = mat('错缝青石路面', (0.35,0.37,0.34),0.91,kind='stone')
    stone_light = mat('青石板表面差异',(0.43,0.43,0.39),0.88,kind='stone')
    wall = mat('旧街粉灰墙',(0.65,0.62,0.54),0.86,kind='stone')
    wood = mat('老铺深木',(0.24,0.15,0.12),0.71,kind='wood')
    charcoal = mat('近代商铺深褐立面',(0.14,0.13,0.12),0.68,kind='wood')
    glass = mat('街铺深色玻璃',(0.13,0.20,0.20),0.18,0.1,kind='glass')
    glow = mat('店铺米白发光字',(0.94,0.86,0.66),0.32,glow=0.65)
    tile = mat('传统深灰瓦',(0.18,0.21,0.20),0.88,kind='tile')
    ridge = mat('瓦脊压条',(0.28,0.30,0.28),0.75,kind='tile')
    red = mat('街巷红灯笼',(0.61,0.085,0.05),0.46,kind='cloth',glow=0.23)
    brass = mat('灯具金属边',(0.61,0.43,0.18),0.35,0.5)
    white = mat('现代白色灯箱',(0.73,0.74,0.68),0.52,glow=0.33)
    global PHOTO_MATS
    PHOTO_MATS = {
        'upper': image_mat('照片材质_茉莉酸奶二层窗带', os.path.join(ROOT,'assets','blender','textures','yishang-moli-upper.png')),
        'sign': image_mat('照片材质_茉莉酸奶门头', os.path.join(ROOT,'assets','blender','textures','yishang-moli-sign.png'), 0.35),
        'display': image_mat('照片材质_茉莉酸奶展示柜', os.path.join(ROOT,'assets','blender','textures','yishang-moli-display.png'), 0.30),
    }
    mats = (wall,wood,charcoal,glass,glow,tile,ridge,red,brass,white)
    font = bpy.data.fonts.load('C:\\Windows\\Fonts\\simhei.ttf') if os.path.exists('C:\\Windows\\Fonts\\simhei.ttf') else None
    root = part('衣裳街_主街与水巷_实景参照重建')
    road = part('折线石板街',root,(0,-1,0),0.85)
    # Pavement axis bends toward the river. Stones are sized and laid individually.
    box(road,'旧街承重地坪',(0,0,-0.18),(7.5,10.2,0.30),stone,0.035)
    for row in range(35):
        yy = -4.8+row*0.28
        bend = 0.28*math.sin((yy+3.5)*0.37)
        for col in range(13):
            xx = bend-1.65+col*0.275+(0.11 if row%2 else 0)
            if xx>1.7+bend: continue
            box(road,'纵横错缝石板',(xx,yy,-0.014+noise(col,row)*0.004),
                (0.263,0.267,0.031),stone if noise(row,col)>0.32 else stone_light,0.002)
    for side in (-1,1):
        path = [(side*(1.82+0.28*math.sin((y+3.5)*0.37)),y,0.01)
                for y in [(-4.8+i*0.23) for i in range(43)]]
        line(road,'两侧石板排水边沟',path,0.024,charcoal,1)
    left = part('左侧逐栋商铺',root,(-1,0,0),1.3)
    right = part('右侧逐栋商铺',root,(1,0,0),1.3)
    roofs = part('各异屋顶与檐口',root,(0,1,0),1.0)
    lights = part('逐檐悬灯',root,(0,1,0),0.8)
    # Each row is individually described; width, height and facade type are not cloned.
    specs = [
        ('left',1,-2.50,-4.05,1.90,1.45,2.78,'rounded','茉莉酸奶'),
        ('left',2,-2.61,-2.39,1.37,1.55,2.55,'wood','米莉酸奶'),
        ('left',3,-2.68,-1.04,1.26,1.69,2.36,'shopdark','传统小吃'),
        ('left',4,-2.66,0.26,1.33,1.62,2.64,'modern','衣裳街'),
        ('left',5,-2.75,1.52,1.20,1.66,2.31,'wood','茶'),
        ('left',6,-2.87,2.90,1.48,1.72,2.47,'shopdark','湖州味道'),
        ('right',1,2.52,-4.15,1.66,1.58,2.64,'wood','狼琥小火锅'),
        ('right',2,2.57,-2.63,1.38,1.68,2.82,'shopdark','吴兴老味'),
        ('right',3,2.58,-1.23,1.42,1.75,2.56,'modern','糖水铺'),
        ('right',4,2.69,0.11,1.18,1.65,2.44,'wood','老街食肆'),
        ('right',5,2.73,1.52,1.59,1.84,2.68,'shopdark','南太湖'),
        ('right',6,2.85,2.98,1.34,1.71,2.38,'wood','点心'),
    ]
    for spec in specs:
        street_building(left if spec[0]=='left' else right,roofs,lights,spec,mats,font)
    # Qinglian Bridge belongs to the wider historic district, outside the main
    # storefront sequence; it is a separate off-axis node, not a duplicate street.
    bridge = part('青莲桥_水巷独立节点',root,(1,0,1),1.9)
    water = mat('青莲桥下河水',(0.16,0.27,0.28),0.20,0.1,kind='water')
    box(bridge,'水巷水面',(4.95,3.20,-0.09),(2.0,3.85,0.075),water)
    for z,width in [(0.05,1.22),(0.17,1.01),(0.29,0.84)]:
        box(bridge,'青莲桥石桥台阶',(4.95,3.25,z),(width,0.47,0.10),stone_light,0.012)
    box(bridge,'青莲桥桥身',(4.95,3.25,0.45),(1.05,1.65,0.20),stone_light,0.035)
    for x in (4.48,5.42):
        for y in (2.61,3.05,3.49,3.93):
            box(bridge,'廊桥木立柱',(x,y,0.98),(0.055,0.055,0.94),wood)
    gable(bridge,'青莲桥黛瓦廊顶',4.95,3.26,1.48,1.41,1.92,0.42,tile,ridge)
    # A street-level, slightly off-axis camera keeps both shopfront rows in
    # view, matching the supplied night photograph instead of exposing a
    # simplified rear wall on one side.
    export('yishang',(0.5,-14.5,4.0),11.9)


def baijian_house(parent, roof_group, wall_group, spec, mats):
    side, index, x, y, width, depth, height, style = spec
    wall, stone, timber, glass, tiles, ridge, dark, red, brass = mats
    sign = 1 if side == 'east' else -1
    front = x-sign*depth/2
    house = part('%s岸_百间楼独立街屋_%02d' % (side,index),parent,(sign,0,(index-4)*0.12),0.10+index*0.025)
    house['referenceBuildingId'] = 'BAIJIAN_%s_%02d' % (side.upper(),index)
    house['facadeWidth'] = width
    house['evidence'] = 'photo-visible river facade; rear inferred'
    # A real corridor: the upper floor projects over an empty lower bay.
    # The old solid cube filled the space behind the outer columns.
    setback=0.40
    box(house,'百间楼二层墙身',(x,y,(height+1.47)/2),(depth,width,height-1.47),wall,0.012)
    box(house,'沿廊后退底层墙',(x+sign*setback/2,y,0.72),(depth-setback,width,1.44),wall,0.01)
    gallery=part('分件_有进深沿廊_%s%02d'%(side,index),house,(-sign,0,0),0.28)
    box(gallery,'临水廊道石地坪',(front+sign*0.12,y,0.105),(0.70,width,0.08),stone,0.008)
    box(gallery,'骑楼上层木楼板',(front+sign*0.06,y,1.46),(0.79,width,0.08),timber,0.008)
    box(house,'临河连续二层木饰带',(front-sign*0.014,y,height*0.735),
        (0.027,width*0.99,height*0.31),timber,0.003)
    # Photo-specific riverside arcade: the lower bay is recessed behind
    # repeated timber posts rather than a flat grey facade.
    for bay in range(2 if width>1.4 else 1):
        bcount=2 if width>1.4 else 1
        yy=y-width/2+(bay+0.5)*width/bcount
        bw=width/bcount*0.91
        door_x=front+sign*(setback-0.025)
        box(house,'廊后木门洞',(door_x,yy,0.68),(0.045,bw*0.81,1.10),dark)
        for panel_index in range(4):
            panel_y=yy-bw*0.36+(panel_index+0.5)*bw*0.18
            box(house,'廊后分扇木门',(door_x-sign*0.025,panel_y,0.68),(0.018,bw*0.174,1.08),timber,0.003)
            for panel_z in (0.37,0.83):
                box(house,'木门凹凸板芯',(door_x-sign*0.037,panel_y,panel_z),(0.014,bw*0.12,0.28),dark,0.003)
        if style in ('arch','gateway'):
            pts=[(door_x-sign*0.036, yy+bw*0.42*math.cos(a),
                  0.64+bw*0.28*math.sin(a)) for a in [i*math.pi/16 for i in range(17)]]
            line(house,'沿河券门石砌拱券',pts,0.035,stone,2)
        for dy in (-bw*0.46,bw*0.46):
            box(gallery,'沿廊灰墙方柱',(front-sign*0.22,yy+dy,0.74),(0.105,0.12,1.45),wall,0.008)
            box(gallery,'方柱石础',(front-sign*0.22,yy+dy,0.16),(0.145,0.155,0.14),stone,0.008)
            box(gallery,'方柱顶木托',(front-sign*0.22,yy+dy,1.42),(0.135,0.15,0.10),timber,0.008)
    box(gallery,'临水披檐梁',(front-sign*0.24,y,1.49),(0.09,width*1.01,0.10),timber,0.009)
    # Continuous second-floor ribbon of distinctly spaced wooden sash windows.
    upper_count=3 if width>1.4 else 2
    for j in range(upper_count):
        yy=y-width/2+(j+0.5)*width/upper_count
        ww=width/upper_count*0.82
        box(house,'二层临河木窗暗洞',(front-sign*0.025,yy,height*0.74),
            (0.045,ww,height*0.25),glass)
        for v in range(4):
            box(house,'雕花木窗纵棂',(front-sign*0.051,yy-ww*0.39+v*ww*0.26,height*0.74),
                (0.018,0.021,height*0.26),timber)
        for zz in (height*0.66,height*0.79,height*0.87):
            box(house,'雕花木窗横档',(front-sign*0.055,yy,zz),(0.017,ww,0.02),timber)
    for yy in (y-width*0.46,y+width*0.46):
        box(house,'二层廊下支柱',(front-sign*0.24,yy,height*0.73),
            (0.06,0.06,height*0.34),timber)
    box(gallery,'沿河连续木栏杆',(front-sign*0.34,y,0.39),(0.055,width*0.92,0.055),timber)
    for j in range(5):
        yy=y-width*0.44+j*width*0.22
        box(gallery,'临河木栏杆立柱',(front-sign*0.34,yy,0.27),(0.052,0.052,0.46),timber)
    # Individually pitched roof units and fire walls at the seams form the
    # hundreds-of-houses skyline photographed on the east bank.
    roof = gable(roof_group,'逐栋黛瓦坡屋顶',x,y,height+0.04,depth+0.24,width+0.16,
          0.28+(index%3)*0.075,tiles,ridge)
    roof['explodeDirection']=[0,1,0]
    roof['explodeDistance']=0.04*index
    canopy=part('分件_临河披檐_%s%02d' % (side,index),roof_group,(0,1,0),0.10+index*0.025)
    tiled_slope(canopy,'临河骑楼披檐实体瓦片',front,y,1.53,0.49,width+0.10,0.13,-sign,tiles)
    box(canopy,'披檐连续封檐板',(front-sign*0.48,y,1.50),(0.035,width+0.1,0.083),timber,0.004)
    yedge=y+width/2
    if style in ('arch','horsehead'):
        wall_outline=[(x-depth*0.52,yedge,height+0.04),
                      (x-depth*0.48,yedge,height+0.35),
                      (x-depth*0.25,yedge,height+0.35),
                      (x-depth*0.25,yedge,height+0.51),
                      (x,yedge,height+0.51),
                      (x,yedge,height+0.64),
                      (x+depth*0.25,yedge,height+0.51),
                      (x+depth*0.25,yedge,height+0.35),
                      (x+depth*0.48,yedge,height+0.35)]
        solid_gable(wall_group,'三叠马头墙_实体砖砌',wall_outline,0.085,wall)
        for pt in wall_outline[1::2]:
            box(wall_group,'马头墙逐级压檐',(pt[0],yedge,pt[2]),(0.21,0.092,0.035),ridge,0.008)
    elif style=='pipa':
        pts=[(x-depth*0.50+depth*i/16,yedge,height+0.12+0.43*math.sin(math.pi*i/16))
             for i in range(17)]
        pts=[(x-depth*0.50,yedge,height+0.04)]+pts+[(x+depth*0.50,yedge,height+0.04)]
        solid_gable(wall_group,'琵琶山墙_实体砖砌',pts,0.085,wall)
    if index%3==0: lantern(house,(front-sign*0.21,y-width*0.28,1.37),red,brass)
    return house


def solid_gable(parent, name, outline, thickness, material):
    mesh=bpy.data.meshes.new(name)
    n=len(outline)
    verts=[(xx,yy+side*thickness/2,zz) for side in (-1,1) for xx,yy,zz in outline]
    faces=[tuple(range(n)),tuple(reversed(range(n,n*2)))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    bm=bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent=parent; obj.data.materials.append(material)
    edge=obj.modifiers.new('石灰墙柔边','BEVEL'); edge.width=0.006; edge.segments=2
    return obj


def build_nanxun_v2():
    clear()
    stone=mat('百间楼驳岸旧石',(0.45,0.43,0.38),0.89,kind='stone')
    wall=mat('百间楼白灰抹墙',(0.47,0.46,0.41),0.93,kind='stone')
    timber=mat('沿河旧木檐廊',(0.20,0.14,0.10),0.77,kind='wood')
    glass=mat('二层深木格窗',(0.11,0.14,0.13),0.32,0.1,kind='glass')
    tile=mat('百间楼灰黑瓦',(0.13,0.15,0.15),0.92,kind='tile')
    ridge=mat('压顶瓦与屋脊',(0.19,0.21,0.20),0.85,kind='tile')
    dark=mat('骑楼下暗门洞',(0.10,0.09,0.08),0.88,kind='wood')
    water=mat('百间楼河暮色水面',(0.095,0.15,0.15),0.13,0.18,kind='water')
    red=mat('屋檐零散红灯笼',(0.52,0.10,0.075),0.47,glow=0.13)
    brass=mat('铜制灯架',(0.59,0.42,0.21),0.35,0.45)
    mats=(wall,stone,timber,glass,tile,ridge,dark,red,brass)
    root=part('南浔百间楼河_实景参照重建')
    river=part('百间楼河道与水面',root,(0,-1,0),0.7)
    box(river,'河床', (0,0,-0.27),(4.15,10.0,0.27),stone,0.02)
    water_mesh=bpy.data.meshes.new('逐波水面')
    verts,faces=[],[]
    for j in range(71):
        yy=-4.9+j*0.14
        for i in range(31):
            xx=-2.0+i*4/30
            zz=-0.044+0.010*math.sin(yy*14+xx*4)+0.003*math.sin(yy*41-xx*8)
            verts.append((xx,yy,zz))
    for j in range(70):
        for i in range(30):
            a=j*31+i; faces.append((a,a+1,a+32,a+31))
    water_mesh.from_pydata(verts,[],faces); water_mesh.update()
    obj=bpy.data.objects.new('百间楼河有纹水面',water_mesh)
    bpy.context.collection.objects.link(obj); obj.parent=river; obj.data.materials.append(water)
    for face in obj.data.polygons: face.use_smooth=True
    banks=part('两岸石护岸与下河埠',root,(0,-1,0),1.0)
    east=part('东岸连续逐栋楼群',root,(1,0,0),1.2)
    west=part('西岸近景短段',root,(-1,0,0),0.9)
    roofs=part('逐栋黛瓦屋顶',root,(0,1,0),0.9)
    gables=part('独立山墙与券门',root,(0,1,0),0.8)
    # The 2016 photograph has a long east-bank arcade and a sparse, close
    # west foreground. The rows deliberately differ in length and topology.
    specs=[
        ('east',1,3.03,-4.11,1.70,1.86,2.30,'arch'),
        ('east',2,3.04,-2.63,1.26,1.77,2.36,'horsehead'),
        ('east',3,3.10,-1.30,1.39,1.89,2.43,'pipa'),
        ('east',4,3.11,0.08,1.27,1.91,2.39,'arch'),
        ('east',5,3.18,1.44,1.45,2.00,2.54,'horsehead'),
        ('east',6,3.24,2.82,1.26,1.91,2.42,'pipa'),
        ('east',7,3.28,4.06,1.18,1.94,2.36,'arch'),
        ('west',1,-3.10,-3.99,1.61,1.95,2.80,'pipa'),
        ('west',2,-3.04,-2.45,1.43,1.82,2.48,'gateway'),
        ('west',3,-3.08,-1.15,1.19,1.91,2.31,'horsehead'),
    ]
    for spec in specs:
        baijian_house(east if spec[0]=='east' else west,roofs,gables,spec,mats)
    for sign in (-1,1):
        x=sign*2.06
        box(banks,'沿河石砌护岸',(x,0,0.075),(0.17,9.8,0.27),stone,0.007)
        for j in range(44):
            yy=-4.78+j*0.22
            box(banks,'石护岸水平长条',(x+sign*0.06,yy,0.10),(0.06,0.20,0.025),stone,0.002)
    for yy in (-3.35,-0.20,2.35):
        for j in range(6):
            x=-2.10+j*0.13
            box(banks,'下河埠石阶',(x,yy,0.20-j*0.045),(0.24,0.62,0.11),stone,0.005)
    # A far-bank passage and trees give the view its photographed depth.
    box(gables,'远端桥影',(0,4.75,0.42),(4.12,0.27,0.22),stone,0.028)
    tree=part('远岸柳树与河巷深景',root,(0,0,-1),0.55)
    leaf=mat('柳树暮色叶',(0.22,0.28,0.20),0.92,kind='leaf')
    for cx,cy in [(-1.95,4.16),(1.75,4.50)]:
        line(tree,'柳树不规则主干',[(cx,cy,0),(cx+0.025,cy,0.65),
             (cx-0.035,cy+0.015,1.25),(cx+0.02,cy,1.65)],0.058,timber,3)
        leaf_verts,leaf_faces=[],[]
        for spray in range(48):
            angle=spray*2.39996
            radius=0.15+0.49*noise(spray,7)
            tipx=cx+radius*math.cos(angle); tipy=cy+radius*math.sin(angle)
            top=1.54+0.28*noise(spray,10)
            line(tree,'柳树细枝与垂条',[(cx,cy,1.30),(tipx*0.6+cx*0.4,tipy*0.6+cy*0.4,top+0.06),
                (tipx,tipy,top),(tipx+0.04*math.cos(angle),tipy+0.04*math.sin(angle),top-0.77)],0.006,timber,1)
            for index in range(15):
                drop=index*0.049
                center=Vector((tipx+drop*0.06*math.cos(angle),tipy+drop*0.06*math.sin(angle),top-drop))
                sideways=Vector((math.cos(angle+index*0.41),math.sin(angle+index*0.41),0))
                stem=Vector((0.014*math.cos(angle),0.014*math.sin(angle),-0.065))
                base=len(leaf_verts)
                leaf_verts.extend([center[:],(center+stem+sideways*0.013)[:],(center+stem*2)[:],(center+stem-sideways*0.013)[:]])
                leaf_faces.extend([(base,base+1,base+2),(base,base+2,base+3)])
        mesh=bpy.data.meshes.new('逐片柳叶'); mesh.from_pydata(leaf_verts,[],leaf_faces); mesh.update()
        obj=bpy.data.objects.new('逐片细柳叶_垂条叶片',mesh); bpy.context.collection.objects.link(obj)
        obj.parent=tree; obj.data.materials.append(leaf)
    # Camera sits inside the photographed canal, facing the long east-bank
    # arcade; the previous outside-bank angle showed only inferred rear walls.
    export('nanxun',(-4.4,-10.2,3.4),10.8)


def export(name, camera_offset, scale):
    bpy.context.view_layer.update()
    ensure_mesh_uvs()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCES, f'city-{name}.blend'))
    # Export glTF geometry (editable curves are preserved in .blend source).
    bpy.ops.object.select_all(action='DESELECT')
    curves = [o for o in bpy.data.objects if o.type in ('CURVE', 'FONT')]
    if curves:
        for o in curves: o.select_set(True)
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.select_all(action='DESELECT')
    ensure_mesh_uvs()
    batch_repeated_geometry()
    bpy.ops.export_scene.gltf(filepath=os.path.join(MODELS, f'city-{name}.glb'),
                              export_format='GLB', export_extras=True,
                              export_lights=False, export_cameras=False, export_apply=False)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 1400
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.eevee.taa_render_samples = 96
    scene.eevee.use_raytracing = True
    scene.view_settings.view_transform = 'AgX'
    world = bpy.data.worlds.new('soft studio world')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.42, 0.49, 0.48, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
    camera_data = bpy.data.cameras.new('preview orthographic camera')
    camera = bpy.data.objects.new('preview camera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = 'PERSP'
    camera.data.lens = 40
    visible_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    corners = [o.matrix_world @ Vector(corner) for o in visible_meshes for corner in o.bound_box]
    lo = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    hi = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    center = (lo + hi) / 2
    camera.location = center + Vector(camera_offset)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    for n, loc, energy, size, color in [
        ('warm key', (2, -5, 8), 1700, 7, (1, 0.88, 0.71)),
        ('cool fill', (-5, -1, 4), 850, 6, (0.7, 0.86, 1)),
        ('edge light', (1, 5, 7), 1450, 5, (0.94, 0.92, 0.79)),
    ]:
        data = bpy.data.lights.new(n, 'AREA')
        light = bpy.data.objects.new(n, data)
        scene.collection.objects.link(light)
        light.location = loc
        light.rotation_euler = (-light.location).to_track_quat('-Z', 'Y').to_euler()
        data.energy = energy
        data.shape = 'DISK'
        data.size = size
        data.color = color
    fit_perspective_camera(camera, visible_meshes)
    scene.render.filepath = os.path.join(PREVIEWS, f'city-{name}.png')
    bpy.ops.render.render(write_still=True)
    for o in bpy.data.objects:
        if 'explodeDirection' in o:
            dx, dy, dz = o['explodeDirection']
            o.location += Vector((dx, -dz, dy)) * o['explodeDistance']
    bpy.context.view_layer.update()
    fit_perspective_camera(camera, visible_meshes)
    scene.render.filepath = os.path.join(PREVIEWS, f'city-{name}-expanded.png')
    bpy.ops.render.render(write_still=True)
    print('EXPORTED CITY', name, os.path.getsize(os.path.join(MODELS, f'city-{name}.glb')))


def ensure_mesh_uvs():
    """PBR needs UVs on authored facade/roof meshes, not only primitive cubes."""
    for obj in bpy.data.objects:
        if obj.type!='MESH' or obj.data.uv_layers: continue
        mesh=obj.data
        uv=mesh.uv_layers.new(name='architectural_uv')
        for polygon in mesh.polygons:
            normal=polygon.normal
            dominant=max(range(3),key=lambda i:abs(normal[i]))
            axes=[i for i in range(3) if i!=dominant]
            for loop_index in polygon.loop_indices:
                pt=mesh.vertices[mesh.loops[loop_index].vertex_index].co
                uv.data[loop_index].uv=(pt[axes[0]]*0.7,pt[axes[1]]*0.7)


def batch_repeated_geometry():
    """Keep part hierarchy while reducing repeated detail's WebGL draw calls."""
    groups={}
    for obj in list(bpy.data.objects):
        if obj.type!='MESH' or len(obj.data.materials)!=1: continue
        key=(obj.parent,re.sub(r'\.\d{3}$','',obj.name),obj.data.materials[0])
        groups.setdefault(key,[]).append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for (_,base_name,_),objects in groups.items():
        if len(objects)<4: continue
        for obj in objects: obj.select_set(True)
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()
        bpy.context.object.name=base_name+'_合批细节'
        bpy.ops.object.select_all(action='DESELECT')


def fit_perspective_camera(camera, meshes):
    bpy.context.view_layer.update()
    corners=[obj.matrix_world@vert.co for obj in meshes for vert in obj.data.vertices]
    lo=Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    hi=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    center=(lo+hi)/2
    direction=(camera.location-center).normalized()
    distance=(camera.location-center).length
    camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    rotation=camera.rotation_euler.to_matrix()
    right=rotation@Vector((1,0,0)); up=rotation@Vector((0,1,0))
    local=[((v-center).dot(right),(v-center).dot(up),(v-center).dot(direction)) for v in corners]
    tangent=camera.data.sensor_width/(2*camera.data.lens)
    # Fit the assembled AND separated bounds, independently; the old expanded
    # poster retained the assembled crop and lost its outer layers.
    camera.data.shift_x=0; camera.data.shift_y=0
    for _ in range(32):
        camera.location=center+direction*distance
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        if any(distance-z<0.1 for _,_,z in local): distance*=1.15; continue
        projected=[(0.5+x/((distance-z)*2*tangent),0.5+y/((distance-z)*2*tangent)) for x,y,z in local]
        xmin,xmax=min(p[0] for p in projected),max(p[0] for p in projected)
        ymin,ymax=min(p[1] for p in projected),max(p[1] for p in projected)
        if xmax-xmin<0.89 and ymax-ymin<0.89:
            # Frame the projected geometry, not the projected box's imaginary
            # top-front corners. Low street views otherwise leave half a page
            # of empty sky above the miniature.
            camera.data.shift_x=(xmin+xmax)/2-0.5
            camera.data.shift_y=(ymin+ymax)/2-0.5
            break
        distance*=1.07


makers = {'yishang': build_yishang_v2, 'dongwu': build_dongwu_v2,
          'longemont': build_longemont, 'nanxun': build_nanxun_v2}
selected = os.environ.get('CITY_ONLY') or (sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 2 else None)
if selected and selected not in makers: raise ValueError(f'Unknown CITY_ONLY: {selected}')
for name, maker in makers.items():
    if not selected or selected == name: maker()
