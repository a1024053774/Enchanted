"""T-187 替身 agy/opencode 受管模式的助手（t187_fake_cli.c 调用），不连模型。
trust <目录>：像 agy 确认信任那样，把目录加进 $HOME/.gemini/antigravity-cli/settings.json 的 trustedWorkspaces，其他键不动。
work <提示文件>：一个回合。审查提示：交结论“可合并”（T-203）：agy 按提示里的命令提交；opencode 的真实会话经 MCP 工具
review_submit 提交，替身不讲 MCP，改用同一个提交入口（reviewResult.ts submit，本会话的 A2A_REQUEST_DIR）模拟工具的效果。派发提示：写 done.txt、提交、
按提示里的交付命令交付。门禁反馈等其他提示：什么都不做。每个回合先停 3 秒，让侧栏能看到“运行中”。
"""
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


def trust(folder):
    settings = Path(os.environ['HOME']) / '.gemini/antigravity-cli/settings.json'
    value = json.loads(settings.read_text(encoding='utf-8'))
    value.setdefault('trustedWorkspaces', []).append(folder)
    settings.write_text(json.dumps(value, indent=2), encoding='utf-8')


def work(prompt_file):
    text = Path(prompt_file).read_text(encoding='utf-8').replace('\x1b[200~', '').replace('\x1b[201~', '')
    time.sleep(3)
    if '审查这一次交付' in text:
        fields = dict(verdict='可合并', findings=[], report={'结论': '候选只改了 done.txt，满足任务卡。',
                                                     '完成条件与变异检查': '变异：删除 done.txt，完成条件失败。'})
        answer = Path(os.environ.get('TMPDIR', '/tmp')) / f'review-fields-{os.getpid()}.json'
        answer.write_text(json.dumps(fields, ensure_ascii=False), encoding='utf-8')
        command = re.search(r'\nELECTRON_RUN_AS_NODE=1 (.+) <文件路径>\n', text)
        if command:
            subprocess.run(['/bin/sh', '-c', 'ELECTRON_RUN_AS_NODE=1 ' + command.group(1) + ' ' + shlex.quote(str(answer))], check=True)
        else:
            # The source tree the backend runs (its gate CLI is src/gates/cli.ts), under the backend's own node.
            source = Path(os.environ['A2A_CLI']).parents[1] / 'reviewResult.ts'
            subprocess.run([os.environ['A2A_NODE'], str(source), 'submit', os.environ['A2A_REQUEST_DIR'], str(answer)], check=True)
        return
    submit = re.search(r'显式交付：\n(.+)\n', text)
    if not submit:
        return
    Path('done.txt').write_text('done\n', encoding='utf-8')
    subprocess.run(['git', 'add', 'done.txt'], check=True)
    subprocess.run(['git', 'commit', '-q', '-m', 'T-187 fixture change'], check=True)
    subprocess.run(['/bin/sh', '-c', submit.group(1).replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')], check=True)


if __name__ == '__main__':
    {'trust': trust, 'work': work}[sys.argv[1]](sys.argv[2])
