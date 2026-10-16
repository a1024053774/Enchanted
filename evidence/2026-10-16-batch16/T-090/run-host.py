"""T-090 宿主检查；由执行主控运行，不启动真实模型。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
VOLUME = Path('/Volumes/WD-Elements')
ARCHIVES = VOLUME / 'a2a-evidence/2026-10-16-batch16/T-090'
FOCUSED = 'test_submit_requires_clean_head_and_cannot_replace_frozen_candidate'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def inventory(root):
    paths = list(root.rglob('*'))
    return {'files': sum(p.is_file() or p.is_symlink() for p in paths),
            'bytes': sum(p.lstat().st_size for p in paths if p.is_file() or p.is_symlink())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['red', 'baseline', 'green'], required=True)
    parser.add_argument('--label', required=True)
    parser.add_argument('--dependencies', type=Path,
                        default=Path('/Users/luckye/Documents/Code/a2a/workbench/node_modules'))
    parser.add_argument('--archive-owned', type=Path, action='append', default=[],
                        help='Archive an explicitly identified, stopped T-090 temporary directory')
    args = parser.parse_args()
    if not VOLUME.is_mount(): raise RuntimeError('外置盘未挂载，不回退内置盘。')
    if not args.label.replace('-', '').isalnum(): raise RuntimeError('Invalid label')
    dependencies = args.dependencies.resolve(strict=True)
    if not (dependencies / 'effect').is_dir() or not (dependencies / 'node-pty').is_dir():
        raise RuntimeError('缺少既有依赖；本脚本不安装依赖。')
    out = ARCHIVES / args.label
    out.mkdir(parents=True, exist_ok=False)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'COOP_', 'CODEX_', 'CLAUDE_', 'NODE_COMPILE_CACHE'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
    report = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'phase': args.phase, 'argv': sys.argv,
              'task': 'T-090', 'attempt': 'a1', 'session': os.environ.get('A2A_SESSION'),
              'launch': 'launch-b4da324aa23d48eda3c1cfcee621a6c5',
              'real_model_turns': 0, 'steps': [], 'archive': str(out),
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}

    def command(argv, cwd=ROOT, expected=0, timeout=600):
        number = len(report['steps']) + 1
        row = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'expected_exit': expected}
        report['steps'].append(row)
        with (out / f'{number:02d}.stdout.txt').open('xb') as stdout, \
                (out / f'{number:02d}.stderr.txt').open('xb') as stderr:
            result = subprocess.run(row['argv'], cwd=cwd, env=env, stdout=stdout, stderr=stderr, timeout=timeout)
        row.update(exit_code=result.returncode, stdout=str(out / f'{number:02d}.stdout.txt'),
                   stderr=str(out / f'{number:02d}.stderr.txt'))
        if expected is not None and result.returncode != expected:
            raise RuntimeError('命令退出码不符：' + repr(row))
        return Path(row['stdout']).read_text(encoding='utf-8').strip()

    def retain_fixture(path):
        path = Path(path).resolve()
        if path.parent != Path('/private/tmp') or not path.name.startswith(('s3f-', 'q76-', 't090-ready-', 't090-source-', 't090-compare-')):
            raise RuntimeError('Unexpected fixture owner: ' + str(path))
        target = out / 'fixtures' / path.name
        before = inventory(path)
        shutil.copytree(path, target, symlinks=True)
        after = inventory(target)
        if before != after: raise RuntimeError('归档文件数或字节数不符')
        save(out / (path.name + '.archive.json'), {'original': str(path), 'archive': str(target),
             **before, 'replay': report['argv']})
        shutil.rmtree(path)
        return str(target)

    try:
        version = command(['node', '--version'])
        if not version.startswith('v26.5.'): raise RuntimeError('需要已核对的 Node 26.5 系列')
        revision = command(['git', 'rev-parse', 'HEAD'])
        report['revision'] = revision
        patch = subprocess.check_output(['git', 'diff', 'HEAD', '--', 'workbench/src/gates', 'workbench/tests'], cwd=ROOT)
        (out / 'candidate.patch').write_bytes(patch)
        for owned in args.archive_owned:
            report.setdefault('collected_archives', []).append(retain_fixture(owned))
        workspace = Path(tempfile.mkdtemp(prefix='t090-source-', dir='/tmp')).resolve()
        source = workspace / 'source'
        report['source_workspace'] = str(workspace)
        command(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--shared', '--no-checkout', ROOT, source])
        command(['git', 'sparse-checkout', 'init', '--cone'], source)
        command(['git', 'sparse-checkout', 'set', 'workbench', 'acceptance', 'fixtures', 'scripts', '.project-map', '.grilling',
                 'evidence/2026-10-15-batch15/T-082/protocol-red-green-01'], source)
        command(['git', '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', revision], source)
        if patch: command(['git', 'apply', out / 'candidate.patch'], source)
        for path in (ROOT / 'workbench/tests').rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and not (source / path.relative_to(ROOT)).exists():
                target = source / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
        frozen = {p: p.read_bytes() for base in ('workbench/src', 'workbench/tests', 'acceptance', 'fixtures')
                  for p in (source / base).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        report['source'] = str(source)
        report['dependencies'] = str(dependencies)

        def legacy(name, suite, focused=False, expected=0):
            target = out / name
            argv = [sys.executable, '-B', source / 'workbench/tests/run_s3_rebased_regression.py',
                    '--suite', suite, '--revision', revision, '--output', target]
            if focused: argv.extend(['--case', FOCUSED])
            # Collect a completed failed run before rejecting its exit status.
            # This preserves the fixture without retrying or changing verdicts.
            command(argv, source, None)
            exit_code = report['steps'][-1]['exit_code']
            result = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            if result['collection_errors']: raise RuntimeError('运行夹具退出未确认，保留原目录')
            retain_fixture(result['artifact_root'])
            if exit_code != expected: raise RuntimeError('原验收退出码不符，已归档现场：' + str(target))
            return result

        def controlled(name, selected, script, cases=(), expected_failure=None):
            target = out / name
            argv = [sys.executable, '-B', source / 'workbench/tests' / script,
                    '--source', selected, '--output', target]
            for case in cases: argv.extend(['--case', case])
            command(argv, source, None)
            exit_code = report['steps'][-1]['exit_code']
            value = json.loads((target / 'run.json').read_text(encoding='utf-8'))
            if any(row['cleanup_failures'] for row in value['cases']):
                raise RuntimeError('宿主退出未确认，保留原目录：' + name)
            retain_fixture(value['artifact_root'])
            if exit_code != (1 if expected_failure else 0):
                raise RuntimeError('受控检查退出码不符，已归档现场：' + name)
            if any(row['outcome'] == 'harness_error' for row in value['cases']):
                raise RuntimeError('宿主或清理错误不能作为业务证据：' + name)
            if not expected_failure and value['status'] != 'PASS':
                raise RuntimeError('业务检查未通过：' + name)
            if expected_failure and not any(row.get('failure_id') == expected_failure for row in value['cases']):
                raise RuntimeError('变异没有命中指定断言：' + name)
            report.setdefault('checks', []).append({'name': name, 'status': 'PASS',
                 'test_status': value['status'], 'expected_failure': expected_failure,
                 'cases': [{'case': row['case'], 'outcome': row['outcome'],
                            'failure_id': row.get('failure_id')} for row in value['cases']]})
            return value

        if args.phase == 'baseline':
            if revision != 'f08a280bdf6142443efd52d4897d2305fd68987f' or (
                    source / 'workbench/src/gates/core.ts').read_bytes() != subprocess.check_output(
                    ['git', 'show', revision + ':workbench/src/gates/core.ts'], cwd=ROOT):
                raise RuntimeError('反例起点检查要求未修复的原产品逻辑')
            controlled('worker-boundary-baseline', source, 'test_t090_review_worker_boundary_e2e.py')
        elif args.phase == 'red':
            if revision != 'f08a280bdf6142443efd52d4897d2305fd68987f':
                raise RuntimeError('红态必须绑定本 worktree 起点')
            if (source / 'workbench/src/gates/core.ts').read_bytes() != subprocess.check_output(
                    ['git', 'show', revision + ':workbench/src/gates/core.ts'], cwd=ROOT):
                raise RuntimeError('红态产品逻辑已改变')
            result = legacy('focused', 'coop', True, 1)
            events = [{**e, 'details': json.loads(e['details'])}
                      for path in (out / 'focused/readbacks').glob('*.json')
                      for e in json.loads(path.read_text(encoding='utf-8'))['tables']['events']]
            errors = [e for e in events if e['type'] == 'review_lifecycle_failed'
                      and e['details']['details'].get('error') == 'review_worker_workspace_changed']
            if result['tests_run'] != 1 or result['errors'] != 1 or not errors:
                raise RuntimeError('未取得指定业务红态；查看原始现场')
            report['red_witness'] = [{'seq': e['seq'], 'type': e['type'],
                                     'phase': e['details']['phase'],
                                     'error': e['details']['details']['error']} for e in errors]
        else:
            command(['node', source / 'workbench/tests/test_ready_file.ts', source, out / 'ready-file-probe'], source)
            publication = json.loads((out / 'ready-file-probe/run.json').read_text(encoding='utf-8'))
            if publication['status'] != 'PASS': raise RuntimeError('Ready 发布探针未通过')
            retain_fixture(publication['artifact_root'])
            report['ready_file_checks'] = [{'id': row['id'], 'passed': row['passed']} for row in publication['checks']]
            result = legacy('focused', 'coop', True)
            if result['tests_run'] != 1 or result['errors'] or result['failures']:
                raise RuntimeError('原冻结候选用例未通过')
            for suite, count in [('coop', 8), ('recovery', 9), ('run', 18), ('cas', 1), ('cards', 15)]:
                result = legacy(suite, suite)
                if result['tests_run'] != count or result['status'] != 'PASS':
                    raise RuntimeError('整组回归未通过：' + suite)

            controlled('worker-boundary', source, 'test_t090_review_worker_boundary_e2e.py')
            controlled('t082-end-and-launch', source, 'test_t082_review_boundary_e2e.py',
                       ['tracer_review_copy', 'external_review_boundary_invalidated', 'real_payload_report_roundtrip',
                        'shared_refs_changed', 'requirements_workspace_changed',
                        'integration_before_end_check', 'integration_before_end_check_clean'])
            # The existing T-082 materializer changes launch facts only. The
            # real gate must refuse each variant; no gate verdict is mocked.
            sys.path.insert(0, str(source / 'workbench/tests'))
            from run_t082_boundary import materialize
            for name, before, after in [
                ('readonly-argv', 'const sandboxMode = "workspace-write";',
                 'const sandboxMode = review ? "read-only" : "workspace-write";'),
                ('wrong-workspace', 'const launchWorkspace = review ? review.candidate_workspace : attempt.workspace;',
                 'const launchWorkspace = review ? review.workspace : attempt.workspace;'),
                ('network-enabled', 'const networkAccess = "false";',
                 'const networkAccess = review ? "true" : "false";'),
                ('tmp-writable', 'const excludeSlashTmp = review ? "true" : "false";',
                 'const excludeSlashTmp = review ? "false" : "false";'),
            ]:
                variant = workspace / 'mutants' / name
                materialize(source, variant, before, after)
                controlled(name, variant, 'test_t082_review_boundary_e2e.py', ['launch_boundary_refused'])

            # A deliberately wrong implementation that skips the unchanged
            # worker check must fail each new behavioral assertion. It leaves
            # copy/launch/refs/reviewer handling intact.
            variant = workspace / 'mutants' / 'worker-check-omitted'
            shutil.copytree(source / 'workbench', variant / 'workbench', symlinks=True,
                            ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
            (variant / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
            core = variant / 'workbench/src/gates/core.ts'
            text = core.read_text(encoding='utf-8')
            before = '''    requireGate(expected && expected.branch === workerBranch && expected.status === "" &&
      await this.git(task.task_id, worker, ["rev-parse", "HEAD"]) === expected.head &&
      await this.git(task.task_id, worker, ["symbolic-ref", "--quiet", "HEAD"], [0, 1]) === expected.branch &&
      await this.git(task.task_id, worker, ["status", "--porcelain=v1", "--untracked-files=all"]) === expected.status,
      "review_worker_workspace_changed", { worker, expected });'''
            if text.count(before) != 1: raise RuntimeError('Worker-boundary mutation target is not unique')
            after = '    // Controlled mutant: omit the unchanged-worker boundary check.'
            core.write_text(text.replace(before, after), encoding='utf-8')
            save(out / 'worker-check-mutation.json', {'path': str(core), 'before': before, 'after': after})
            for case, failure in [('worker_head_changed', 'T090-WORKER-HEAD'),
                                  ('worker_became_dirty', 'T090-WORKER-DIRTY'),
                                  ('worker_branch_changed', 'T090-WORKER-BRANCH')]:
                controlled('worker-check-omitted-' + case, variant,
                           'test_t090_review_worker_boundary_e2e.py', [case], failure)
        changed = [str(p) for p, data in frozen.items() if p.read_bytes() != data]
        report['changed_source_paths'] = changed
        if changed: raise RuntimeError('测试期间源码变化')
        report['source_archive'] = retain_fixture(workspace)
        if args.phase == 'green': report['product_status'] = 'PASS'
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        report['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', report)
        save(BASE / (args.label + '.json'), report)
        save(BASE / (args.label + '.archive.json'), {'original': str(out), 'archive': str(out),
             **inventory(out), 'replay': report['argv']})
        print(json.dumps({'status': report['status'], 'phase': args.phase, 'archive': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
