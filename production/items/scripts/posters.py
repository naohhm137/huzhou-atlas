# Final renders → web posters (hero = default, close-up = "expanded").
import bpy, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; W, OUT = a[0], a[1]
s = bpy.context.scene.render.image_settings; s.file_format = 'WEBP'; s.quality = 80
for id_ in ["brush", "loom", "tea", "yishang", "dongwu", "nanxun"]:
    for k, suffix in ((1, ""), (2, "-detail")):
        img = bpy.data.images.load(f"{W}/renders/final/{id_}_{k}.jpg"); w, h = img.size; img.scale(1600, round(h * 1600 / w))
        img.save_render(f"{OUT}/{id_}{suffix}.webp")
print("POSTERS", sorted(os.listdir(OUT)))
