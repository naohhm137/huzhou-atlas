import bpy, sys, os
a=sys.argv[sys.argv.index("--")+1:]; d=a[0]; out=a[1]; idx=[int(x) for x in a[2].split(',')]
imgs=[bpy.data.images.load(os.path.join(d,"f%02d.jpg"%i)) for i in idx]
w,h=imgs[0].size; cols=len(idx)
big=bpy.data.images.new("s",w*cols,h)
import numpy as np
buf=np.zeros((h,w*cols,4),dtype=np.float32)
for c,im in enumerate(imgs):
    p=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4); buf[:,c*w:(c+1)*w]=p
big.pixels=buf.ravel(); big.filepath_raw=out; big.file_format='JPEG'; big.save()
