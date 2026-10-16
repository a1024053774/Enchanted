"""Freeze A15 files from a committed source revision; no Git writes or launch."""
import json
from pathlib import Path
import subprocess
import sys

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
PACKET = BASE / '09b-a15-materials-01'
LABEL = '09b-executable-materials-15'


def main():
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
    source_base = json.loads((PACKET / 'SOURCE-BASE.json').read_bytes())
    subprocess.run(['git', 'merge-base', '--is-ancestor', source_base['source_base'], revision], cwd=SOURCE, check=True)
    assert not subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all'], cwd=SOURCE), 'Source handoff must be committed first'
    assert LABEL.startswith('09b-executable-materials-') and not (BASE / LABEL).exists()
    assert not (BASE / '09b-a15-source-freeze-01.json').exists()
    commit_out = BASE / '09b-a15-commit-01'; commit_out.mkdir(exist_ok=False)
    command = [sys.executable, '-B', str(BASE / 'prepare-09b-executable.py'), '--label', LABEL, '--protocol', '--prompt-file', str(PACKET / 'i1-prompt.txt')]
    with (commit_out / 'prepare.stdout.bin').open('xb') as stdout, (commit_out / 'prepare.stderr.bin').open('xb') as stderr:
        completed = subprocess.run(command, cwd=SOURCE, stdout=stdout, stderr=stderr, timeout=300)
    (commit_out / 'prepare.command.json').write_text(json.dumps({'argv': command, 'exit_code': completed.returncode}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert completed.returncode == 0, 'Prepare failed; retain output, no retry'
    static = json.loads((BASE / LABEL / 'static-check.json').read_bytes())
    assert static['status'] == 'PASS' and static['revision'] == revision and static['protocol'] is True
    assert Path(static['root']).is_dir() and static['real_cli_starts'] == static['api_starts'] == static['target_starts'] == 0
    approval = json.loads((PACKET / 'stage-a-approval.json').read_bytes())
    assert approval['approved_by'] is None and approval['approval_ref'] is None
    approval['source_revision'] = revision
    (PACKET / 'stage-a-approval.json').write_text(json.dumps(approval, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    source_base['source_revision'] = revision
    (PACKET / 'SOURCE-BASE.json').write_text(json.dumps(source_base, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    frozen = {'status': 'PASS', 'source_base': source_base['source_base'], 'source_commit': revision,
              'materials': str(BASE / LABEL), 'static_root': static['root'], 'fixture_profile': 'a14-approved-gate-history-v1',
              'launch': 'NO_GO', 'real_runtime_starts': 0}
    (BASE / '09b-a15-source-freeze-01.json').write_text(json.dumps(frozen, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(frozen, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
