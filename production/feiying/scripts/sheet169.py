import bpy, sys, numpy as np
a=sys.argv[sys.argv.index("--")+1:]; out=a[0]; files=a[1:]
ims=[bpy.data.images.load(f) for f in files]
for im in ims: im.scale(512,288)
cols=3; rows=(len(ims)+cols-1)//cols; buf=np.zeros((rows*288,cols*512,4),np.float32)
for i,im in enumerate(ims):
    r=rows-1-i//cols; c=i%cols
    buf[r*288:(r+1)*288,c*512:(c+1)*512]=np.array(im.pixels[:],np.float32).reshape(288,512,4)
s=bpy.data.images.new("s",cols*512,rows*288); s.pixels=buf.ravel(); s.filepath_raw=out; s.file_format='JPEG'; s.save()
