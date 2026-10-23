"""判据自测，非产品 e2e。失败方式：只凭超时放行；阶段、目标或退出
证据缺失仍放行；正常 ended 也算反例；controller 未关闭就被算反例。
固定业务期望来自 T-146 B；两个不同 launch 输入检验目标关联。
"""
import copy
import json
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[2]
evidence = root / 'evidence/2026-10-23-batch23/T-146-a3'
verify = runpy.run_path(str(evidence / 'red_verdict.py'))['verify']
output = Path(sys.argv[1])
assert not output.exists(), '必须保留旧证据'
report = dict(status='INCOMPLETE', checks=[], scope='只测试红态判据，不证明产品边界')


def rejects(value, kind):
    try:
        verify(value, 1, kind)
    except (AssertionError, KeyError, StopIteration):
        return
    raise AssertionError('无效反例被判据接受')


try:
    sentinel = json.loads((evidence / 'red-verdict-sentinel.json').read_text(encoding='utf-8'))
    for kind in ('baseline', 'flow', 'controller'):
        rejects(sentinel, kind)
    report['checks'].append('initial_timeout_sentinel_rejected_for_all_modes')
    for suffix in ('one', 'different-launch'):
        worker, controller, live = (name + suffix for name in ('worker-', 'controller-', 'live-'))
        r = dict(status='INCOMPLETE', checks=['flow_running', 'flow_natural_cli_exit'],
                 launches={'T-done': worker, 'executor': controller, 'T-live': live},
                 native_exit_observation=dict(shell='/bin/zsh', child_pids=''),
                 mutant='flow-hide-ended', controller_close_result=dict(ok=True),
                 observed={'02-after-cli-exit': dict(flow=[dict(launch=live, state='running')],
                    api_flow=dict(lanes=[], unassigned=[dict(id=live, state='running')])),
                    '03-after-close': dict(api_reflect=dict(nodes=[dict(launch=controller, state='ended')]),
                    api_sidebar=dict(agents=[dict(id=live, state='running')],
                                     terminals=[dict(id=controller, role='shell', state='ended')]))})
        verify(r, 1, 'flow')
        baseline = copy.deepcopy(r)
        baseline.update(mutant=None, revision='bf932d49940104ec099023aa957d06fe95116e92')
        verify(baseline, 1, 'baseline')
        c = copy.deepcopy(r)
        c['mutant'] = 'controller-becomes-shell'
        verify(c, 1, 'controller')
        bad = copy.deepcopy(r)
        bad['observed']['02-after-cli-exit']['flow'].append(dict(launch=worker, state='ended'))
        rejects(bad, 'flow')
        bad = copy.deepcopy(r)
        bad['native_exit_observation']['child_pids'] = '12345'
        rejects(bad, 'flow')
        for field in ('controller_close_result', 'native_exit_observation'):
            bad = copy.deepcopy(c)
            del bad[field]
            rejects(bad, 'controller')
        bad = copy.deepcopy(c)
        bad['observed']['03-after-close']['api_sidebar']['terminals'][0]['id'] = 'unrelated'
        rejects(bad, 'controller')
    report['checks'].append('target_stage_and_business_fields_required_with_two_launch_sets')
    report['status'] = 'PASS'
finally:
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
