"""Literal stale-fence contract through the CLI inside a real Muster pane."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--coop', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    runtime = ROOT / '.runtime' / ('t029-fence-' + out.name)
    runtime.mkdir(parents=True, exist_ok=False)
    repo = runtime / 'repo'
    repo.mkdir()
    state = runtime / 'state'
    assert os.environ.get('MUSTER_ENV') == '1' and os.environ.get('MUSTER_PANE_ID'), 'Must run inside a Muster pane'
    commands = []

    def command(argv, expected=0):
        argv = [str(v) for v in argv]
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=60)
        record = dict(argv=argv, exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr,
                      time=datetime.datetime.now(datetime.timezone.utc).isoformat())
        commands.append(record)
        with (out / 'commands.jsonl').open('a', encoding='utf-8') as log:
            log.write(json.dumps(record, ensure_ascii=False) + '\n')
        if expected is not None:
            assert proc.returncode == expected, record
        return proc

    def cli(*argv):
        return json.loads(command([sys.executable, '-B', args.coop, '--state', state, *argv]).stdout)

    def git(*argv, cwd=repo):
        return command(['git', '-C', cwd, *argv]).stdout.strip()

    task = 't029-fence'
    current_pane = json.loads(command([os.environ['MUSTER_BIN'], 'pane', 'current', '--current']).stdout)['result']
    git('init', '-b', 'main')
    git('config', 'user.name', 'Independent fence check')
    git('config', 'user.email', 'fixture@localhost')
    git('config', 'commit.gpgsign', 'false')
    for name in ('pager.py', 'CONTRACT.md'):
        shutil.copyfile(ROOT / 'fixtures/pagination' / name, repo / name)
    git('add', 'pager.py', 'CONTRACT.md')
    git('commit', '-m', 'test: independent baseline')
    base = git('rev-parse', 'HEAD')
    cli('create', '--task', task, '--repo', repo, '--base', base,
        '--oracle', ROOT / 'acceptance/pagination_oracle.py', '--instructions', repo / 'CONTRACT.md')
    attempt = cli('claim', '--task', task, '--owner', 'fence-check')['attempt']
    workspace = Path(attempt['workspace'])
    shutil.copyfile(ROOT / 'acceptance/reference/pager.py', workspace / 'pager.py')
    git('add', 'pager.py', cwd=workspace)
    git('commit', '-m', 'test: independent valid candidate', cwd=workspace)
    candidate = git('rev-parse', 'HEAD', cwd=workspace)
    before = cli('status', '--task', task)['task']
    response = command([sys.executable, '-B', args.coop, '--state', state, 'submit', '--task', task,
                        '--attempt', attempt['attempt_id'], '--session', attempt['session_id'],
                        '--fence', str(attempt['fence'] + 31), '--spec-rev', str(attempt['spec_rev']),
                        '--commit', candidate], expected=None)
    value = json.loads(response.stdout)
    after = cli('status', '--task', task)['task']
    ref = git('rev-parse', 'refs/a2a/integration')
    assertions = dict(stale_fence_rejected=response.returncode == 1 and value.get('error') == 'stale_fence',
                      task_unchanged=before == after, integration_unchanged=ref == base)
    result = dict(status='PASS' if all(assertions.values()) else 'INCOMPLETE', assertions=assertions,
                  current_pane=current_pane, candidate=candidate, base=base, before=before, after=after,
                  response=value, coop=str(args.coop.resolve()), runtime=str(runtime))
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
