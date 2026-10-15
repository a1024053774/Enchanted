"""Check every launch-phase P1 input before subprocess spawn; no CLI/API/daemon."""
import json
import os
import tarfile
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def main():
    materials = BASE / '09b-stage-b-ideation-p1-01'
    approval = json.loads((materials / 'approval.json').read_bytes())
    root = Path(approval['input']['root']); role_root = root / 'roles' / 'ideation'
    names = ['materials/approval.json', 'materials/input.json', 'materials/role.md',
             'materials/isolated-settings.json', 'materials/source-files.json', 'materials/sources.tar.gz',
             'materials/nonce.txt', 'root/input.json', 'root/nonce.txt', 'root/scenario.json',
             'root/operator.json', 'root/repo/value.txt', 'root/roles/ideation/role.md',
             'root/roles/ideation/claude/settings.json', 'root/roles/ideation/home',
             'root/roles/ideation/tmp', 'root/roles/ideation/shell', 'root/roles/ideation/requests',
             'root/roles/ideation/hooks', 'root/roles/ideation/user-data']
    checks = []
    def require(name, condition):
        checks.append({'name': name, 'status': 'PASS' if condition else 'INCOMPLETE'})
        assert condition, name
    require('external-volume-mounted', os.path.ismount('/Volumes/WD-Elements'))
    require('root-input-matches-material', (root / 'input.json').exists() and (root / 'input.json').read_bytes() == (materials / 'input.json').read_bytes())
    require('nonce-present-and-matches', (root / 'nonce.txt').exists() and (root / 'nonce.txt').read_bytes() == (materials / 'nonce.txt').read_bytes())
    require('scenario-present', (root / 'scenario.json').is_file() and json.loads((root / 'scenario.json').read_bytes())['name'] == 'stage-b-ideation')
    require('isolated-role-directories', all((role_root / name).is_dir() for name in ['home', 'claude', 'tmp', 'shell', 'requests', 'hooks', 'user-data']))
    require('role-file-matches-material', (role_root / 'role.md').read_bytes() == (materials / 'role.md').read_bytes())
    require('settings-matches-material', (role_root / 'claude/settings.json').read_bytes() == (materials / 'isolated-settings.json').read_bytes())
    frozen = json.loads((materials / 'source-files.json').read_bytes())
    with tarfile.open(materials / 'sources.tar.gz') as archive:
        require('source-tar-complete', all(archive.extractfile(name) is not None for name in frozen))
    require('operator-credential-present', (root / 'operator.json').is_file())
    result = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'INCOMPLETE',
              'checks': checks, 'scope': 'run_t078_p1 launch prerequisites only; stopped before API/CLI/daemon spawn',
              'spawned': False, 'p1_spawned': False, 'cli_spawned': False, 'prerequisite_files': names,
              'root': str(root), 'role': 'ideation', 'api_url': approval['input']['api_url'], 'api_pid': 70730}
    out = BASE / '09b-stage-b1-p1-prereq-02'; out.mkdir(exist_ok=False)
    (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False)); return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
