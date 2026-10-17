#!/bin/bash
# UTF-8。只审冻结候选；只在每次新建的 /private/tmp 目录解包、变异和运行。
# 不启动供应商 CLI，不读取或复制 auth，不调用模型，不触碰 A-14。
set -u
REPO=/Users/luckye/Documents/Code/a2a-wt-t078
OUT=$(mktemp -d /private/tmp/t078-startup-review-outside-02.XXXXXX)
RC=${?}
echo "段名：建立第二轮独立运行器；新输出目录：${OUT}；退出码：${RC}"
if [ "${RC}" -ne 0 ]; then exit "${RC}"; fi
cat > "${OUT}/runner.py" <<'PY'
import difflib
import io
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import traceback

REPO, ROOT, CASE, SUITE = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4]
CANDIDATE = '68d7749c284892a4bd43c9284e949b1ed3ea7e48'
PRODUCT = '06fc9feca6b91febd9879222d82bcb800e2e18ba'
BASELINE = 'd1ca480223dd874721af71c36488af0ed8b96f37'
NODE = '/opt/homebrew/bin/node'
FIXTURE = 'evidence/2026-10-11-batch13/T-078/09b-startup-pending-fixture-01'
PATHS = ['workbench/src', 'workbench/package.json', 'workbench/bin/inbox',
         'workbench/tests/test_t078_startup_pending.ts',
         'workbench/tests/test_t078_a13_rehearsal.ts', FIXTURE]
OUT = ROOT / (CASE + '-' + SUITE)
OUT.mkdir(exist_ok=False)
SNAP = OUT / 'snapshot'
SNAP.mkdir()

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])

def once(text, before, after):
    assert text.count(before) == 1, ('变异锚点不唯一', before)
    return text.replace(before, after, 1)

def run(argv, name, timeout, env):
    with (OUT / (name + '.stdout.bin')).open('xb') as stdout, (OUT / (name + '.stderr.bin')).open('xb') as stderr:
        child = subprocess.Popen(argv, cwd=SNAP, env=env, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, start_new_session=True)
        timed_out = False
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            # 只终止本次新建的子进程组；保留部分证据与副本。
            os.killpg(child.pid, signal.SIGTERM)
            try:
                code = child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait(timeout=3)
    save(name + '-command.json', {'argv': argv, 'cwd': str(SNAP), 'pid': child.pid,
         'timeout_seconds': timeout, 'start_new_session': True, 'exit_code': code, 'timed_out': timed_out})
    assert not timed_out, '超时不算业务反例被拒绝'
    return code

verdict = {'status': 'INCOMPLETE', 'candidate': CANDIDATE, 'product': PRODUCT,
           'baseline': BASELINE, 'case': CASE, 'suite': SUITE, 'real_model_turns': 0}
