#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
exec python3 -B - "$@" <<'PYCODE'
import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

source = Path.cwd()
base = source / 'evidence/2026-10-11-batch13/T-078'
expected_head = 'cc96540efe5b1841a76fbd132fe3155705dc2cc0'
label = '09b-executable-materials-14'
packet = base / '09b-a14-materials-01'
check_only = sys.argv[1:] == ['--check-only']
assert check_only or not sys.argv[1:], 'Only --check-only is accepted'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=source, text=True).strip()
def status():
    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=source)
    entries = raw.decode('utf-8').split('\0')
    assert not any(entry[:1] in ['R', 'C'] for entry in entries if entry), 'Rename/copy requires a new ownership review'
    return [{'status': entry[:2], 'path': entry[3:]} for entry in entries if entry]
allow = json.loads((base / '09b-a14-allowlist.json').read_bytes())
first = allow['existing_or_preflight']
second = allow['generated_second'] + allow['updated_second']
first_generated = allow['generated_first']
def covered(path, paths):
    return any(path == root or path.startswith(root.rstrip('/') + '/') for root in paths)

# Main #304: both check-only and formal mode enforce the same runtime gate.
rehearsal_file = base / '09b-a14-rehearsal-01/result.json'
assert rehearsal_file.is_file(), 'A14 rehearsal NOT_RUN; no git mutation'
rehearsal = json.loads(rehearsal_file.read_bytes())
assert rehearsal['status'] == 'PASS' and rehearsal['real_model_turns'] == 0
assert [row['kind'] for row in rehearsal['scenes']] == ['flow','timeout']
assert all(row['status']=='PASS' and row['cleanup']['status']=='PASS' and row['cleanup']['scratch_removed'] for row in rehearsal['scenes'])
assert rehearsal['scenes'][0]['POST_counts'] == {'ideation':3,'executor':1}
assert rehearsal['scenes'][1]['observed_scene_status'] == 'INCOMPLETE'
assert rehearsal['scenes'][1]['http']['elapsed_seconds'] >= 180 and rehearsal['scenes'][1]['no_retry'] is True
frozen_rehearsal_source = base / '09b-a14-rehearsal-01/source'
assert frozen_rehearsal_source.is_dir()
for file in frozen_rehearsal_source.rglob('*'):
    if file.is_file():
        live = source / file.relative_to(frozen_rehearsal_source)
        assert live.read_bytes() == file.read_bytes(), ('Rehearsal source changed; rerun required', str(live))

