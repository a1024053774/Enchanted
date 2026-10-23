"""红态判定：只接受目标阶段保存的业务违约；错误字符串不能替代证据。

失败方式：初始场景的超时被算作 controller 反例；缺失退出/关闭证据；
目标对象取错；一个正常的 ended 快照也被当作反例。合同来自任务卡 B。
"""
import json
from pathlib import Path
import sys


def verify(report, exit_code, kind):
    assert exit_code != 0 and report['status'] != 'PASS', '进程必须失败'
    assert 'flow_running' in report['checks'], '必须先通过初始三处运行检查'
    launches = report['launches']
    worker, controller, live = launches['T-done'], launches['executor'], launches['T-live']
    exit_observation = report['native_exit_observation']
    assert exit_observation['shell'].endswith('zsh') and not exit_observation['child_pids'], '缺 CLI 已退出且 shell 存活的观察'
    if kind in ('baseline', 'flow'):
        assert report.get('mutant') == ('flow-hide-ended' if kind == 'flow' else None)
        if kind == 'baseline':
            assert report['revision'] == 'bf932d49940104ec099023aa957d06fe95116e92'
        phase = report['observed']['02-after-cli-exit']
        dom = {row['launch']: row['state'] for row in phase['flow']}
        api = phase['api_flow']
        flow = {row['id']: row['state'] for row in api['unassigned'] +
                [a for lane in api['lanes'] for a in lane['agents'] + lane['monitors']]}
        assert dom.get(live) == flow.get(live) == 'running', '对照 worker 应仍运行'
        assert dom.get(worker) != 'ended' and flow.get(worker) != 'ended', '必须观察到目标结束会话被流程遗漏或状态错误'
    elif kind == 'controller':
        assert report['mutant'] == 'controller-becomes-shell'
        assert 'flow_natural_cli_exit' in report['checks'], '必须先通过 worker 退出场景'
        assert report['controller_close_result']['ok'], '必须确实关闭主控终端'
        phase = report['observed']['03-after-close']
        node = next(row for row in phase['api_reflect']['nodes'] if row['launch'] == controller)
        assert node['state'] == 'ended', 'Reflect 必须观察到该主控已结束'
        sidebar = phase['api_sidebar']
        assert any(row['id'] == live and row['state'] == 'running' for row in sidebar['agents'])
        assert not any(row['id'] == controller for row in sidebar['agents']), '变异应丢失主控 agent'
        assert any(row['id'] == controller and row['role'] == 'shell' and row['state'] == 'ended'
                   for row in sidebar['terminals']), '必须观察到同一 launch 被降成普通终端'
    else:
        raise AssertionError('未知反例类型')


if __name__ == '__main__':
    summary, code, kind = sys.argv[1:]
    verify(json.loads(Path(summary).read_text(encoding='utf-8')), int(code), kind)
    print('PASS: 目标阶段的实际业务字段拒绝了已知坏实现')
