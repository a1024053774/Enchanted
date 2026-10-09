import datetime,json,os,runpy,shutil,signal,sqlite3,subprocess,sys,time
from pathlib import Path
out=Path(__file__).resolve().parent;fork=Path('/Users/luckye/Documents/Code/synara');label=sys.argv[1]
sys.argv=[str(out/'coverage-matrix-03.py'),label];c=runpy.run_path(str(out/'coverage-matrix-03.py'))
root=c['root'];save=c['save'];ordinary=c['ordinary'];revision=c['summary']['fork'];launch_path=out/('server-'+label+'-launch.json');launch=json.loads(launch_path.read_text(encoding='utf-8'))
assert launch['source_revision']==revision and not launch['tracked_status']
def rows(root):
 with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
  return [json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs ORDER BY rowid')], [dict(seq=r[0],type=r[1],details=json.loads(r[2])) for r in db.execute('SELECT seq,type,details FROM events ORDER BY seq')]
def stop_owned(path,process=None):
 data=json.loads(path.read_text(encoding='utf-8'));pid=data['pid'];ps=subprocess.check_output(['ps','-p',str(pid),'-o','lstart=,command='],text=True,env={**os.environ,'LC_ALL':'C'})
 assert 'server-fixture-61.ts' in ps
 stamp=datetime.datetime.strptime(ps.strip()[:24],'%a %b %d %H:%M:%S %Y').timestamp()
 assert abs(stamp-path.stat().st_mtime)<10
 os.kill(pid,signal.SIGTERM)
 if process is not None:process.wait(timeout=15)
 for _ in range(100):
  try:os.kill(pid,0)
  except ProcessLookupError:break
  time.sleep(.1)
 else:raise RuntimeError('Own fixture did not exit')
 return dict(pid=pid,identity=ps,terminated=True)
before,before_events=rows(root)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
 for table in ['user_inputs','user_input_ingress','user_input_events']:
  db.execute(f"CREATE TRIGGER t056_gap_failure_{table} BEFORE INSERT ON {table} BEGIN SELECT RAISE(FAIL,'T056 ordinary recorder outage'); END")
commands=[]
for name,origin in [('lost-explicit',None),('lost-derived','ui-derived')]:
 command=dict(type='thread.turn.interrupt',commandId=c['uid'](),threadId=ordinary,createdAt=c['now']())
 if origin:command['origin']=origin
 c['rpc'](name,command);commands.append(command)
time.sleep(.4);domain=c['control']('events');ids={v['commandId'] for v in commands};events=[e for e in domain if e.get('commandId') in ids]
assert len(events)==2 and all(e['type']=='thread.turn-interrupt-requested' for e in events)
assert all('origin' not in e['metadata'] and 'origin' not in e['payload'] for e in events)
after,after_events=rows(root);assert after==before and after_events==before_events
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
 ingress=[db.execute('SELECT count(*) FROM user_input_ingress WHERE command_id=?',(v['commandId'],)).fetchone()[0] for v in commands]
assert ingress==[0,0]
observer=c['gate']('events',task='t056')['user_input_observer'];assert observer['state']=='healthy',observer
save('gap-before-recovery',dict(source_revision=revision,commands=commands,domain_events=events,inputs=after,gate_events=after_events,ingress_counts=ingress,observer=observer))
cleanup=[stop_owned(launch_path)];stages=[];current=root
for stage in [1,2]:
 # Preserve the original failed store; both restarts use complete fresh copies.
 copy=root.with_name(root.name+f'-recovery-{stage}-68');shutil.copytree(current,copy);(copy/'ready.json').unlink()
 if stage==1:
  with sqlite3.connect(copy/'userdata/a2a-gates/state.sqlite3') as db:
   for table in ['user_inputs','user_input_ingress','user_input_events']:db.execute(f'DROP TRIGGER t056_gap_failure_{table}')
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip();assert head==revision
 status=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=fork,text=True);assert not status
 env=dict(launch['environment']);env.update(T056_ROOT=str(copy),HOME=str(copy/'os-home'),CODEX_HOME=str(copy/'codex-empty'),CLAUDE_CONFIG_DIR=str(copy/'claude-empty'),T056_SOURCE_REVISION=head,A2A_SYNARA_SLOT='t056-'+label+f'-restart-{stage}')
 log=out/f'server-{label}-recovery-{stage}-68.log';started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with log.open('x',encoding='utf-8') as stream:p=subprocess.Popen(launch['argv'],cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 path=out/f'server-{label}-recovery-{stage}-68-launch.json'
 with path.open('x',encoding='utf-8') as stream:json.dump(dict(argv=launch['argv'],cwd=str(fork),pid=p.pid,root=str(copy),environment=env,source_revision=head,tracked_status=status,started=started),stream,indent=2);stream.write('\n')
 for _ in range(450):
  if (copy/'ready.json').exists():break
  if p.poll() is not None:raise RuntimeError('Recovery fixture exited')
  time.sleep(.1)
 else:raise TimeoutError('Recovery ready')
 ready=json.loads((copy/'ready.json').read_text(encoding='utf-8'));assert ready['source_revision']==revision
 time.sleep(.4);records,gate_events=rows(copy)
 gaps=[v for v in records if v['form']=='gap'];assert len(gaps)==1,gaps
 gap=gaps[0];assert gap['target']['thread']==ordinary and gap['target']['attempt'] is None
 assert gap['target']['task'] is None and gap['target']['project']=='t056-project' and gap['certainty']=='observed'
 assert gap['content']['reason'] and all(gap['content']['from_sequence']<=e['sequence']<=gap['content']['through_sequence'] for e in events)
 assert not any(v['source_ref'].get('command_id') in ids for v in records)
 assert [v for v in records if v['form']!='gap']==before
 assert [e for e in gate_events if e['type']=='human_intervention']==[e for e in before_events if e['type']=='human_intervention']
 if stages:assert records==stages[0]['inputs'] and gate_events==stages[0]['gate_events']
 stages.append(dict(stage=stage,source_revision=head,launch=path.name,root=str(copy),inputs=records,gate_events=gate_events,gaps=gaps))
 save(f'gap-stage-{stage}',stages[-1])
 cleanup.append(stop_owned(path,p));current=copy
save('gap-oracle',dict(status='PASS',source_revision=revision,commands=commands,events=events,stages=stages,checks=['ordinary WS business accepted while input and ingress inserts fail','observer stays healthy','source not inferred','one gap covers unavailable sequence range','no derived intervention','second restart byte-for-byte field comparison no duplicates'],cleanup=cleanup,provider_enabled=False,new_model_turns=0))
print('PASS current frozen gap branch and two restarts',revision)
