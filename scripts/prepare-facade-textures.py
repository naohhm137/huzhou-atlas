"""Rectify selected, unobscured storefront patches from the credited local photo.

No people, whole streets or fabricated PBR normal maps are projected onto the
model. Coordinates are measured in the 1824x1368 reference display, then scaled
to the supplied local image. CC BY-SA attribution is in the adjacent manifest.
"""
from pathlib import Path
import sys
from PIL import Image

root = Path(sys.argv[1])
source = root / 'public/media/city-yishang-street.jpg'
target = root / 'assets/blender/textures'
target.mkdir(parents=True, exist_ok=True)
image = Image.open(source).convert('RGB')
sx, sy = image.width / 1824, image.height / 1368
patches = {
    # UL, LL, LR, UR: upper window band, sign fascia, pastry display.
    'yishang-moli-upper': ((1024, 320), [0, 118, 0, 324, 646, 381, 634, 213]),
    'yishang-moli-sign': ((1024, 256), [0, 361, 0, 515, 680, 566, 674, 426]),
    'yishang-moli-display': ((512, 256), [341, 743, 338, 812, 498, 803, 499, 742]),
}
for name, (size, quad) in patches.items():
    points = tuple(n * (sx if index % 2 == 0 else sy) for index, n in enumerate(quad))
    patch = image.transform(size, Image.Transform.QUAD, points, Image.Resampling.BICUBIC)
    patch.save(target / (name + '.png'))
    print(name, size)
