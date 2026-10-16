"""一次性离线证据检查；不启动 PTY、模型、daemon，不写隔离 home。"""
from pathlib import Path
import ast
import json
import os
import re
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog

log = CommandLog(OUT)
report = {'status': 'INCOMPLETE', 'scope': '只限离线检查；不证明能力通过', 'real_codex_turns_started': 0}
try:
    checks = []
    for argv in [
        ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'],
        ['git', 'diff', '--name-only'],
        ['/opt/homebrew/Cellar/node/26.5.0/bin/node', '--check', 'workbench/tests/prepare_t081_capability_run03.ts'],
        ['/opt/homebrew/Cellar/node/26.5.0/bin/node', '--check', 'workbench/tests/t081_capability_audit.ts'],
        ['python3', '-B', 'workbench/tests/check_t081_capability_run03.py', '--mode', 'candidate', '--output', str(OUT / 'replay')],
    ]:
        result = log.run(argv, cwd=ROOT, env=os.environ, timeout=30)
        checks.append({'argv': argv, 'exit': result.returncode, 'id': result.evidence['id']})
        assert result.returncode == 0, checks[-1]
        if argv[:2] == ['git', 'diff']:
            assert not result.stdout.strip(), '产品或其他受控文件发生了变更'
    for name in ['run_t081_capability_turn.py', 'capability_poll_evidence.py', 'archive_t081_capability_run02.py',
                 'diagnose_t081_capability_run02.py', 'check_t081_capability_run03.py']:
        ast.parse((ROOT / 'workbench/tests' / name).read_text(encoding='utf-8'))
    document = BASE / 'RUN-02-DIAG.md'
    text = document.read_text(encoding='utf-8')
    assert '\ufffd' not in text and not document.read_bytes().startswith(bytes([239, 187, 191]))
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if not target.startswith('https:'):
            assert (document.parent / target).resolve().exists(), target
    large = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size}
             for p in BASE.rglob('*') if p.is_file() and p.stat().st_size > 5_000_000]
    assert large == [{'path': 'evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl', 'bytes': 5_027_291}], large
    assert not Path('/private/tmp/t081-capability-01/run-03').exists()
    home = Path('/private/tmp/t081-capability-01/codex-home')
    diagnosis = json.loads((BASE / 'capability-run02-diagnosis-02/run.json').read_text(encoding='utf-8'))
    assert (home / 'config.toml').read_text(encoding='utf-8') == diagnosis['configured_trust_text']
    policy = json.loads((BASE / 'capability-review-03/launch-policy.first-turn.pending.json').read_text(encoding='utf-8'))
    assert policy['trust_config_before'] == diagnosis['configured_trust_text']
    assert policy['trust_config_after'] == policy['trust_config_before'].replace('projects."/private/tmp/t081-capability-01"',
          'projects."/private/tmp/t081-capability-01/run-03/repo"')
    assert policy['approved'] is False and policy['consumed_turns_before'] == 1 and policy['turn_limit'] == 1
    report.update(status='PASS', checks=checks, known_oversized_file_preserved=large,
                  no_product_diff=True, home_config_preserved=True, run03_created=False, utf8_and_links='PASS')
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
(OUT / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 2)
