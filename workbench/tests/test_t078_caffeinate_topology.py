"""Replay original probe ps through NativeRuntime.topology; path lookup is explicit transport."""
import argparse
import copy
import ctypes
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import traceback
from unittest.mock import patch
import t078_raw_retention as raw

SOURCE=Path(__file__).resolve().parents[2];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
PROBE=BASE/'09c-topology-probe-run-01'
SAMPLE=PROBE/'turn-01/permission-wait/sample-0001'


def cases(module,output):
    from t078_process_tree import graph_rows
    original=raw.read_json(PROBE/'probe-original-role.json')
    graph=graph_rows((SAMPLE/'graph.stdout.bin').read_text())
    details=raw.read_json(SAMPLE/'result.json')['processes']
    baseline=graph_rows((PROBE/'idle-02/sample-0001/graph.stdout.bin').read_text())
    expected={key:baseline[v['pid']] for key,v in original['processes'].items()}
    labels=['recorded-real-ps','duration-1','duration-299','parent-shell','parent-daemon','parent-target','wrong-path','named-caffeinate-other-program',
            'flag-w','flag-s','flag-d','extra-arg','timeout-301','timeout-zero','timeout-negative','timeout-fraction',
            'two-same-role','other-process','missing-role','missing-target','helper-PID-reused','helper-parent-race']
    results=[]
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='t078-caff-unit-',dir='/private/tmp') as tmp:
            owner={**copy.deepcopy(original),'root':str(Path(tmp).resolve()),'process_graph':copy.deepcopy(expected)}
            current=copy.deepcopy(graph);rows=copy.deepcopy(details);executable='/usr/bin/caffeinate';reads={}
            child=rows['12761'];cli=owner['processes']['ideation_cli']['pid']
            if label.startswith('parent-'):
                parent={'parent-shell':'ideation_shell','parent-daemon':'daemon','parent-target':'target_leader'}[label]
                current[12761]['ppid']=owner['processes'][parent]['pid'];child['ppid']=current[12761]['ppid']
            if label=='wrong-path':executable='/private/tmp/other/caffeinate'
            if label=='named-caffeinate-other-program':executable='/bin/sleep'
            if label in ['flag-w','flag-s','flag-d']:child['command']='caffeinate -i -'+label[-1]+' 300'
            if label=='extra-arg':child['command']+=' -d'
            if label.startswith('duration-'):child['command']='caffeinate -i -t '+label.split('-')[1]
            if label.startswith('timeout-'):
                n={'timeout-301':'301','timeout-zero':'0','timeout-negative':'-1','timeout-fraction':'1.5'}[label]
                child['command']='caffeinate -i -t '+n
            if label=='two-same-role':
                current[2000000000]=copy.deepcopy(current[12761]);rows['2000000000']={**copy.deepcopy(child),'pid':2000000000}
            if label=='other-process':
                current[2000000000]={'ppid':cli,'pgid':cli,'tpgid':cli}
                rows['2000000000']={**copy.deepcopy(child),'pid':2000000000,'command':'/usr/bin/other --new'}
            if label in ['missing-role','missing-target']:
                target=owner['processes']['ideation_cli' if label=='missing-role' else 'target_leader']['pid'];current.pop(target)
            def ps(argv,**kwargs):
                if '-axo' in argv:
                    text=''.join(f"{pid} {r['ppid']} {r['pgid']} {r['tpgid']}\n" for pid,r in current.items())
                    return subprocess.CompletedProcess(argv,0,text,'')
                pid=int(argv[argv.index('-p')+1]);row=rows[str(pid)];reads[pid]=reads.get(pid,0)+1
                if argv[-1]=='comm=':return subprocess.CompletedProcess(argv,0,row['name']+'\n','')
                if argv[-1]=='pid=,lstart=,command=':
                    return subprocess.CompletedProcess(argv,0,f"{pid} {row['lstart']} {row['command']}\n",'')
                start=row['lstart'];ppid=row['ppid']
                if label=='helper-PID-reused' and pid==12761 and reads[pid]>1:start='Fri Oct 16 23:59:59 2026'
                if label=='helper-parent-race' and pid==12761 and reads[pid]>1:ppid=1
                return subprocess.CompletedProcess(argv,0,f"{pid} {ppid} {row['pgid']} {row['tpgid']} {start} {row['command']}\n",'')
            error=None;allowed=None
            with patch.object(module.subprocess,'run',ps),patch.object(module.NativeRuntime,'executable_path',return_value=executable,create=True):
                try:allowed=module.NativeRuntime(owner).topology()
                except ValueError as ex:error=str(ex)
            accepted=error is None
            expected_accept=label in ['recorded-real-ps','duration-1','duration-299']
            result={'case':label,'expected_accept':expected_accept,'accepted':accepted,'error':error,
                'allowed_helpers':allowed,'kernel_path_transport':'fixture /usr/bin/caffeinate from main #367; actual proc_pidpath test is separate',
                'recorded_source':str(SAMPLE),'keys':0,'signals':0}
            raw.save(output/(label+'.json'),result);results.append(result)
            assert accepted==expected_accept,(label,error)
            if accepted:
                assert len(allowed)==1 and allowed[0]['pid']==12761 and allowed[0]['role']=='ideation'
                assert owner['processes']==original['processes'] and 12761 not in {v['pid'] for v in owner['processes'].values()}
    return results


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--source-file',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False);result={'status':'INCOMPLETE','scope':__doc__,'scene_starts':0}
    try:
        module=raw
        if a.source_file:
            spec=importlib.util.spec_from_file_location('old_raw',a.source_file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result.update(checks=cases(module,a.output),status='PASS')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    raw.save(a.output/'result.json',result);print(json.dumps({'status':result['status'],'checks':len(result.get('checks',[])),'error':result.get('error'),'scene_starts':0}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