assert git('rev-parse', 'HEAD') == expected_head, ('HEAD changed', git('rev-parse','HEAD'), expected_head)
assert git('branch', '--show-current') == 'exec/t078'
assert git('diff', '--cached', '--name-only') == '', 'Staged work exists; no mutation'
assert label.startswith('09b-executable-materials-')
assert not (base / label).exists(), 'Executable material directory already exists'
assert not (base / '09b-a14-commit-01').exists(), 'Commit output directory already exists'
assert not (base / '09b-a14-source-freeze-01.json').exists()
command = (packet / 'STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
assert '--materials ' + str(base / label) + ' ' in command
assert '--stage A --protocol' in command
assert '--approval ' + str(packet / 'stage-a-approval.json') in command
approval = json.loads((packet / 'stage-a-approval.json').read_bytes())
assert approval['materials'] == label and approval['allow_role_cli_spawn'] is False
assert approval['approved_by'] is None and approval['approval_ref'] is None and approval['source_revision'] is None
assert (packet / 'protocol.json').read_bytes() == (base / '09b-materials-01/protocol.json').read_bytes()
results = (base / 'RESULTS.md').read_text(encoding='utf-8')
assert '## 主控 #303：独立审查收尾与 A-14 待审材料' in results
assert '不是用户另外逐字批准' in (packet / 'PLAN.md').read_text(encoding='utf-8')
for item in first:
    assert (source / item).exists() or item in first_generated, ('git add path missing', item)
for item in second:
    assert (source / item).exists() or item in allow['generated_second'], ('generated path has no producer', item)
# Every generated result belongs to a real add group, including this report.
for item in first_generated:
    assert covered(item, first)
rows = status()
unowned = [row for row in rows if not covered(row['path'], first)]
assert not unowned, ('Unowned work; no mutation', unowned)
planned_generated = first_generated + allow['generated_second'] + allow['updated_second']
simulated = [row for row in rows if not covered(row['path'], first + second)]
simulated += [{'path': item} for item in planned_generated if not covered(item, first + second)]
assert simulated == [], ('Final worktree would be dirty', simulated)
changed_python = [source / row['path'] for row in rows if row['path'].endswith('.py')]
for path in changed_python:
    ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
# The Python body and shell syntax of this very script are checked too.
self_path = base / 'commit-09b-a14.sh'
subprocess.run(['sh','-n',str(self_path)], check=True)
ast.parse(self_path.read_text(encoding='utf-8').split("<<'PYCODE'\n",1)[1].rsplit('\nPYCODE',1)[0], filename=str(self_path))
subprocess.run(['git', 'diff', '--check'], cwd=source, check=True)
spec = importlib.util.spec_from_file_location('a14_static_preflight', base / 'check-a14.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
checks = module.check()
assert checks['status'] == 'PASS' and checks['http_checks'] == 'NOT_RUN'
assert len(checks['generated_phase_commands']) == 25
assert json.loads((base / '09b-a14-static-check-03.json').read_bytes())['status'] == 'PASS'
report = {'status':'PASS','mode':'check-only' if check_only else 'precommit','head':expected_head,
          'cached_paths':0,'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':simulated,
          'git_add_paths_exist_or_have_producer':True,'prepare_label':label,
          'pure_data_messages':checks['current_transcript_messages'],'generated_phase_commands':len(checks['generated_phase_commands']),
          'http_checks':'NOT_RUN','launch':'NO_GO','entries':rows}
if check_only:
    print(json.dumps({key:value for key,value in report.items() if key!='entries'}, ensure_ascii=False))
    raise SystemExit(0)
assert os.environ.get('A2A_ROLE') == 'worker', 'Run with the original worker launch identity'
# No files are written before all pre-add checks above have passed.
with (base / '09b-a14-ownership-preflight-01.json').open('x',encoding='utf-8') as stream:
    stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
with (base / 'RESULTS.md').open('a',encoding='utf-8') as stream:
    stream.write('\n主控执行 A14 无模型排练：PASS；正例 POST 为 ideation=3/executor=1；'
                 '超时场景按要求 INCOMPLETE、未重试，实际 HTTP 等待 '
                 + str(rehearsal['scenes'][1]['http']['elapsed_seconds'])
                 + ' 秒；两场 owner-bound 清理 PASS、scratch 已删除。'
                 '原件：09b-a14-rehearsal-01/result.json，供应商模型 0。\n')
subprocess.run(['git','add','--',*first],cwd=source,check=True)
subprocess.run(['git','commit','-m','test(T-078): prepare approved A14 pending delivery phases'],cwd=source,check=True)
revision = git('rev-parse','HEAD')
assert git('status','--porcelain') == '', 'First add group was not exhaustive'
commit_out = base / '09b-a14-commit-01'; commit_out.mkdir()
prepare = [sys.executable,'-B',str(base/'prepare-09b-executable.py'),'--label',label,'--protocol']
with (commit_out/'prepare.stdout.bin').open('xb') as stdout, (commit_out/'prepare.stderr.bin').open('xb') as stderr:
    completed = subprocess.run(prepare,cwd=source,stdout=stdout,stderr=stderr)
(commit_out/'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':completed.returncode},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert completed.returncode == 0, 'Prepare failed; keep output and stop, do not rerun'
static = json.loads((base/label/'static-check.json').read_bytes())
assert static['status']=='PASS' and static['revision']==revision and static['protocol'] is True
assert Path(static['root']).is_dir() and static['real_cli_starts']==static['api_starts']==static['target_starts']==0
approval['source_revision'] = revision
(packet/'stage-a-approval.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(base/'09b-a14-source-freeze-01.json').write_text(json.dumps({'status':'PASS','revision':revision,'materials':str(base/label),
    'static_root':static['root'],'fixture_profile':'a14-approved-gate-history-v1','launch':'NO_GO',
    'claim':'File-only executable packet; complete dual-role runtime NOT_RUN'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert all(covered(row['path'], second) for row in status()), ('Unexpected output after prepare',status())
subprocess.run(['git','add','--',*second],cwd=source,check=True)
subprocess.run(['git','commit','-m','docs(T-078): freeze A14 executable proposal and unsigned approval'],cwd=source,check=True)
assert git('status','--porcelain') == '', 'Final worktree is dirty'
print(json.dumps({'status':'PASS','source_commit':revision,'materials_commit':git('rev-parse','HEAD'),
                  'git_status':'clean','launch':'NO_GO'},ensure_ascii=False))
PYCODE
