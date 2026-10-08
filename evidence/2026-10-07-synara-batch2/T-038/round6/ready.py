#!/usr/bin/env python3
import json,sys,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent;label,url=sys.argv[1:3];out=root/(label+'.json');assert not out.exists()
started=time.time();attempts=[];success=False
for i in range(90):
    try:
        with urllib.request.urlopen(url,timeout=2) as r: status=r.status
        attempts.append({'status':status,'at':time.time()});success=status==200
        if success:break
    except Exception as e:attempts.append({'error':str(e),'at':time.time()})
    time.sleep(1)
out.write_text(json.dumps({'url':url,'success':success,'seconds':time.time()-started,'attempts':attempts},indent=2)+'\n',encoding='utf-8');print(label,success)
raise SystemExit(0 if success else 1)
