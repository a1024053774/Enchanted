"""No-model native startup probe. Run outside Codex's sandbox; retains the screen and hook input.
Only the probe's isolated home is removed. Never loads the user's credentials or configuration.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import shutil
import signal
import subprocess
import tempfile
import termios
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--trust', choices=['trusted', 'untrusted', 'unset'], default='trusted')
    parser.add_argument('--open-restricted', action='store_true', help='Only select the non-persisting Open restricted choice')
    args = parser.parse_args()
    assert not args.open_restricted or args.trust == 'untrusted'
    assert not args.summary.exists(), 'Fresh summary path required'
    root = Path(tempfile.mkdtemp(prefix='t141-start-', dir='/private/tmp')).resolve()
    home, repo = root / 'codex', root / 'worktrees' / 'demo' / 'T-1'
    home.mkdir(); repo.mkdir(parents=True)
    subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-q', str(repo)], check=True)
    hook = root / 'start.jsonl'
    script = root / 'hook.py'
    script.write_text('import sys,pathlib\npathlib.Path(' + repr(str(hook)) + ').open("a").write(sys.stdin.read()+"\\n")\n', encoding='utf-8')
    trust = '' if args.trust == 'unset' else f'[projects.{json.dumps(str(root))}]\ntrust_level="{args.trust}"\n'
    (home / 'config.toml').write_text('model="gpt-6.1-sol"\nmodel_provider="fixture"\n' + trust +
        '[model_providers.fixture]\nname="No-model startup probe"\nbase_url="http://127.0.0.1:1/v1"\n'
        'wire_api="responses"\nrequires_openai_auth=false\n', encoding='utf-8')
    report = dict(status='INCOMPLETE', fixture=str(root), model_calls=0, trust=args.trust)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, b'\x2d\x00\xa0\x00\x00\x00\x00\x00')
    env = dict(os.environ, CODEX_HOME=str(home))
    argv = [shutil.which('codex'), '--no-daemon', '--no-alt-screen', '-C', str(repo), '-a', 'never', '-s', 'workspace-write',
            '-c', 'check_for_update_on_startup=false', '-c', 'tui.notifications=false',
            '-c', 'hooks.SessionStart=[{hooks=[{type="command",command=' + json.dumps('python3 ' + str(script)) + ',timeout=10}]}]',
            '--dangerously-bypass-hook-trust']
    process = None
    screen = b''
    choice_written = False
    choice_seen_at = None
    last_output_at = time.monotonic()
    try:
        def control_terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        process = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, env=env, preexec_fn=control_terminal)
        os.close(slave)
        deadline = time.monotonic() + 18
        while process.poll() is None and time.monotonic() < deadline:
            if args.open_restricted and not choice_written and choice_seen_at is not None and (
                    time.monotonic() - last_output_at >= .8 or time.monotonic() - choice_seen_at >= 5):
                os.write(master, b'\r')
                choice_written = True
            if not select.select([master], [], [], .2)[0]:
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            screen += chunk
            last_output_at = time.monotonic()
            if b'\x1b[6n' in chunk:
                os.write(master, b'\x1b[1;1R')
            if b'\x1b[c' in chunk or b'\x1b[0c' in chunk:
                os.write(master, b'\x1b[?1;2c')
            visible = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*?(?:\x07|\x1b\\)', '', screen.decode(errors='replace'))
            if args.open_restricted and choice_seen_at is None and '›1.Openrestricted' in re.sub(r'\s+', '', visible):
                choice_seen_at = time.monotonic()
        report.update(status='INCOMPLETE', probe_completed=True, argv=argv, exit_code=process.poll(), screen=screen.decode(errors='replace'),
                      session_start=hook.read_text(encoding='utf-8') if hook.exists() else None,
                      choice_written=choice_written,
                      sessions=[str(p.relative_to(home)) for p in home.rglob('*.jsonl')])
    finally:
        if process and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
        os.close(master)
        shutil.rmtree(home)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
