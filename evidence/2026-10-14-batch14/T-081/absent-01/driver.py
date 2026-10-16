"""主控或本会话运行：6a 完全无尾注。唯一变异先红，再记候选恰好一次人工介入并集成。"""
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
from test_bad_worker_e2e import ABSENT_BASIS, ABSENT_EXPECTATION

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
SOURCE_ROOTS = ('workbench', 'scripts', 'acceptance', 'fixtures')
LIMIT = 5_000_000
PRODUCT_BASE = '391d70b07ceda29462c06b47116b36829d767001'


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
    report = {'status': 'INCOMPLETE', 'case': '6a', 'variant': 'trailer_absent',
              'expected_behavior': ABSENT_EXPECTATION, 'expectation_basis': ABSENT_BASIS,
              'steps': [], 'real_codex_turns': 0, 'other_cases_rerun': False,
              'product_modified': False, 'refusal_cases_unchanged': [
                  'trailer_partial', 'trailer_duplicate', 'trailer_task', 'trailer_attempt']}
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    try:
        branch = log.run(['git', 'branch', '--show-current'], cwd=ROOT, env=env)
        head = log.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env)
        product = log.run(['git', 'diff', PRODUCT_BASE, '--', 'workbench/src', 'workbench/hooks'], cwd=ROOT, env=env)
        if branch.returncode or branch.stdout.strip() != 'exec/t081':
            raise RuntimeError('不是分配的 exec/t081，停止。')
        if head.returncode or product.returncode or product.stdout:
            raise RuntimeError('产品代码与 T-081 起点不一致，停止，不修产品。')
        report['head'] = head.stdout.strip()
        report['product_base'] = PRODUCT_BASE
        difference = log.run(['git', 'diff', 'HEAD', '--', 'workbench/tests/test_bad_worker_e2e.py',
                              'workbench/tests/prepare_t081_mutants.py', 'workbench/tests/run_t081_bad_worker_suite.py',
                              'workbench/tests/run_t081_absent_case.py'], cwd=ROOT, env=env,
                             stdout_file=out / 'candidate-working-tree.patch')
        if difference.returncode:
            raise RuntimeError('不能保存本次测试差异，停止。')
        temporary = Path(tempfile.mkdtemp(prefix='t81absent-', dir='/tmp')).resolve()
        report['temporary_source'] = str(temporary)
        candidate = temporary / 'candidate'
        candidate.mkdir()
        for directory in SOURCE_ROOTS:
            shutil.copytree(ROOT / directory, candidate / directory, symlinks=True,
                            ignore=shutil.ignore_patterns('node_modules', 'dist', '__pycache__', '.DS_Store'))
        (candidate / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            for directory in SOURCE_ROOTS:
                archive.add(candidate / directory, arcname=directory)
        mutation = prepare(candidate, temporary / 'mutant', 'trailer_absent', out / 'trailer-absent.patch')
        save(out / 'source-manifest.json', {'head': report['head'], 'product_base': PRODUCT_BASE,
             'working_tree_candidate': True, 'candidate': str(candidate), 'mutant': mutation,
             'frozen_source': 'candidate-source.tar.gz', 'tracked_test_diff': 'candidate-working-tree.patch',
             'driver': 'workbench/tests/test_bad_worker_e2e.py', 'entry': 'workbench/src/gates/cli.ts',
             'real_codex_turns': 0})
        shutil.copyfile(Path(__file__), out / 'driver.py')
        sizes(candidate)
        sizes(out)
        for label, source in [('red', Path(mutation['source'])), ('green', candidate)]:
            destination = out / label
            result = log.run([sys.executable, '-B', candidate / 'workbench/tests/test_bad_worker_e2e.py',
                              '--source', source, '--output', destination, '--case', 'trailer_absent'],
                             cwd=ROOT, env=env, timeout=240)
            run = json.loads((destination / 'run.json').read_text(encoding='utf-8'))
            rows = run['cases']
            row = rows[0] if len(rows) == 1 else {}
            observation_path = destination / 'trailer_absent/observation.json'
            observation = json.loads(observation_path.read_text(encoding='utf-8')) if observation_path.is_file() else {}
            checks = observation.get('trailer_checks') or []
            admitted = (len(checks) == 1 and checks[0]['details'].get('missing') is True
                        and checks[0]['details'].get('passed') is True and checks[0]['details'].get('error') is None)
            valid = (len(rows) == 1 and row.get('case') == 'trailer_absent' and not row.get('cleanup_failures')
                     and observation.get('expected') == ABSENT_EXPECTATION and admitted)
            if label == 'red':
                valid = (valid and result.returncode == 1 and row.get('outcome') == 'contract_failure'
                         and row.get('failure_id') == 'BW-ABSENT-ONCE'
                         and observation.get('intervention_count') == 0
                         and observation.get('task', {}).get('state') == 'verified')
            else:
                valid = (valid and result.returncode == 0 and row.get('outcome') == 'passed' and run.get('status') == 'PASS'
                         and observation.get('intervention_count') == 1
                         and observation.get('actual') == 'integrated'
                         and observation.get('task', {}).get('state') == 'accepted'
                         and observation.get('value') == 'worker\n'
                         and observation.get('integrate', {}).get('ok') is True
                         and observation.get('second_integrate', {}).get('ok') is True
                         and len(observation.get('scores') or []) == 1
                         and observation['scores'][0]['facts']['human_interventions'] == 1)
            report['steps'].append({'label': label, 'exit': result.returncode, 'report': str(destination / 'run.json'),
                                    'outcome': row.get('outcome'), 'failure_id': row.get('failure_id'),
                                    'valid_evidence': valid, 'intervention_count': observation.get('intervention_count'),
                                    'observation': str(observation_path)})
            artifact = Path(run['artifact_root'])
            sizes(artifact)
            with tarfile.open(destination / 'fixtures.tar.gz', 'x:gz') as archive:
                archive.add(artifact, arcname=artifact.name)
            sizes(out)
            if not valid:
                raise RuntimeError('非目标业务红态或候选未按契约集成，停止保留：' + label)
        report.update(status='PASS', counted_as_positive_pass=True,
                      note='只证明 6a 完全无尾注。缺一部分、重复、错 task/attempt 的拒收案未改、本轮未重跑。6e 未加。真实回合数 0。')
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    save(out / 'run.json', report)
    (out / 'RESULTS.md').write_text(
        '# 6a 完全无尾注\n\n状态：' + report['status']
        + '\n\n预期：' + ABSENT_EXPECTATION
        + '\n\n红态关掉缺尾注的人工介入写入后，业务断言 BW-ABSENT-ONCE 失败。'
        + '绿态经真实门禁入口集成，人工介入恰好一次，再次集成不新增。'
        + '缺一部分、重复、错 task/attempt 仍由原拒收案覆盖，本轮没有重跑。6e 未加。真实 Codex 回合数 0。\n',
        encoding='utf-8')
    print(json.dumps({key: report.get(key) for key in ('status', 'steps', 'error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
