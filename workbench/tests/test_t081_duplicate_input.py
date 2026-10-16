"""只核对坏行为输入的真实 Git 尾注解析；不启动 daemon 或模型。"""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from test_bad_worker_e2e import BadWorker


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='t081-duplicate-input-') as temporary:
        root = Path(temporary)
        class InputOnly:
            task, launch = 'T-081-input-only', 'fixture-launch'
            native = {'native': 'fixture-native'}
            evidence = root
            a = {'attempt_id': 'fixture-attempt', 'session_id': '11111111-1111-4111-8111-111111111111',
                 'thread_id': 'fixture-thread', 'workspace': str(root)}
            message = None
            def git(self, *values, **kwargs):
                if values[0] == 'commit':
                    self.message = values[values.index('-m') + 1]
                return self.message if values[0] == 'show' else ''
            def oid(self, *args):
                return '1' * 40
            def delivered(self, files, **kwargs):
                return self.a, BadWorker.make_commit(self, self.a, files, **kwargs)
            def refused(self):
                pass
            def check(self, name, condition, expected, actual):
                if not condition:
                    raise AssertionError(name)
        actor = InputOnly()
        BadWorker.trailer_duplicate(actor)
        result = subprocess.run(['git', 'interpret-trailers', '--parse'], input=actor.message + '\n',
                                text=True, capture_output=True, check=True)
        sessions = [line.partition(':')[2].strip() for line in result.stdout.splitlines()
                    if line.startswith('A2A-Session:')]
        valid = len(sessions) == 2 and len(set(sessions)) == 2 and sessions.count(actor.a['session_id']) == 1
        report = {'status': 'PASS' if valid else 'NO_GO',
                  'failure_id': None if valid else 'DUPLICATE-INPUT-NOT-CONTRADICTORY',
                  'requirement': '两个相矛盾 Session：恰好一个本会话，另一个不是；不以重复同值作为错误身份',
                  'current_session': actor.a['session_id'], 'parsed_sessions': sessions,
                  'git_parse': {'argv': result.args, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
                  'scope': '仅证明夹具输入构造；Git 写操作为 spy，不证明真实门禁拒收',
                  'real_codex_turns': 0, 'real_daemon_started': False}
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False))
        return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
