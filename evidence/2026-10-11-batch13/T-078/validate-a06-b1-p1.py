"""Read-only A-06 B1 P1 prerequisite validation; never starts a CLI or API."""
import argparse
import json
import tarfile
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
STAGE_A = BASE / '09b-a06-stage-a-02'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--materials', type=Path, default=BASE / '09b-a06-b1-ideation-p1-01')
    parser.add_argument('--output', type=Path, default=BASE / '09b-a06-b1-p1-preflight-01')
    args = parser.parse_args()
    materials = args.materials.resolve(); out = args.output.resolve()
    assert materials.is_dir() and not out.exists(), 'material_or_output_state'
    readiness_file = STAGE_A / 'readiness.json'; readiness = json.loads(readiness_file.read_bytes())
    inp = json.loads((materials / 'input.json').read_bytes())
    approval = json.loads((materials / 'approval.json').read_bytes())
    required = [
        'input.json', 'approval.json', 'nonce.txt', 'scenario.json', 'role.md',
        'isolated-settings.json', 'source-files.json', 'sources.tar.gz',
        'readiness-template.json', 'screen-key-approval-template.json',
        'control-plane.json', 'generation.json',
    ]
    assert all((materials / name).is_file() for name in required), 'p1_prerequisite_file_missing'
    root = Path(inp['root']).resolve(); role_root = root / 'roles' / 'ideation'
    assert root == Path(readiness['root']).resolve() and inp['task'] == readiness['task']
    assert inp['preset'] == 'ideation' and inp['api_url'] == 'http://127.0.0.1:0'
    assert inp['code_revision'] == readiness['source_revision']
    assert json.loads((root / 'input.json').read_bytes()) == inp
    assert (root / 'nonce.txt').read_bytes() == (materials / 'nonce.txt').read_bytes()
    assert json.loads((root / 'scenario.json').read_bytes()) == json.loads((materials / 'scenario.json').read_bytes())
    assert (role_root / 'role.md').read_bytes() == (materials / 'role.md').read_bytes()
    assert json.loads((role_root / 'claude/settings.json').read_bytes()) == {'theme': 'dark'}
    assert approval['input'] == inp and approval['status'] == 'INCOMPLETE'
    assert (materials / 'control-plane.json').read_text(encoding='utf-8').find(str(readiness_file.resolve())) >= 0
    with tarfile.open(materials / 'sources.tar.gz') as archive:
        source_files = json.loads((materials / 'source-files.json').read_bytes())
        assert source_files == archive.getnames()
        for name in source_files:
            assert (SOURCE / name).read_bytes() == archive.extractfile(name).read()
    result = {
        'status': 'PASS', 'scope': 'A-06 B1 P1 prerequisite readback only',
        'stage_a_readiness': str(readiness_file.resolve()), 'root': str(root),
        'task': inp['task'], 'preset': inp['preset'],
        'api_url_template': inp['api_url'], 'protocol': True,
        'required_files': len(required), 'real_cli_starts': 0,
        'api_starts': 0, 'daemon_starts': 0, 'target_starts': 0,
    }
    out.mkdir(parents=False)
    (out / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'command.json').write_text(json.dumps({
        'argv': ['python3', '-B', str(Path(__file__).resolve()), '--materials', str(materials), '--output', str(out)],
        'launch': 'NO_GO', 'process_starts': 0,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
