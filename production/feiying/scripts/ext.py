import bpy, sys, os
args = sys.argv[sys.argv.index("--")+1:]
src, outdir, n = args[0], args[1], int(args[2])
scn = bpy.context.scene
se = scn.sequence_editor_create()
strip = (se.strips if hasattr(se,'strips') else se.sequences).new_movie("v", src, 1, 1)
total = strip.frame_final_duration
scn.frame_start, scn.frame_end = 1, total
scn.render.resolution_x, scn.render.resolution_y = strip.elements[0].orig_width//2, strip.elements[0].orig_height//2
scn.render.resolution_percentage = 100
scn.render.image_settings.file_format = 'JPEG'
print("TOTAL", total, strip.elements[0].orig_width, strip.elements[0].orig_height, scn.render.fps)
for i in range(n):
    f = 1 + int(i*(total-1)/(n-1))
    scn.frame_set(f)
    scn.render.filepath = os.path.join(outdir, "f%02d.jpg" % i)
    bpy.ops.render.render(write_still=True)
