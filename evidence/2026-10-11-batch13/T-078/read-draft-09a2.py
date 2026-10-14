"""Read preserved 09A-2 facts; no CLI, socket, signal, key or cleanup operation."""
import argparse, json, shutil, sqlite3, tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
base=Path(__file__).resolve().parent;m=base/'p1-materials-09a2'
approval=json.loads((m/'approval.json').read_text(encoding='utf-8'));root=Path(approval['input']['root'])
out=args.output;out.mkdir()
run=json.loads((m/'continue-esc/result.json').read_text(encoding='utf-8'))
frame=json.loads((m/'continue-esc/electron/before-user-release.json').read_text(encoding='utf-8'))
with sqlite3.connect((root/'state/state.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
    events=[dict(seq=r[0],time=r[1],type=r[2],data=json.loads(r[3])) for r in db.execute('SELECT seq,time,type,data FROM orchestration_events ORDER BY seq')]
    inputs=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs')]
raw=(root/'state/traces'/approval['input']['launch']/'pty.raw').read_bytes()
first=run['first_dispatch']['dispatch'];second=run['second_dispatch']['dispatch']
before=run['window_before_esc']['offset'];after=frame['offset']
assert run['after_esc']['active'] is None and run['after_esc']['interrupted'] and run['after_esc']['user_draft']
assert first['text'].split('\n',1)[1].encode() in raw[before:after]
assert second['text'].split('\n',1)[1].encode() not in raw[:after]
assert first['text'].split('\n',1)[1] in frame['terminal']
api=[]
for line in (root/'api.jsonl').read_text(encoding='utf-8').splitlines():
    item=json.loads(line)
    if item['path']!='/v1/messages':continue
    texts=[part['text'] for message in item['body']['messages'] if message['role']=='user' for part in message['content'] if part.get('type')=='text']
    api.append({'at':item['at'],'last_user_text':texts[-1],'model':item['body']['model'],'stream':item['body']['stream']})
assert [v['last_user_text'] for v in api]==[first['text'],first['text']+second['text'],first['text']+second['text']]
assert [e['data']['text'] for e in events if e['type']=='paste_intent']==[first['text'],second['text']]
assert len([e for e in events if e['type']=='paste_written' and e['data']['dispatch']==second['id']])==1
assert len([e for e in events if e['type']=='turn_submitted' and e['data']['dispatch']==second['id']])==1
assert [e['data']['data'] for e in events if e['type']=='terminal_input_write_intent']==['\x1b']
hook=[]
for directory in sorted((root/'hooks').iterdir()):
    if not (directory/'stdin.bin').exists():continue
    payload=json.loads((directory/'stdin.bin').read_bytes());finished=json.loads((directory/'finished.json').read_bytes())
    dest=out/('hook-'+payload['prompt_id']);dest.mkdir()
    for n in ['stdin.bin','finished.json','stdout.bin','stderr.bin']:
        if (directory/n).exists():shutil.copyfile(directory/n,dest/n)
    hook.append({'directory':str(directory),'payload':payload,'finished':finished})
assert sorted((v['payload']['prompt'],v['finished']['exit_code']) for v in hook)==sorted([(first['text'],0),(first['text']+second['text'],1)])
archive=json.loads((base/'external-archive-93611737c0674a7aa55d1fcf3863a0b0.json').read_text(encoding='utf-8'))['files'][0]
with tarfile.open(archive['archive']) as arc:
    member=root.name+'/state/traces/'+approval['input']['launch']+'/pty.raw'
    assert raw==arc.extractfile(member).read()
selected=[e for e in events if e['type'] in ['paste_intent','paste_written','turn_submitted','terminal_input_write_intent','terminal_input_written','claude_submission_retired','user_queue_release','turn_start_signal','pane_stop_intent','pane_exit','daemon_stopped']]
report={'status':'PASS','scope':'Readback confirms restoration/append failure, not a product acceptance PASS','argv':__import__('sys').argv,
        'root':str(root),'code_revision':approval['input']['code_revision'],'launch':approval['input']['launch'],
        'before_esc_output_offset':before,'before_release_output_offset':after,'pty_output_bytes':len(raw),
        'api_requests':api,'events':selected,'user_inputs':inputs,'hook_receipts':hook,'after_esc':run['after_esc'],
        'declared_second_pty_writes':['\x1b[200~'+second['text']+'\x1b[201~','\r'],
        'draft_flag_source':'panes.userInput sets userDraft=true for every nonbinary input, including Esc; it does not read the CLI draft.',
        'release_source':'releaseByUser clears userDraft/interrupted/state metadata then drain writes second paste+CR; no PTY clear key.',
        'original_archive':archive,'pty_archive_byte_readback':'PASS','cleanup':json.loads((m/'cleanup/result.json').read_text(encoding='utf-8'))}
(out/'pty.raw').write_bytes(raw);(out/'after-esc-output.bin').write_bytes(raw[before:after])
with (out/'result.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'PASS','api_requests':len(api),'user_actions':len(inputs),'restored_nonce_output_range':[before,after],
                  'request2_equals_exact_concatenation':True,'second_hook_exit':1,'api_error':json.loads((root/'api-error.json').read_bytes())},ensure_ascii=False))
