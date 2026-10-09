import json,sqlite3,sys,time,uuid,subprocess,shutil,os,signal,datetime as dt
from pathlib import Path
out=Path(__file__).resolve().parent;results=out/'extras-16';results.mkdir();fork=Path('/Users/luckye/Documents/Code/synara')
launch_path=out/'server-source-loss-14-restart-launch.json';launch=json.loads(launch_path.read_text());root=Path(launch['root']);summary=json.loads((out/'source-loss-14/summary.json').read_text());thread=summary['cases'][2]['thread'];question=summary['cases'][4]['request']
def save(n,v):(results/(n+'.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def control(operation,**args):
 key=str(uuid.uuid4());(root/'control'/f'{key}.request.json').write_text(json.dumps(dict(operation=operation,**args)));p=root/'control'/f'{key}.result.json'
 for _ in range(450):
  if p.exists():
   v=json.loads(p.read_text())
   if not v.get('pending'):assert v['ok'],v;return v['result']
  time.sleep(.1)
 raise TimeoutError(operation)
def inputs():
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:return [json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
text='长负载 Ω '+('汉字🧪'*8192)
cmd=dict(type='thread.turn.start',commandId=str(uuid.uuid4()),threadId=thread,dispatchOrigin='user',message=dict(messageId=str(uuid.uuid4()),role='user',text=text,attachments=[dict(type='assistant-selection',id='selection_16',assistantMessageId=question,text='引用的原生消息片段'*300)]),runtimeMode='approval-required',interactionMode='default',createdAt=dt.datetime.now(dt.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'))
save('input',cmd);control('command',command=cmd);control('command',command=cmd);time.sleep(.5)
matched=[v for v in inputs() if v['target']['message']==cmd['message']['messageId']]
assert len(matched)==1 and matched[0]['text']==text
assert matched[0]['content']==dict(attachments=[dict(id='selection_16',type='assistant-selection',message_id=question)]),matched
save('payload-oracle',dict(status='PASS',input_characters=len(text),expected_attachment_refs=[dict(id='selection_16',type='assistant-selection',message_id=question)],inputs=matched))
before=inputs();save('before-replay',before)
pid=launch['pid'];identity=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=,command='],text=True);assert 'server-fixture-02.ts' in identity
os.kill(pid,signal.SIGTERM)
for _ in range(100):
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(.1)
else:raise RuntimeError('still running')
copy=root.with_name(root.name+'-replay');shutil.copytree(root,copy);(copy/'ready.json').unlink();env=launch['environment'];env['T056_ROOT']=str(copy)
log=(out/'server-extras-restart-16.log').open('x');p=subprocess.Popen(launch['argv'],cwd=env['T056_FORK'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(out/'server-extras-restart-16-launch.json').write_text(json.dumps(dict(argv=launch['argv'],environment=env,pid=p.pid,root=str(copy)),indent=2)+'\n')
for _ in range(450):
 if (copy/'ready.json').exists():break
 if p.poll() is not None:raise RuntimeError('restart failed')
 time.sleep(.1)
else:raise TimeoutError('ready')
root=copy;time.sleep(.5);after=inputs();save('after-replay',after);assert before==after,'replay changed input IDs/data/count or duplicated a gap'
save('summary',dict(status='PASS',large_payload=True,attachments_reference_only=True,duplicate_command=True,replay_and_live_overlap=True,replay_same_records=True,root=str(root),pid=p.pid,limits='Actual engine/domain recorder/SQLite with native provider disabled. Attachment canonical event is supplied via the internal engine; does not test file upload UI.'))
print('PASS large payload/attachment references/duplicate command/exact replay',p.pid)
