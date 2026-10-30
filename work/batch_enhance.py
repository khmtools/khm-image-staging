"""Download + enhance a list of [url,[w,h]] into OUT dir. Usage: batch_enhance.py batch.json OUTDIR"""
import sys, json, io, os, re, requests, cv2, numpy as np
from PIL import Image, ImageFilter
from concurrent.futures import ProcessPoolExecutor
TARGET=1000; MODEL=os.environ.get("SR_MODEL","/home/claude/models/FSRCNN_x4.pb")
items=json.load(open(sys.argv[1])); OUT=sys.argv[2]; os.makedirs(OUT,exist_ok=True)
_sr=None
def sr():
    global _sr
    if _sr is None:
        _sr=cv2.dnn_superres.DnnSuperResImpl_create(); _sr.readModel(MODEL); _sr.setModel("fsrcnn",4)
    return _sr
def fname(u): return u.split('?')[0].rsplit('/',1)[1]
def work(it):
    u=it[0]; fn=fname(u); out=os.path.join(OUT, re.sub(r'\.[A-Za-z]+$','',fn)+'.jpg')
    if os.path.exists(out): return u,fn,out,'skip'
    try:
        im=Image.open(io.BytesIO(requests.get(u,timeout=60).content))
        if im.mode in ("RGBA","LA","P"):
            im=im.convert("RGBA"); bg=Image.new("RGBA",im.size,(255,255,255,255)); bg.alpha_composite(im); im=bg
        im=im.convert("RGB")
        if max(im.size)<TARGET:
            a=cv2.cvtColor(np.array(im),cv2.COLOR_RGB2BGR)
            while max(a.shape[:2])<TARGET: a=sr().upsample(a)
            im=Image.fromarray(cv2.cvtColor(a,cv2.COLOR_BGR2RGB))
        im.thumbnail((int(TARGET*.94),int(TARGET*.94)),Image.LANCZOS)
        im=im.filter(ImageFilter.UnsharpMask(radius=1.2,percent=60,threshold=2))
        c=Image.new("RGB",(TARGET,TARGET),"white"); c.paste(im,((TARGET-im.width)//2,(TARGET-im.height)//2))
        c.save(out,"JPEG",quality=88,optimize=True,progressive=True); return u,fn,out,'ok'
    except Exception as e: return u,fn,None,'err:'+str(e)[:80]
if __name__=='__main__':
    with ProcessPoolExecutor(6) as ex: res=list(ex.map(work,items,chunksize=4))
    json.dump(res,open(OUT+'.result.json','w'))
    import collections; print(collections.Counter(r[3][:3] for r in res))
