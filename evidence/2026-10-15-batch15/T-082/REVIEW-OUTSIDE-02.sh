#!/usr/bin/env bash
# T-082 第二轮独立审查；由主控在沙箱外运行，不申请权限升级。
# 所有新输出和源码副本都在新的 /tmp 目录。保留现场，不清理旧输出。
# 只用受控 PTY；不启动真实 Codex，不读 auth，不调用模型，不安装或构建。
set -u
ROOT=/Users/luckye/Documents/Code/a2a-wt-t082
OUTPUT=$(mktemp -d /tmp/r82r2-XXXXXX)
CODE=$?
echo "段名：创建第二轮审查输出目录"
echo "output=${OUTPUT}"
echo "exit_code=${CODE}"
if [ "${CODE}" -ne 0 ]; then exit "${CODE}"; fi
export PYTHONDONTWRITEBYTECODE=1
export NODE_DISABLE_COMPILE_CACHE=1
cat > "${OUTPUT}/driver.py" <<'PY'
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

root, out = (Path(x).resolve() for x in sys.argv[1:3])
stage = sys.argv[3]
target = out / stage
target.mkdir()
candidate = '5f7f9816eb9a996377c5b255695244d99c0259e7'
source = out / 'candidate'
prefix = 'evidence/2026-10-15-batch15/T-082/'
paths = [
    'workbench/src', 'workbench/hooks', 'workbench/package.json', 'workbench/LICENSE.synara',
    'workbench/tests/test_task_cards_e2e.py', 'workbench/tests/test_quality_chain_e2e.py',
    'workbench/tests/test_quality_tracer_e2e.py', 'workbench/tests/quality_chain_host.ts',
    'workbench/tests/controlled_quality_pty.ts', 'workbench/tests/test_review_worktree_lifecycle_e2e.py',
    'workbench/tests/test_t082_review_boundary_e2e.py', 'workbench/tests/run_t082_boundary.py',
    prefix + 'protocol-red-green-01/real-review-submit.json',
]
env = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'ELECTRON_', 'NODE_'))}
env.update(PYTHONDONTWRITEBYTECODE='1', NODE_DISABLE_COMPILE_CACHE='1',
           GIT_OPTIONAL_LOCKS='0', A2A_TEST_ARTIFACT_PARENT=str(out / 'f'))
