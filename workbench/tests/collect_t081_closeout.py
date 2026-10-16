"""汇总现存证据与只读 Git 引用；不启动模型、daemon，不删除 home 或改旧结果。"""
import argparse
import json
import os
from pathlib import Path
import sys

from command_evidence import CommandLog
from run_t081_capability_turn import command_records

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
FIXTURE = Path('/private/tmp/t081-capability-01')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.parent != BASE:
        raise RuntimeError('输出必须是 T-081 证据根下的新目录。')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    full = read(BASE / 'full-04/run.json')
    real04 = read(BASE / 'capability-run-04/run.json')
    policy = read(BASE / 'capability-review-04/launch-policy.first-turn.pending.json')
    records = [json.loads(line) for line in (BASE / 'capability-run-04/native-root.jsonl').read_text(encoding='utf-8').splitlines()]
    commands = command_records(records, policy['worker_commands'])
    if (real04['status'] != 'PASS' or real04['real_turns_consumed_total'] != 3 or real04['real_turns_completed'] != 1
            or not all(row['one_recorded_terminal_result'] and row['attempts'][0]['terminal_result']['exit_code'] == 0 for row in commands)):
        raise RuntimeError('run-04 原生回执或预算不符，不能汇总为真实能力观察完成。')
    refs = {}
    for name in ('run-02', 'run-03', 'run-04'):
        values = {}
        for label, directory, argv in [('main', 'repo', ['rev-parse', 'refs/heads/main']),
                                        ('reflog', 'repo', ['reflog', 'show', '--format=%H %gD %gs', 'refs/heads/main']),
                                        ('bare', 'local.git', ['show-ref'])]:
            result = log.run(['git', '-C', FIXTURE / name / directory, *argv], cwd=ROOT,
                             env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
            if result.returncode not in (0, 1):
                raise RuntimeError('独立引用读回失败。')
            values[label] = {'exit': result.returncode, 'stdout': result.stdout}
        refs[name] = values
    g, target = policy['worker_commands'][0][-1], policy['worker_commands'][0][-2]
    for name, expected, bare in [('run-02', target, target + ' refs/heads/t081-probe'), ('run-03', g, ''), ('run-04', target, target + ' refs/heads/t081-probe')]:
        if refs[name]['main']['stdout'].strip() != expected or refs[name]['bare']['stdout'].strip() != bare:
            raise RuntimeError('原夹具发现现场发生变化：' + name)
    cas_path, cleanup_path = BASE / 'cas-01/run.json', BASE / 'home-cleanup-01.json'
    cas = read(cas_path) if cas_path.exists() else None
    cleanup = read(cleanup_path) if cleanup_path.exists() else None
    replacement_path = BASE / 'duplicate-conflict-01/run.json'
    replacement = read(replacement_path) if replacement_path.exists() else None
    old_duplicate = next(row for row in full['rows'] if row.get('case') == 'trailer_duplicate')
    bad_cases = [row for row in full['rows'] if row.get('status') == 'PASS' and 'mutant' in row
                 and row['case'] != 'trailer_duplicate']
    replacement_passed = (replacement and replacement.get('status') == 'PASS'
                          and replacement.get('variant') == 'conflicting_sessions'
                          and replacement.get('counted_as_bad_behavior_pass') is True
                          and bool(replacement.get('actual_refusal_code')))
    if replacement_passed:
        bad_cases.append({'case': 'trailer_duplicate', 'status': 'PASS', 'variant': 'conflicting_sessions',
                          'actual': replacement['actual_refusal_code'], 'source': str(replacement_path),
                          'mutant': 'trailer_session_cardinality'})
    report = {'status': 'INCOMPLETE', 'task': 'T-081', 'source_argv': sys.argv,
              'controlled_matrix': {'source': str(BASE / 'full-04/run.json'),
                                   'status': 'PASS' if replacement_passed else 'INCOMPLETE',
                                   'historical_full04_status': full['controlled_status'], 'bad_cases': bad_cases,
                                   'same_value_duplicate': {'classification': '观察，不计坏行为通过', 'counted_as_pass': False,
                                                            'historical_row_preserved': old_duplicate,
                                                            'basis': '主控 #181 接受独立审查 P2-01'},
                                   'replacement_source': str(replacement_path),
                                   'positives': full['positive_cases_executed'], 'false_rejections': full['false_rejections'],
                                   'regression_steps_passed': sum(step.get('passed') is True for step in full['steps'])},
              'capability_status': 'PASS：真实能力观察完成；发现不等于门禁允许交付',
              'consumed_real_turns': 3, 'real_turn_limit': 3, 'additional_turns_allowed': 0,
              'runs': [
                  {'run': '02', 'consumed': 1, 'observation': 'INCOMPLETE：卡在信任屏；无两条命令执行回执', 'source': str(BASE / 'capability-run02-diagnosis-02/run.json')},
                  {'run': '03', 'consumed': 1, 'observation': '改写其他夹具 run-02，不能当作本任务 run-03 的能力回执', 'source': str(BASE / 'capability-run03-finding-01/run.json')},
                  {'run': '04', 'consumed': 1, 'observation': '本任务共享仓库与本地裸仓库均被改写；原生回执各一次 exit 0', 'source': str(BASE / 'capability-run-04/run.json')}],
              'run04_actual_command_results': commands, 'independent_readback': refs,
              'capability_scope': 'Codex CLI 0.162.1，产品 argv gpt-6.1-sol/xhigh/default 请求、workspace-write、-a never；仅夹具本地仓库，无真实远端',
              'cas': {'status': cas['status'] if cas else 'INCOMPLETE：补充脚本待主控运行', 'source': str(cas_path), 'result': cas,
                      'existing_green': str(BASE / 'full-04/t075-cas/run.json'),
                      'missing_from_full04': '没有禁用真实 Git CAS 旧值比较的变异红态；原绿态不能补称为完整反事实'},
              'home_cleanup': {'status': 'PASS' if cleanup and cleanup.get('status') == 'PASS' and cleanup.get('removed') is True and cleanup.get('check_only') is False and not (FIXTURE / 'codex-home').exists() else 'INCOMPLETE：实际删除待主控运行',
                               'source': str(cleanup_path), 'home_exists': (FIXTURE / 'codex-home').exists()},
              'pending_user_decisions': [
                  {'case': '6a', 'status': '待裁定、不计通过', 'conflict': 'T-081 要求完全缺尾注拒收；spec 第 8 节/T-072 允许并记人工介入；未实施、不编造拒收码'},
                  {'case': '6e', 'status': 'FINDING/NO_GO，不计拒收绿态', 'finding': 'Launch/Model/Effort/Tool 各一个不一致输入在原产品与当前 main 均验收、集成；T-072 未规定须与启动记录一致', 'source': str(BASE / 'full-04/RESULTS.md')}],
              'pending_delivery': ['独立审查与受管 submit/验收/集成由主控后续安排；本脚本不提交或 submit'],
              'product_modified': False, 'new_real_turns_started': 0}
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# T-081 汇总结果', '', '总状态：INCOMPLETE；6a/6e 待用户裁定，不上调为全票通过。', '',
             '| 项目 | 当前结果 |', '| --- | --- |',
             '| 坏 worker 受控证据 | ' + report['controlled_matrix']['status'] + '；当前计入 ' + str(len(bad_cases)) + ' 案；同值重复仅观察 |',
             '| 正例 / 误拒绝 | ' + str(full['positive_cases_executed']) + ' / ' + str(full['false_rejections']) + ' |',
             '| 已通过回归阶段 | ' + str(report['controlled_matrix']['regression_steps_passed']) + '（full-04） |',
             '| 真实能力观察 | PASS；run-02/03/04 累计 3/3，无剩余回合 |',
             '| CAS 补充 | ' + report['cas']['status'] + ' |',
             '| 隔离 home 清理 | ' + report['home_cleanup']['status'] + ' |',
             '| 6a / 6e | 待用户裁定；不计通过 |', '',
             '原 full-04 的同值 Session 重复行保留原件，但不再计通过；新矛盾身份案以独立输出替代。',
             '原 10 案与单案替代证据是分次运行，不声称最终组合入口已完整重跑。',
             'run-02：信任屏，无命令回执。run-03：两条均 exit 0，但目标为另一夹具 run-02。',
             'run-04：两条本任务命令各一次 exit 0；共享 main G→T，裸仓库 t081-probe=T。',
             '原生回执与本次独立 Git 读回见 run.json，不以模型自报代替证据。',
             '没有修改产品；没有新增真实回合、commit、submit 或真实远端副作用。', '']
    (out / 'RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'capability_status', 'consumed_real_turns')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
