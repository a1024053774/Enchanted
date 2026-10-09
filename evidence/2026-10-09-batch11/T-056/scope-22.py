import runpy,sys,json,sqlite3,time,urllib.request
from pathlib import Path
out=Path(__file__).resolve().parent;sys.argv=[str(out/'coverage-matrix-03.py'),'scope-22'];ctx=runpy.run_path(str(out/'coverage-matrix-03.py'))
root=ctx['root'];rpc=ctx['rpc'];uid=ctx['uid'];now=ctx['now'];save=ctx['save'];worker=ctx['worker'];ordinary=ctx['ordinary'];origin=ctx['origin']
def status():
 with urllib.request.urlopen(origin+'/api/a2a?thread='+worker) as r:return json.load(r)
before=status();assert before['user_input_observer']['state']=='healthy';save('observer-before',before)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
 db.execute("CREATE TRIGGER t056_nonmanaged_failure BEFORE INSERT ON user_inputs WHEN json_extract(NEW.data,'$.target.attempt') IS NULL BEGIN SELECT RAISE(FAIL,'T056 only non-managed input writes fail'); END")
cmd=dict(type='thread.turn.interrupt',commandId=uid(),threadId=ordinary,createdAt=now());rpc('nonmanaged-failure',cmd);time.sleep(.3)
middle=status();save('observer-after-nonmanaged',middle);assert middle['user_input_observer']['state']=='healthy'
# This metadata event is not an input. No managed input write fails or occurs.
rpc('managed-noninput-event',dict(type='thread.meta.update',commandId=uid(),threadId=worker,title='仅元数据 Ω'))
time.sleep(.3);after=status();save('observer-after-managed-noninput',after)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
 saved=[json.loads(row[0]) for row in db.execute('SELECT data FROM user_inputs ORDER BY rowid')]
save('scope-oracle',dict(status='INCOMPLETE',expected='healthy: only a non-managed input sink failed; metadata event is not a managed input',observed=after['user_input_observer'],inputs=saved,managed_target=worker,failed_input_target=ordinary,fork='c7aaaa433 + scope fix working diff'))
assert after['user_input_observer']['state']=='healthy','non-managed recorder failure latched managed fail-closed on an unrelated metadata event'

save('scope-green',dict(status='PASS',nonmanaged_failure_only=True,managed_metadata_healthy=True,observer=after['user_input_observer']))
