#!/usr/bin/env python3
"""T-106 CLI 权限基线探针；不启动后台、Electron、CLI agent 或模型。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    # 先独占打开，保留既有结果；异常也写进本次摘要。
    with args.summary.open('x', encoding='utf-8') as output:
        report = dict(status='INCOMPLETE', task='T-106', attempt='a1',
                      scope='真实 gates CLI 的本地身份拒绝；不证明 daemon、Electron 或模型行为',
                      source=str(source), model_turns=0, fake_api_requests=0, commands=[])
        try:
            report['revision'] = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
            report['node'] = subprocess.check_output(['node', '--version'], text=True).strip()
            # 不沿用 worker 的身份或 operator 凭据；合成主控身份只用于触发本地拒绝。
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('A2A_', 'CLAUDE_', 'CODEX_', 'ANTHROPIC_', 'GIT_'))
                   and key not in ('NODE_OPTIONS', 'NODE_PATH', 'ELECTRON_RUN_AS_NODE')}
            env.update(A2A_LAUNCH='t106-synthetic-controller', A2A_ROLE='controller',
                       A2A_PRESET='executor')
            state = '/private/tmp/a2a-t106-no-daemon-' + uuid.uuid4().hex
            card = state + '/uncreated-card.json'
            cases = [
                ['card_template', '--repo', str(source)],
                ['card_validate', '--card', card],
                ['card_save', '--card', card, '--expected-version', '0'],
                ['create', '--repo', str(source), '--project', 't106-probe',
                 '--branch', 'refs/heads/main', '--card-version', '1'],
            ]
            for fields in cases:
                argv = ['node', str(source / 'workbench/src/gates/cli.ts'),
                        '--state', state, '--task', 'T106-probe'] + fields
                result = subprocess.run(argv, env=env, text=True, capture_output=True, timeout=15)
                item = dict(argv=argv, exit=result.returncode,
                            stdout=result.stdout, stderr=result.stderr)
                report['commands'].append(item)
                observed = json.loads(result.stdout)
                if result.returncode != 1 or observed != dict(
                        ok=False, error='daemon_call_failed', details='Error: worker_command_forbidden'):
                    raise RuntimeError('CLI 拒绝与基线预期不符；停止，不推断其他入口可用。')
            report['status'] = 'BLOCKED'
            report['observed'] = '四条任务卡/注册命令均在本地身份检查处被拒绝；未连接后台。'
        except Exception as error:
            report['error'] = repr(error)
            raise
        finally:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write('\n')


if __name__ == '__main__':
    main()
