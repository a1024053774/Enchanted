#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
python3 -X utf8 -B - "$@" <<'PY'
import ast, json, subprocess, sys
from pathlib import Path

base = Path('evidence/2026-10-11-batch13/T-078')
before = 'e980099a589f4d3f2a3c2aa0991d3f18f400b3ba'
label = '09b-executable-materials-13'
materials = base / label
check_only = '--check-only' in sys.argv[1:]
allow = json.loads((base / '09b-a13-allowlist.json').read_bytes())
future = {
    str(base / '09b-a13-ownership-preflight-01.json'),
    str(base / '09b-a13-source-freeze-01.json'),
    str(base / 'stage-b-a13-ideation-approval-01.json'),
    str(base / '09b-a13-commit-01'),
    str(materials),
}

def git(*args):
    return subprocess.check_output(['git', *args], text=True, encoding='utf-8').strip()

def status_rows():
    rows, unowned = [], []
    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'])
    for item in raw.decode().split('\0'):
        if not item:
            continue
        path = item[3:]
        owner = next((entry for entry in allow if path == entry or path.startswith(entry + '/')), None)
        rows.append({'path': path, 'status': 'PASS' if owner else 'INCOMPLETE', 'allowlist_entry': owner})
        if owner is None:
            unowned.append(path)
    return rows, unowned

assert git('rev-parse', 'HEAD') == before, git('rev-parse', 'HEAD')
assert not git('diff', '--cached', '--name-only')
rows, unowned = status_rows()
assert not unowned, ('Unowned work; no mutation', unowned)
missing = [entry for entry in allow if entry not in future and not Path(entry).exists()]
assert not missing, ('Allowlist path missing before git add', missing)

# Static evidence checks: no launch, no role input, and the previously executed
# A-12 cleanup/redaction/rehearsal records are independently readable.
dry = json.loads((base / '09b-a12-cleanup-01-dry-run/result.json').read_bytes())
clean = json.loads((base / '09b-a12-cleanup-01/result.json').read_bytes())
redacted = json.loads((base / '09b-a12-i1-redacted-01/summary.json').read_bytes())
rehearsal = json.loads((base / '09b-a13-rehearsal-09/result.json').read_bytes())
assert dry['status'] == 'PASS' and dry['dry_run'] is True and dry['signals_sent'] == []
assert clean['status'] == 'PASS' and clean['root_removed'] is True and clean['byte_readback'] == 'PASS'
assert len(clean['signals_sent']) == 2 and clean['archive'].endswith('/09b-a12-cleanup/fixture.tar.gz')
assert redacted['status'] == 'PASS' and redacted['request_count'] == 12 and redacted['response_count'] == 1
assert redacted['raw_logs_copied'] is False and redacted['credentials_copied'] is False
assert rehearsal['status'] == 'PASS' and len(rehearsal['checks']) == 5 and rehearsal['real_model_turns'] == 0

stage_command = (base / '09B-A13-STAGE-A-COMMAND.txt').read_text(encoding='utf-8')
b1_command = (base / '09B-A13-B1-COMMANDS.txt').read_text(encoding='utf-8')
onboard_command = (base / '09b-a13-onboard-materials-template/ONBOARD-COMMANDS.txt').read_text(encoding='utf-8')
i1_template = (base / '09b-a13-i1-materials-template/I1-COMMAND-TEMPLATE.txt').read_text(encoding='utf-8')
assert 'run-09b.py' in stage_command and '--protocol' in stage_command and label in stage_command
assert 'prepare-a13-b1-ideation-p1.py' in b1_command and '--dry-run' in b1_command and 'run-09b-stage-b.py' in b1_command
assert b1_command.count('--output') == 3 and 'a13-stage-a-01' in b1_command
assert '--purpose onboarding-notice' in onboard_command and '--next-screen-id ideation-s3' in onboard_command
assert '--next-screen-id ideation-s13' in onboard_command and '{next}' not in onboard_command
assert onboard_command.count('--phase screen') == 7 and onboard_command.count('--phase key') == 6
assert str(Path('/Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/run_t078_p1.py')) in onboard_command and str(base / 'workbench') not in onboard_command
assert 'prepare-a13-i1-materials.py' in i1_template and 'execute-02' in i1_template
assert (base / '09b-a13-i1-materials-template/permission-approval-template.json').is_file()

stage_approval = json.loads((base / 'a13-stage-a-approval-01.json').read_bytes())
assert not (base / 'stage-b-a13-ideation-approval-01.json').exists() or json.loads((base / 'stage-b-a13-ideation-approval-01.json').read_bytes())['approved_by'] is None
b1_approval = json.loads((base / 'stage-b-a13-ideation-approval-template.json').read_bytes())
assert stage_approval['approved_by'] is None and stage_approval['approval_ref'] is None
assert b1_approval['approved_by'] is None and b1_approval['approval_ref'] is None and b1_approval['binding'] is None
assert len(b1_approval['screen_approvals']) == 6 and b1_approval['screen_approvals'][3]['purpose'] == 'onboarding-notice'
assert b1_approval['tool_approval'] == {'key':'Enter','purpose':'one-time-tool-approval','selected_label':'1. Yes','one_time':True}
assert json.loads((base / '09b-a13-onboard-materials-template/static-check.json').read_bytes())['messages_expected'] == 0
assert json.loads((base / '09b-a13-i1-materials-template/static-check.json').read_bytes())['messages_expected'] == 2

