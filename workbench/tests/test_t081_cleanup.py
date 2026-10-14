"""离线核对 cleanup 的四轮 PID 前提；从不删除真实隔离 home。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from t081_capability_home import inspect_cleanup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = []
    with tempfile.TemporaryDirectory(prefix='t081-cleanup-check-') as temporary:
        root = Path(temporary).resolve()
        fixture, evidence = root / 'fixture', root / 'evidence'
        fixture.mkdir(); evidence.mkdir()
        home = fixture / 'codex-home'
        home.mkdir()
        marker = home / 'preserve.txt'
        marker.write_text('preserve home\n', encoding='utf-8')
        child = subprocess.Popen([sys.executable, '-c', 'pass'])
        child.wait(timeout=10)
        def populate(number, pid, **changes):
            run = fixture if number == 1 else fixture / ('run-%02d' % number)
            run.mkdir(exist_ok=True)
            (run / 'state').mkdir(exist_ok=True)
            record = {'root': str(fixture), 'run_root': str(run), 'pids': [pid], 'all_confirmed_exited': True, **changes}
            (run / 'owned-pids.json').write_text(json.dumps(record), encoding='utf-8')
            output = evidence / ('capability-run-%02d' % number)
            output.mkdir(exist_ok=True)
            (output / 'run.json').write_text(json.dumps({'processes_stopped': True,
                 'pid_exit': {'all_confirmed_exited': True, 'pids': [pid]}}), encoding='utf-8')
        for number in range(1, 5):
            populate(number, child.pid)
        checked = inspect_cleanup(fixture, evidence)
        assert len(checked['checked_runs']) == 4 and checked['checked_exited_pids'] == [child.pid]
        cases.append('四轮完整退出记录通过')
        for label, change in [('最后一轮 PID 仍活着', lambda: populate(4, __import__('os').getpid())),
                              ('最后一轮未确认退出', lambda: populate(4, child.pid, all_confirmed_exited=False))]:
            change()
            try:
                inspect_cleanup(fixture, evidence)
            except RuntimeError as error:
                cases.append({'rejected': label, 'error': str(error)})
            else:
                raise AssertionError(label + '必须拒绝')
            assert marker.read_text(encoding='utf-8') == 'preserve home\n'
            populate(4, child.pid)
        endpoint = fixture / 'run-04/state/control.sock'
        endpoint.touch()
        try:
            inspect_cleanup(fixture, evidence)
        except RuntimeError as error:
            cases.append({'rejected': '最后一轮端点仍在', 'error': str(error)})
        else:
            raise AssertionError('最后一轮端点必须拒绝')
        assert marker.read_text(encoding='utf-8') == 'preserve home\n'
    result = {'status': 'PASS', 'cases': cases, 'scope': '四轮清理前提；没有调用真实 home 删除',
              'real_codex_turns': 0, 'real_fixture_or_home_written': False}
    (args.output / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
