#!/usr/bin/env bash
# T-082 冻结候选独立审查。由主控在沙箱外运行；本脚本不请求权限升级。
# 不启动真实 Codex、不调用模型、不读取或复制 auth、不改候选或主 checkout。
# Git 写操作只由既有测试在新建的 /tmp 夹具仓库内执行。
# 只解出列明的必要源码、测试及一个已记录的报告输入；不构建、不安装依赖。
set -u
ROOT=/Users/luckye/Documents/Code/a2a-wt-t082
OUTPUT=$(mktemp -d /tmp/r82-review01-XXXXXX)
CODE=$?
echo "段名：新建独立审查输出目录"
echo "output=${OUTPUT}"
echo "exit_code=${CODE}"
if [ "${CODE}" -ne 0 ]; then exit "${CODE}"; fi
export PYTHONDONTWRITEBYTECODE=1
export NODE_DISABLE_COMPILE_CACHE=1
python3 -B - "${ROOT}" "${OUTPUT}" <<'PY'
import datetime
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import traceback

root, out = map(lambda x: Path(x).resolve(), sys.argv[1:])
candidate = 'f589d19387c2dcc5eeda6505423d794f2b3be1f3'
paths = [
    'workbench/src', 'workbench/hooks', 'workbench/package.json', 'workbench/LICENSE.synara',
    'workbench/tests/test_task_cards_e2e.py', 'workbench/tests/test_quality_chain_e2e.py',
    'workbench/tests/test_quality_tracer_e2e.py', 'workbench/tests/quality_chain_host.ts',
    'workbench/tests/controlled_quality_pty.ts', 'workbench/tests/test_review_worktree_lifecycle_e2e.py',
    'workbench/tests/test_t082_review_boundary_e2e.py', 'workbench/tests/test_t082_review_protocol.ts',
    'evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json',
]
# Panes 为 worker 注入这个 hooksPath；保留冻结产品的钩子入口及实现。
# 仅这些固定名称可作为 symlink，且只能指向同目录的普通文件 hook.py。
hook_links = {'workbench/hooks/' + name for name in (
    'applypatch-msg', 'commit-msg', 'fsmonitor-watchman', 'p4-changelist',
    'p4-post-changelist', 'p4-prepare-changelist', 'post-applypatch', 'post-checkout',
    'post-commit', 'post-index-change', 'post-merge', 'post-receive', 'post-rewrite',
    'post-update', 'pre-applypatch', 'pre-commit', 'pre-merge-commit', 'pre-push',
    'pre-rebase', 'pre-receive', 'prepare-commit-msg', 'proc-receive',
    'push-to-checkout', 'reference-transaction', 'sendemail-validate', 'update',
)}
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_', 'NODE_'))}
env.update(PYTHONDONTWRITEBYTECODE='1', NODE_DISABLE_COMPILE_CACHE='1', GIT_OPTIONAL_LOCKS='0')
record = {'status': 'INCOMPLETE', 'candidate': candidate, 'real_codex_turns': 0,
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'output': str(out), 'steps': [], 'mutations': [], 'necessary_paths': paths}

def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def run(name, argv, cwd, timeout=300):
    target = out / name
    target.mkdir()
    print('段名：' + name, flush=True)
    print('output=' + str(target), flush=True)
    row = {'name': name, 'argv': list(map(str, argv)), 'cwd': str(cwd), 'output': str(target)}
    record['steps'].append(row)
    save(target / 'command.json', row)
    try:
        with (target / 'stdout.txt').open('xb') as stdout, (target / 'stderr.txt').open('xb') as stderr:
            done = subprocess.run(row['argv'], cwd=cwd, env=env, stdout=stdout,
                                  stderr=stderr, timeout=timeout)
        row['exit_code'] = done.returncode
    except subprocess.TimeoutExpired as error:
        row.update(exit_code=None, error=repr(error), status='INCOMPLETE')
    print('exit_code=' + str(row['exit_code']), flush=True)
    return row, target

def read_suite(target):
    path = target / 'result' / 'run.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None

