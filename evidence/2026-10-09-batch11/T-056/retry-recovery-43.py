import json,os,sqlite3,sys,time,subprocess,shutil
from pathlib import Path
out=Path(__file__).resolve().parent;fork=Path('/Users/luckye/Documents/Code/synara')
label=sys.argv[1];launch=json.loads((out/('server-'+label+'-launch.json')).read_text());original=Path(launch['root']);evidence=out/label
checks=json.loads((evidence/'retry-oracle.json').read_text())['checks'];commands=[c['input']['commandId'] for c in checks]
before=json.loads((evidence/'retry-gate-events.json').read_text());allchecks=[]
for mode in ['receipt','gap']:
 root=original.with_name(original.name+'-'+mode+'-recovery-43');root.mkdir()
 (root/'userdata/a2a-gates').mkdir(parents=True)
 for name in ['os-home','codex-empty','claude-empty','control']: (root/name).mkdir(mode=0o700)
 shutil.copy2(original/'userdata/settings.json',root/'userdata/settings.json')
 for source in (original/'userdata').glob('*.sqlite'):
  with sqlite3.connect(source) as src,sqlite3.connect(root/'userdata'/source.name) as dst:src.backup(dst)
 state=root/'userdata/a2a-gates/state.sqlite3'
 with sqlite3.connect(original/'userdata/a2a-gates/state.sqlite3') as src,sqlite3.connect(state) as db:src.backup(db)
 with sqlite3.connect(state) as db:
  # Model observer outage only on copies. The authoritative native journal remains untouched.
  db.execute('DROP TRIGGER user_inputs_no_delete')
  db.execute('DROP TRIGGER events_no_delete')
  if mode=='gap':db.execute('DROP TRIGGER user_input_ingress_no_delete')
  for command in commands:
   input_ids=[r[0] for r in db.execute("SELECT id FROM user_inputs WHERE json_extract(data,'$.source_ref.command_id')=?",(command,))]
   for input_id in input_ids:db.execute("DELETE FROM events WHERE type='human_intervention' AND json_extract(details,'$.input_id')=?",(input_id,))
   db.execute("DELETE FROM user_inputs WHERE json_extract(data,'$.source_ref.command_id')=?",(command,))
   db.execute('DELETE FROM user_input_events WHERE event_id=?',('rpc:'+command,))
   if mode=='gap':db.execute('DELETE FROM user_input_ingress WHERE command_id=?',(command,))
  first=min(e['sequence'] for c in checks for e in c['events'])
  db.execute('UPDATE user_input_checkpoint SET sequence=? WHERE id=1',(first-1,))
 env=dict(launch['environment']);env.update(T056_ROOT=str(root),HOME=str(root/'os-home'),CODEX_HOME=str(root/'codex-empty'),CLAUDE_CONFIG_DIR=str(root/'claude-empty'),A2A_SYNARA_SLOT='t056-'+label+'-'+mode)
 argv=launch['argv'];log=out/('server-'+label+'-'+mode+'-recovery-43.log')
 with log.open('x') as stream:p=subprocess.Popen(argv,cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 with (out/('server-'+label+'-'+mode+'-recovery-43-launch.json')).open('x') as stream:json.dump(dict(argv=argv,root=str(root),pid=p.pid,environment=env),stream,indent=2)
 for _ in range(450):
  if (root/'ready.json').exists():break
  if p.poll() is not None:raise RuntimeError('Recovery server failed')
  time.sleep(.1)
 else:raise TimeoutError('Recovery ready')
 time.sleep(.4)
 with sqlite3.connect(state) as db:
  rows=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
  interventions=[json.loads(r[0]) for r in db.execute("SELECT details FROM events WHERE type='human_intervention'")]
 if mode=='receipt':
  for case in checks:
   matches=[r for r in rows if r['source_ref'].get('command_id')==case['input']['commandId']]
   assert len(matches)==1,matches
   recovered=dict(matches[0]);source=dict(recovered['source_ref'])
   event_id=source.pop('event_id',None);sequence=source.pop('source_sequence',None)
   assert any(e['eventId']==event_id and e['sequence']==sequence for e in case['events'])
   recovered['source_ref']=source
   assert recovered==case['records'][0],recovered
 else:
  for case in checks:
   matches=[r for r in rows if r['form']=='gap' and r['target']['thread']==case['input']['threadId']]
   assert len(matches)==1 and matches[0]['content']['from_sequence']<=min(e['sequence'] for e in case['events'] if e['type'] in ['thread.message-edit-resend-requested','thread.checkpoint-revert-requested']),matches
   assert not [r for r in rows if r['source_ref'].get('command_id')==case['input']['commandId']]
 # Output-loss copy removes both transactional outputs. Recovery with a receipt
 # recreates the one intervention; without a receipt, it emits only a gap.
 expected=len([e for e in before if e['type']=='human_intervention'])-(1 if mode=='gap' else 0)
 assert len(interventions)==expected,(mode,len(interventions),expected)
 allchecks.append(dict(mode=mode,status='PASS',root=str(root),pid=p.pid,inputs=rows,interventions=interventions))
with (evidence/'retry-recovery-oracle-43.json').open('x') as stream:json.dump(dict(status='PASS',checks=allchecks,source_journal='real WS commands; no provider; copied native SQLite unchanged'),stream,ensure_ascii=False,indent=2)
print('PASS receipt replay and missing-receipt gaps')
