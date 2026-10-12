# Convert generated layers and final renders into web assets.
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index("--") + 1:]; W, OUT = a[0], a[1]
def save(img, path, fmt, quality=82):
    img.filepath_raw = path; img.file_format = fmt
    s = bpy.context.scene.render.image_settings; s.file_format = fmt; s.quality = quality
    if fmt == 'PNG': s.color_mode = 'RGBA'; s.compression = 90
    img.save_render(path)
def load(path, width):
    img = bpy.data.images.load(path); w, h = img.size
    img.scale(width, round(h * width / w)); return img
# sky: plain webp
save(load(f"{W}/layers/sky.png", 1920), f"{OUT}/sky.webp", 'WEBP', 80)
# mist: white-on-black, blended with `screen`
save(load(f"{W}/layers/mist.png", 1920), f"{OUT}/mist.webp", 'WEBP', 80)
# pines: black silhouette on white → ink-teal colour with alpha = 1 - luminance
img = load(f"{W}/layers/pines.png", 1920); w, h = img.size
px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(-1, 4)
lum = px[:, :3].mean(1); alpha = np.clip((1 - lum - 0.04) / 0.92, 0, 1)
px[:, 0], px[:, 1], px[:, 2], px[:, 3] = 0.018, 0.034, 0.034, alpha
out = bpy.data.images.new("pines_alpha", w, h, alpha=True)
out.pixels.foreach_set(px.ravel())
save(out, f"{OUT}/pines.webp", 'WEBP', 82)
# posters (loading + WebGL fallback)
for n in ["01_初见", "02_塔身", "03_塔中塔", "04_斗栱", "05_石塔", "06_守护"]:
    save(load(f"{W}/renders/final/{n}.jpg", 1600), f"{OUT}/poster-{n[:2]}.webp", 'WEBP', 78)
print("WEBASSETS", sorted(os.listdir(OUT)))
