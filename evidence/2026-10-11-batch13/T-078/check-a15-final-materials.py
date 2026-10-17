"""Read-only source, command-path, encoding and ownership preflight for A15 closeout."""
import argparse
import ast
import json
from pathlib import Path
import re
import shlex
import subprocess

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parents[2]
NAMES = ['RESULTS.md', '09B-A15-FINAL-CHECK.md', '09B-A15-CLEANUP-PLAN.md',
         '09B-A15-CLEANUP-COMMANDS.txt', 'REVIEW-REQUEST-T078-FINAL.md',
         '09b-a15-cleanup-owner.json', '09b-a15-cleanup-approval.json',
         'a15-final-evidence.py', 'redact-a15-scene.py', 'cleanup-09b-a15.py',
         'check-a15-closeout.py', 'check-a15-final-materials.py']
PREFIXES = ['09b-a15-final-check-', '09b-a15-closeout-file-check-', '09b-a15-final-material-check-']
DISPOSITION = '.project-map/inbox/20261016T133204Z-user-disposition-001.md'


def owned(name):
    return name == DISPOSITION or (name.startswith(str(BASE.relative_to(SOURCE)) + '/') and
            (name[len(str(BASE.relative_to(SOURCE))) + 1:] in NAMES or
             any(name[len(str(BASE.relative_to(SOURCE))) + 1:].startswith(prefix) for prefix in PREFIXES)))


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(exist_ok=False)
    syntax, links = [], []
    for name in NAMES:
        path = BASE / name; raw = path.read_bytes(); text = raw.decode('utf-8')
        assert not raw.startswith(b'\xef\xbb\xbf') and '\ufffd' not in text
        if path.suffix == '.py': ast.parse(text, filename=str(path)); syntax.append(name)
        if name.endswith('.md'):
            for destination in re.findall(r'\]\(([^)]+)\)', text):
                if destination.startswith(('http:', 'https:')): continue
                target = (BASE / destination.split('#')[0]).resolve()
                assert target.exists(), ('missing linked source', destination)
                links.append(destination)
    commands = [shlex.split(line) for line in (BASE / '09B-A15-CLEANUP-COMMANDS.txt').read_text(encoding='utf-8').splitlines()
                if line and not line.startswith('#')]
    assert len(commands) == 3
    for argv in commands:
        assert argv[:2] == ['python3', '-B'] and Path(argv[2]).is_file()
        for flag in ['--owner', '--approval']:
            if flag in argv: assert Path(argv[argv.index(flag) + 1]).is_file()
        assert not Path(argv[argv.index('--output') + 1]).exists()
        if '--redaction-result' in argv:
            assert Path(argv[argv.index('--redaction-result') + 1]) == BASE / '09b-a15-redacted-01/result.json'
    owner = json.loads((BASE / '09b-a15-cleanup-owner.json').read_bytes())
    approval = json.loads((BASE / '09b-a15-cleanup-approval.json').read_bytes())
    assert approval['approved_by'] is approval['approval_ref'] is None
    for role in owner['roles'].values():
        for name in ['manifest', 'launch_result', 'runtime_manifest', 'input']: assert Path(role[name]).is_file()
    for path in [Path(owner['stage_a']) / 'readiness.json', Path(owner['I1_result']), Path(owner['identity_reference'])]: assert path.is_file()
    changed = subprocess.check_output(['git', 'diff', '--name-only', owner['original_source_revision'], '--', 'workbench/src', 'workbench/app'], cwd=SOURCE, text=True)
    assert not changed.strip()
    harness = subprocess.run(['python3', '-B', str(SOURCE / 'workbench/tests/run_t078_frozen_harness.py'),
                              '--freeze', str(BASE / '09b-a15-reader-harness-01'), '--check-only'], cwd=SOURCE, capture_output=True, text=True)
    assert harness.returncode == 0, harness.stderr
    entries = subprocess.check_output(['git', 'status', '--porcelain', '-uall'], cwd=SOURCE, text=True).splitlines()
    paths = [line[3:] for line in entries]
    assert all(owned(path) and (SOURCE / path).is_file() for path in paths), ('unowned or missing work', [path for path in paths if not owned(path)])
    assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=SOURCE, text=True).strip()
    report = {'status': 'PASS', 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip(),
              'syntax': syntax, 'linked_sources_checked': len(links), 'commands_checked': 3,
              'future_generated_input': str(BASE / '09b-a15-redacted-01/result.json'),
              'owner_paths_exist': True, 'signatures_blank': True, 'git_add_paths_exist': True,
              'harness_check_only': json.loads(harness.stdout), 'product_diff_from_loaded_revision': [],
              'owned_paths': paths + [str((args.output / 'result.json').resolve().relative_to(SOURCE))],
              'simulated_final_status': [], 'scene_actions': 0}
    (args.output / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ['status', 'head', 'commands_checked', 'git_add_paths_exist', 'simulated_final_status', 'scene_actions']}))


if __name__ == '__main__': main()