record = {'status': 'INCOMPLETE', 'stage': stage, 'candidate': candidate,
          'output': str(target), 'real_codex_turns': 0,
          'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def command(argv, cwd, timeout=600):
    argv = list(map(str, argv))
    record.update(argv=argv, cwd=str(cwd))
    save(target / 'command.json', {'argv': argv, 'cwd': str(cwd),
         'environment_overrides': {k: env[k] for k in ('PYTHONDONTWRITEBYTECODE',
             'NODE_DISABLE_COMPILE_CACHE', 'GIT_OPTIONAL_LOCKS', 'A2A_TEST_ARTIFACT_PARENT')}})
    with (target / 'stdout.txt').open('xb') as stdout, (target / 'stderr.txt').open('xb') as stderr:
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
    record['observed_exit_code'] = result.returncode
    return result.returncode

def variant(label, changes):
    selected = out / label
    shutil.copytree(source, selected, symlinks=True)
    file = selected / 'workbench/src/gates/core.ts'
    content = file.read_text(encoding='utf-8')
    for before, after in changes:
        if content.count(before) != 1:
            raise RuntimeError('变异目标不唯一：' + label)
        content = content.replace(before, after)
    file.write_text(content, encoding='utf-8')
    record['mutation'] = {'source': str(selected), 'path': 'workbench/src/gates/core.ts',
                          'changes': [{'before': a, 'after': b} for a, b in changes]}
    return selected

def suite(script, cases, selected=source, failure=None):
    argv = [sys.executable, '-B', source / 'workbench/tests' / script,
            '--source', selected, '--output', target / 'result']
    for case in cases:
        argv.extend(['--case', case])
    exit_code = command(argv, source)
    report = json.loads((target / 'result/run.json').read_text(encoding='utf-8'))
    rows = report['cases']
    record.update(report=str(target / 'result/run.json'),
                  outcomes=[{k: row.get(k) for k in ('case', 'outcome', 'failure_id', 'cleanup_failures')}
                            for row in rows], expected_failure=failure)
    valid = (not cases or [row['case'] for row in rows] == cases) and all(
        row['outcome'] != 'harness_error' and not row['cleanup_failures'] for row in rows)
    if failure:
        valid = (valid and len(rows) == 1 and exit_code == 1
                 and rows[0]['outcome'] == 'contract_failure' and rows[0].get('failure_id') == failure
                 and any(a['id'] == failure and a['passed'] is False for a in rows[0]['assertions']))
    else:
        valid = valid and exit_code == 0 and report['status'] == 'PASS'
    if not valid:
        raise RuntimeError('未在规定业务断言取得预期结果；保留 stdout、stderr 和夹具。')

try:
    if stage == '01-source':
        head = subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip()
        if head != candidate:
            raise RuntimeError('冻结候选已改变：' + head)
        node = subprocess.check_output(['node', '--version'], text=True).strip()
        if node != 'v26.5.0':
            raise RuntimeError('需要固定 Node v26.5.0，实际为 ' + node)
        argv = ['git', '-C', str(root), 'archive', candidate, '--', *paths]
        archive_bytes = subprocess.check_output(argv)
        (target / 'necessary-source.tar').write_bytes(archive_bytes)
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode='r:') as archive:
            members = archive.getmembers()
            hook = archive.getmember('workbench/hooks/hook.py')
            if not hook.isfile():
                raise RuntimeError('冻结 hook.py 不是普通文件。')
            for member in members:
                path = Path(member.name)
                permitted = (any(member.name == p or member.name.startswith(p + '/') for p in paths)
                             or any(p.startswith(member.name.rstrip('/') + '/') for p in paths))
                if path.is_absolute() or '..' in path.parts or not permitted:
                    raise RuntimeError('归档成员不在白名单：' + member.name)
                if member.issym():
                    if path.parent.as_posix() != 'workbench/hooks' or member.linkname != 'hook.py':
                        raise RuntimeError('非预期归档链接：' + member.name)
                elif not (member.isfile() or member.isdir()):
                    raise RuntimeError('非预期归档成员类型：' + member.name)
            source.mkdir()
            archive.extractall(source)
        dependencies = (root / 'workbench/node_modules').resolve(strict=True)
        (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
        (out / 'f').mkdir()
        record.update(head=head, node=node, materialize_argv=argv, necessary_paths=paths,
                      dependency_directory=str(dependencies),
                      archive_members=[{'name': m.name, 'link': m.linkname if m.issym() else None} for m in members])
    elif stage == '02-candidate-green':
        suite('test_t082_review_boundary_e2e.py', [
            'tracer_review_copy', 'real_payload_report_roundtrip', 'external_review_boundary_invalidated',
            'shared_refs_changed', 'requirements_workspace_changed',
            'integration_before_end_check', 'integration_before_end_check_clean'])
    elif stage == '03-M1-report-only':
        selected = variant('M1-report-only', [
            ('requireGate(ended, "review_end_check_required");',
             'requireGate(row, "review_end_check_required");')])
        suite('test_t082_review_boundary_e2e.py', ['integration_before_end_check_clean'], selected,
              'REVIEW-END-BEFORE-INTEGRATE')
    elif stage == '04-M2-nonempty-workspace':
        selected = variant('M2-nonempty-workspace', [
            ('requireGate(evidence.review_requirements.mutation_checks.workspace === review.candidate_workspace,',
             'requireGate(Boolean(evidence.review_requirements.mutation_checks.workspace),')])
        suite('test_t082_review_boundary_e2e.py', ['requirements_workspace_changed'], selected,
              'REVIEW-REQUIREMENTS-WORKSPACE')
    elif stage == '05-M3-omit-shared-refs':
        selected = variant('M3-omit-shared-refs', [
            ('requireGate(refs === review.shared_refs, "review_shared_refs_changed",',
             'requireGate(true, "review_shared_refs_changed",')])
        suite('test_t082_review_boundary_e2e.py', ['shared_refs_changed'], selected, 'REVIEW-REFS-INVALIDATE')
    elif stage == '06-M4-false-copy-removed':
        selected = variant('M4-false-copy-removed', [
            ('    rmSync(review.candidate_workspace, { recursive: true, force: false });\n'
             '    requireGate(!existsSync(review.candidate_workspace), "review_candidate_copy_unconfirmed", binding);',
             '    // 独立错误实现：保留副本，却继续记录 removed 和 reclaimed。')])
        suite('test_t082_review_boundary_e2e.py', ['tracer_review_copy'], selected, 'T082-COPY-REMOVED')
    elif stage == '07-t076-properties':
        suite('test_quality_tracer_e2e.py', ['tracer_wrong_candidate', 'tracer_reused_native',
              'tracer_writer_cannot_review', 'tracer_malformed_review',
              'tracer_launch_policy_worker', 'tracer_launch_policy_reviewer'])
    elif stage == '08-t077-lifecycle':
        suite('test_review_worktree_lifecycle_e2e.py', [])
    elif stage == '09-four-launch-refusals':
        code = command([sys.executable, '-B', source / 'workbench/tests/run_t082_boundary.py',
                        '--source', source, '--output', target / 'result'], source)
        result = json.loads((target / 'result/run.json').read_text(encoding='utf-8'))
        record.update(report=str(target / 'result/run.json'), observed_status=result['status'])
        if code != 0 or result['status'] != 'PASS' or result['failures']:
            raise RuntimeError('四种启动参数拒收未全部成立。')
        expected = ['green-tracer', 'readonly-argv', 'wrong-workspace', 'network-enabled', 'tmp-writable']
        if [row['name'] for row in result['steps']] != expected:
            raise RuntimeError('启动拒收用例不完整。')
        if any(row['returncode'] or row['report']['status'] != 'PASS'
               or any(c['outcome'] != 'passed' or c['cleanup_failures'] for c in row['report']['cases'])
               for row in result['steps']):
            raise RuntimeError('启动拒收存在夹具或断言失败。')
    elif stage == '10-tier-evidence-readback':
        # 复用已经独立运行的负例，逐字核对其全部生产源码及驱动与冻结候选相同。
        base = root / prefix / 'outside-command-12-01/t076-launch-policy'
        compared = []
        with tarfile.open(base / 'candidate-source.tar.gz', 'r:gz') as archive:
            for member in archive.getmembers():
                name = member.name
                if member.isfile() and (name.startswith('workbench/src/') or name.startswith('workbench/hooks/')
                    or name in ('workbench/tests/test_quality_tracer_e2e.py',
                                'workbench/tests/test_quality_chain_e2e.py', 'workbench/tests/quality_chain_host.ts',
                                'workbench/tests/controlled_quality_pty.ts', 'workbench/tests/test_task_cards_e2e.py')):
                    actual = archive.extractfile(member).read()
                    frozen = subprocess.check_output(['git', '-C', root, 'show', candidate + ':' + name])
                    if actual != frozen:
                        raise RuntimeError('历史证据源码与候选不同：' + name)
                    compared.append(name)
        if 'workbench/src/gates/core.ts' not in compared or 'workbench/src/panes.ts' not in compared:
            raise RuntimeError('历史归档缺少关键源码。')
        checks = []
        for label, failure in [('worker-missing-override-red', 'TRACER-WORKER-DEFAULT-ARGV'),
                               ('reviewer-missing-override-red', 'TRACER-REVIEWER-DEFAULT-ARGV')]:
            result = json.loads((base / label / 'run.json').read_text(encoding='utf-8'))
            row = result['cases'][0]
            good = (len(result['cases']) == 1 and row['outcome'] == 'contract_failure'
                    and row['failure_id'] == failure and not row['cleanup_failures']
                    and any(a['id'] == failure and a['passed'] is False for a in row['assertions']))
            if not good:
                raise RuntimeError('默认 tier 负例不在原断言处失败：' + label)
            checks.append({'source': str(base / label / 'run.json'), 'failure_id': failure,
                           'assertions': row['assertions']})
        record.update(compared_paths=compared, checks=checks,
                      evidence_type='历史负例只读核对；本次未重跑，不改变其时间含义')
    elif stage == '11-final-receipts':
        receipts = []
        for path in out.rglob('database-readback.json'):
            data = json.loads(path.read_text(encoding='utf-8'))
            stop = json.loads(path.with_name('cleanup.json').read_text(encoding='utf-8'))
            if data['phase'] != 'before-host-stop' or stop['host_exit'] != 0 or stop['failures']:
                raise RuntimeError('夹具停止未核实：' + str(path))
            # 不在清理后重开 WAL 数据库。这里使用每个用例保存的原始读回。
            receipts.append({'database_readback': str(path), 'cleanup': str(path.with_name('cleanup.json')),
                             'host_exit': stop['host_exit'],
                             'launch_ids': [json.loads(r['data'])['id'] for r in data['tables']['launch_records']]})
        previous = [json.loads((out / name / 'assessment.json').read_text(encoding='utf-8'))
                    for name in [
                        '01-source', '02-candidate-green', '03-M1-report-only', '04-M2-nonempty-workspace',
                        '05-M3-omit-shared-refs', '06-M4-false-copy-removed', '07-t076-properties',
                        '08-t077-lifecycle', '09-four-launch-refusals', '10-tier-evidence-readback']]
        head = subprocess.check_output(['git', '-C', root, 'rev-parse', 'HEAD'], text=True).strip()
        if head != candidate:
            raise RuntimeError('审查期间 HEAD 已改变。')
        for path in source.rglob('*'):
            if path.is_file() and 'node_modules' not in path.parts:
                name = path.relative_to(source).as_posix()
                actual = os.readlink(path).encode('utf-8') if path.is_symlink() else path.read_bytes()
                if actual != subprocess.check_output(['git', '-C', root, 'show', candidate + ':' + name]):
                    raise RuntimeError('未变异的候选副本被修改：' + name)
        record.update(head=head, receipts=receipts,
                      sections=[{'stage': r['stage'], 'status': r['status']} for r in previous],
                      preserved_output=str(out), limitation='受控 PTY 只证明门禁；不新增真实 Codex 权限证据。')
        save(target / 'git-status.txt.json', {'stdout': subprocess.check_output(
            ['git', '-C', root, 'status', '--short'], text=True)})
        if not all(r['status'] == 'PASS' for r in previous):
            raise RuntimeError('前面存在未满足预期的段落。')
    else:
        raise RuntimeError('未知段落：' + stage)
    record['status'] = 'PASS'
except Exception as error:
    record.update(error=repr(error), traceback=traceback.format_exc())
finally:
    record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(target / 'assessment.json', record)
    print(json.dumps({k: record.get(k) for k in ('stage', 'status', 'observed_exit_code', 'error')}, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
PY
CODE=$?
echo "exit_code=${CODE}"
if [ "${CODE}" -ne 0 ]; then exit "${CODE}"; fi

TOTAL=0
run_section() {
  NAME=${1}
  echo "段名：${NAME}"
  echo "output=${OUTPUT}/${NAME}"
  python3 -B "${OUTPUT}/driver.py" "${ROOT}" "${OUTPUT}" "${NAME}"
  CODE=$?
  echo "exit_code=${CODE}"
  if [ "${CODE}" -ne 0 ]; then TOTAL=1; fi
}
run_section 01-source
if [ "${TOTAL}" -ne 0 ]; then
  echo "output=${OUTPUT}"
  echo "exit_code=${TOTAL}"
  exit "${TOTAL}"
fi
run_section 02-candidate-green
run_section 03-M1-report-only
run_section 04-M2-nonempty-workspace
run_section 05-M3-omit-shared-refs
run_section 06-M4-false-copy-removed
run_section 07-t076-properties
run_section 08-t077-lifecycle
run_section 09-four-launch-refusals
run_section 10-tier-evidence-readback
run_section 11-final-receipts
echo "段名：第二轮独立审查执行结束，保留全部输出和一次性副本"
echo "output=${OUTPUT}"
echo "exit_code=${TOTAL}"
exit "${TOTAL}"
