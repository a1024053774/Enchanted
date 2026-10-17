#!/bin/bash
# UTF-8；仅审查冻结候选。用 bash 执行；所有新产物放新建 /private/tmp 目录。
# 不启动供应商 CLI、不调用模型、不读取或复制 auth、不操作 A-14。
set -u
REPO=/Users/luckye/Documents/Code/a2a-wt-t078
OUT=$(mktemp -d /private/tmp/t078-startup-review-outside-01.XXXXXX)
RC=${?}
echo "段名：建立独立审查运行器；新输出目录：${OUT}；退出码：${RC}"
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
CANDIDATE = '06fc9feca6b91febd9879222d82bcb800e2e18ba'
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

def replace_once(text, before, after):
    assert text.count(before) == 1, ('变异锚点不唯一', before)
    return text.replace(before, after, 1)

def run(argv, name, timeout, env, cwd):
    with (OUT / (name + '.stdout.bin')).open('xb') as stdout, (OUT / (name + '.stderr.bin')).open('xb') as stderr:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=stdout, stderr=stderr, start_new_session=True)
        timed_out = False
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            # 只终止本运行器刚创建的进程组；保留整个副本和输出。
            os.killpg(child.pid, signal.SIGTERM)
            try:
                code = child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait(timeout=3)
    result = {'argv': argv, 'cwd': str(cwd), 'timeout_seconds': timeout,
              'pid': child.pid, 'start_new_session': True, 'exit_code': code, 'timed_out': timed_out}
    save(name + '-command.json', result)
    assert not timed_out, ('超时不算变异被拒绝', result)
    return code

verdict = {'status': 'INCOMPLETE', 'candidate': CANDIDATE, 'baseline': BASELINE,
           'case': CASE, 'suite': SUITE, 'real_model_turns': 0}
