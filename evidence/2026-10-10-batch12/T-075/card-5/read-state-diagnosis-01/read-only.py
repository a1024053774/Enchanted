import json,sqlite3,sys
from pathlib import Path
p=Path(sys.argv[1]).resolve()
result={"python":sys.version,"sqlite":sqlite3.sqlite_version,"database":str(p),"exists":p.is_file(),"sidecars":[str(x) for x in p.parent.glob(p.name+"-*")]}
try:
    with sqlite3.connect(p.as_uri()+"?mode=ro",uri=True) as db:
        result["tables"]=[row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
except sqlite3.Error as exc:
    result["error"]=str(exc)
    print(json.dumps(result,ensure_ascii=False))
    raise SystemExit(1)
print(json.dumps(result,ensure_ascii=False))
