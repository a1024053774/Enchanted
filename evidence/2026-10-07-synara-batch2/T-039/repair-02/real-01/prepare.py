import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
A2A = Path("/Users/luckye/Documents/Code/a2a")
FORK = Path('/Users/luckye/Documents/Code/synara')
CANDIDATE = 'fc9e36c75af3bbcf701551abbb911883b94217c2'

def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def run(argv, cwd=FORK, **kwargs):
    p = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, **kwargs)
    record = dict(time=datetime.now(timezone.utc).isoformat(), argv=argv, cwd=str(cwd),
                  stdout=p.stdout, stderr=p.stderr, exit=p.returncode)
    with (HERE / 'preparation.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')
    return p

assert not (HERE / 'runtime.json').exists()
assert run(['git', 'rev-parse', 'HEAD']).stdout.strip() == CANDIDATE
assert run(['git', 'diff', '--exit-code', 'HEAD']).returncode == 0
assert Path('/Volumes/WD-Elements').is_mount()
root = Path(tempfile.mkdtemp(prefix='a2a-t039-r02-', dir='/tmp')).resolve()
root.chmod(0o700)
repo = root / 'fixture'
repo.mkdir()
home = root / 'codex-home'
home.mkdir(mode=0o700)
synara = root / 'synara-home'
(synara / 'userdata').mkdir(parents=True)
shutil.copyfile(Path('/Users/luckye/.codex/auth.json'), home / 'auth.json')
(home / 'auth.json').chmod(0o600)
config = f'''check_for_update_on_startup = false
cli_auth_credentials_store = "file"
service_tier = "fast"
[projects.{json.dumps(str(repo))}]
trust_level = "trusted"
'''
(home / 'config.toml').write_text(config, encoding='utf-8')
(home / 'rules').mkdir()
(home / 'rules/default.rules').write_text(
    'prefix_rule(pattern=["git", "add"], decision="allow")\n'
    'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
for name in ('pager.py', 'CONTRACT.md'):
    shutil.copyfile(A2A / 'fixtures/pagination' / name, repo / name)
for args in (['init'], ['config', 'user.name', 'T-039 isolated fixture'],
             ['config', 'user.email', 't039@invalid.local'],
             ['add', 'pager.py', 'CONTRACT.md'], ['commit', '-m', 'Frozen faulty pagination starter']):
    assert run(['git', *args], cwd=repo).returncode == 0
base = run(['git', 'rev-parse', 'HEAD'], cwd=repo).stdout.strip()
instructions = '只在分配的 worktree 内按照 CONTRACT.md 实现 pager.py。不得修改合同或任何验收工具。自行检查实现并 git add、git commit，然后使用门禁提供的 a2a_submit 工具显式交付完整提交号。模型结束或自述完成不算交付。不需要向人提问；若发生任何权限或问题对话，停止并保留现场。不要读写用户配置、Herdr 或其他 Synara 数据。\n'
(root / 'instructions.txt').write_text(instructions, encoding='utf-8')
binary = Path(shutil.which('codex')).resolve()
version = run([str(binary), '--version']).stdout.strip()
# Only the concrete fixed CLI and required startup flags are injected.
launcher = root / 'codex-fixed'
launcher.write_text('#!/bin/sh\nexec ' + str(binary) + ' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n', encoding='utf-8')
launcher.chmod(0o700)
providers = {name: {'enabled': False} for name in
             ('claude', 'antigravity', 'grok', 'droid', 'cursor', 'opencode', 'pi', 'omp', 'devin', 'acp')}
providers['codex'] = {'enabled': True, 'binaryPath': str(launcher), 'homePath': str(home)}
settings = {'enableProviderUpdateChecks': False, 'providers': providers}
(synara / 'userdata/settings.json').write_text(json.dumps(settings), encoding='utf-8')
with socket.socket() as ipv4, socket.socket(socket.AF_INET6) as ipv6:
    ipv4.bind(('127.0.0.1', 0))
    port = ipv4.getsockname()[1]
    ipv6.bind(('::1', port))
runtime = dict(root=str(root), repo=str(repo), codex_home=str(home), synara_home=str(synara),
               base=base, endpoint=f'http://127.0.0.1:{port}', port=port, slot='t039-real02',
               fork=CANDIDATE, codex_binary=str(binary), codex_version=version,
               controller='Claude Code wF:pM', worker='s2-t039', spec='synara-m1-2026-10-07',
               runtimeMode='full-access', model='gpt-6.1-sol', reasoningEffort='xhigh', fastMode=True)
save('runtime.json', runtime)
save('isolated-config.json', dict(config=config, rules=(home / 'rules/default.rules').read_text(),
                                settings=settings, launcher=launcher.read_text(), copied=['auth.json'], hooks=[]))
oracle = run(['python3', '-B', str(A2A / 'acceptance/pagination_oracle.py'), str(repo)], cwd=A2A)
save('oracle-known-bad.json', dict(argv=oracle.args, stdout=oracle.stdout, stderr=oracle.stderr, exit=oracle.returncode))
assert oracle.returncode == 1
env = dict(os.environ, A2A_SYNARA_SLOT='t039-real02', CODEX_HOME=str(home))
dry = run(['./a2a/scripts/bun', 'run', 'dev:server', '--home-dir', str(synara),
           '--port', str(port), '--host', '127.0.0.1', '--dry-run'], env=env, timeout=60)
save('server-dry-run.json', dict(argv=dry.args, stdout=dry.stdout, stderr=dry.stderr, exit=dry.returncode))
assert dry.returncode == 0
print(json.dumps(runtime, ensure_ascii=False, indent=2))
