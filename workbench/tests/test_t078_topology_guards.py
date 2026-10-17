"""Exercise the actual identity/topology gate with recorded process transports."""
import argparse
import copy
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
import t078_raw_retention as raw

SOURCE=Path(__file__).resolve().parents[2]
BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'


def run(output,only=None):
    owner=raw.read_json(BASE/'09c-attempt-2-materials-02/owner.json')
    checks=[]
    class Transport:
        def identities(self):return copy.deepcopy(owner['processes'])
        def topology(self):raise ValueError('actual topology sentinel')
    # Requirements come from #364: a scene label cannot remove the check.
    for scene in ([] if only=='diagnostics' else ['09C','REHEARSAL']):
        value={**owner,'scene':scene};calls=[]
        def receipts(arg):calls.append('receipt')
        try:
            with patch.object(raw,'validate_owner_receipts',receipts):raw.check_identities(value,Transport())
        except ValueError as error:assert str(error)=='actual topology sentinel'
        else:raise AssertionError('topology bypass:'+scene)
        assert calls==['receipt']
        checks.append('receipt/topology always reached:'+scene)
    if only is None:
        value=copy.deepcopy(owner);value['processes'].pop('executor_api')
        class Eight:
            def identities(self):return value['processes']
            def topology(self):raise AssertionError('eight processes reached topology')
        try:
            with patch.object(raw,'validate_owner_receipts',lambda value:None):raw.check_identities(value,Eight())
        except ValueError as error:assert str(error)=='nine_owned_processes_required'
        else:raise AssertionError('eight processes admitted')
        checks.append('eight processes rejected before any topology transport')
    with tempfile.TemporaryDirectory(prefix='t078-topology-unit-',dir='/private/tmp') as tmp:
        value={**owner,'root':str(Path(tmp).resolve())}
        graph={item['pid']:value['process_graph'][name] for name,item in value['processes'].items()}
        graph[2000000000]={'ppid':value['processes']['ideation_cli']['pid'],'pgid':2000000000,'tpgid':-1}
        graph_text=''.join(f"{pid} {r['ppid']} {r['pgid']} {r['tpgid']}\n" for pid,r in graph.items())
        def ps(argv,**kwargs):
            if '-axo' in argv:return subprocess.CompletedProcess(argv,0,graph_text,'')
            pid=int(argv[argv.index('-p')+1])
            if argv[-1]=='comm=':return subprocess.CompletedProcess(argv,0,'/usr/bin/false\n','')
            row=graph[pid];ident=next((r for r in value['processes'].values() if r['pid']==pid),None)
            command=ident['command'] if ident else '/usr/bin/false --synthetic-unknown-child'
            started=ident['started'] if ident else 'Fri Oct 16 21:06:14 2026'
            return subprocess.CompletedProcess(argv,0,f"{pid} {row['ppid']} {row['pgid']} {row['tpgid']} {started} {command}\n",'')
        with patch.object(raw.subprocess,'run',ps):
            try:raw.NativeRuntime(value).topology()
            except ValueError as error:assert str(error)=='unexpected_daemon_descendants'
            else:raise AssertionError('unknown child accepted')
        root=Path(tmp)/'topology-diagnostics'
        records=list(root.glob('*/result.json'))
        assert len(records)==1,'failure must persist raw ps before rejection'
        result=raw.read_json(records[0]);assert result['extra']==[2000000000] and result['missing']==[]
        assert (records[0].parent/'graph.stdout.bin').read_bytes()==graph_text.encode()
        assert result['processes']['2000000000']['command']=='/usr/bin/false --synthetic-unknown-child'
        assert result['processes']['2000000000']['parent_chain'][:2]==[2000000000,value['processes']['ideation_cli']['pid']]
        checks.append('unknown child rejected with raw graph/full command/chain saved')
        # Persist the fixture originals before its temporary root disappears.
        import shutil
        shutil.copytree(root,output/'diagnostic-fixture-originals')
    return checks


