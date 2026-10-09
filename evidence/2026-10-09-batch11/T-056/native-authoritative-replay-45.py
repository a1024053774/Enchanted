import json,os,sqlite3,subprocess,shutil,time
from pathlib import Path
out=Path(__file__).resolve().parent;fork=Path('/Users/luckye/Documents/Code/synara')
prior=json.loads((out/'native-authoritative-replay-34.json').read_text());source=Path(prior['copy_root'])
native=json.loads((out/'native-frozen-15/answer-oracle.json').read_text())
question=json.loads((out/'native-frozen-15/question-observation.json').read_text())
root=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t056-native-authoritative-replay-45');root.mkdir(mode=0o700)
(root/'userdata/a2a-gates').mkdir(parents=True)
for name in ['os-home','codex-empty','claude-empty']: (root/name).mkdir(mode=0o700)
shutil.copy2(source/'userdata/settings.json',root/'userdata/settings.json')
for relative in ['userdata/state.sqlite','userdata/a2a-gates/state.sqlite3']:
 with sqlite3.connect(source/relative) as src,sqlite3.connect(root/relative) as dst:src.backup(dst)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:
 db.execute('DROP TRIGGER user_inputs_no_delete')
 rows=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs')]
 removed=[r for r in rows if r['target']['request']==native['native_question_id'] and r['target']['thread']==native['thread']]
 assert len(removed)==1
 for row in removed:
  db.execute('DELETE FROM user_inputs WHERE id=?',(row['id'],))
  db.execute('DELETE FROM user_input_events WHERE event_id=?',(row['source_ref']['event_id'],))
 db.execute('UPDATE user_input_checkpoint SET sequence=0 WHERE id=1')
env={k:v for k,v in os.environ.items() if k in ['PATH','SHELL','LANG','LC_ALL']};env.update(HOME=str(root/'os-home'),CODEX_HOME=str(root/'codex-empty'),CLAUDE_CONFIG_DIR=str(root/'claude-empty'),A2A_SYNARA_SLOT='t056-native-replay-45',T056_ROOT=str(root),T056_FORK=str(fork))
argv=['./a2a/scripts/bun','run',str(out/'server-fixture-30.ts')]
with (out/'server-native-replay-45.log').open('x') as stream:p=subprocess.Popen(argv,cwd=fork,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
with (out/'server-native-replay-45-launch.json').open('x') as stream:json.dump(dict(argv=argv,pid=p.pid,root=str(root),environment=env),stream,indent=2)
for _ in range(450):
 if (root/'ready.json').exists():break
 if p.poll() is not None:raise RuntimeError('Native replay server failed')
 time.sleep(.1)
else:raise TimeoutError('Native replay ready')
time.sleep(.4)
with sqlite3.connect(root/'userdata/a2a-gates/state.sqlite3') as db:rows=[json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs')]
records=[r for r in rows if r['target']['request']==native['native_question_id'] and r['target']['thread']==native['thread']]
assert len(records)==1 and records[0]['form']=='answer' and records[0]['content']==['蓝色 Ω 用户哨兵']
assert records[0]['target']['project']=='t056-project' and records[0]['certainty']=='observed'
assert records[0]['source_ref']['event_id']==removed[0]['source_ref']['event_id']
assert question['has_native_questions']
with (out/'native-authoritative-replay-45.json').open('x') as stream:json.dump(dict(status='PASS',fork=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip(),source_root=str(source),copy_root=str(root),expected_answers=['蓝色 Ω 用户哨兵'],records=records,source_model_cli='0.162.0',new_model_turns=0,limits=['真实 provider 事件来自 c7 原生问答；最终候选仅重放，未新跑原生 turn。','原生 journal 未修改；只在隔离复制库模拟输入记录器中断。']),stream,ensure_ascii=False,indent=2)
print('PASS final candidate consumes real native question and answer')