def classify(row, target, expected_failure=None):
    result = read_suite(target)
    row['report'] = str(target / 'result' / 'run.json')
    row['expected_failure'] = expected_failure
    if result is None:
        row['verified'] = False
        save(target / 'assessment.json', row)
        raise RuntimeError('未取得完整子进程凭据；保留现场并停止：' + row['name'])
    cases = result.get('cases', [])
    row['cases'] = [{k: c.get(k) for k in ('case', 'outcome', 'failure_id', 'error', 'cleanup_failures')}
                    for c in cases]
    if expected_failure:
        good = (row.get('exit_code') == 1 and len(cases) == 1
                and cases[0].get('outcome') == 'contract_failure'
                and cases[0].get('failure_id') == expected_failure
                and not cases[0].get('cleanup_failures'))
    else:
        good = row.get('exit_code') == 0 and result.get('status') == 'PASS'
    row['verified'] = bool(good)
    # 保留原路径，避免移动后破坏夹具 worktree 的绝对 .git 指针。
    # close_fixture 已复制请求原文；只在停止成功后删除该凭据列明的请求目录。
    artifact = Path(result.get('artifact_root', '/nonexistent')).resolve()
    if artifact.exists() and artifact.parent == Path('/private/tmp') and artifact.name.startswith('q76-'):
        row['fixture_preserved_at'] = str(artifact)
        row['request_dirs_removed'] = []
        if not any(c.get('cleanup_failures') for c in cases):
            for case in cases:
                state = Path(case['fixture']) / 'state'
                receipt_dir = target / 'result' / case['case']
                captured = json.loads((receipt_dir / 'database-readback.json').read_text(encoding='utf-8'))
                cleanup = json.loads((receipt_dir / 'cleanup.json').read_text(encoding='utf-8'))
                if (captured['phase'] != 'before-host-stop' or cleanup['host_exit'] != 0
                    or cleanup['failures'] or Path(case['fixture']).parent != artifact):
                    raise RuntimeError('夹具归属或停止凭据不符；停止清理：' + case['case'])
                # 使用 close_fixture 在停止前保存的记录；不再重开已关闭的 WAL 数据库。
                for launch_row in captured['tables']['launch_records']:
                    launch = json.loads(launch_row['data'])
                    request_dir = Path(launch['request_dir']).resolve()
                    if (request_dir.parent != Path('/private/tmp')
                        or not request_dir.name.startswith('a2a-requests-')
                        or launch['env']['A2A_STATE'] != str(state)):
                        raise RuntimeError('请求目录归属不明；停止清理：' + str(request_dir))
                    if request_dir.is_dir():
                        shutil.rmtree(request_dir)
                        row['request_dirs_removed'].append(str(request_dir))
    save(target / 'assessment.json', row)
    print(json.dumps({'段名': row['name'], '预期失败点': expected_failure,
                      '检查成立': row['verified'], 'cases': row['cases']}, ensure_ascii=False), flush=True)
    if any(c.get('cleanup_failures') for c in cases):
        raise RuntimeError('夹具停止未确认；不启动后续检查：' + row['name'])
    return bool(good)

