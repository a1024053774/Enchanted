"""Read archived raw API/hooks/PTY and a disposable SQLite+WAL copy, no native starts."""
import argparse,json,sqlite3,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
BASE=Path(__file__).resolve().parent
checks=[];fixtures=[]
def require(name,condition,facts):
    checks.append({'name':name,'status':'PASS' if condition else 'INCOMPLETE','observed':facts})
    if not condition:raise AssertionError(name)
for label,block in [('p1-materials-09a3r2',False),('p1-materials-09a3r2-block',True)]:
    m=BASE/label;declared=json.loads((m/'input.json').read_bytes());run=json.loads((m/'continue-esc/result.json').read_bytes())
    if block:
        cleanup=json.loads((m/'cleanup-recovery-154/result.json').read_bytes());archive=Path(cleanup['archive'])
        require(label+'-recovery-scope',cleanup['status']=='PASS' and cleanup['signals_sent']==[{'pid':48954,'signal':'SIGTERM'}]
                and cleanup['api_exit_confirmed'] and cleanup['root_removed'] and cleanup['byte_readback']=='PASS' and cleanup['slots_removed']==[],
                {k:cleanup[k] for k in ['status','signals_sent','api_exit_confirmed','root_removed','byte_readback','slots_removed']})
    else:
        cleanup=json.loads((m/'cleanup/result.json').read_bytes());manifest=json.loads((BASE/'external-archive-20323dd797a64b74b90e9633065b15df.json').read_bytes())
        require(label+'-cleanup-and-archive',cleanup['status']=='PASS' and len(manifest['files'])==1 and manifest['files'][0]['byte_readback']=='PASS',{'cleanup':cleanup['status'],'archive_files':manifest['files']})
        archive=Path(manifest['files'][0]['archive'])
    prefix=Path(declared['root']).name
    with tarfile.open(archive) as arc:
        names=set(arc.getnames())
        def data(name):return arc.extractfile(prefix+'/'+name).read()
        def obj(name):return json.loads(data(name))
        require(label+'-raw-binding',obj('input.json')==declared and run['input']==declared and run['status']=='PASS',{'revision':declared['code_revision'],'launch':declared['launch'],'session':declared['session']})
        api=[json.loads(line) for line in data('api.jsonl').decode('utf-8').splitlines()]
        requests=[v for v in api if v['path']=='/v1/messages'];nonce1=(m/'nonce.txt').read_text();nonce2=(m/'nonce-2.txt').read_text()
        require(label+'-api-count',len(requests)==(1 if block else 2) and prefix+'/api-error.json' not in names,{'messages':len(requests),'count_tokens':sum(v['path']=='/v1/messages/count_tokens' for v in api),'api_error':prefix+'/api-error.json' in names})
        if not block:
            text=[part['text'] for message in requests[1]['body']['messages'] if message['role']=='user' for part in message['content'] if part.get('type')=='text'][-1]
            require(label+'-second-exact-input',text=='⟦主控 #2⟧\n'+nonce2 and nonce1 not in text,{'last_user_text':text})
        hooks=[]
        for name in sorted(names):
            if name.startswith(prefix+'/hooks/') and name.endswith('/finished.json'):
                directory=name.removesuffix('/finished.json');done=json.loads(arc.extractfile(name).read());payload=json.loads(arc.extractfile(directory+'/stdin.bin').read())
                hooks.append({'directory':directory,'event':payload['hook_event_name'],'exit_code':done['exit_code'],'payload':payload,'stdout':arc.extractfile(directory+'/stdout.bin').read().decode('utf-8')})
        require(label+'-real-hook-sequence',len(hooks)==(2 if block else 3) and all(v['exit_code']==0 for v in hooks),{'events':[v['event'] for v in hooks],'exits':[v['exit_code'] for v in hooks]})
        ups=[v for v in hooks if v['event']=='UserPromptSubmit'];first=next(v for v in ups if nonce1 in v['payload']['prompt'] and nonce2 not in v['payload']['prompt']);second=next(v for v in ups if nonce2 in v['payload']['prompt'])
        require(label+'-prompt-epochs',first['payload']['prompt_id']!=second['payload']['prompt_id'],{'first':first['payload']['prompt_id'],'second':second['payload']['prompt_id']})
        if block:
            output=json.loads(second['stdout']);require(label+'-concatenation-block',nonce1 in second['payload']['prompt'] and output['decision']=='block' and not any(v['event']=='Stop' for v in hooks),{'prompt':second['payload']['prompt'],'stdout':output})
        else:
            stop=next(v for v in hooks if v['event']=='Stop');require(label+'-matched-stop',stop['payload']['prompt_id']==second['payload']['prompt_id'],{'stop_prompt_id':stop['payload']['prompt_id']})
        with tempfile.TemporaryDirectory(prefix='t078-readback-db-',dir='/tmp') as temporary:
            dbpath=Path(temporary)/'state.sqlite3'
            for suffix in ['', '-wal','-shm']:
                name='state/state.sqlite3'+suffix
                if prefix+'/'+name in names:(Path(str(dbpath)+suffix)).write_bytes(data(name))
            db=sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True)
            events=[{'seq':row[0],'type':row[1],'data':json.loads(row[2])} for row in db.execute('SELECT seq,type,data FROM orchestration_events WHERE launch=? ORDER BY seq',(declared['launch'],))]
            inputs=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs')];db.close()
        declarations=[v for v in inputs if v.get('content',{}).get('action')=='queue-release'];release=[v for v in events if v['type']=='user_queue_release']
        require(label+'-declaration-binding',len(declarations)==len(release)==1 and declarations[0]['text']=='用户声明输入框已空'
                and declarations[0]['content']['declaration']==release[0]['data']['declaration'] and release[0]['data']['declaration']['interruption']==run['after_esc']['interruption'],{'declaration':declarations[0],'release':release[0]})
        clear=[v for v in inputs if v.get('content',{}).get('data')=='\x03'];require(label+'-control-action',len(clear)==(0 if block else 1) and all(v['form']=='action' for v in clear),{'ctrl_c_records':clear})
        require(label+'-retired-before-release',any(v['type']=='claude_submission_retired' and v['data']['reason']=='user-esc' and v['seq']<release[0]['seq'] for v in events),{'interruption':run['after_esc']['interruption']})
        if not block:
            empty=run['empty_editor_observation'];raw=data('state/traces/'+declared['launch']+'/pty.raw')
            require(label+'-empty-observation-and-bytes',empty['frame']['empty'] and empty['snapshot']['input_generation']==2 and (m/'continue-esc/cleared-draft-pty.bin').read_bytes()==raw[:empty['pty_highwater']],{'empty':empty['frame']['empty'],'highwater':empty['pty_highwater'],'input_generation':empty['snapshot']['input_generation']})
            require(label+'-idle-once',len([v for v in events if v['type']=='pane_idle'])==1 and run['after_completion']['state']=='idle',{'pane_idle_count':sum(v['type']=='pane_idle' for v in events),'final_state':run['after_completion']['state']})
        require(label+'-automation-provenance',run['automation']['source']=='test-simulated-user' and run['automation']['approved_by']=='executor',{'source':run['automation']['source'],'approved_by':run['automation']['approved_by'],'approval_ref':run['automation']['approval_ref']})
        fixtures.append({'label':label,'archive':str(archive),'archive_bytes':archive.stat().st_size,'archive_members':len(names),'source_revision':declared['code_revision'],'root_exists':Path(declared['root']).exists(),'status':'PASS'})
r={'status':'PASS','scope':'Worker raw readback, not a fresh-context independent reviewer; archive originals untouched, SQLite/WAL read via disposable copy','checks':checks,'fixtures':fixtures,'real_model_turns':0,'new_starts':0,'block_old_manifest_files':len(json.loads((BASE/'external-archive-3fc9ebfa7b8b4183a45aa58f2bd16dff.json').read_bytes())['files'])}
(args.output/'result.json').open('x',encoding='utf-8').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'PASS','checks':len(checks),'fixtures':fixtures,'new_starts':0},ensure_ascii=False))
