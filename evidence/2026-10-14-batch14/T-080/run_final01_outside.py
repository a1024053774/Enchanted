#!/usr/bin/env python3
"""主控运行：冻结候选、T-080 全套、去检查变异体及 T-075/076/077 串行回归。"""
import argparse
import ast
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import traceback


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = 'cdf8fe9b0eebfacf9f8d2ffeff3aecebf1e6eb37'
LIMIT = 5_000_000
OWNED = ['.project-map/templates/task-card.md', 'acceptance/test_coop_e2e.py',
         'acceptance/test_herdr_traceability_e2e.py',
         'workbench/src/gates/taskCards.ts', 'workbench/src/gates/core.ts',
         'workbench/src/gates/qualityProtocol.ts', 'scripts/score', 'workbench/README.md',
         'workbench/tests/run_p_review.py', 'workbench/tests/run_pane_lifecycle.py',
         'workbench/tests/run_s3_rebased_regression.py', 'workbench/tests/run_t076_quality_real.py',
         'workbench/tests/run_t076_real.py', 'workbench/tests/run_worker_delivery.py',
         'workbench/tests/test_attachment_windows.py', 'workbench/tests/test_electron_e2e.py',
         'workbench/tests/test_quality_tracer_e2e.py',
         'workbench/tests/test_quality_chain_e2e.py',
         'workbench/tests/test_quality_widen_e2e.py', 'workbench/tests/test_startup_shutdown_e2e.py',
         'workbench/tests/test_task_cards_e2e.py', 'workbench/tests/test_worktree_lifecycle_e2e.py',
         'workbench/tests/test_protected_acceptance_e2e.py', 'workbench/tests/test_score_schemas.py']
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
ENV.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)


def save(path, data):
    with path.open('x', encoding='utf-8') as output:
        json.dump(data, output, ensure_ascii=False, indent=2)
        output.write('\n')


def sizes(out):
    large = [{'path': str(p), 'bytes': p.stat().st_size} for p in out.rglob('*')
             if p.is_file() and p.stat().st_size > LIMIT]
    if large:
        raise RuntimeError('单文件超过 5 MB；停止并保留现场：' + json.dumps(large))


def run(out, label, argv, timeout=1200):
    sizes(out)
    row = {'label': label, 'argv': list(map(str, argv)), 'cwd': str(ROOT)}
    save(out / (label + '.start.json'), row)
    with (out / (label + '.stdout.bin')).open('xb') as stdout, (out / (label + '.stderr.bin')).open('xb') as stderr:
        p = subprocess.run(row['argv'], cwd=ROOT, env=ENV, stdout=stdout, stderr=stderr, timeout=timeout)
    row['exit'] = p.returncode
    save(out / (label + '.command.json'), row)
    sizes(out)
    return row


