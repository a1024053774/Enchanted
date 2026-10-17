"""Save numeric process graphs and full commands for the owned tree only."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time


def descendants(graph, root):
    found={root}
    while True:
        more=found|{pid for pid,row in graph.items() if row['ppid'] in found}
        if more==found:return found
        found=more


def graph_rows(text):
    result={}
    for line in text.splitlines():
        pid,ppid,pgid,tpgid=map(int,line.split())
        if pid in result:raise ValueError('duplicate_ps_PID')
        result[pid]={'ppid':ppid,'pgid':pgid,'tpgid':tpgid}
    return result


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def snapshot(owner,folder,graph_result=None,reason=None):
    """No env reads or signals. A vanished child is recorded, never adopted."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    env={**os.environ,'LC_ALL':'C','LANG':'C'}
    value={'status':'INCOMPLETE','reason':reason,'observed_at':datetime.now(timezone.utc).isoformat(),
        'wall_ns':time.time_ns(),'processes':{},'signals_sent':[],'key_writes':0}
    def run(argv):return subprocess.run(argv,capture_output=True,text=True,timeout=5,env=env)
    result=graph_result if graph_result is not None else run(['/bin/ps','-axo','pid=,ppid=,pgid=,tpgid='])
    # These bytes are durable before parsing or attempting per-process probes.
    (folder/'graph.stdout.bin').write_bytes(result.stdout.encode())
    (folder/'graph.stderr.bin').write_bytes(result.stderr.encode())
    save(folder/'started.json',{'observed_at':value['observed_at'],'graph_exit':result.returncode,
                              'scope':'global numeric IDs only; full commands only for owned tree/original identities'})
    try:
        if result.returncode or result.stderr.strip():raise ValueError('process_graph_read_failed')
        graph=graph_rows(result.stdout);daemon=owner['processes']['daemon']['pid']
        current=descendants(graph,daemon)
        expected={v['pid'] for k,v in owner['processes'].items() if not k.endswith('_api')}
        value.update(daemon=daemon,current_descendants=sorted(current),expected_managed=sorted(expected),
                     extra=sorted(current-expected),missing=sorted(expected-current))
        complete=True
        for pid in sorted(current|{v['pid'] for v in owner['processes'].values()}):
            probe=run(['/bin/ps','-ww','-p',str(pid),'-o','pid=,ppid=,pgid=,tpgid=,lstart=,command='])
            (folder/(str(pid)+'.stdout.bin')).write_bytes(probe.stdout.encode())
            (folder/(str(pid)+'.stderr.bin')).write_bytes(probe.stderr.encode())
            row={'exit':probe.returncode,'observed_at':datetime.now(timezone.utc).isoformat()}
            if probe.returncode==1 and not probe.stdout.strip():
                row['status']='vanished_before_full_identity';complete=False
            else:
                if probe.returncode or probe.stderr.strip():raise ValueError('process_detail_read_failed:'+str(pid))
                cells=probe.stdout.strip().split(None,9)
                if len(cells)!=10 or int(cells[0])!=pid:raise ValueError('process_detail_parse_failed:'+str(pid))
                name=run(['/bin/ps','-p',str(pid),'-o','comm='])
                (folder/(str(pid)+'.comm.stdout.bin')).write_bytes(name.stdout.encode())
                (folder/(str(pid)+'.comm.stderr.bin')).write_bytes(name.stderr.encode())
                chain=[pid];seen={pid}
                while chain[-1]!=daemon and graph.get(chain[-1],{}).get('ppid') in graph:
                    parent=graph[chain[-1]]['ppid']
                    if parent in seen:raise ValueError('process_chain_cycle')
                    chain.append(parent);seen.add(parent)
                row.update(pid=pid,ppid=int(cells[1]),pgid=int(cells[2]),tpgid=int(cells[3]),
                    lstart=' '.join(cells[4:9]),command=cells[9],name=name.stdout.strip(),
                    parent_chain=chain,creator_evidence='current PPID/lstart; not a historical fork trace')
                if graph.get(pid)!={key:row[key] for key in ['ppid','pgid','tpgid']}:
                    row['graph_changed_during_detail']=True;complete=False
                if name.returncode or name.stderr.strip():row['name_probe_exit']=name.returncode;complete=False
            value['processes'][str(pid)]=row
        value['status']='PASS' if complete else 'INCOMPLETE'
    except Exception as error:
        import traceback
        value.update(error=repr(error),traceback=traceback.format_exc())
    save(folder/'result.json',value)
    return value
