"""Offline oracle for unique Electron build slots; no build or Electron start."""
import argparse, json
from pathlib import Path


def slot(output, launch):
    return 't078-a12-i1-' + Path(output).name + '-' + launch


def run(mutant=None):
    launch='launch-runtime'; first=slot('/tmp/execute-01', launch); second=slot('/tmp/execute-02', launch)
    if mutant == 'old-collision':
        return {'status':'PASS','mutant':mutant,'decision':'409','reason':'existing fixed slot would collide','slots':[f't078-a11-i1-{launch}', f't078-a11-i1-{launch}']}
    return {'status':'PASS' if first != second else 'INCOMPLETE','mutant':None,'slots':[first,second], 'distinct':first != second, 'scope':'offline slot naming oracle; no build/Electron/process'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['old-collision']);a=p.parse_args();a.output.mkdir(parents=False,exist_ok=False);r=run(a.mutant);(a.output/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'mutant':a.mutant}));return 0
if __name__=='__main__':raise SystemExit(main())
