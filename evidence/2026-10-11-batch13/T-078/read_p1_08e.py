"""Read immutable 08e results and specific archived members; start no services."""
import argparse,json,tarfile
from pathlib import Path
BASE=Path('/Users/luckye/Documents/Code/a2a-wt-t078/evidence/2026-10-11-batch13/T-078')
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--raw-dir',type=Path,required=True);args=p.parse_args()
args.raw_dir.mkdir();m=BASE/'p1-materials-08e';i=json.loads((m/'input.json').read_bytes())
r={'status':'INCOMPLETE','scope':'Read-only 08e single-round evidence; pre-rebase feasibility only','argv':__import__('sys').argv,'real_vendor_model_turns':0}
try:
    c=json.loads((m/'continue/result.json').read_bytes());cleanup=json.loads((m/'cleanup/result.json').read_bytes())
    assert c['status']=='PASS' and cleanup['status']=='PASS' and cleanup['cli_exit_verdict']['reason']=='recorded_cli_exited'
    assert c['before_completion']['state']=='busy' and c['before_completion']['active']['dispatch']==c['dispatch']['dispatch']['id']
    assert c['after_completion']['state']=='idle' and c['after_completion']['active'] is None
    types=[e['type'] for e in c['events']]
    assert types.count('turn_start_signal')==types.count('turn_end_signal')==types.count('pane_idle')==1
    assert types.index('turn_start_signal')<types.index('turn_end_signal')<types.index('pane_idle')
    manifest=json.loads((BASE/'external-archive-73249ada8f364b0d8abea0bad2fcf29a.json').read_bytes())
    f=manifest['files'][0];arc=Path(f['archive']);assert manifest['status']=='PASS' and arc.stat().st_size==f['bytes']==8103787
    assert f['byte_readback']=='PASS' and f['local_original_removed'] and not Path(f['source']).exists()
    prefix=Path(i['root']).name
    with tarfile.open(arc) as t:
        def member(name):
            entry=t.getmember(name);assert entry.isfile() and entry.size<=5*1024*1024
            return t.extractfile(entry).read()
        hooks=[]
        for receipt in c['hook_receipts']:
            directory=prefix+'/'+str(Path(receipt['directory']).relative_to(i['root']))
            raw=member(directory+'/stdin.bin');done=json.loads(member(directory+'/finished.json'));v=json.loads(raw)
            assert done['exit_code']==0 and done['launch']==i['launch'] and v['session_id']==i['session']
            assert any(e['type']=='hook_received' and e['data']['raw_stdin'].encode()==raw for e in c['events'])
            name=v['hook_event_name'];(args.raw_dir/(name+'.stdin.bin')).write_bytes(raw)
            (args.raw_dir/(name+'.finished.json')).write_bytes(member(directory+'/finished.json'))
            assert member(directory+'/stderr.bin')==b''
            hooks.append(v)
        ups=next(h for h in hooks if h['hook_event_name']=='UserPromptSubmit');stop=next(h for h in hooks if h['hook_event_name']=='Stop')
        assert ups['prompt']==c['dispatch']['dispatch']['text'] and stop['stop_hook_active'] is False
        assert ups['prompt_id']==stop['prompt_id'] and ups['prompt_id']
        assert stop['last_assistant_message']=='P1_ACK '+(m/'nonce.txt').read_text()
        api=[json.loads(line) for line in member(prefix+'/api.jsonl').splitlines()]
        requests=[x for x in api if x['path']=='/v1/messages'];assert len(requests)==1
        body=requests[0]['body'];assert body['model']=='claude-haiku-5-5' and body['stream'] is True
        assert any(x['role']=='user' and any(part.get('type')=='text' and part.get('text')==ups['prompt'] for part in x['content']) for x in body['messages'])
        path=prefix+'/claude/projects/-'+i['root'].strip('/').replace('/','-')+'-repo/'+i['session']+'.jsonl'
        transcript=[json.loads(line) for line in member(path).splitlines()]
        summary=[x for x in transcript if x.get('subtype')=='stop_hook_summary'];assert len(summary)==1 and summary[0]['hookCount']==1
    r.update(status='PASS',code_revision=i['code_revision'],launch=i['launch'],session=i['session'],prompt_id=ups['prompt_id'],
             dispatch=c['dispatch']['dispatch'],hook_events=[h['hook_event_name'] for h in hooks],hook_exit_codes=[0,0],
             event_order=['turn_start_signal','turn_end_signal','pane_idle'],messages_requests=1,model_requested=body['model'],
             archive=str(arc),archive_bytes=f['bytes'],archive_byte_readback='Controller manifest PASS; worker verified size and specific raw member consistency',
             transcript_stop_hook_summary=summary[0],cleanup=cleanup['cli_exit_verdict'])
except Exception as error:
    import traceback
    r.update(error=repr(error),traceback=traceback.format_exc())
with args.output.open('x',encoding='utf-8') as f:json.dump(r,f,ensure_ascii=False,indent=2)
print(json.dumps({k:r.get(k) for k in ['status','code_revision','prompt_id','messages_requests','error']}));raise SystemExit(0 if r['status']=='PASS' else 1)