def ensure_frozen(archive):
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream.getmembers():
            path = ROOT / member.name
            if member.isfile():
                with stream.extractfile(member) as content:
                    if path.is_symlink() or not path.is_file() or path.read_bytes() != content.read():
                        raise RuntimeError('冻结候选已经改变：' + member.name)
                if path.stat().st_mode & 0o777 != member.mode & 0o777:
                    raise RuntimeError('冻结候选的文件权限改变：' + member.name)
            elif member.issym() and (not path.is_symlink() or os.readlink(path) != member.linkname):
                raise RuntimeError('冻结候选的链接改变：' + member.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != HERE:
        raise RuntimeError('输出必须是 T-080 证据根的一个新子目录。')
    out.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-080',
              'command': sys.argv, 'real_model_calls': 0, 'steps': [],
              'independent_review': '待主控新开只读 reviewer；本阶段不是独立审查',
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    archive = None
    try:
        if sys.version_info[:2] != (3, 9) or not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('需要本机 Python 3.9 及已挂载外置盘；不安装或回退。')
        version = run(out, 'node-version', ['node', '--version'])
        if version['exit'] or not (out / 'node-version.stdout.bin').read_text().startswith('v26.5.'):
            raise RuntimeError('需要已安装的 Node 26.5。')
        for label, argv in [('branch', ['git', 'branch', '--show-current']),
                            ('head', ['git', 'rev-parse', 'HEAD']),
                            ('ancestor', ['git', 'merge-base', '--is-ancestor', BASE, 'HEAD']),
                            ('diff', ['git', 'diff', '--binary', 'HEAD']),
                            ('status', ['git', 'status', '--porcelain=v1', '--untracked-files=all']),
                            ('diff-check', ['git', 'diff', '--check'])]:
            if run(out, label, argv)['exit']:
                raise RuntimeError('预检查失败：' + label)
        if (out / 'branch.stdout.bin').read_text().strip() != 'exec/t080':
            raise RuntimeError('不是分配的 exec/t080 分支。')
        head = (out / 'head.stdout.bin').read_text().strip()
        dependencies = ROOT / 'workbench/node_modules'
        if not dependencies.is_dir() or not os.access(dependencies / 'node-pty/prebuilds/darwin-arm64/spawn-helper', os.X_OK):
            raise RuntimeError('已安装依赖或 spawn-helper 执行权限缺失。')
        fixture = Path(tempfile.mkdtemp(prefix='t80f-', dir='/tmp')).resolve()
        source = fixture / 'source'
        ignore = shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store')
        for folder in ('workbench', 'acceptance', 'fixtures', 'scripts', '.project-map'):
            shutil.copytree(ROOT / folder, source / folder, symlinks=True, ignore=ignore)
        for name in ('AGENTS.md', 'CONTEXT.md', 'intent.md'):
            shutil.copy2(ROOT / name, source / name)
        driver_directory = source / HERE.relative_to(ROOT)
        driver_directory.mkdir(parents=True)
        driver_files = []
        for path in HERE.glob('*.py'):
            shutil.copy2(path, driver_directory / path.name)
            driver_files.append(str(path.relative_to(ROOT)))
        archive = out / 'candidate-source.tar.gz'
        with tarfile.open(archive, 'x:gz') as stream:
            for name in ('workbench', 'acceptance', 'fixtures', 'scripts', '.project-map', 'AGENTS.md', 'CONTEXT.md', 'intent.md', str(HERE.relative_to(ROOT))):
                stream.add(source / name, arcname=name)
        (source / 'workbench/node_modules').symlink_to(dependencies.resolve(), target_is_directory=True)
        save(out / 'source-manifest.json', {'head': head, 'source': str(source), 'source_archive': str(archive),
             'tracked_diff': str(out / 'diff.stdout.bin'), 'owned_files': OWNED,
             'dependencies': str(dependencies), 'uncommitted_candidate': True,
             'driver_files': sorted(driver_files), 'python': sys.version,
             'score_schema_authorization': '主控 #145：逐行读取 v1/v2，新行只写 v2；历史不迁移，不补零'})
        record.update(source=str(source), source_archive=str(archive), head=head)
        sizes(out)
        ensure_frozen(archive)
        # The existing fixture race was red on both products before this edit.
        # Reuse its controlled ACK/repair ordering with the repaired fixture;
        # change no production file in the cdf8fe9b control.
        red_root = HERE / 'run-repair-probe-01'
        red = json.loads((red_root / 'result.json').read_text(encoding='utf-8'))
        if (red.get('status') != 'PASS' or red.get('baseline') != BASE
                or {r['label'] for r in red['observations']} != {'baseline', 'candidate'}
                or any(r['status'] != 'PASS' or r['exit'] != 1 or r['case_outcome'] != 'harness_error'
                       for r in red['observations'])):
            raise RuntimeError('缺少修夹具前的 cdf8fe9b/候选同因红态；停止。')
        save(out / 'run-repair-red-reference.json', {'report': str(red_root / 'result.json'),
             'baseline': BASE, 'observations': red['observations'],
             'classification': '既有夹具缺陷；不是 T-080 产品回归'})
        from run_red_outside import unpack_source
        baseline = fixture / 'run-repair-baseline'
        baseline.mkdir()
        baseline_archive = out / 'run-repair-baseline-source.tar.gz'
        shutil.copy2(red_root / 'baseline-source.tar.gz', baseline_archive)
        with tarfile.open(baseline_archive, 'r:gz') as stream:
            unpack_source(stream, baseline)
        relative = 'workbench/tests/test_quality_chain_e2e.py'
        original_fixture = (baseline / relative).read_text(encoding='utf-8')
        fixed_fixture = (source / relative).read_text(encoding='utf-8')

        def business_checks(text):
            return [ast.dump(node, include_attributes=False) for node in ast.walk(ast.parse(text))
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'self'
                    and node.func.attr == 'check']

        if original_fixture == fixed_fixture or business_checks(original_fixture) != business_checks(fixed_fixture):
            raise RuntimeError('ACK 夹具没有修正，或原业务断言发生改变；停止。')
        (baseline / relative).write_text(fixed_fixture, encoding='utf-8')
        with tarfile.open(baseline_archive, 'r:gz') as stream:
            for member in stream.getmembers():
                if member.isfile() and member.name != relative:
                    with stream.extractfile(member) as content:
                        if (baseline / member.name).read_bytes() != content.read():
                            raise RuntimeError('原产品对照中修改了 ACK 夹具之外的文件：' + member.name)
        (baseline / 'workbench/node_modules').symlink_to(dependencies.resolve(), target_is_directory=True)
        save(out / 'run-repair-fixture-change.json', {'baseline': BASE, 'source': str(baseline),
             'changed_files_from_baseline_archive': [relative], 'business_check_calls_unchanged': True,
             'candidate_fixture': str(source / relative), 'real_model_calls': 0})
        for label, selected in [('run-repair-baseline-fixed', baseline), ('run-repair-candidate-fixed', source)]:
            destination = out / label
            result = run(out, label, [sys.executable, '-B', driver_directory / 'probe_run_repair_outside.py',
                         '--source', selected, '--output', destination])
            report = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
            case = report['cases'][0]
            directory = destination / 'red_run_reject_preserves_worker'
            barrier = json.loads((directory / 'ack-repair-barrier.json').read_text(encoding='utf-8'))
            acknowledgements = list(directory.glob('submit-ack-*.json'))
            ack = json.loads(acknowledgements[0].read_text(encoding='utf-8')) if len(acknowledgements) == 1 else None
            tables = json.loads((directory / 'database-readback.json').read_text(encoding='utf-8'))['tables']
            submissions = [row for row in tables['orchestration_events'] if row['type'] == 'turn_submitted'
                           and json.loads(row['data']).get('dispatch') == barrier['message']['id']]
            reply = json.loads((directory / 'run-result.json').read_text(encoding='utf-8'))['reply']
            correct = (result['exit'] == 0 and report['status'] == 'PASS' and len(report['cases']) == 1
                       and case['outcome'] == 'passed' and not case['cleanup_failures'] and barrier['matched'] is True
                       and any(a['id'] == 'RED-RUN-REPAIR' and a['passed'] for a in case['assertions'])
                       and ack is not None and len(ack['matched_end_events']) == len(submissions) == 1
                       and ack['matched_end_events'][0]['seq'] < submissions[0]['seq']
                       and reply.get('error') == 'run_deadline' and reply['task']['repair'] == barrier['repair'])
            step = {**result, 'report': str(destination / 'run.json'), 'status': 'PASS' if correct else 'INCOMPLETE',
                    'same_ordering_as_red': barrier['matched'], 'business_assertions_unchanged': True}
            record['steps'].append(step)
            save(destination / 'comparison.json', step)
            with tarfile.open(destination / 'fixtures.tar.gz', 'x:gz') as stream:
                stream.add(report['artifact_root'], arcname=Path(report['artifact_root']).name)
            sizes(out)
            ensure_frozen(archive)
            if not correct:
                raise RuntimeError('修后原产品/候选的同一受控时序未通过；保留现场：' + label)
        # The quick format probe and the following full CLI suite both require v2.
        payload = {'schema': 2, 'score_id': 't080-format-fixture', 'created_at': '2026-10-14T00:00:00Z',
                   'source': 'executor', 'launch_id': 'fixture', 'project': 'fixture', 'task': 'T-080',
                   'attempt': 'a1', 'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh',
                   'data': {'result': '通过', 'boundary_discipline': 3, 'boundary_reason': 'fixture',
                            'engineering_taste': 2, 'engineering_reason': 'fixture', 'notes': ''},
                   'facts': {'task_type': '后端逻辑', 'complexity': 'M', 'delivery_rounds': 2,
                             'elapsed_seconds': 1, 'human_interventions': 0,
                             'rejections': {'identity_version': 0, 'path_boundary': 0, 'oracle': 1,
                                            'completion': 0, 'red_state': 0, 'rule_checks': 0,
                                            'independent_review': 0, 'commit_trailers': 0}}}
        format_input = out / 'format-input.jsonl'
        with format_input.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + '\n')
        js = 'const {scoreRecords}=await import(process.argv[1]);const {readFileSync}=await import("node:fs");scoreRecords(readFileSync(process.argv[2],"utf8"));'
        py = 'import json,runpy,sys;sys.path.insert(0,sys.argv[1]);m=runpy.run_path(sys.argv[1]+"/score",run_name="validator");m["validate_scores"]([json.loads(l) for l in open(sys.argv[2],encoding="utf-8")])'
        formats = [run(out, 'format-node', ['node', '--input-type=module', '-e', js,
                    (source / 'workbench/src/gates/qualityProtocol.ts').as_uri(), format_input]),
                   run(out, 'format-herdr', [sys.executable, '-B', '-c', py, source / 'scripts', format_input])]
        save(out / 'score-format-precheck.json', {'status': 'PASS' if all(r['exit'] == 0 for r in formats) else 'INCOMPLETE',
             'schema': 2, 'commands': formats})
        if any(row['exit'] for row in formats):
            raise RuntimeError('v2 完整分数未通过两个格式校验器；停止并保留原始输出。')

        def suite(label, script, flags, *, actual=False, expected_failures=None):
            selected = ROOT if actual else source
            destination = out / label
            command = [sys.executable, '-B', selected / 'workbench/tests' / script,
                       '--output', destination, *flags]
            result = run(out, label, command)
            report = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
            step = {**result, 'report': str(destination / 'run.json'), 'status': report['status']}
            record['steps'].append(step)
            if expected_failures:
                rows = report['cases']
                correct = (result['exit'] == 1 and len(rows) == len(expected_failures)
                           and {row['case'] for row in rows} == set(expected_failures)
                           and all(row['outcome'] == 'contract_failure'
                                   and row.get('failure_id') == expected_failures[row['case']]
                                   and not row['cleanup_failures'] for row in rows))
                step['business_red_confirmed'] = correct
            else:
                correct = result['exit'] == 0 and report['status'] == 'PASS'
            artifact_root = report.get('artifact_root') or (report.get('fixture') if script == 'test_score_schemas.py' else None)
            if artifact_root and not (destination / 'fixtures.tar.gz').exists():
                with tarfile.open(destination / 'fixtures.tar.gz', 'x:gz') as stream:
                    stream.add(artifact_root, arcname=Path(artifact_root).name)
            sizes(out)
            ensure_frozen(archive)
            if not correct:
                raise RuntimeError('验证失败或变异不是业务红态；保留现场：' + label)

        # Full mixed-version CLI checks precede daemon regressions; no main records are written.
        suite('score-schemas', 'test_score_schemas.py', ['--source', source])
        for index, case in enumerate(('test_score_required_abandon_upgrade_and_user',
                                      'test_score_concurrency_corruption_and_start_failure',
                                      'test_score_missing_or_unknown_check_rejected'), 1):
            label = 'score-existing-cli-%d' % index
            herdr_out = out / label
            # launch-worker records its Git version, so use the real checkout's
            # frozen, byte-checked scripts; the test's --root remains /tmp.
            herdr_result = run(out, label, [sys.executable, '-B',
                               ROOT / 'acceptance/test_herdr_traceability_e2e.py',
                               '--scripts-root', ROOT / 'scripts', '--artifacts', herdr_out, '--case', case])
            herdr_report = json.loads((herdr_out / 'summary.json').read_text(encoding='utf-8'))
            record['steps'].append({**herdr_result, 'case': case, 'report': str(herdr_out / 'summary.json'),
                                    'summary': herdr_report})
            if herdr_result['exit'] or herdr_report['tests'] != 1 or herdr_report['failures'] or herdr_report['errors']:
                raise RuntimeError('scripts/score 的既有临时 records / fake Herdr 回归失败：' + case)
            sizes(out)
            ensure_frozen(archive)
        # All primary business assertions are exercised before broader regression.
        suite('protected', 'test_protected_acceptance_e2e.py', ['--source', source])
        mutant = fixture / 'no-oracle-check'
        shutil.copytree(source, mutant, symlinks=True)
        core = mutant / 'workbench/src/gates/core.ts'
        original = core.read_text(encoding='utf-8')
        anchor = '    requireGate(modified.length === 0, "oracle_modified", { modified });\n'
        if original.count(anchor) != 1:
            raise RuntimeError('变异位置不是唯一的一条验收文件拒收检查。')
        core.write_text(original.replace(anchor, '', 1), encoding='utf-8')
        save(out / 'mutation.json', {'source': str(mutant), 'changed_files': ['workbench/src/gates/core.ts'],
             'remove_once': anchor, 'schema_claim_feedback_and_score_unchanged': True, 'committed': False})
        suite('mutant', 'test_protected_acceptance_e2e.py',
              ['--source', mutant, '--case', 'oracle_modified', '--case', 'oracle_directory_added'],
              expected_failures={'oracle_modified': 'ORACLE-MODIFIED', 'oracle_directory_added': 'ORACLE-MODIFIED'})
        limit_mutant = fixture / 'fourth-rejection-limit'
        shutil.copytree(source, limit_mutant, symlinks=True)
        limit_core = limit_mutant / 'workbench/src/gates/core.ts'
        before = limit_core.read_text(encoding='utf-8')
        anchor = 'check, count, stopped: count >= 3, failure'
        if before.count(anchor) != 1:
            raise RuntimeError('第三次打回上限的变异位置不唯一。')
        replacement = 'check, count, stopped: count >= 4, failure'
        limit_core.write_text(before.replace(anchor, replacement, 1), encoding='utf-8')
        save(out / 'limit-mutation.json', {'source': str(limit_mutant),
             'changed_files': ['workbench/src/gates/core.ts'], 'replace_once': [anchor, replacement],
             'purpose': '证明修正后的上限测试仍会拒绝第三次不停止的产品', 'committed': False})
        suite('limit-mutant', 'test_protected_acceptance_e2e.py',
              ['--source', limit_mutant, '--case', 'oracle_three_rejections'],
              expected_failures={'oracle_three_rejections': 'ORACLE-THREE-LIMIT'})
        for name in ('cards', 'coop', 'recovery', 'run', 'cas'):
            suite('t075-' + name, 'run_s3_rebased_regression.py', ['--suite', name, '--revision', head], actual=True)
        suite('t077-lifecycle-conflicts', 'test_worktree_lifecycle_e2e.py', ['--phase', 'candidate'], actual=True)
        pane_report = out / 't077-conflict-panes.json'
        pane_result = run(out, 't077-conflict-panes', ['node', source / 'workbench/tests/test_conflict_panes.ts',
                          '--product', source, '--output', pane_report])
        pane_data = json.loads(pane_report.read_text(encoding='utf-8'))
        record['steps'].append({**pane_result, 'report': str(pane_report), 'status': pane_data['status']})
        if pane_result['exit'] or pane_data['status'] != 'PASS':
            raise RuntimeError('T-077 原窗格冲突边界回归失败。')
        for label, script, flags in [
                ('t076-tracer', 'test_quality_tracer_e2e.py', []),
                ('t076-controls', 'test_quality_chain_e2e.py', ['--group', 'controls', '--card-dialect', 'current']),
                ('t076-quality-red-contracts', 'test_quality_chain_e2e.py', ['--group', 'red', '--card-dialect', 'current']),
                ('t076-legacy-boundaries', 'test_quality_legacy_e2e.py', []),
                ('t076-wide', 'test_quality_widen_e2e.py', ['--group', 'wide']),
                ('t076-review-faults', 'test_quality_widen_e2e.py', ['--group', 'review-red']),
                ('t077-review-worktrees', 'test_review_worktree_lifecycle_e2e.py', []),
                ('t077-joint', 'test_s3_quality_joint_e2e.py', []),
                ('t077-relay-conflict', 'test_relay_conflict_e2e.py', []),
                ('t077-trailer-conflicts', 'test_conflict_trailer_proofs.py',
                 ['--input', ROOT / 'evidence/2026-10-11-batch13/T-077/controlled-trailer-input.json']),
                ('t076-startup-shutdown', 'test_startup_shutdown_e2e.py', []),
                ('t076-attachment-windows', 'test_attachment_windows.py', [])]:
            suite(label, script, ['--source', source, *flags])
        check = run(out, 'project-map', [sys.executable, '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
        if check['exit']:
            raise RuntimeError('project-map status 不是 0 problems / 0 stale。')
        ensure_frozen(archive)
        record.update(status='PASS', product_status='INCOMPLETE',
                      scope='受控机械门禁和指定回归通过；未做真实模型或独立交付审查')
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