try:
    assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE, '冻结候选发生变化'
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
    mutated = original
    if CASE == 'baseline':
        mutated = git('show', BASELINE + ':workbench/src/panes.ts').decode('utf-8')
    elif CASE == 'startup_drain':
        mutated = replace_once(original, '    return {key,purpose,screen_id,written:true,state:pane.state};',
                               '    pane.state="idle"; await this.drain(pane);\n    return {key,purpose,screen_id,written:true,state:pane.state};')
    elif CASE == 'early_delivery':
        mutated = replace_once(original, 'return { state: queued ? "queued" : "unknown", at: item.registered_at };',
                               'return { state: queued ? "delivered" : "unknown", at: item.registered_at };')
    elif CASE == 'key_receipt_is_delivery':
        # 错把首启控制键收据当成 inbox 投递；上线前仍报 queued，release 后走原分支。
        mutated = replace_once(original, 'return { state: queued ? "queued" : "unknown", at: item.registered_at };',
                               'return { state: queued ? (this.store.lastEvent(item.launch, ["controller_screen_key_written"]) ? "delivered" : "queued") : "unknown", at: item.registered_at };')
    elif CASE == 'no_startup_guard':
        line = next(line for line in original.splitlines() if 'const assertStartup=()=>check(' in line)
        mutated = replace_once(original, line, '    const assertStartup=()=>{};')
    elif CASE == 'duplicate_release':
        mutated = replace_once(original, '      this.store.event("turn_submitted", submission, pane.record);',
                               '      this.store.event("turn_submitted", submission, pane.record);\n      pane.pty.write("\\x1b[200~" + item.text + "\\x1b[201~"); pane.pty.write("\\r");')
    else:
        assert CASE == 'candidate'
    if mutated != original:
        product.write_text(mutated, encoding='utf-8')
    (OUT / 'mutation.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), mutated.splitlines(True),
                                                                 fromfile='candidate/panes.ts', tofile=CASE + '/panes.ts')), encoding='utf-8')
    save('snapshot-manifest.json', {'revision': CANDIDATE, 'necessary_paths': PATHS, 'files': files,
                                   'dependency_read_link': str(dependency), 'mutated_product': str(product),
                                   'tests_modified': False, 'fixture_modified': False})
    env = {key: value for key, value in os.environ.items()
           if key in ['PATH', 'HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'USER', 'LOGNAME']}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['GIT_OPTIONAL_LOCKS'] = '0'
    if SUITE == 'domain':
        # 只读 Git 元数据：原测试的版本字段来自冻结提交，diff 来自这个变异副本。
        env['GIT_DIR'] = git('rev-parse', '--absolute-git-dir').decode().strip()
        env['GIT_WORK_TREE'] = str(SNAP)
        test = 'workbench/tests/test_t078_startup_pending.ts'
        argv = [NODE, str(SNAP / test), str(OUT / 'test'), str(SNAP / FIXTURE)]
        code = run(argv, 'test', 45, env, SNAP)
        observed = json.loads((OUT / 'test/results.json').read_text(encoding='utf-8'))
        failed = [item for item in observed['checks'] if item['status'] != 'PASS']
        if CASE in ['candidate', 'key_receipt_is_delivery']:
            assert code == 0 and observed['status'] == 'PASS' and len(observed['checks']) == 15
        else:
            assert code != 0 and observed['status'] == 'INCOMPLETE' and failed
            if CASE == 'baseline':
                assert failed[0]['code'] == 'screen_requires_startup' and failed[0]['writes'] == []
            elif CASE == 'no_startup_guard':
                guard = [item for item in failed if item['name'].startswith('queued_')]
                assert len(guard) == 9 and all(item['code'] == 'ERR_ASSERTION' and item['writes'] == ['\x1b[A'] for item in guard)
                assert any(item['name'] == 'state_change_during_identity_check_is_denied' for item in failed)
            elif CASE in ['startup_drain', 'duplicate_release']:
                assert any(item.get('code') == 'ERR_ASSERTION' and any(value.startswith('\x1b[200~') for value in item['writes']) for item in failed)
            else:
                raise AssertionError('该变异必须跑 entry 完成条件')
        verdict.update(test_exit_code=code, observed_status=observed['status'], failures=failed)
    elif SUITE == 'entry':
        # 先证明真实 inbox 入口文件完整，缺模块不能充当业务红态。
        preflight = run([NODE, str(SNAP / 'workbench/bin/inbox'), 'not-a-command'], 'inbox-loader', 10, env, SNAP)
        loader = (OUT / 'inbox-loader.stdout.bin').read_text(encoding='utf-8')
        assert preflight == 2 and json.loads(loader)['error'] == 'inbox_client_arguments'
        argv = [NODE, str(SNAP / 'workbench/tests/test_t078_a13_rehearsal.ts'),
                str(OUT / 'test'), '--recipient-offline', str(SNAP / FIXTURE)]
        code = run(argv, 'test', 145, env, SNAP)
        observed = json.loads((OUT / 'test/result.json').read_text(encoding='utf-8'))
        if CASE in ['candidate', 'key_receipt_is_delivery']:
            assert code == 0 and observed['status'] == 'PASS' and len(observed['checks']) == 14
            assert all(item['status'] == 'PASS' for item in observed['checks'])
            detail = json.loads((OUT / 'test/offline-delivery.json').read_text(encoding='utf-8'))
            assert detail['target_writes'][:6] == ['\x1b[A', '\x1b[B', '\r', '\r', '\x1b[B', '\r']
            assert detail['target_writes'][6].startswith('\x1b[200~') and detail['target_writes'][7] == '\r'
            assert detail['delivery']['state'] == 'delivered' and detail['created_at_unchanged'] is True
            # 独立读回 SQLite 的时序与计数；不调用产品判断函数。
            with sqlite3.connect((OUT / 'test/state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True) as db:
                assert db.execute('pragma integrity_check').fetchone()[0] == 'ok'
                rows = [(seq, launch, kind, json.loads(raw)) for seq, launch, kind, raw in
                        db.execute('select seq,launch,type,data from orchestration_events order by seq')]
            message = detail['delivery']['message']
            submissions = [row for row in rows if row[2] == 'turn_submitted' and row[3].get('dispatch') == message]
            assert len(submissions) == 1
            target = submissions[0][1]
            releases = [row for row in rows if row[1] == target and row[2] == 'executor_action' and row[3].get('action') == 'initial_release']
            assert len(releases) == 1
            release_seq = releases[0][0]
            keys = [row for row in rows if row[1] == target and row[2] == 'controller_screen_key_written']
            assert [row[3]['key'] for row in keys] == ['ArrowUp', 'ArrowDown', 'Enter', 'Enter', 'ArrowDown', 'Enter']
            assert all(row[0] < release_seq for row in keys)
            assert not [row for row in rows if row[1] == target and row[0] < release_seq and row[2] in ['paste_intent', 'turn_submit_intent', 'turn_submitted']]
            i2 = [row for row in rows if row[2] == 'relay_feedback_intent' and row[3].get('entry_id') == detail['stop']['id']]
            assert len(i2) == 1 and i2[0][0] > submissions[0][0] > release_seq
            verdict['sqlite_oracle'] = {'keys': [row[0] for row in keys], 'release': release_seq,
                                        'submission': submissions[0][0], 'original_I2': i2[0][0], 'integrity': 'ok'}
        else:
            expected = {
                'baseline': ('approved startup keys keep the pending inbox queued', 'startup CLI exit 0: observed=1 expected=0'),
                'startup_drain': ('approved startup keys keep the pending inbox queued', 'startup remains unknown 0: observed="busy" expected="unknown"'),
                'early_delivery': ('real controller_start queues without writing to unknown first screen', 'queue admission is not delivered: observed="delivered" expected="queued"'),
                'duplicate_release': ('initial release writes once then registers exactly the original I2', 'one bracketed paste: observed=2 expected=1'),
            }[CASE]
            assert code != 0 and observed['status'] == 'INCOMPLETE'
            assert observed['step'] == expected[0] and expected[1] in observed['error'], observed
            if CASE == 'baseline':
                commands = [json.loads(path.read_text(encoding='utf-8')) for path in (OUT / 'test').glob('command-*.json')]
                refusal = [item for item in commands if 'pane_screen_key' in item['argv'] and item['code'] != 0]
                assert len(refusal) == 1 and json.loads(refusal[0]['stdout'])['error'] == 'screen_requires_startup'
            verdict['rejection'] = {'step': observed['step'], 'error': observed['error']}
        verdict.update(test_exit_code=code, observed_status=observed['status'])
    else:
        raise AssertionError('未知检查面')
    if CASE in ['candidate', 'key_receipt_is_delivery']:
        # 分开运行：上面的冻结完成条件原文未改。以下独立探针只增加一个时点断言。
        source_test = (SNAP / 'workbench/tests/test_t078_startup_pending.ts').read_text(encoding='utf-8')
        probe_text = replace_once(source_test, '  await send();\n  assert.deepEqual(writes, ["\\x1b[A"]);',
                                 '  await send();\n  assert.equal((await panes.readWakeDelivery(pane.record.thread, queued.id)).state, "queued", "reviewer: startup key cannot deliver inbox");\n  assert.deepEqual(writes, ["\\x1b[A"]);')
        probe = SNAP / 'workbench/tests/reviewer_delivery_probe.ts'
        probe.write_text(probe_text, encoding='utf-8')
        (OUT / 'probe.diff').write_text(''.join(difflib.unified_diff(source_test.splitlines(True), probe_text.splitlines(True),
                                                                  fromfile='frozen-completion.ts', tofile='reviewer-delivery-probe.ts')), encoding='utf-8')
        probe_env = dict(env)
        probe_env['GIT_DIR'] = git('rev-parse', '--absolute-git-dir').decode().strip()
        probe_env['GIT_WORK_TREE'] = str(SNAP)
        probe_code = run([NODE, str(probe), str(OUT / 'probe'), str(SNAP / FIXTURE)], 'probe', 45, probe_env, SNAP)
        probe_result = json.loads((OUT / 'probe/results.json').read_text(encoding='utf-8'))
        if CASE == 'candidate':
            assert probe_code == 0 and probe_result['status'] == 'PASS'
        else:
            failures = [item for item in probe_result['checks'] if item['status'] != 'PASS']
            assert probe_code == 1 and len(failures) == 1
            assert failures[0]['code'] == 'ERR_ASSERTION' and 'reviewer: startup key cannot deliver inbox' in failures[0]['error']
            assert failures[0]['writes'] == ['\x1b[A'] and failures[0]['state'] == 'unknown' and len(failures[0]['queue']) == 1
            verdict.update(completion_condition='NO_GO', mutant_survived_frozen_checks=True, independent_probe_failure=failures[0])
        verdict['independent_probe_exit_code'] = probe_code
    assert git('rev-parse', 'HEAD').decode().strip() == CANDIDATE, '运行中候选发生变化'
    verdict['status'] = 'PASS'
except Exception as error:
    verdict.update(error=repr(error), traceback=traceback.format_exc())
finally:
    save('review-verdict.json', verdict)
    print(json.dumps(verdict, ensure_ascii=False))
sys.exit(0 if verdict['status'] == 'PASS' else 1)
PY
RC=${?}
echo "运行器写入退出码：${RC}"
if [ "${RC}" -ne 0 ]; then exit "${RC}"; fi
ALL_RC=0
for SPEC in candidate:entry baseline:entry startup_drain:entry early_delivery:entry no_startup_guard:domain duplicate_release:entry key_receipt_is_delivery:entry; do
  CASE=${SPEC%:*}
  SUITE=${SPEC#*:}
  echo "段名：${CASE} / ${SUITE}；新输出目录：${OUT}/${CASE}-${SUITE}"
  python3 -B "${OUT}/runner.py" "${REPO}" "${OUT}" "${CASE}" "${SUITE}"
  RC=${?}
  echo "段名：${CASE} / ${SUITE}；退出码：${RC}"
  if [ "${RC}" -ne 0 ]; then ALL_RC=1; fi
done
echo "独立审查完整输出目录：${OUT}"
echo "说明：运行器 PASS 仅表示预期现象得到证实；若 key_receipt_is_delivery 标记 completion_condition=NO_GO，则冻结完成条件需修复。"
echo "总退出码：${ALL_RC}"
exit "${ALL_RC}"
