"""Pure geometry used by the photo-led architectural Blender builder."""
import math


def ellipsoid_sector(rx, ry, height, start, end, segments, rings):
    """Upper ellipsoidal shell; counter-clockwise faces point outward."""
    verts = []
    for ring in range(rings+1):
        latitude = ring*math.pi/(2*rings)
        for column in range(segments+1):
            angle = start+(end-start)*column/segments
            verts.append((rx*math.cos(latitude)*math.cos(angle),
                          ry*math.cos(latitude)*math.sin(angle),
                          height*math.sin(latitude)))
    faces = []
    stride = segments+1
    for ring in range(rings):
        for column in range(segments):
            a = ring*stride+column
            if ring == rings-1:
                faces.append((a,a+1,a+stride))
            else:
                faces.append((a,a+1,a+stride+1,a+stride))
    return verts, faces


def clipped_rectangle(width, depth, clip):
    x,y=width/2,depth/2
    return [(-x+clip,-y),(x-clip,-y),(x,-y+clip),(x,y-clip),
            (x-clip,y),(-x+clip,y),(-x,y-clip),(-x,-y+clip)]
