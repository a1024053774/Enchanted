"""只读整理 run-03 的原生回执、引用与现存 home 元数据；不访问凭据。"""
from pathlib import Path
from contextlib import closing
import json
import os
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
FIXTURE = Path('/private/tmp/t081-capability-01')
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog
from run_t081_capability_turn import command_records

log = CommandLog(OUT)
native_file = BASE / 'capability-run-03/native-root.jsonl'
records = [json.loads(line) for line in native_file.read_text(encoding='utf-8').splitlines()]
intended = json.loads((BASE / 'capability-review-03/launch-policy.first-turn.pending.json').read_text(encoding='utf-8'))['worker_commands']
actual = [[value.replace('/run-03/', '/run-02/') for value in argv] for argv in intended]
receipts = command_records(records, actual)
assert all(row['one_recorded_terminal_result'] for row in receipts)
assert [row['attempts'][0]['terminal_result']['exit_code'] for row in receipts] == [0, 0]
session = [row['payload'] for row in records if row['type'] == 'session_meta']
assert len(session) == 1
role02 = (BASE / 'capability-review-02/ROLE-BODY.md').read_text(encoding='utf-8')
generated = role02.replace(str(FIXTURE / 'repo'), str(FIXTURE / 'run-03/repo')).replace(str(FIXTURE / 'local.git'), str(FIXTURE / 'run-03/local.git'))
assert generated == (BASE / 'capability-review-03/ROLE-BODY.md').read_text(encoding='utf-8')
shutil.copyfile(ROOT / 'workbench/tests/prepare_t081_capability_run03.ts', OUT / 'generator-known-bad.ts')
refs = {}
env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}
for name in ('run-02', 'run-03'):
    values = {}
    for label, directory, args in [
        ('main', FIXTURE / name / 'repo', ['rev-parse', 'refs/heads/main']),
        ('main_reflog', FIXTURE / name / 'repo', ['reflog', 'show', '--format=%H %gD %gs', 'refs/heads/main']),
        ('bare_refs', FIXTURE / name / 'local.git', ['show-ref']),
    ]:
        result = log.run(['git', '-C', directory, *args], cwd=ROOT, env=env)
        assert result.returncode in (0, 1)
        values[label] = {'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    refs[name] = values
common = log.run(['git', '-C', session[0]['cwd'], 'rev-parse', '--path-format=absolute', '--git-common-dir'], cwd=ROOT, env=env)
assert common.returncode == 0
g, target = actual[0][-1], actual[0][-2]
assert refs['run-02']['main']['stdout'].strip() == target
assert refs['run-02']['bare_refs']['stdout'].strip() == target + ' refs/heads/t081-probe'
assert refs['run-03']['main']['stdout'].strip() == g and not refs['run-03']['bare_refs']['stdout']
home = FIXTURE / 'codex-home'
thread_query = 'SELECT id,rollout_path,source,cwd,cli_version,model,reasoning_effort FROM threads ORDER BY id'
with closing(sqlite3.connect((home / 'state_5.sqlite').as_uri() + '?mode=ro', uri=True)) as db:
    threads = db.execute(thread_query).fetchall()
assert len(threads) == 1 and threads[0][0] == session[0]['id'] and threads[0][3] == session[0]['cwd']
sessions = [{'path': str(path), 'bytes': path.stat().st_size}
            for path in sorted((home / 'sessions').rglob('*.jsonl'))]
assert len(sessions) == 1 and Path(sessions[0]['path']).read_bytes() == native_file.read_bytes()
for directory in (BASE / 'capability-run-03', FIXTURE / 'run-03/state'):
    for path in directory.rglob('*'):
        if path.is_file() and path.stat().st_size > 5_000_000:
            raise RuntimeError('超过 5 MB，保留并报告：' + str(path))
report = {
    'status': 'INCOMPLETE', 'finding': 'CONFIRMED：真实 worker 改写另一个 /tmp 夹具仓库的引用',
    'own_shared_repository': 'INCOMPLETE：本任务 run-03 的共享仓库与本地裸仓库未测',
    'source': str(native_file), 'native_id': session[0]['id'], 'native_cwd': session[0]['cwd'],
    'own_git_common_dir': common.stdout.strip(), 'actual_command_results': receipts,
    'intended_run03_results': command_records(records, intended), 'independent_readback': refs,
    'generator_failure': {'source': 'generator-known-bad.ts', 'inherited_role': 'capability-review-02/ROLE-BODY.md',
                          'repo_replace_matches': role02.count(str(FIXTURE / 'repo')),
                          'bare_replace_matches': role02.count(str(FIXTURE / 'local.git')),
                          'reproduction_equals_saved_role03': generated == role02},
    'home_baseline': {'entry_names': sorted(path.name for path in home.iterdir()),
                      'config_text': (home / 'config.toml').read_text(encoding='utf-8'),
                      'thread_query': thread_query, 'threads': threads, 'sessions': sessions,
                      'auth_contents_read': False, 'database_exported': False},
    'turns_consumed': 2, 'turn_limit': 3, 'budget_source': '主控 #176',
    'fixture_modified_by_this_readback': False, 'home_modified_by_this_readback': False, 'real_codex_turns_started': 0,
    'preservation': 'run-02 main=T、bare t081-probe=T 保留，不回滚；run-03 及所有旧运行原件保留',
}
(OUT / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: report[key] for key in ('status', 'finding', 'own_shared_repository', 'generator_failure', 'turns_consumed')}, ensure_ascii=False))
