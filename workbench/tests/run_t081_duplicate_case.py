"""主控运行：只跑矛盾 Session 一案；唯一变异先红，再记录候选实际拒收码。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback

from command_evidence import CommandLog
from prepare_t081_mutants import prepare
from test_bad_worker_e2e import IDENTITY_BASIS, IDENTITY_EXPECTATION

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
SOURCE_ROOTS = ('workbench', 'scripts', 'acceptance', 'fixtures')
LIMIT = 5_000_000
EXPECTED_BASE = '3ee28bc3ad77595e23b77dbef34af20c5370dea9'


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write('\n')


def sizes(root):
    for path in root.rglob('*'):
        if path.is_file() and not path.is_symlink() and path.stat().st_size > LIMIT:
            raise RuntimeError('单文件超过 5 MB，停止并保留：' + str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != BASE:
        raise RuntimeError('输出须为本票证据根的新子目录。')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    report = {'status': 'INCOMPLETE', 'case': 'trailer_duplicate', 'variant': 'conflicting_sessions',
              'expected_behavior': IDENTITY_EXPECTATION, 'expectation_basis': IDENTITY_BASIS,
              'expected_refusal_code': None, 'actual_refusal_code': None, 'steps': [],
              'real_codex_turns': 0, 'other_cases_rerun': False, 'product_modified': False,
              'differential_review': '运行后进行，当前未执行'}
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        head = log.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env)
        product = log.run(['git', 'diff', '391d70b0', '--', 'workbench/src', 'workbench/hooks'], cwd=ROOT, env=env)
        if head.returncode or head.stdout.strip() != EXPECTED_BASE or product.returncode or product.stdout:
            raise RuntimeError('产品代码与 T-081 起点不一致，停止，不修产品。')
        report['base_revision'] = head.stdout.strip()
        difference = log.run(['git', 'diff', 'HEAD', '--', 'workbench/tests'], cwd=ROOT, env=env,
                             stdout_file=out / 'candidate-working-tree.patch')
        if difference.returncode:
            raise RuntimeError('不能保存本次测试差异，停止。')
        old_path = BASE / 'full-04/green-trailer_duplicate/trailer_duplicate/observation.json'
        old = json.loads(old_path.read_text(encoding='utf-8'))
        old_sessions = old['reply']['details']['trailers']['session']
        if len(old_sessions) != 2 or len(set(old_sessions)) != 1:
            raise RuntimeError('历史同值观察的输入不符，不能重新分类。')
        save(out / 'same-value-observation.json', {'status': 'INCOMPLETE', 'classification': '仅观察，不计坏行为通过',
             'counted_as_pass': False, 'source': str(old_path), 'sessions': old_sessions,
             'observed_refusal_code': old['actual'], 'basis': '主控 #181 接受 independent-review-01 P2-01',
             'original_evidence_preserved': True})
        temporary = Path(tempfile.mkdtemp(prefix='t81dup-', dir='/tmp')).resolve()
        candidate = temporary / 'candidate'
        candidate.mkdir()
        for directory in SOURCE_ROOTS:
            shutil.copytree(ROOT / directory, candidate / directory, symlinks=True,
                            ignore=shutil.ignore_patterns('node_modules', 'dist', '__pycache__', '.DS_Store'))
        (candidate / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            for directory in SOURCE_ROOTS:
                archive.add(candidate / directory, arcname=directory)
        mutation = prepare(candidate, temporary / 'mutant', 'trailer_session_cardinality', out / 'session-cardinality.patch')
        save(out / 'source-manifest.json', {'revision': report['base_revision'], 'working_tree_candidate': True,
             'candidate': str(candidate), 'mutant': mutation, 'frozen_source': 'candidate-source.tar.gz',
             'tracked_test_diff': 'candidate-working-tree.patch',
             'driver': 'workbench/tests/test_bad_worker_e2e.py', 'real_codex_turns': 0})
        shutil.copyfile(Path(__file__), out / 'driver.py')
        sizes(candidate); sizes(out)
        for label, source in [('red', Path(mutation['source'])), ('green', candidate)]:
            destination = out / label
            result = log.run([sys.executable, '-B', candidate / 'workbench/tests/test_bad_worker_e2e.py',
                              '--source', source, '--output', destination, '--case', 'trailer_duplicate'],
                             cwd=ROOT, env=env, timeout=180)
            run = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
            rows = run['cases']
            row = rows[0] if len(rows) == 1 else {}
            observation = json.loads((destination / 'trailer_duplicate/observation.json').read_text(encoding='utf-8'))
            checks = observation['trailer_checks']
            sessions = observation['expected_sessions']
            valid = (len(rows) == 1 and row.get('case') == 'trailer_duplicate' and not row.get('cleanup_failures')
                     and len(checks) == 1 and len(sessions) == 2 and len(set(sessions)) == 2
                     and checks[0]['details']['trailers'].get('session') == sessions)
            if label == 'red':
                valid = (valid and result.returncode == 1 and row['outcome'] == 'contract_failure'
                         and row['failure_id'] == 'BW-REJECT-trailer_duplicate'
                         and observation['reply'].get('ok') is True and checks[0]['details']['passed'] is True)
            else:
                valid = (valid and result.returncode == 0 and row['outcome'] == 'passed' and run['status'] == 'PASS'
                         and observation['reply'].get('ok') is False and isinstance(observation['actual'], str)
                         and bool(observation['actual']) and checks[0]['details']['passed'] is False
                         and checks[0]['details']['error'] == observation['actual']
                         and observation['before'] == observation['after'] and observation['task']['state'] != 'accepted')
                report['actual_refusal_code'] = observation['actual']
            report['steps'].append({'label': label, 'exit': result.returncode, 'report': str(destination / 'run.json'),
                                    'outcome': row.get('outcome'), 'failure_id': row.get('failure_id'), 'valid_evidence': valid,
                                    'observation': str(destination / 'trailer_duplicate/observation.json')})
            artifact = Path(run['artifact_root'])
            sizes(artifact)
            with tarfile.open(destination / 'fixtures.tar.gz', 'x:gz') as archive:
                archive.add(artifact, arcname=artifact.name)
            sizes(out)
            if not valid:
                if label == 'green' and observation['reply'].get('ok') is True:
                    report['status'] = 'NO_GO'
                    report['product_finding'] = 'NO_GO：矛盾 Session 被当前产品放过，停下报告，不修产品'
                raise RuntimeError('非目标业务红态或候选未拒收，停止保留：' + label)
        report.update(status='PASS', counted_as_bad_behavior_pass=True, replacement_bad_cases=1,
                      note='只证明新矛盾身份案；原同值案为观察。其他 10 案/正例/回归未在本次重跑。')
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    save(out / 'run.json', report)
    (out / 'RESULTS.md').write_text('# 矛盾 Session 单案结果\n\n状态：' + report['status']
        + '\n\n规范预期：' + IDENTITY_EXPECTATION + '\n\n实际拒收码：' + str(report['actual_refusal_code'])
        + '\n\n原同值案例只作观察，不计通过。其他案例没有重跑，真实回合数 0。\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
