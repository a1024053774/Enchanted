"""RPC origin loss during an isolated recorder-store failure; no providers enabled."""
import runpy, sys, json, sqlite3, subprocess, os, signal, time, shutil
from pathlib import Path
out=Path(__file__).resolve().parent
label=sys.argv[1] if len(sys.argv)>1 else 'source-loss-06'
sys.argv=[str(out/'coverage-matrix-03.py'),label]
ctx=runpy.run_path(str(out/'coverage-matrix-03.py'))
root=ctx['root']; results=ctx['results']; rpc=ctx['rpc']; uid=ctx['uid']; now=ctx['now']; control=ctx['control'];save=ctx['save']
summary=json.loads((results/'summary.json').read_text()); ordinary=summary['cases'][2]['thread']
state=root/'userdata/a2a-gates/state.sqlite3'
with sqlite3.connect(state) as db:
 for table in ['user_inputs','user_input_ingress','user_input_events']:
  db.execute(f"CREATE TRIGGER t056_failure_{table} BEFORE INSERT ON {table} BEGIN SELECT RAISE(FAIL,'T056 isolated recorder unavailable'); END")
commands=[]
for name,origin in [('lost-explicit',None),('lost-derived','ui-derived')]:
 cmd=dict(type='thread.turn.interrupt',commandId=uid(),threadId=ordinary,createdAt=now())
 if origin: cmd['origin']=origin
 rpc(name,cmd);commands.append(cmd)
time.sleep(.4)
events=control('events');save('loss-domain-events',events)
matched=[event for event in events if event.get('commandId') in {cmd['commandId'] for cmd in commands}]
assert len(matched)==2,matched
assert all('origin' not in e['metadata'] and 'origin' not in e['payload'] for e in matched)
with sqlite3.connect(state) as db:
 count=db.execute('SELECT count(*) FROM user_inputs').fetchone()[0]
 absent=[db.execute('SELECT count(*) FROM user_input_ingress WHERE command_id=?',(cmd['commandId'],)).fetchone()[0] for cmd in commands]
assert absent==[0,0],absent
launch=json.loads((out/('server-'+label+'-launch.json')).read_text());pid=launch['pid']
identity=subprocess.check_output(['ps','-p',str(pid),'-o','pid=,lstart=,command='],text=True)
assert 'server-fixture-02.ts' in identity,identity
os.kill(pid,signal.SIGTERM)
for _ in range(100):
 try: os.kill(pid,0)
 except ProcessLookupError: break
 time.sleep(.1)
else: raise RuntimeError('fixture still running')
# Retain original fault database; recovery runs only on a complete copy.
copy=root.with_name(root.name+'-restart-copy')
shutil.copytree(root,copy)
(copy/'ready.json').unlink()
with sqlite3.connect(copy/'userdata/a2a-gates/state.sqlite3') as db:
 for table in ['user_inputs','user_input_ingress','user_input_events']: db.execute(f'DROP TRIGGER t056_failure_{table}')
env=launch['environment'];env['T056_ROOT']=str(copy)
log=(out/('server-'+label+'-restart.log')).open('x')
p=subprocess.Popen(launch['argv'],cwd=env['T056_FORK'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(out/('server-'+label+'-restart-launch.json')).write_text(json.dumps(dict(argv=launch['argv'],environment=env,pid=p.pid,root=str(copy)),indent=2)+'\n')
for _ in range(450):
 if (copy/'ready.json').exists():break
 if p.poll() is not None:raise RuntimeError('restart failed')
 time.sleep(.1)
else:raise TimeoutError('ready')
time.sleep(.5)
with sqlite3.connect(copy/'userdata/a2a-gates/state.sqlite3') as db:
 records=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
recovered=[value for value in records if value.get('source_ref',{}).get('command_id') in {cmd['commandId'] for cmd in commands}]
save('loss-after-restart-inputs',records)
report=dict(status='INCOMPLETE',commands=commands,persisted_events=matched,ingress_rows_before_restart=absent,inputs_before_restart=count,recovered_input_or_gap_count=len(recovered),expected='2 observed inputs recovered with authoritative origin, or gap records covering the unavailable sequence range',source_sequences=[e['sequence'] for e in matched],first_process_identity=identity,restart_pid=p.pid,limitation='All service/WS/SQLite/event-log layers are real. Failure is an INSERT trigger in this fixture gate DB only. Providers disabled; model turns 0.')
save('loss-summary',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
gaps=[value for value in records if value['form']=='gap']
assert len(recovered)==2 or all(any(value['content']['from_sequence']<=e['sequence']<=value['content']['through_sequence'] for value in gaps) for e in matched), 'T056 recovery contract violated: no input or gap coverage'
save('loss-oracle',dict(status='PASS',recovered_count=len(recovered),gaps=gaps))
