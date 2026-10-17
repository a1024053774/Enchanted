"""Read the owned scene's current process tree; never signal or send input."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import time
import traceback

BASE=Path(__file__).resolve().parent.parent
OWNER=BASE/'09c-attempt-2-materials-02/owner.json'
ROOT='/private/tmp/t078-2-09c-run-iznfrv18'


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def run(folder,name,argv):
    result=subprocess.run(argv,capture_output=True,text=True,timeout=5,env={**os.environ,'LC_ALL':'C','LANG':'C'})
    save(folder/(name+'.json'),{'argv':argv,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
         'observed_at':datetime.now(timezone.utc).isoformat()})
    if result.returncode or result.stderr.strip():raise RuntimeError({'step':name,'exit':result.returncode,'stderr':result.stderr})
    return result.stdout


def sample(folder,owner):
    folder.mkdir()
    raw=run(folder,'graph-raw',['/bin/ps','-axo','pid=,ppid=,pgid=,tpgid='])
    graph={}
    for line in raw.splitlines():
        pid,ppid,pgid,tpgid=map(int,line.split());graph[pid]={'ppid':ppid,'pgid':pgid,'tpgid':tpgid}
    daemon=owner['processes']['daemon']['pid'];desc={daemon}
    while True:
        expanded=desc|{pid for pid,row in graph.items() if row['ppid'] in desc}
        if expanded==desc:break
        desc=expanded
    managed={v['pid'] for k,v in owner['processes'].items() if not k.endswith('_api')}
    details={}
    for pid in sorted(desc|{v['pid'] for v in owner['processes'].values()}):
        if pid not in graph:
            details[str(pid)]={'status':'absent at graph read'};continue
        raw=run(folder,'process-'+str(pid),['/bin/ps','-ww','-p',str(pid),'-o','pid=,ppid=,pgid=,tpgid=,lstart=,command='])
        cells=raw.strip().split(None,9)
        if len(cells)!=10:raise ValueError('full process identity parse failed')
        comm=run(folder,'name-'+str(pid),['/bin/ps','-p',str(pid),'-o','comm=']).strip()
        chain=[pid];seen={pid}
        while chain[-1]!=daemon and graph.get(chain[-1],{}).get('ppid') in graph:
            parent=graph[chain[-1]]['ppid']
            if parent in seen:raise ValueError('process cycle')
            chain.append(parent);seen.add(parent)
        details[str(pid)]={'pid':int(cells[0]),'ppid':int(cells[1]),'pgid':int(cells[2]),'tpgid':int(cells[3]),
            'lstart':' '.join(cells[4:9]),'name':comm,'command':cells[9],'argv':shlex.split(cells[9]),
            'current_parent_chain':chain,'creator_claim':'current PPID only; no historical fork event recorded'}
    value={'status':'OBSERVED','observed_at':datetime.now(timezone.utc).isoformat(),'daemon':daemon,
       'expected_managed':sorted(managed),'current_descendants':sorted(desc),'extra':sorted(desc-managed),
       'missing':sorted(managed-desc),'original_graph':owner['process_graph'],'details':details,
       'scope':'current snapshot only; does not reconstruct missing failure-time ps','signals_sent':[],'key_writes':0}
    save(folder/'summary.json',value);return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','historical_failure_topology':'NOT_RECORDED','classification':'UNKNOWN; no allowlist change',
            'signals_sent':[],'key_writes':0,'SQLite_reads':0}
    try:
        owner=json.loads(OWNER.read_bytes());assert owner['root']==ROOT
        result['samples']=[]
        for index in range(2):
            if index:time.sleep(.1)
            result['samples'].append(sample(args.output/('sample-'+str(index+1)),owner))
        result['status']='PASS'
        result['scope']='current process evidence captured; legitimacy and historical membership remain to be reviewed'
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    save(args.output/'result.json',result)
    print(json.dumps({k:result[k] for k in ['status','classification','historical_failure_topology','signals_sent','key_writes']}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
