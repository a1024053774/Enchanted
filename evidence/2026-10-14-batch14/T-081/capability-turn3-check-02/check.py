"""离线路径反例与 run-04 启动前事实核对；不启动模型或写夹具。"""
from pathlib import Path
from contextlib import closing
from copy import deepcopy
import ast
import json
import os
import sqlite3
import stat
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
FIXTURE = Path('/private/tmp/t081-capability-01')
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from capability_command_paths import check_command_paths
from command_evidence import CommandLog

report = {'status': 'INCOMPLETE', 'scope': '离线材料与只读基线检查；不证明 run-04 实际结果',
          'real_codex_turns_started': 0, 'fixture_or_home_written': False}
log = CommandLog(OUT)
try:
    review = BASE / 'capability-review-04'
    policy = json.loads((review / 'launch-policy.first-turn.pending.json').read_text(encoding='utf-8'))
    role = (review / 'ROLE-BODY.md').read_text(encoding='utf-8')
    first = (review / 'FIRST-TURN.template.md').read_text(encoding='utf-8')
    fixture = json.loads((BASE / 'capability-prepared-01/fixture.json').read_text(encoding='utf-8'))
    run_root = FIXTURE / 'run-04'
    def check(p, r, f):
        return check_command_paths(p, r, f, run_root=run_root, task='T-081-CAP-04', g=fixture['G'], target=fixture['T'])
    assert check(policy, role, first)['status'] == 'PASS'
    negatives = []
    for label, replacement in [('foreign-run', str(FIXTURE / 'run-02')), ('same-prefix-other-run', str(run_root) + '-other')]:
        changed = deepcopy(policy)
        changed['worker_commands'] = [[value.replace(str(run_root), replacement) for value in argv]
                                       for argv in changed['worker_commands']]
        try:
            check(changed, role.replace(str(run_root), replacement), first.replace(str(run_root), replacement))
        except ValueError as error:
            negatives.append({'case': label, 'error': error.args[0]})
        else:
            raise AssertionError('旧路径即使正文与 policy 一致也必须拒绝：' + label)
    for label, text in [('actual-FIRST-TURN', first.replace(policy['repo'], str(FIXTURE / 'run-02/repo'))),
                        ('bare-target', first.replace(policy['bare_repo'], str(FIXTURE / 'run-02/local.git')))]:
        try:
            check(policy, role, text)
        except ValueError as error:
            assert error.args[0]['where'] == 'FIRST-TURN'
            negatives.append({'case': label, 'error': error.args[0]})
        else:
            raise AssertionError('实际首轮正文的错路径必须拒绝：' + label)
    for name in ('run_t081_capability_turn.py', 'capability_command_paths.py', 'check_t081_capability_paths.py'):
        ast.parse((ROOT / 'workbench/tests' / name).read_text(encoding='utf-8'))
    source = (ROOT / 'workbench/tests/run_t081_capability_turn.py').read_text(encoding='utf-8')
    assert source.index("save(out / 'command-path-check.json'") < source.index('RUN_ROOT.mkdir(')
    assert source.index("save(out / 'actual-command-path-check.json'") < source.index("call('pane_release'")
    assert "'real_turns_consumed_before': 2" in source and "else 2 + report['real_turns_consumed_this_run']" in source
    assert not run_root.exists()
    finding = json.loads((BASE / 'capability-run03-finding-01/run.json').read_text(encoding='utf-8'))
    baseline = finding['home_baseline']
    home = FIXTURE / 'codex-home'
    assert sorted(p.name for p in home.iterdir()) == baseline['entry_names']
    assert (home / 'config.toml').read_text(encoding='utf-8') == baseline['config_text'] == policy['trust_config_before']
    assert stat.S_IMODE((home / 'auth.json').stat().st_mode) == 0o600 and not (home / 'auth.json').is_symlink()
    assert (home / 'rules/default.rules').read_text(encoding='utf-8') == 'prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
    with closing(sqlite3.connect((home / 'state_5.sqlite').as_uri() + '?mode=ro', uri=True)) as db:
        assert [list(row) for row in db.execute(baseline['thread_query'])] == baseline['threads']
    assert Path(baseline['sessions'][0]['path']).read_bytes() == (BASE / 'capability-run-03/native-root.jsonl').read_bytes()
    old_launch = json.loads((BASE / 'capability-run-03/launch-record.json').read_text(encoding='utf-8'))
    expected_argv = [value.replace(str(FIXTURE / 'run-03'), str(run_root)).replace('T-081-CAP-03', 'T-081-CAP-04').replace(old_launch['id'], '${LAUNCH_ID}')
                     for value in old_launch['argv']]
    assert policy['argv'] == expected_argv, '本次 argv 必须只改实际产品的本轮路径与 launch UUID'
    actual03 = json.loads((BASE / 'capability-run-03/first-turn-before-queue.json').read_text(encoding='utf-8'))['actual']
    attempt = json.loads((BASE / 'capability-run-03/attempt.json').read_text(encoding='utf-8'))
    for key, marker in [('attempt_id', '${ATTEMPT_ID}'), ('session_id', '${SESSION_ID}'), ('thread_id', '${THREAD_ID}')]:
        actual03 = actual03.replace(attempt[key], marker)
    actual03 = actual03.replace('T-081-CAP-03', 'T-081-CAP-04').replace(str(FIXTURE / 'run-03'), str(run_root))
    actual03 = actual03.replace(str(FIXTURE / 'run-02/repo'), policy['repo']).replace(str(FIXTURE / 'run-02/local.git'), policy['bare_repo'])
    assert first == actual03, '准确首轮模板必须等于前次真实产品文本仅重绑身份和命令目标'
    checks = []
    for argv in [
        ['git', '-C', str(FIXTURE / 'repo'), 'rev-parse', 'refs/heads/main'],
        ['git', '-C', str(FIXTURE / 'run-02/repo'), 'rev-parse', 'refs/heads/main'],
        ['git', '-C', str(FIXTURE / 'run-02/local.git'), 'show-ref'],
        ['git', '-C', str(FIXTURE / 'run-03/repo'), 'rev-parse', 'refs/heads/main'],
        ['git', '-C', str(FIXTURE / 'run-03/local.git'), 'show-ref'],
        ['/opt/homebrew/Cellar/node/26.5.0/bin/node', '--check', 'workbench/tests/prepare_t081_capability_run04.ts'],
        ['/opt/homebrew/Cellar/node/26.5.0/bin/node', '--check', 'workbench/tests/t081_capability_audit.ts'],
        ['git', 'diff', '--name-only'],
        ['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py', 'status', '--root', '.'],
    ]:
        result = log.run(argv, cwd=ROOT, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}, timeout=30)
        allowed = (0, 1) if argv[-1] == 'show-ref' else (0,)
        assert result.returncode in allowed
        checks.append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'id': result.evidence['id']})
    assert [row['stdout'].strip() for row in checks[:5]] == [fixture['G'], fixture['T'], fixture['T'] + ' refs/heads/t081-probe', fixture['G'], '']
    assert not checks[-2]['stdout'].strip()
    report.update(status='PASS', negative_cases=negatives, checks=checks,
                  product_argv_rebind='PASS', product_prompt_rebind='PASS', home_baseline='PASS',
                  old_refs_preserved=True, run04_created=False, consumed_before=2, total_limit=3)
except Exception as error:
    report.update(error=repr(error), traceback=traceback.format_exc())
(OUT / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in report.items() if key not in ('checks', 'negative_cases')}, ensure_ascii=False))
raise SystemExit(0 if report['status'] == 'PASS' else 2)
