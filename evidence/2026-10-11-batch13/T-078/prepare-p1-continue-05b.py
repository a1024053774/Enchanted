"""Freeze same-instance continuation materials. No CLI, API, or state mutation."""
import ast
import difflib
import json
import subprocess
import tarfile
from pathlib import Path

SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
ORIGINAL = BASE / 'p1-materials-05'
OUT = BASE / 'p1-resume-materials-05b'
OUT.mkdir()
record = {'status': 'INCOMPLETE', 'scope': 'Preparation and static checks only',
          'real_cli_starts': 0, 'api_starts': 0, 'real_vendor_model_turns': 0, 'commands': []}

def command(argv):
    p = subprocess.run(argv, cwd=SOURCE, capture_output=True, text=True, encoding='utf-8')
    record['commands'].append({'argv': argv, 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    if p.returncode:
        raise RuntimeError({'unexpected_exit': p.returncode, 'argv': argv})
    return p.stdout

try:
    approval = json.loads((ORIGINAL / 'approval.json').read_text(encoding='utf-8'))
    root = Path(approval['input']['root'])
    assert root.is_dir()
    # Preserve the controller's observation and approval, not a worker observation.
    decision = Path('/Users/luckye/Documents/Code/a2a/evidence/2026-10-11-batch13/T-078/controller-decision-04.md')
    copied_decision = OUT / 'controller-decision-04-update-93.md'
    with copied_decision.open('xb') as output:
        output.write(decision.read_bytes())
    ready = {'schema': 1, 'launch': approval['input']['launch'], 'session': approval['input']['session'],
             'confirmed_by': 'executor', 'readiness': 'confirmed',
             'basis': '执行主控 #93：CLI 直接到主提示符（Haiku 5.5 with low effort · API Usage Billing · Not logged in），没有主题/API key/目录信任提示。',
             'confirmation_source': str(copied_decision),
             'prior_continue_approval': 'T-078 controller-decision-04 p1-05-continue',
             'prepared_by': 'worker:s13-t078s', 'scope': 'Recorded controller readiness only; continue-05b still needs approval'}
    with (OUT / 'readiness.json').open('x', encoding='utf-8') as output:
        json.dump(ready, output, ensure_ascii=False, indent=2)
    # No write in the retained instance; screen copy is a read-only observation.
    with (OUT / 'ready-screen.bin').open('xb') as output:
        output.write((root / 'state/traces' / approval['input']['launch'] / 'pty.raw').read_bytes())
    original_files = json.loads((ORIGINAL / 'source-files.json').read_text(encoding='utf-8'))
    changed = []
    patches = []
    with tarfile.open(ORIGINAL / 'sources.tar.gz') as archive:
        for name in original_files:
            before = archive.extractfile(name).read()
            after = (SOURCE / name).read_bytes()
            if before != after:
                changed.append(name)
                patches.extend(difflib.unified_diff(before.decode('utf-8').splitlines(True), after.decode('utf-8').splitlines(True),
                                                   fromfile='p1-launch-05/' + name, tofile='continue-05b/' + name))
            if name.endswith('.py'):
                ast.parse(after, filename=name)
    assert set(changed) == {'workbench/tests/run_t078_p1.py', 'workbench/README.md',
                            'evidence/2026-10-11-batch13/T-078/outside-sandbox.sh'}, changed
    (OUT / 'driver-only.diff').write_text(''.join(patches), encoding='utf-8')
    files = sorted([*original_files, str(Path(__file__).resolve().relative_to(SOURCE))])
    with tarfile.open(OUT / 'sources.tar.gz', 'x:gz') as archive:
        for name in files:
            archive.add(SOURCE / name, arcname=name)
    with (OUT / 'source-files.json').open('x', encoding='utf-8') as output:
        json.dump(files, output, indent=2)
    with (OUT / 'binding.json').open('x', encoding='utf-8') as output:
        json.dump({'original_materials': str(ORIGINAL), 'root': str(root), 'launch': ready['launch'], 'session': ready['session'],
                   'runtime_manifest': str(ORIGINAL / 'launch/runtime-manifest.json'),
                   'process_manifest': str(ORIGINAL / 'launch/process-manifest.json'),
                   'source_changes': changed, 'production_sources_unchanged': True,
                   'stage': 'p1-continue-05b', 'real_cli_starts': 0, 'real_vendor_model_budget': 0,
                   'messages_request_budget': 1, 'input_budget': 'Exactly the originally approved nonce once'},
                  output, ensure_ascii=False, indent=2)
    # Source is read-only here; argument help does not enter lifecycle or call a CLI.
    command(['/usr/bin/python3', '-B', str(SOURCE / 'workbench/tests/run_t078_p1.py'), '--help'])
    command(['bash', '-n', str(BASE / 'outside-sandbox.sh')])
    command(['git', 'diff', '--check'])
    command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'])
    assert not command(['find', str(BASE), '-type', 'f', '-size', '+5M']).strip()
    record.update(status='PASS', root=str(root), changed=changed, production_sources_unchanged=True)
except Exception as error:
    import traceback
    record.update(error=repr(error), traceback=traceback.format_exc())
with (OUT / 'preparation.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(0 if record['status'] == 'PASS' else 1)