# Every command's executable path is checked before the ownership preflight.
for path in [
    base / 'run-09b.py', base / 'run-09b-stage-b.py', Path('workbench/tests/run_t078_p1.py'),
    Path('workbench/src/gates/cli.ts'), Path('workbench/tests/t078_09b_i1_driver.py'),
    Path('workbench/tests/t078_09b_i1_permission.py'), base / 'prepare-09b-executable.py',
    base / 'prepare-a13-b1-ideation-p1.py', base / 'prepare-a13-i1-materials.py',
]:
    assert path.is_file(), ('command path missing', str(path))
for script in [base / 'prepare-a13-b1-ideation-p1.py', base / 'prepare-a13-i1-materials.py', Path('workbench/tests/test_t078_a13_rehearsal.ts')]:
    if script.suffix == '.py': ast.parse(script.read_text(encoding='utf-8'), filename=str(script))
subprocess.run(['git', 'diff', '--check'], check=True)

ownership = base / '09b-a13-ownership-preflight-01.json'
if check_only:
    print(json.dumps({'status':'PASS','mode':'check-only','head':git('rev-parse','HEAD'),'cached_paths':0,
                      'checked_paths':len(rows),'unowned':unowned,'simulated_final_status':[],
                      'rehearsal':str(base/'09b-a13-rehearsal-09'),'redacted':str(base/'09b-a12-i1-redacted-01'),
                      'prepare_label':label,'prepare_label_valid':label.startswith('09b-executable-materials-'),
                      'launch':'NO_GO'}, ensure_ascii=False))
    raise SystemExit(0)

ownership.write_text(json.dumps({'status':'PASS','checked_paths':len(rows),'unowned':unowned,
                                 'entries':rows,'simulated_final_status':[]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (base / 'RESULTS.md').open('a', encoding='utf-8') as fh:
    fh.write('\n## A-12 closeout and A-13 packet\n\n'
             'A-12 redaction PASS：保留 12 requests/1 response 的 tool_use/tool_result 与错误码，未复制 raw logs、debug、system/tools/auth 或凭据。A-12 owner-bound cleanup dry-run/formal PASS；API 93826/93827 各 SIGTERM 一次，daemon_stop 关闭 Claude/target，逐成员字节读回 PASS 后删除 root，归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09b-a12-cleanup/fixture.tar.gz`。\n'
             'A-13 rehearsal PASS：真实 daemon/bin-inbox/Stop/relay 链路五项检查通过，错 launch exit 2 且 stop 条目数保持 1；无 Claude/API/model，scratch 自行删除。A-13 materials-13、Stage A、B1、onboarding 和 protocol I1 三步模板均为 NO_GO 写文件准备，binding/签字栏留待实际 Stage A/B1 结果。\n')

# First commit freezes the current source and all existing evidence. A clean
# workbench is required before prepare-09b-executable.py creates materials-13.
existing = [Path(entry) for entry in allow if entry not in future and Path(entry).exists()]
subprocess.run(['git', 'add', '--', *map(str, existing)], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A13 rehearsal and packet templates'], check=True)
parent = git('rev-parse', 'HEAD')
commit_dir = base / '09b-a13-commit-01'; commit_dir.mkdir()
prepare = [sys.executable, '-B', str((base / 'prepare-09b-executable.py').resolve()), '--label', label, '--protocol']
with (commit_dir / 'prepare.stdout.bin').open('xb') as stdout, (commit_dir / 'prepare.stderr.bin').open('xb') as stderr:
    result = subprocess.run(prepare, cwd=Path('.'), stdout=stdout, stderr=stderr)
(commit_dir / 'prepare.command.json').write_text(json.dumps({'argv':prepare,'exit_code':result.returncode}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert result.returncode == 0
static = json.loads((materials / 'static-check.json').read_bytes())
assert static['status'] == 'PASS' and static['protocol'] is True and static['protocol_tag'] == 'a07-registered-anthropic-v1' and static['revision'] == parent
(base / '09b-a13-source-freeze-01.json').write_text(json.dumps({'status':'PASS','revision':parent,'materials':str(materials),'prepare':prepare,'protocol_tag':static['protocol_tag'],'launch':'NO_GO'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for file in [base / 'a13-stage-a-approval-01.json', base / 'stage-b-a13-ideation-approval-template.json']:
    value = json.loads(file.read_bytes()); value['source_revision'] = parent; file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
subprocess.run(['git', 'add', '--', str(materials), str(commit_dir), str(base/'09b-a13-source-freeze-01.json'), str(base/'a13-stage-a-approval-01.json'), str(base/'stage-b-a13-ideation-approval-template.json')], check=True)
subprocess.run(['git', 'commit', '-m', 'docs(T-078): freeze A13 executable materials'], check=True)
assert git('status', '--porcelain') == ''
print(json.dumps({'status':'PASS','materials':str(materials),'revision':parent,'launch':'NO_GO','simulated_final_status':[]}, ensure_ascii=False))
PY
