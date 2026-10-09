import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from surface_maps import surface_maps


class MaterialMapsTests(unittest.TestCase):
    def test_normal_vectors_are_unit_length_and_glass_is_smooth(self):
        maps = surface_maps('glass', (0.1, 0.2, 0.3), 0.15, 128)
        normal = maps['normal'][..., :3] * 2 - 1
        np.testing.assert_allclose(np.linalg.norm(normal, axis=-1), 1, atol=1e-5)
        self.assertLess(float(np.max(np.abs(normal[..., :2]))), 0.01)

    def test_stone_has_micro_relief_and_seamless_edges(self):
        maps = surface_maps('stone', (0.4, 0.4, 0.4), 0.8, 128)
        self.assertGreater(float(maps['normal'][..., 0].std()), 0.003)
        for pixels in maps.values():
            self.assertTrue(np.isfinite(pixels).all())
            self.assertGreaterEqual(float(pixels.min()), 0)
            self.assertLessEqual(float(pixels.max()), 1)
            np.testing.assert_allclose(pixels[0], pixels[-1], atol=1e-5)
            np.testing.assert_allclose(pixels[:, 0], pixels[:, -1], atol=1e-5)

    def test_wood_has_directional_grain_and_glaze_preserves_low_roughness(self):
        wood = surface_maps('wood', (0.3, 0.2, 0.1), 0.7, 128)['color'][..., 0]
        self.assertGreater(float(np.abs(np.diff(wood, axis=1)).mean()),
                           float(np.abs(np.diff(wood, axis=0)).mean()) * 2)
        glaze = surface_maps('glaze', (0.5, 0.6, 0.4), 0.18, 128)
        self.assertLess(float(glaze['roughness'][..., 0].max()), 0.22)


if __name__ == '__main__':
    unittest.main()
