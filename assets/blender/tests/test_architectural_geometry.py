"""Geometry contracts, not a substitute for comparing the model to a photo."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from architectural_geometry import ellipsoid_sector, clipped_rectangle


class DomeTests(unittest.TestCase):
    def test_closed_sector_has_flat_elliptical_footprint_and_correct_height(self):
        verts, faces = ellipsoid_sector(7.4, 5.0, 2.6, 0, 2*math.pi, 64, 16)
        self.assertAlmostEqual(min(p[0] for p in verts), -7.4)
        self.assertAlmostEqual(max(p[0] for p in verts), 7.4)
        self.assertAlmostEqual(min(p[1] for p in verts), -5.0)
        self.assertAlmostEqual(max(p[1] for p in verts), 5.0)
        self.assertAlmostEqual(max(p[2] for p in verts), 2.6)
        # The surface is a dome, not a vertical semicircular entrance arch.
        self.assertTrue(all(z >= 0 for x,y,z in verts))
        self.assertTrue(all(0 <= idx < len(verts) for face in faces for idx in face))

    def test_sector_faces_point_outward_for_front_and_back_culling(self):
        verts, faces = ellipsoid_sector(7.4, 5.0, 2.6, 0, math.pi/2, 8, 4)
        a,b,c = (verts[i] for i in faces[0][:3])
        ab = tuple(b[i]-a[i] for i in range(3))
        ac = tuple(c[i]-a[i] for i in range(3))
        normal = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
        centroid = tuple((a[i]+b[i]+c[i])/3 for i in range(3))
        self.assertGreater(sum(normal[i]*centroid[i] for i in range(3)), 0)


class TowerTests(unittest.TestCase):
    def test_cut_corner_profile_is_octagonal_not_a_rectangular_box(self):
        profile = clipped_rectangle(2.4, 1.8, 0.2)
        self.assertEqual(len(profile), 8)
        self.assertNotIn((-1.2,-0.9), profile)
        self.assertIn((-1.0,-0.9), profile)
        self.assertIn((-1.2,-0.7), profile)


if __name__ == '__main__':
    unittest.main()