def metadata_cases(output):
    from t078_owner_receipt_fixture import write_owner_receipts
    results=[]
    labels=['green','scene','source','claim','target','receipt','daemon','target-pids','api-ready','api-role','api-stage','api-protocol','api-model','api-argv','manifest-session','manifest-cli','manifest-shell','role-argv','missing-process','PID-reuse','reordered-labels']
    for label in labels:
        with tempfile.TemporaryDirectory(prefix='t078-owner-metadata-',dir='/private/tmp') as tmp:
            root=Path(tmp).resolve();(root/'roles/ideation').mkdir(parents=True);(root/'roles/executor').mkdir()
            value={'root':str(root),'target_binding':{k:'fixture-'+k for k in ['task_id','attempt_id','session_id','spec_rev','thread_id','workspace','launch']},'processes':{}}
            value['target_binding']['fence']=1;write_owner_receipts(value,root/'receipts')
            def alter(path,change):
                item=raw.read_json(path);change(item);path.write_text(json.dumps(item),encoding='utf-8')
            ready=Path(value['stage_a'])/'readiness.json';api=root/'roles/ideation/api-ready.json'
            manifest=Path(value['roles']['ideation']['manifest'])
            if label=='scene':value['scene']='REHEARSAL'
            if label=='source':value['source_revision']='unbound'
            if label=='claim':value['claim_binding']['fence']=2
            if label=='target':value['target_binding']['attempt_id']='foreign'
            if label=='receipt':value['processes']['daemon']['started']='reused'
            if label=='daemon':alter(ready,lambda x:x['daemon'].update(pid=17))
            if label=='target-pids':alter(ready,lambda x:x['target_process'].update(leader=17))
            if label=='api-ready':alter(api,lambda x:x.update(pid=17))
            if label in ['api-role','api-stage','api-protocol','api-model']:
                key={'api-role':'role','api-stage':'stage','api-protocol':'protocol','api-model':'model_turns'}[label]
                change=lambda x:x.update({key:'bad'})
                alter(api,change);alter(ready,lambda x:change(x['api_processes'][0]['ready']))
            if label=='api-argv':alter(ready,lambda x:x['api_processes'][0].update(argv=['/fixture/wrong','--extra']))
            if label=='manifest-session':alter(manifest,lambda x:x.update(session='foreign'))
            if label=='manifest-cli':alter(manifest,lambda x:x['cli'].update(started='reused'))
            if label=='manifest-shell':alter(manifest,lambda x:x.update(shell_pid=17))
            if label=='role-argv':alter(manifest,lambda x:x['cli'].update(command='/fixture/wrong'))
            if label=='missing-process':value['processes'].pop('executor_cli')
            runtime=type('Transport',(),{'identities':lambda self:copy.deepcopy(value['processes']),
                'topology':lambda self:None})()
            if label=='PID-reuse':runtime.identities=lambda:{**value['processes'],'daemon':{**value['processes']['daemon'],'started':'reused'}}
            topology=[]
            if label=='reordered-labels':runtime.topology=lambda:topology.append('called')
            error=None
            try:raw.check_identities(value,runtime,list(reversed(value['processes'])) if label=='reordered-labels' else None)
            except (ValueError,KeyError) as ex:error=str(ex)
            assert (error is None)==(label in ['green','reordered-labels']),(label,error)
            if label=='reordered-labels':assert topology==['called']
            results.append({'case':label,'status':'PASS','observed_error':error,'scope':'real receipt files, explicit identity transport'})
    raw.save(output/'metadata-cases.json',results);return len(results)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--only',choices=['diagnostics']);p.add_argument('--source-file',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','scene_starts':0,'key_writes':0,'signals_sent':[],'scope':'recorded real owner, explicit ps transport fixture; not live process proof'}
    try:
        if a.source_file:
            import importlib.util
            global raw
            spec=importlib.util.spec_from_file_location('raw_known_bad',a.source_file)
            raw=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw)
            result['loaded_raw_source']=str(a.source_file.resolve())
        result.update(checks=run(a.output,a.only),metadata_cases=metadata_cases(a.output),status='PASS')
    except Exception as error:
        import traceback
        result.update(error=repr(error),traceback=traceback.format_exc())
    raw.save(a.output/'result.json',result);print(json.dumps(result,ensure_ascii=False));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
