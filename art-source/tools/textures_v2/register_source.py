from pathlib import Path
import json,shutil,sys
from PIL import Image
from catalog import WORK,JOBS

key,source=sys.argv[1:3]
job=next(job for job in JOBS if job['key']==key)
target=WORK/'sources'/job['arena']/(key+'.png')
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(source,target)
with Image.open(target) as image:
    meta={'key':key,'source':str(target),'native_size':list(image.size),'native_mode':image.mode,'generator':'built-in image_gen','requested_size':job['size_px']}
target.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps({'saved':key,'native_size':meta['native_size']}))
