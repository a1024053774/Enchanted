"""主控沙箱外运行：6e 拒收先红后绿，再跑矩阵与串行回归。产品须与 main 一致。"""
import argparse
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

from command_evidence import CommandLog
from prepare_t081_mutants import CASE_MUTANT, prepare
from test_bad_worker_e2e import (ABSENT, ABSENT_EXPECTATION, IDENTITY_CASES, IDENTITY_EXPECTATION,
                                NEGATIVES, POSITIVES, REFUSALS)


ROOT = Path(__file__).resolve().parents[2]
LIMIT = 5_000_000
SUITE_ARCHIVES = {
    'run_s3_rebased_regression.py', 'test_worktree_lifecycle_e2e.py',
    'test_relay_conflict_e2e.py', 'test_conflict_trailer_proofs.py',
    'test_startup_shutdown_e2e.py', 'test_attachment_windows.py',
    'test_multiturn_identity_e2e.py',
}
SOURCE_ROOTS = ('workbench', 'scripts', 'acceptance', 'fixtures')


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def check_sizes(*roots):
    for root in roots:
        for path in root.rglob('*'):
            if path.is_file() and not path.is_symlink() and path.stat().st_size > LIMIT:
                raise RuntimeError('单文件超过 5 MB，停止并保留：' + str(path))