try:
    print('段名：冻结版本与运行前置核对', flush=True)
    print('output=' + str(out), flush=True)
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], env=env, text=True).strip()
    if head != candidate:
        raise RuntimeError('冻结候选已变化：' + head)
    if not Path('/Volumes/WD-Elements').is_mount():
        raise RuntimeError('外置盘未挂载；不回退缓存、不安装依赖。')
    version = subprocess.check_output(['node', '--version'], env=env, text=True).strip()
    if version != 'v26.5.0':
        raise RuntimeError('需要已有 Node v26.5.0，实际为 ' + version)
    dependencies = (root / 'workbench/node_modules').resolve()
    if not (dependencies / 'effect').exists() or not (dependencies / 'node-pty').exists():
        raise RuntimeError('既有依赖不可用；不安装。')
    record.update(node_version=version, dependency_path=str(dependencies))
    archive_argv = ['git', '-C', str(root), 'archive', candidate, '--', *paths]
    data = subprocess.check_output(archive_argv, env=env)
    source = out / 'source'
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            expected = (member.isdir() and any(p.startswith(member.name.rstrip('/') + '/') for p in paths)
                        or any(member.name == p or member.name.startswith(p + '/') for p in paths))
            if member.name.startswith('workbench/hooks/'):
                expected = member.name == 'workbench/hooks/hook.py' or member.name in hook_links
            if member.name in hook_links:
                allowed_type = member.issym() and member.linkname == 'hook.py'
            else:
                allowed_type = member.isdir() or member.isfile()
            if path.is_absolute() or '..' in path.parts or not expected or not allowed_type:
                raise RuntimeError('归档含未授权成员：' + member.name)
        archive.extractall(source)
    (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
    save(out / 'source-manifest.json', {'candidate': candidate, 'argv': archive_argv,
         'files': [m.name for m in members if m.isfile()], 'dependency_path': str(dependencies)})
    print('exit_code=0', flush=True)

    # 本文件是独立夹具，只提供外部改动、socket 时序和独立预期，不替换门禁结果。
    probe = out / 'independent_probe.py'
    probe.write_text(r'''
import datetime
import json
from pathlib import Path
import socket
import sys
import uuid

harness, selected, output, case = map(str, sys.argv[1:])
sys.path.insert(0, str(Path(harness) / 'workbench/tests'))
from test_quality_chain_e2e import HarnessFailure, run_cases, save
from test_t082_review_boundary_e2e import ReviewBoundary

class IndependentReview(ReviewBoundary):
    def requirements_workspace_changed(self):
        _, candidate = self.good_submission()
        review, packet_record = self.start_review(candidate)
        packet = self.review_packet(review, candidate)
        packet['review_requirements']['mutation_checks']['workspace'] = str(self.root / 'wrong-copy')
        task = self.send_review(review, packet_record, packet)
        save(self.evidence / 'requirements-workspace-readback.json', {'submitted': packet, 'task': task,
             'expected_workspace': review['candidate_workspace'], 'events': self.events()})
        self.check('REVIEW-REQUIREMENTS-WORKSPACE', task['state'] == 'paused'
                   and task['review']['state'] == 'unknown' and not task['review'].get('result'),
                   '请求要求 review_requirements 原样返回，改成别的副本路径须拒收', task)

    def refs_changed(self):
        _, candidate = self.good_submission()
        review, packet_record = self.start_review(candidate)
        self.git('update-ref', 'refs/reviewer-oracle/unexpected', candidate)
        self.send_review(review, packet_record, self.review_packet(review, candidate))
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        task = self.cli('status')['task']
        save(self.evidence / 'independent-refs-readback.json', {'task': task, 'events': events,
             'refs': self.git('for-each-ref', '--format=%(refname)=%(objectname)'),
             'copy_exists': Path(review['candidate_workspace']).exists()})
        self.check('REVIEW-REFS-INVALIDATE', task['state'] == 'paused'
                   and task['review']['state'] == 'unknown'
                   and Path(review['candidate_workspace']).exists()
                   and any(e['type'] == 'issue_issue' for e in events)
                   and any(e['type'] == 'review_lifecycle_failed'
                           and e['details']['details'].get('error') == 'review_shared_refs_changed'
                           for e in events)
                   and not any(e['type'] == 'review_reclaimed' for e in events),
                   '新增共享引用须作废结论、上报并保留副本；不能正常回收', task)

    def integration_before_end_check(self):
        _, candidate = self.good_submission()
        review, packet_record = self.start_review(candidate)
        outside = Path(review['workspace']) / 'independent-external-change.txt'
        outside.write_text('外部改动必须在集成之前被发现。\n', encoding='utf-8')
        packet = self.review_packet(review, candidate)
        stop = {'session_id': packet_record['native'], 'turn_id': 'fixture-turn-1',
                'hook_event_name': 'Stop', 'last_assistant_message': json.dumps(packet, ensure_ascii=False)}
        # 只延迟客户端关闭写半边；产品 daemon 和其 connection.close 回调保持原样。
        # 这给异步回收一个确定、可复现的暂停点，不靠 sleep 或进程调度运气。
        message = {'id': str(uuid.uuid4()), 'input': {'command': 'signal',
                   'launch': packet_record['launch'], 'raw_stdin': json.dumps(stop, ensure_ascii=False),
                   'received_at': datetime.datetime.now(datetime.timezone.utc).isoformat()},
                   'identity': {'launch': packet_record['launch'],
                       'token': packet_record['env']['A2A_CAPABILITY'],
                       'native_session': packet_record['native']}}
        held = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        held.settimeout(15)
        try:
            held.connect(str(self.state / 'control.sock'))
            held.sendall((json.dumps(message, ensure_ascii=False) + '\n').encode())
            response = b''
            while b'\n' not in response:
                chunk = held.recv(65536)
                if not chunk:
                    raise HarnessFailure('Stop 回执在换行前断开。')
                response += chunk
            receipt = json.loads(response.split(b'\n', 1)[0])
            if not receipt.get('ok') or not receipt.get('completedReview'):
                raise HarnessFailure('未取得有效报告回执：' + json.dumps(receipt))
            before = self.cli('status')['task']
            events = self.events()
            if any(e['type'] == 'review_reclaimed' for e in events):
                raise HarnessFailure('确定性暂停点未成立：回收已执行。')
            result = self.gate('integrate', '--attempt', self.a['attempt_id'], '--score-file', self.score_file())
            proof = {'stop_receipt': receipt, 'before_integration': before,
                     'integration': result, 'main_head': self.oid(), 'base': self.base,
                     'outside_change_exists': outside.exists(), 'events': self.events()}
            save(self.evidence / 'integration-before-end-check.json', proof)
        finally:
            held.close()
        events = self.wait_for(self.events, lambda rows: any(
            e['type'] in ('review_reclaimed', 'review_lifecycle_failed') for e in rows))
        save(self.evidence / 'after-release.json', {'task': self.cli('status')['task'], 'events': events})
        self.check('REVIEW-END-BEFORE-INTEGRATE', not result.get('ok') and proof['main_head'] == self.base,
                   '结束边界尚未核对，且审查目录已脏，集成须拒绝并保持 main 不变', proof)

raise SystemExit(run_cases(Path(selected), Path(output), [case], IndependentReview,
                          dialect='current', stop_on_failure=True))
'''.lstrip(), encoding='utf-8')

    payload = source / 'evidence/2026-10-15-batch15/T-082/protocol-red-green-01/real-review-submit.json'
    passed = []

    def suite(name, selected, script, cases=None, expected_failure=None, independent=False):
        target = out / name
        if independent:
            argv = [sys.executable, '-B', str(probe), str(source), str(selected), str(target / 'result'), cases[0]]
        else:
            argv = [sys.executable, '-B', str(source / 'workbench/tests' / script),
                    '--source', str(selected), '--output', str(target / 'result')]
            for case in cases or []:
                argv.extend(['--case', case])
        row, target = run(name, argv, source)
        passed.append(classify(row, target, expected_failure))
        return row

    suite('01-候选请求副本与结束核对', source, 'test_t082_review_boundary_e2e.py',
          ['tracer_review_copy', 'external_review_boundary_invalidated', 'real_payload_report_roundtrip'])
    suite('02-T076三性质与严格协议', source, 'test_quality_tracer_e2e.py',
          ['tracer_wrong_candidate', 'tracer_reused_native', 'tracer_writer_cannot_review', 'tracer_malformed_review'])
    suite('03-T077审查生命周期', source, 'test_review_worktree_lifecycle_e2e.py')
    suite('04-独立共享引用反例', source, None, ['refs_changed'], independent=True)

    protocol_script = source / 'workbench/tests/test_t082_review_protocol.ts'
    row, target = run('05-候选报告协议', ['node', str(protocol_script), str(source), str(payload),
                                       str(out / '05-候选报告协议' / 'result.json')], source)
    protocol = json.loads((target / 'result.json').read_text(encoding='utf-8'))
    row['verified'] = row.get('exit_code') == 0 and protocol['status'] == 'PASS'
    passed.append(row['verified'])
    save(target / 'assessment.json', row)

    def variant(name, changes, wrong_implementation=False):
        selected = out / name
        shutil.copytree(source, selected, symlinks=True)
        rows = []
        for path, before, after in changes:
            file = selected / path
            text = file.read_text(encoding='utf-8')
            if text.count(before) != 1:
                raise RuntimeError('变异目标不唯一：' + path + ': ' + before)
            file.write_text(text.replace(before, after), encoding='utf-8')
            rows.append({'path': path, 'before': before, 'after': after})
        save(out / (name + '.changes.json'), rows)
        if wrong_implementation:
            record['mutations'].append({'name': name, 'source': str(selected), 'changes': rows})
        return selected

    core = 'workbench/src/gates/core.ts'
    panes = 'workbench/src/panes.ts'
    protocol_path = 'workbench/src/gates/qualityProtocol.ts'
    bad_cwd = (panes, '"--no-alt-screen", "-C", launchWorkspace,',
               '"--no-alt-screen", "-C", review ? review.workspace : launchWorkspace,')
    bad_tmp = (panes, 'const excludeSlashTmp = review ? "true" : "false";',
               'const excludeSlashTmp = "false";')
    no_cwd = (core, 'live.workspace === review.candidate_workspace && cwd >= 0 && argv[cwd + 1] === review.candidate_workspace &&',
              'live.workspace === review.candidate_workspace &&')
    no_tmp = (core, 'config("sandbox_workspace_write.exclude_slash_tmp=true") &&', 'true &&')
    no_refs = (core, 'requireGate(refs === review.shared_refs, "review_shared_refs_changed",',
               'requireGate(true, "review_shared_refs_changed",')
    no_section = (protocol_path, 'requireValue(Object.hasOwn(report, "完成条件与变异检查"), "report.section");',
                  '// 独立错误实现：不检查报告节键。')
    no_delete = (core, 'rmSync(review.candidate_workspace, { recursive: true, force: false });\n'
                 '    requireGate(!existsSync(review.candidate_workspace), "review_candidate_copy_unconfirmed", binding);',
                 '// 独立错误实现：省略删除及其确认，但仍发出 removed 事件。')

    # 两个坏启动输入是外部事实夹具；与门禁错误实现分开记录、先跑正确门禁对照。
    injection = variant('input-bad-cwd', [bad_cwd])
    suite('06-坏C参数正确拒收', injection, 'test_t082_review_boundary_e2e.py', ['launch_boundary_refused'])
    m1 = variant('M1-no-cwd-check', [bad_cwd, no_cwd], True)
    suite('07-M1不核对C参数', m1, 'test_t082_review_boundary_e2e.py',
          ['launch_boundary_refused'], 'T082-LAUNCH-REFUSED')
    injection = variant('input-bad-tmp', [bad_tmp])
    suite('08-tmp放开正确拒收', injection, 'test_t082_review_boundary_e2e.py', ['launch_boundary_refused'])
    m2 = variant('M2-no-tmp-check', [bad_tmp, no_tmp], True)
    suite('09-M2不核对tmp', m2, 'test_t082_review_boundary_e2e.py',
          ['launch_boundary_refused'], 'T082-LAUNCH-REFUSED')
    m3 = variant('M3-no-shared-refs-check', [no_refs], True)
    suite('10-M3已有结束测试覆盖', m3, 'test_t082_review_boundary_e2e.py',
          ['tracer_review_copy', 'external_review_boundary_invalidated'])
    suite('11-M3独立引用反例', m3, None, ['refs_changed'], 'REVIEW-REFS-INVALIDATE', independent=True)
    m4 = variant('M4-missing-report-section-accepted', [no_section], True)
    row, target = run('12-M4缺节仍收', ['node', str(protocol_script), str(m4), str(payload),
                                      str(out / '12-M4缺节仍收' / 'result.json')], source)
    result = json.loads((target / 'result.json').read_text(encoding='utf-8'))
    row['verified'] = (row.get('exit_code') == 1 and result['status'] == 'INCOMPLETE'
                       and 'Missing expected exception: T082-REPORT-SECTION' in str(result.get('failure')))
    row['expected_failure'] = 'T082-REPORT-SECTION'
    passed.append(row['verified'])
    save(target / 'assessment.json', row)
    m5 = variant('M5-copy-not-deleted', [no_delete], True)
    suite('13-M5副本不删', m5, 'test_t082_review_boundary_e2e.py',
          ['tracer_review_copy'], 'T082-COPY-REMOVED')

    # 非变异：冻结产品的真实 socket/门禁集成顺序反例。
    suite('14-结束核对前集成窗口', source, None, ['integration_before_end_check'], independent=True)
    suite('15-review_requirements副本绑定', source, None, ['requirements_workspace_changed'], independent=True)

    record['status'] = 'PASS' if all(passed) else 'INCOMPLETE'
    record['note'] = ('PASS 只表示本批预期检查成立；第 10 段若通过，表示已有结束测试未杀死 M3。'
                      '第 14 段若在 REVIEW-END-BEFORE-INTEGRATE 失败，表示候选集成顺序存在真实业务反例。')
    after = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], env=env, text=True).strip()
    record['head_after'] = after
    if after != candidate:
        record['status'] = 'INCOMPLETE'
        record['snapshot_changed'] = True
except Exception as error:
    record.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
finally:
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(out / 'review-run.json', record)
    print('段名：独立检查汇总', flush=True)
    print('output=' + str(out), flush=True)
    print(json.dumps({'status': record['status'], 'mutants': len(record['mutations']),
          'real_codex_turns': 0, 'steps': [{k: s.get(k) for k in ('name', 'exit_code', 'verified', 'expected_failure')}
                                        for s in record['steps']]}, ensure_ascii=False, indent=2), flush=True)
    print('临时源码、变异与诊断现场保留在本次独立输出目录；没有删除历史现场。', flush=True)
sys.exit(0 if record['status'] == 'PASS' else 1)
PY
CODE=$?
echo "段名：脚本结束"
echo "output=${OUTPUT}"
echo "exit_code=${CODE}"
exit "${CODE}"