try:
    assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE, '冻结候选发生变化'
    for revision in [PRODUCT, CANDIDATE]:
        subprocess.run(['git', '-C', str(REPO), 'merge-base', '--is-ancestor', revision, 'HEAD'], check=True)
    assert not git('diff', '--', 'workbench/src', 'workbench/tests/test_t078_startup_pending.ts',
                   'workbench/tests/test_t078_a13_rehearsal.ts'), '候选源码或完成条件有未提交改动'
    archive = git('archive', CANDIDATE, '--', *PATHS)
    files = []
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            relative = Path(member.name)
            assert not relative.is_absolute() and '..' not in relative.parts
            if member.isdir():
                (SNAP / relative).mkdir(parents=True, exist_ok=True)
            else:
                assert member.isfile(), ('不解出链接或特殊文件', member.name)
                target = SNAP / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.extractfile(member).read())
                files.append(member.name)
    dependency = (REPO / 'workbench/node_modules').resolve(strict=True)
    (SNAP / 'workbench/node_modules').symlink_to(dependency, target_is_directory=True)
    product = SNAP / 'workbench/src/panes.ts'
    original = product.read_text(encoding='utf-8')
    baseline = git('show', BASELINE + ':workbench/src/panes.ts').decode('utf-8')
    assert once(baseline,
        ' && !pane.queue.length && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup"',
        ' && !pane.userDraft && !pane.pendingInputs,"screen_requires_startup"') == original, '产品差异超出指定的一处删除'
    mutated = original
    if CASE == 'baseline':
        mutated = baseline
    elif CASE == 'M5':
        mutated = once(original,
            '    return { state: queued ? "queued" : "unknown", at: item.registered_at };',
            '    return { state: queued ? (this.store.lastEvent(item.launch, ["controller_screen_key_written"]) ? "delivered" : "queued") : "unknown", at: item.registered_at };')
    elif CASE == 'startup_drain':
        mutated = once(original, '    return {key,purpose,screen_id,written:true,state:pane.state};',
            '    pane.state="idle"; await this.drain(pane);\n    return {key,purpose,screen_id,written:true,state:pane.state};')
    elif CASE == 'no_startup_guard':
        line = next(line for line in original.splitlines() if 'const assertStartup=()=>check(' in line)
        mutated = once(original, line, '    const assertStartup=()=>{};')
    elif CASE == 'omit_post_identity_guard':
        mutated = once(original,
            'const info=await this.processInfo(thread);check(info.leader && !info.failed,"foreground_claude_required");assertStartup();',
            'const info=await this.processInfo(thread);check(info.leader && !info.failed,"foreground_claude_required");')
    else:
        assert CASE == 'candidate'
    if mutated != original:
        product.write_text(mutated, encoding='utf-8')
    (OUT / 'mutation.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), mutated.splitlines(True),
        fromfile='candidate/panes.ts', tofile=CASE + '/panes.ts')), encoding='utf-8')
    save('snapshot-manifest.json', {'revision': CANDIDATE, 'necessary_paths': PATHS, 'files': files,
         'dependency_read_link': str(dependency), 'tests_modified': False, 'fixture_modified': False})
    env = {key: value for key, value in os.environ.items()
           if key in ['PATH', 'HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'USER', 'LOGNAME']}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['GIT_OPTIONAL_LOCKS'] = '0'
    if SUITE == 'domain':
        env['GIT_DIR'] = git('rev-parse', '--absolute-git-dir').decode().strip()
        env['GIT_WORK_TREE'] = str(SNAP)
        argv = [NODE, str(SNAP / 'workbench/tests/test_t078_startup_pending.ts'), str(OUT / 'test'), str(SNAP / FIXTURE)]
        code = run(argv, 'test', 60, env)
        observed = json.loads((OUT / 'test/results.json').read_text(encoding='utf-8'))
        failed = [row for row in observed['checks'] if row['status'] != 'PASS']
        if CASE == 'candidate':
            assert code == 0 and observed['status'] == 'PASS' and len(observed['checks']) == 15
            reads = [item for row in observed['checks'] for item in row['receipt_refreshes']]
            assert len(reads) == 7
            assert all(row['refreshed']['state'] == 'queued' and not row['i2'] and
                       not any(item['state'] == 'delivered' for item in row['history']) for row in reads)
        else:
            assert code == 1 and observed['status'] == 'INCOMPLETE' and failed
            if CASE == 'M5':
                assert len(failed) == 2 and all('startup refreshed receipt remains queued' in row['error'] for row in failed)
                assert all(row['receipt_refreshes'][0]['refreshed']['state'] == 'delivered' and
                           row['writes'] == ['\x1b[A'] and row['state'] == 'unknown' and len(row['queue']) == 1 for row in failed)
            elif CASE == 'no_startup_guard':
                guards = [row for row in failed if row['name'].startswith('queued_')]
                assert len(guards) == 9 and all('Missing expected rejection' in row['error'] and row['writes'] == ['\x1b[A'] for row in guards)
            elif CASE == 'omit_post_identity_guard':
                assert len(failed) == 1 and failed[0]['name'] == 'state_change_during_identity_check_is_denied'
                assert 'Missing expected rejection' in failed[0]['error'] and failed[0]['writes'] == ['\x1b[A']
            else:
                raise AssertionError('此变异请运行真实入口完成条件')
        verdict.update(test_exit_code=code, check_count=len(observed['checks']), failures=failed)
    elif SUITE == 'entry':
        preflight = run([NODE, str(SNAP / 'workbench/bin/inbox'), 'not-a-command'], 'inbox-loader', 10, env)
        loader = json.loads((OUT / 'inbox-loader.stdout.bin').read_text(encoding='utf-8'))
        assert preflight == 2 and loader['error'] == 'inbox_client_arguments'
        argv = [NODE, str(SNAP / 'workbench/tests/test_t078_a13_rehearsal.ts'),
                str(OUT / 'test'), '--recipient-offline', str(SNAP / FIXTURE)]
        code = run(argv, 'test', 190, env)
        observed = json.loads((OUT / 'test/result.json').read_text(encoding='utf-8'))
        if CASE == 'candidate':
            assert code == 0 and observed['status'] == 'PASS' and len(observed['checks']) == 14
            assert all(row['status'] == 'PASS' for row in observed['checks'])
            detail = json.loads((OUT / 'test/offline-delivery.json').read_text(encoding='utf-8'))
            message, entry = detail['delivery']['message'], detail['stop']['id']
            reads = []
            for index in range(6):
                row = json.loads((OUT / 'test' / ('startup-receipt-' + str(index) + '.json')).read_text(encoding='utf-8'))
                assert row['entry_id'] == row['refreshed']['entry']['id'] == entry
                assert row['refreshed']['delivery']['message'] == message
                assert row['refreshed']['delivery']['state'] == 'queued' and not row['I2']
                assert not any(item['state'] == 'delivered' for item in row['history'])
                assert row['state'] == 'unknown' and row['active'] is None and row['queue'] == [message]
                reads.append(row)
            with sqlite3.connect((OUT / 'test/state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                rows = [(seq, launch, kind, json.loads(raw)) for seq, launch, kind, raw in
                        db.execute('SELECT seq,launch,type,data FROM orchestration_events ORDER BY seq')]
            submitted = [row for row in rows if row[2] == 'turn_submitted' and row[3].get('dispatch') == message]
            assert len(submitted) == 1
            target = submitted[0][1]
            release = [row for row in rows if row[1] == target and row[2] == 'executor_action' and row[3].get('action') == 'initial_release']
            assert len(release) == 1
            keys = [row for row in rows if row[1] == target and row[2] == 'controller_screen_key_written']
            assert [row[3]['key'] for row in keys] == ['ArrowUp', 'ArrowDown', 'Enter', 'Enter', 'ArrowDown', 'Enter']
            assert all(row[0] < release[0][0] for row in keys)
            assert not [row for row in rows if row[1] == target and row[0] < release[0][0] and row[2] in ['paste_intent', 'turn_submit_intent', 'turn_submitted']]
            feedback = [row for row in rows if row[2] == 'relay_feedback_intent' and row[3].get('entry_id') == entry]
            assert len(feedback) == 1 and feedback[0][0] > submitted[0][0] > release[0][0]
            verdict['sqlite_oracle'] = {'keys': [row[0] for row in keys], 'release': release[0][0],
                'submission': submitted[0][0], 'original_I2': feedback[0][0], 'integrity': 'ok'}
            verdict['pre_release_refreshes'] = len(reads)
        else:
            assert code == 1 and observed['status'] == 'INCOMPLETE'
            assert observed['step'] == 'approved startup keys keep the pending inbox queued'
            if CASE == 'baseline':
                assert 'startup CLI exit 0' in observed['error']
                commands = [json.loads(path.read_text(encoding='utf-8')) for path in (OUT / 'test').glob('command-*.json')]
                refused = [row for row in commands if 'pane_screen_key' in row['argv'] and row['code'] == 1]
                assert len(refused) == 1 and json.loads(refused[0]['stdout'])['error'] == 'screen_requires_startup'
            elif CASE in ['M5', 'startup_drain']:
                assert 'startup refreshed delivery 0' in observed['error'] and observed['observed'] == 'delivered' and observed['expected'] == 'queued'
                row = json.loads((OUT / 'test/startup-receipt-0.json').read_text(encoding='utf-8'))
                if CASE == 'M5':
                    assert row['state'] == 'unknown' and row['active'] is None and len(row['queue']) == 1 and row['writes'] == ['\x1b[A']
                else:
                    assert row['state'] == 'busy' and row['active'] and row['queue'] == []
                    assert len(row['writes']) == 3 and row['writes'][1].startswith('\x1b[200~') and row['writes'][2] == '\r'
            else:
                raise AssertionError('未配置的入口变异')
        verdict.update(test_exit_code=code, observed_status=observed['status'], check_count=len(observed['checks']),
                       failure=None if CASE == 'candidate' else observed)
    else:
        raise AssertionError('未知检查面')
    assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE, '运行期间冻结候选发生变化'
    verdict['status'] = 'PASS'
except Exception as error:
    verdict.update(error=repr(error), traceback=traceback.format_exc())
finally:
    save('review-verdict.json', verdict)
print(json.dumps(verdict, ensure_ascii=False))
raise SystemExit(0 if verdict['status'] == 'PASS' else 1)
PY
RC=${?}
echo "段名：保存独立运行器；新输出目录：${OUT}；退出码：${RC}"
if [ "${RC}" -ne 0 ]; then exit "${RC}"; fi
TOTAL=0
for SPEC in candidate:entry baseline:entry M5:entry startup_drain:entry candidate:domain no_startup_guard:domain omit_post_identity_guard:domain; do
  CASE=${SPEC%:*}
  SUITE=${SPEC#*:}
  echo "段名：${CASE}/${SUITE}；新输出目录：${OUT}/${CASE}-${SUITE}"
  python3 -B "${OUT}/runner.py" "${REPO}" "${OUT}" "${CASE}" "${SUITE}" > "${OUT}/${CASE}-${SUITE}.log" 2>&1
  RC=${?}
  cat "${OUT}/${CASE}-${SUITE}.log"
  echo "段名：${CASE}/${SUITE}结束；新输出目录：${OUT}/${CASE}-${SUITE}；退出码：${RC}"
  if [ "${RC}" -ne 0 ]; then TOTAL=1; fi
done
echo "段名：第二轮独立检查结束；新输出目录：${OUT}；退出码：${TOTAL}"
exit "${TOTAL}"