def unpack(archive, target):
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            relative = Path(member.name)
            if relative.is_absolute() or '..' in relative.parts or member.size > LIMIT:
                raise RuntimeError('归档路径/大小越界：' + member.name)
            destination = target / relative
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                with stream.extractfile(member) as source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output)
                destination.chmod(member.mode)
            elif member.issym() and relative.parent in (Path('workbench/hooks'), Path('scripts/git-hooks')) and member.linkname == 'hook.py':
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.symlink_to('hook.py')
            else:
                raise RuntimeError('归档含未批准的非普通文件：' + member.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    evidence = ROOT / 'evidence/2026-10-14-batch14/T-081'
    if out.parent != evidence:
        raise RuntimeError('输出必须是 T-081 证据根内的新子目录。')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    report = {'status': 'INCOMPLETE', 'controlled_status': 'INCOMPLETE', 'product_status': 'INCOMPLETE',
              'task': 'T-081', 'ready_rev': 1, 'argv': sys.argv, 'real_codex_turns': 0,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'steps': [], 'rows': [{'case': '7', 'status': '已知行为', 'counted_as_pass': False,
                                    'finding_verdict': '不改',
                                    'expected': '记为已知行为，不改',
                                    'actual': '20261015T044138Z-ideation-answer-001',
                                    'branch_unchanged': '见 RESULTS.md 第 7 项',
                                    'integration_state': '本轮不重跑'}],
              'false_rejections': None, 'positive_cases_executed': 0, 'findings': [],
              'pending': ['独立交付审查由主控另开只读会话'],
              'excluded_file': 'acceptance/test_herdr_traceability_e2e.py（主控 #160：T-083 所有）'}
    fixtures = None
    frozen = {}

    def command(argv, **kwargs):
        result = log.run(argv, cwd=ROOT, env=env, **kwargs)
        check_sizes(out)
        return result

    def ensure_frozen():
        for name, data in frozen.items():
            path = ROOT / name
            if not path.is_file() or path.read_bytes() != data:
                raise RuntimeError('冻结候选发生变化：' + name)

    def archive_fixture(result, destination, *, suite_owns=False):
        if suite_owns:
            archive = destination / 'fixtures.tar.gz'
            if not archive.is_file() or archive.is_symlink():
                raise RuntimeError('子套件没有交付普通归档文件：' + str(archive))
            check_sizes(destination)
            return
        artifact = result.get('artifact_root')
        if artifact:
            root = Path(artifact)
            check_sizes(root)
            with tarfile.open(destination / 'fixtures.tar.gz', 'x:gz') as stream:
                stream.add(root, arcname=root.name)
            check_sizes(out)

    def case(label, source, name, failure=None):
        ensure_frozen()
        destination = out / label
        result = command([sys.executable, '-B', ROOT / 'workbench/tests/test_bad_worker_e2e.py',
                          '--source', source, '--output', destination, '--case', name], timeout=180)
        data = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
        archive_fixture(data, destination)
        rows = data['cases']
        row = rows[0] if len(rows) == 1 else {}
        valid = (len(rows) == 1 and row.get('case') == name and not row.get('cleanup_failures'))
        if failure:
            valid = (valid and result.returncode == 1 and row.get('outcome') == 'contract_failure'
                     and row.get('failure_id') == failure)
        else:
            valid = valid and result.returncode == 0 and data['status'] == 'PASS' and row.get('outcome') == 'passed'
        report['steps'].append({'label': label, 'report': str(destination / 'run.json'),
                                'exit': result.returncode, 'expected_business_failure': failure,
                                'outcome': row.get('outcome'), 'failure_id': row.get('failure_id'),
                                'valid_evidence': valid, 'counts_toward_acceptance': True,
                                'evidence_kind': 'acceptance'})
        ensure_frozen()
        if not valid:
            raise RuntimeError('非预期结果或非业务红态，停止：' + label)
        observation = destination / name / 'observation.json'
        return json.loads(observation.read_text(encoding='utf-8')) if observation.exists() else {}

    def regression(label, script, flags, *, driver_root=ROOT):
        ensure_frozen()
        destination = out / label
        argv = [sys.executable, '-B', driver_root / 'workbench/tests' / script, '--output', destination, *flags]
        result = command(argv, timeout=2400)
        data = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
        archive_data = {'artifact_root': data['fixture']} if script == 'test_score_schemas.py' else data
        if script == 'run_t081_cas_suite.py':
            for phase in ('red', 'green'):
                archive_fixture({}, destination / phase, suite_owns=True)
        else:
            archive_fixture(archive_data, destination, suite_owns=script in SUITE_ARCHIVES)
        passed = result.returncode == 0 and data['status'] == 'PASS'
        report['steps'].append({'label': label, 'exit': result.returncode,
                                'report': str(destination / 'run.json'), 'passed': passed,
                                'driver_root': str(driver_root),
                                'fixture_archive_owner': 'suite' if script in SUITE_ARCHIVES or script == 'run_t081_cas_suite.py' else 'runner'})
        ensure_frozen()
        if not passed:
            raise RuntimeError('回归失败，停止并保留：' + label)

    try:
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('外置盘未挂载；不安装依赖或回退缓存。')
        for label, argv in [('node-version', ['node', '--version']),
                            ('branch', ['git', 'branch', '--show-current']),
                            ('head', ['git', 'rev-parse', 'HEAD']),
                            ('main-head', ['git', 'rev-parse', '--verify', 'refs/heads/main^{commit}']),
                            ('product-diff', ['git', 'diff', 'main', '--', 'workbench/src', 'workbench/hooks']),
                            ('diff-check', ['git', 'diff', '--check'])]:
            result = command(argv)
            save(out / (label + '.json'), {'argv': result.args, 'exit': result.returncode,
                                         'stdout': result.stdout, 'stderr': result.stderr})
            if result.returncode:
                raise RuntimeError('预检查失败：' + label)
            if label == 'node-version' and not result.stdout.startswith('v26.5.'):
                raise RuntimeError('需要已安装的 Node 26.5。')
            if label == 'branch' and result.stdout.strip() != 'exec/t081':
                raise RuntimeError('不是分配的 exec/t081。')
            if label == 'head':
                head = result.stdout.strip()
                report['head'] = head
            if label == 'main-head':
                main_revision = result.stdout.strip()
                report['main_revision'] = main_revision
            if label == 'product-diff' and result.stdout:
                raise RuntimeError('T-081 产品代码必须与 main 一致；发现差异，停止。')
            if label == 'product-diff':
                report['product_status'] = 'MATCHES_MAIN'
        dependencies = ROOT / 'workbench/node_modules'
        if not dependencies.is_dir():
            raise RuntimeError('已安装依赖不存在。')
        for directory in ('workbench/src', 'workbench/hooks', 'workbench/tests', 'scripts', 'acceptance', 'fixtures'):
            for path in (ROOT / directory).rglob('*'):
                if path.is_file() and not path.is_symlink() and '__pycache__' not in path.parts:
                    frozen[str(path.relative_to(ROOT))] = path.read_bytes()
        fixtures = Path(tempfile.mkdtemp(prefix='t81-', dir='/tmp')).resolve()
        report['fixture_root'] = str(fixtures)
        candidate, current_main = fixtures / 'candidate', fixtures / 'main'
        candidate.mkdir()
        current_main.mkdir()
        for directory in SOURCE_ROOTS:
            shutil.copytree(ROOT / directory, candidate / directory, symlinks=True,
                            ignore=shutil.ignore_patterns('node_modules', 'dist', '__pycache__', '.DS_Store'))
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as stream:
            for directory in SOURCE_ROOTS:
                stream.add(candidate / directory, arcname=directory)
        result = command(['git', 'archive', '--format=tar.gz', main_revision, *SOURCE_ROOTS],
                         stdout_file=out / 'main-source.tar.gz')
        if result.returncode:
            raise RuntimeError('不能冻结当前 main。')
        unpack(out / 'main-source.tar.gz', current_main)
        for source in (candidate, current_main):
            (source / 'workbench/node_modules').symlink_to(dependencies.resolve(), target_is_directory=True)
        save(out / 'source-manifest.json', {
            'product_pin': 'main', 'candidate_revision': head, 'main_revision': main_revision,
            'candidate': str(candidate), 'main': str(current_main),
            'candidate_is_uncommitted': True, 'frozen_paths': list(frozen),
            'source_roots': list(SOURCE_ROOTS),
            'dependencies': str(dependencies.resolve()), 'real_codex_turns': 0,
            'evidence_layer': 'real CLI/daemon/relay/gates/Git/SQLite; controlled PTY/process/native inputs',
        })
        check_sizes(out)
        red = ROOT / 'evidence/2026-10-14-batch14/T-081/full-03/t076-wide/run.json'
        failed = json.loads(red.read_text(encoding='utf-8'))['cases'][0]
        if (failed['case'] != 'widen_red_rules_success' or failed['outcome'] != 'harness_error'
                or not failed['error'].startswith('FileNotFoundError')
                or 'acceptance/test_recovery_e2e.py' not in failed['traceback']):
            raise RuntimeError('缺少 full-03 已保留的快照遗漏失败证据。')
        save(out / 'wide-source-red-reference.json', {'source': str(red), 'case': failed['case'],
             'outcome': failed['outcome'], 'error': failed['error'], 'classification': 'runner 源快照遗漏；不是门禁业务红态'})
        for label, selected in (('main', current_main), ('candidate', candidate)):
            regression('wide-source-control-' + label, 'test_quality_widen_e2e.py',
                       ['--source', selected, '--group', 'wide', '--case', 'widen_red_rules_success'], driver_root=selected)
        mutants = {}
        for name in NEGATIVES:
            mutation = CASE_MUTANT[name]
            if mutation not in mutants:
                mutants[mutation] = prepare(candidate, fixtures / mutation, mutation,
                                            out / (mutation + '.patch'))
            failure = 'BW-FROZEN-INTEGRATION' if name == 'after_review' else 'BW-REJECT-' + name
            red_observed = case('red-' + name, Path(mutants[mutation]['source']), name, failure)
            if name in IDENTITY_CASES and red_observed.get('reply', {}).get('ok') is not True:
                raise RuntimeError('变异体未放行该交付，红态不是删掉对应比较：' + name)
            observed = case('green-' + name, candidate, name)
            report['rows'].append({'case': name, 'status': 'PASS',
                                   'expected': IDENTITY_EXPECTATION if name == 'trailer_duplicate' else REFUSALS.get(name, 'stale_turn; integrate C1 only'),
                                   'actual': observed.get('actual', observed.get('reply', {}).get('error')),
                                   'mutant': mutation, 'red_failure': failure,
                                   'event_location': str(out / ('green-' + name) / name / 'observation.json') + ' events',
                                   'branch_unchanged': ('否；仅允许集成 C1' if name == 'after_review'
                                                        else observed['before'] == observed['after']),
                                   'integration_state': observed['task']['state'],
                                   'observation': str(out / ('green-' + name) / name / 'observation.json')})
        for name in ABSENT:
            mutation = CASE_MUTANT[name]
            if mutation not in mutants:
                mutants[mutation] = prepare(candidate, fixtures / mutation, mutation,
                                            out / (mutation + '.patch'))
            case('red-' + name, Path(mutants[mutation]['source']), name, 'BW-ABSENT-ONCE')
            observed = case('green-' + name, candidate, name)
            report['positive_cases_executed'] += 1
            report['rows'].append({'case': '6a', 'status': 'PASS', 'expected': ABSENT_EXPECTATION,
                                   'actual': observed.get('actual'), 'mutant': mutation,
                                   'red_failure': 'BW-ABSENT-ONCE',
                                   'event_location': str(out / ('green-' + name) / name / 'observation.json') + ' events',
                                   'branch_unchanged': False,
                                   'integration_state': observed['task']['state'],
                                   'intervention_count': observed.get('intervention_count'),
                                   'observation': str(out / ('green-' + name) / name / 'observation.json')})
        save(out / 'mutants.json', mutants)
        for name in POSITIVES:
            case('positive-' + name, candidate, name)
            report['positive_cases_executed'] += 1
            report['rows'].append({'case': name, 'status': 'PASS', 'actual': 'integrated',
                                   'event_location': str(out / ('positive-' + name) / name / 'observation.json') + ' events',
                                   'branch_unchanged': False, 'integration_state': 'accepted'})
        report['false_rejections'] = 0
        for suite in ('coop', 'recovery', 'run', 'cas', 'cards'):
            regression('t075-' + suite, 'run_s3_rebased_regression.py', ['--suite', suite, '--revision', head])
        regression('t077-lifecycle-conflicts', 'test_worktree_lifecycle_e2e.py', ['--phase', 'candidate'])
        pane_path = out / 't077-conflict-panes.json'
        pane = command(['node', ROOT / 'workbench/tests/test_conflict_panes.ts',
                        '--product', candidate, '--output', pane_path])
        if pane.returncode or json.loads(pane_path.read_text(encoding='utf-8'))['status'] != 'PASS':
            raise RuntimeError('T-077 conflict panes 回归失败。')
        for label, script, flags in [
            ('t080-protected', 'test_protected_acceptance_e2e.py', []),
            ('t076-tracer', 'test_quality_tracer_e2e.py', []),
            ('t076-controls', 'test_quality_chain_e2e.py', ['--group', 'controls', '--card-dialect', 'current']),
            ('t076-red', 'test_quality_chain_e2e.py', ['--group', 'red', '--card-dialect', 'current']),
            ('t076-legacy-boundaries', 'test_quality_legacy_e2e.py', []),
            ('t076-wide', 'test_quality_widen_e2e.py', ['--group', 'wide']),
            ('t076-review-faults', 'test_quality_widen_e2e.py', ['--group', 'review-red']),
            ('t076-score-schemas', 'test_score_schemas.py', []),
            ('t077-review-worktrees', 'test_review_worktree_lifecycle_e2e.py', []),
            ('t077-joint', 'test_s3_quality_joint_e2e.py', []),
            ('t077-relay-conflict', 'test_relay_conflict_e2e.py', []),
            ('t077-trailer-conflict', 'test_conflict_trailer_proofs.py',
             ['--input', ROOT / 'evidence/2026-10-11-batch13/T-077/controlled-trailer-input.json']),
            ('t076-startup-shutdown', 'test_startup_shutdown_e2e.py', []),
            ('t076-attachment', 'test_attachment_windows.py', []),
            ('t075-multiturn-identity', 'test_multiturn_identity_e2e.py', []),
        ]:
            regression(label, script, ['--source', candidate, *flags])
        regression('t081-cas-counterfactual', 'run_t081_cas_suite.py', ['--source', candidate])
        report['controlled_status'] = 'PASS'
        status = command([sys.executable, '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py',
                          'status', '--root', ROOT])
        if status.returncode:
            raise RuntimeError('项目地图检查失败。')
        report['status'] = 'PASS'
        ensure_frozen()
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        report['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', report)
        lines = ['# T-081 结果表', '', '状态：' + report['status'], '',
                 '| 案例 | 状态 | 发现判定 | 预期 | 实际拒收码/结果 | 事件位置 | 工作分支是否不动 | 集成状态 |',
                 '| --- | --- | --- | --- | --- | --- | --- | --- |']
        for row in report['rows']:
            lines.append('| ' + ' | '.join(str(row.get(key, '')).replace('|', '\\|')
                                          for key in ('case', 'status', 'finding_verdict', 'expected', 'actual', 'event_location',
                                                      'branch_unchanged', 'integration_state')) + ' |')
        lines.extend(['', '正例执行数：' + str(report['positive_cases_executed']),
                      '误拒绝数：' + str(report['false_rejections']),
                      '原始事件与命令输出位置见 run.json 的 steps 与逐案 observation.json。',
                      '6e 拒收：伪造 Launch、Tool、Model、Effort 期望 trailer_identity_mismatch；带尾注且无启动记录期望 trailer_launch_record_missing。每案先在 /tmp 副本删掉对应比较，红态须放行该交付，再在候选上取绿。',
                      '6a 正向核对完全无尾注恰好记一次人工介入并集成。三个正例计入正例执行数。正确拒收不计入误拒绝。真实 Codex 回合为 0；未运行项不计通过。', ''])
        with (out / 'RESULTS.md').open('x', encoding='utf-8') as stream:
            stream.write('\n'.join(lines))
    print(json.dumps({key: report[key] for key in ('status', 'controlled_status', 'real_codex_turns')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
