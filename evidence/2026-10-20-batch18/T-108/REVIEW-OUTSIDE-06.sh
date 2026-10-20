#!/bin/zsh
# T-108 第六轮独立审查补证：仅本地假 API，不读取登录凭据，不调用真实模型。
# 在沙箱外由执行主控运行；本 reviewer 只检查脚本，不启动 Electron；完整入口主控原件另在报告中核对。
# 运行：zsh evidence/2026-10-20-batch18/T-108/REVIEW-OUTSIDE-06.sh
# 可选参数：源仓库、依赖目录、内置盘 Electron dist。
set -eu
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
SOURCE=${1:-/Users/luckye/Documents/Code/a2a-wt-t108}
DEPENDENCIES=${2:-/Users/luckye/Documents/Code/a2a/workbench/node_modules}
ELECTRON_DIST=${3:-/Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist}
REVIEW_RUN=$(mktemp -d /private/tmp/t108-review-outside-06-XXXXXX)
export REVIEW_RUN SOURCE DEPENDENCIES ELECTRON_DIST
print -r -- "本次独立临时目录：$REVIEW_RUN"
/usr/bin/python3 -B - <<'PY'
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile

assert sys.version_info[:2] == (3, 9), '本脚本要求 Python 3.9'
revision = 'ee17cddf8c146ffb8cdaaa7d942ac610811cb915'
root = Path(os.environ['REVIEW_RUN']).resolve(strict=True)
source = Path(os.environ['SOURCE']).resolve(strict=True)
dependencies = Path(os.environ['DEPENDENCIES']).resolve(strict=True)
dist = Path(os.environ['ELECTRON_DIST']).resolve(strict=True)
assert not str(dist).startswith('/Volumes/'), 'Electron 必须在内置盘'
assert (dist/'version').read_text(encoding='utf-8').strip() == '43.4.1'
assert (dist/'Electron.app/Contents/MacOS/Electron').is_file()
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('GIT_', 'A2A_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))
       and k not in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE')}
env.update(LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0',
           GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
archive = subprocess.check_output(['git', '-C', str(source), 'archive', revision, 'workbench'], env=env)
candidate = root/'candidate'
candidate.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
    members = tar.getmembers()
    assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
    assert not any(m.islnk() for m in members)
    tar.extractall(candidate, members=[m for m in members if not m.issym()])
    # 仓库的 Git hook 链接展开成普通文件；不新建任何符号链接。
    for member in members:
        if member.issym():
            path = candidate/member.name
            target = (path.parent/member.linkname).resolve(strict=True)
            assert candidate in target.parents
            path.write_bytes(target.read_bytes())
            path.chmod(member.mode)
shutil.copytree(dependencies, candidate/'workbench/node_modules', symlinks=False)
for helper in (candidate/'workbench/node_modules/node-pty/prebuilds').glob('darwin-*/spawn-helper'):
    helper.chmod(0o755)
assert not any(path.is_symlink() for path in candidate.rglob('*'))
# 本脚本仅复跑冻结候选的无模型完整入口；历轮异常反例、确认后撤权/改输入/未知对照与三个变异的本轮结果见第六轮报告。
# 此脚本不读取真实登录凭据、不重跑已批准的真实模型回合，也不能替代地图 0 问题条件。
# git archive 没有 .git。仅把测试的版本来源替换成已指定的冻结 SHA；
# 产品、业务断言、原生 CLI、Electron 驱动和假 API 逻辑全部保持原文。
runner = candidate/'workbench/tests/run_t108_native_e2e.py'
text = runner.read_text(encoding='utf-8')
old = "        revision=run(['git','rev-parse','HEAD']).strip()"
assert text.count(old) == 1
runner.write_text(text.replace(old, '        revision='+repr(revision)), encoding='utf-8')
(root/'manager-home').mkdir()
env.update(HOME=str(root/'manager-home'), TMPDIR='/private/tmp',
           ELECTRON_OVERRIDE_DIST_PATH=str(dist))
command = ['/usr/bin/python3', '-B', str(runner), '--summary', str(root/'native-e2e.json'),
           '--electron-dist', str(dist)]
metadata = {'candidate': revision, 'source': str(source), 'archive_copy': str(candidate),
            'command': command, 'model_calls_expected': 0, 'vendor_calls_expected': 0,
            'harness_change': '仅 git archive 的版本来源；无产品改动；符号链接展开为文件'}
(root/'run.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
# 先跑当前候选的信号合同；完整入口仍必须独立通过。
focused = ['node', str(candidate/'workbench/tests/test_t108_questions.mjs'), str(root/'questions.json')]
with (root/'questions.stdout').open('xb') as out, (root/'questions.stderr').open('xb') as err:
    focused_result = subprocess.run(focused, cwd=candidate, env=env, stdout=out, stderr=err, timeout=120)
assert focused_result.returncode == 0
# 独立时序反例：原生确认在最后一个预设按键前到达；正常晚到对照应成功。
# 不改产品，只在临时副本增加审查夹具；两者都保存输出，不用失败冒充通过。
probe_results = []
probe = candidate/'workbench/tests/review05-early-native-confirmation.mjs'
probe.write_text("// Contract from T-108 and installed CLI hook samples. Real signal entry, SQLite,\n// PTY write boundary; supplied process identity is not a live CLI proof.\n// Failures: missing/stale/auxiliary fields, duplicate answer, changed input,\n// failed recorder/write, early state release, root completion swallowed.\nimport assert from 'node:assert/strict';\nimport { mkdtempSync, writeFileSync } from 'node:fs';\nimport { OrchestrationStore } from '../src/store.ts';\nimport { Panes } from '../src/panes.ts';\nimport { agentState } from '../src/sidebar.ts';\n\nconst output=process.argv[2];\nconst root=mkdtempSync('/private/tmp/t108-question-contract-');\nconst store=new OrchestrationStore(root), panes=new Panes(root,store,{},()=>{});\nconst record={id:'launch',thread:'thread',task:'task',project:'project',attempt:null,role:'controller',preset:'ideation',\n  session:'native',cli:'Claude Code',turn_limit:1,worktree:root};\nstore.launch(record);\nconst dispatch=store.register(record.id,'Ask region.');\nconst writes=[],inputs=[];\nconst pane={record,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,\n  stopInProgress:false,active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null},\n  claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,\n  userDraft:false,inputGeneration:0,pty:{write:data=>writes.push(data)}};\npanes.panes.set('thread',pane);\nconst questions=[{question:'选择发布区域？',header:'区域',options:[{label:'南区',description:'南部'},{label:'北区',description:'北部'}],multiSelect:false}];\nconst base={session_id:'native',prompt_id:'prompt',cwd:root,transcript_path:root+'/native.jsonl',tool_name:'AskUserQuestion',tool_use_id:'toolu_sentinel'};\nconst signal=(event,extra={})=>panes.signal('launch',JSON.stringify({...base,hook_event_name:event,...extra}),new Date().toISOString());\nconst state=()=>agentState({...panes.status('thread'),lifecycle:'running'},store.read(),root);\nconst report={status:'INCOMPLETE',scope:'real signal/SQLite; supplied PTY and runtime identity',model_turns:0,checks:[]};\ntry {\n store.event('turn_submitted',{id:'submission'},record);\n await signal('UserPromptSubmit',{prompt:dispatch.text});\n await signal('PreToolUse',{tool_input:{questions}});\n let guards=0,answerError;\n try {await panes.answerQuestion('launch','launch:toolu_sentinel',['北区'],async(...args)=>inputs.push(args),async()=>{\n   if(++guards===4) await signal('PostToolUse',{tool_input:{questions,answers:{'选择发布区域？':'北区'}},tool_response:{questions,answers:{'选择发布区域？':'北区'}}});\n });}catch(error){answerError=String(error);}\n report.answer_error=answerError;report.answer_inputs=inputs.length;report.pty_keys=[...writes];\n report.question=panes.questions('launch')[0];report.observed=state();\n let nextInputError;\n try {await panes.userInput('launch','next sentinel', {request_id:'next',sequence:2},async()=>{},async()=>{});} catch(error){nextInputError=String(error);}\n report.next_input_error=nextInputError;report.all_pty_keys=[...writes];\n report.events=store.read().map(e=>({type:e.type,data:e.data}));\n assert.equal(report.question.status,'answered');assert.equal(report.answer_inputs,1);\n assert.deepEqual(report.pty_keys,['\\x1b[B','\\r'],'Native confirmation must stop further selection keys');\n assert.equal(answerError,undefined,'Native confirmed the valid answer; original answer request must succeed');\n assert.equal(nextInputError,undefined,'Confirmed answer cannot poison future terminal input');\n report.status='PASS';\n} catch(error) {report.error=String(error);report.stack=error.stack;}\nfinally {store.close();report.retained_fixture=root;writeFileSync(output,JSON.stringify(report,null,2)+'\\n',{flag:'wx'});}\nconsole.log(JSON.stringify({status:report.status,observed:report.observed,refusal:report.refusal,error:report.error}));process.exitCode=report.status==='PASS'?0:1;\n", encoding='utf-8')
probe_command = ['node', str(probe), str(root/'early-native-confirmation.json')]
with (root/'early-native-confirmation.stdout').open('xb') as out, (root/'early-native-confirmation.stderr').open('xb') as err:
    probe_run = subprocess.run(probe_command, cwd=candidate, env=env, stdout=out, stderr=err, timeout=60)
probe_results.append({'name':'early-native-confirmation', 'command':probe_command, 'exit':probe_run.returncode})
probe = candidate/'workbench/tests/review05-late-native-confirmation.mjs'
probe.write_text("// Contract from T-108 and installed CLI hook samples. Real signal entry, SQLite,\n// PTY write boundary; supplied process identity is not a live CLI proof.\n// Failures: missing/stale/auxiliary fields, duplicate answer, changed input,\n// failed recorder/write, early state release, root completion swallowed.\nimport assert from 'node:assert/strict';\nimport { mkdtempSync, writeFileSync } from 'node:fs';\nimport { OrchestrationStore } from '../src/store.ts';\nimport { Panes } from '../src/panes.ts';\nimport { agentState } from '../src/sidebar.ts';\n\nconst output=process.argv[2];\nconst root=mkdtempSync('/private/tmp/t108-question-contract-');\nconst store=new OrchestrationStore(root), panes=new Panes(root,store,{},()=>{});\nconst record={id:'launch',thread:'thread',task:'task',project:'project',attempt:null,role:'controller',preset:'ideation',\n  session:'native',cli:'Claude Code',turn_limit:1,worktree:root};\nstore.launch(record);\nconst dispatch=store.register(record.id,'Ask region.');\nconst writes=[],inputs=[];\nconst pane={record,native:'native',state:'busy',failed:null,stopped:false,archived:false,interrupted:false,\n  stopInProgress:false,active:{id:'submission',dispatch:dispatch.id,at:'2026-10-20T00:00:00Z',nativeTurn:null},\n  claudePromptId:null,claudePromptIds:new Set(),queue:[],writing:false,writes:Promise.resolve(),pendingInputs:0,\n  userDraft:false,inputGeneration:0,pty:{write:data=>writes.push(data)}};\npanes.panes.set('thread',pane);\nconst questions=[{question:'选择发布区域？',header:'区域',options:[{label:'南区',description:'南部'},{label:'北区',description:'北部'}],multiSelect:false}];\nconst base={session_id:'native',prompt_id:'prompt',cwd:root,transcript_path:root+'/native.jsonl',tool_name:'AskUserQuestion',tool_use_id:'toolu_sentinel'};\nconst signal=(event,extra={})=>panes.signal('launch',JSON.stringify({...base,hook_event_name:event,...extra}),new Date().toISOString());\nconst state=()=>agentState({...panes.status('thread'),lifecycle:'running'},store.read(),root);\nconst report={status:'INCOMPLETE',scope:'real signal/SQLite; supplied PTY and runtime identity',model_turns:0,checks:[]};\ntry {\n store.event('turn_submitted',{id:'submission'},record);\n await signal('UserPromptSubmit',{prompt:dispatch.text});\n await signal('PreToolUse',{tool_input:{questions}});\n let guards=0,answerError;\n try {await panes.answerQuestion('launch','launch:toolu_sentinel',['北区'],async(...args)=>inputs.push(args),async()=>{\n   ++guards;\n });}catch(error){answerError=String(error);}\n await signal('PostToolUse',{tool_input:{questions,answers:{'选择发布区域？':'北区'}},tool_response:{questions,answers:{'选择发布区域？':'北区'}}});\n report.answer_error=answerError;report.answer_inputs=inputs.length;report.pty_keys=[...writes];\n report.question=panes.questions('launch')[0];report.observed=state();\n let nextInputError;\n try {await panes.userInput('launch','next sentinel', {request_id:'next',sequence:2},async()=>{},async()=>{});} catch(error){nextInputError=String(error);}\n report.next_input_error=nextInputError;report.all_pty_keys=[...writes];\n report.events=store.read().map(e=>({type:e.type,data:e.data}));\n assert.equal(report.question.status,'answered');assert.equal(report.answer_inputs,1);\n assert.deepEqual(report.pty_keys,['\\x1b[B','\\r','\\r'],'Native confirmation must stop further selection keys');\n assert.equal(answerError,undefined,'Native confirmed the valid answer; original answer request must succeed');\n assert.equal(nextInputError,undefined,'Confirmed answer cannot poison future terminal input');\n report.status='PASS';\n} catch(error) {report.error=String(error);report.stack=error.stack;}\nfinally {store.close();report.retained_fixture=root;writeFileSync(output,JSON.stringify(report,null,2)+'\\n',{flag:'wx'});}\nconsole.log(JSON.stringify({status:report.status,observed:report.observed,refusal:report.refusal,error:report.error}));process.exitCode=report.status==='PASS'?0:1;\n", encoding='utf-8')
probe_command = ['node', str(probe), str(root/'late-native-confirmation.json')]
with (root/'late-native-confirmation.stdout').open('xb') as out, (root/'late-native-confirmation.stderr').open('xb') as err:
    probe_run = subprocess.run(probe_command, cwd=candidate, env=env, stdout=out, stderr=err, timeout=60)
probe_results.append({'name':'late-native-confirmation', 'command':probe_command, 'exit':probe_run.returncode})
(root/'probe-results.json').write_text(json.dumps(probe_results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
with (root/'stdout.txt').open('xb') as out, (root/'stderr.txt').open('xb') as err:
    completed = subprocess.run(command, cwd=candidate, env=env, stdout=out, stderr=err, timeout=600)
metadata['exit'] = completed.returncode
summary = json.loads((root/'native-e2e.json').read_text(encoding='utf-8'))
metadata['status'] = summary['status']
metadata['model_calls'] = summary['model_calls']
metadata['vendor_calls'] = summary['vendor_calls']
# 完整入口新增八项包含首答回执和同窗格后续输入；这里另按原始 request 独立核对。
with sqlite3.connect('file:'+summary['fixture']+'/state/state.sqlite3?mode=ro', uri=True) as db:
    events = [{'seq':seq, 'type':typ, 'data':json.loads(data)}
              for seq,typ,data in db.execute('SELECT seq,type,data FROM orchestration_events ORDER BY seq')]
first = next(e for e in events if e['type']=='request_received' and e['data'].get('input',{}).get('command')=='window_answer')
outcome = next(e for e in events if e['type'] in ('request_result','request_rejected') and e['data'].get('id')==first['data']['id'])
metadata['first_answer_outcome'] = outcome
metadata['independent_answer_audit'] = 'PASS' if outcome['type']=='request_result' and outcome['data'].get('ok') is True else 'NO_GO'
metadata['probe_results'] = probe_results
(root/'result.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(metadata, ensure_ascii=False))
assert completed.returncode == 0 and summary['status'] == 'PASS'
assert summary['model_calls'] == 0 and summary['vendor_calls'] == 0
assert {'first_window_answer_final_receipt_ok', 'same_pty_followup_input_written_and_echoed'}.issubset(summary['checks'])
assert metadata['independent_answer_audit'] == 'PASS', '原生已回答，但首答请求没有成功回执'
assert all(probe['exit'] == 0 for probe in probe_results), '正常确认时序反例未通过，见 probe-results.json'
PY
