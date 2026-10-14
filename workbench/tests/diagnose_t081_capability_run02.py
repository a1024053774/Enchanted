"""只读 run-02 PTY、原始轮询与隔离 SQLite；不读取凭据或日志正文。"""
from collections import Counter
from contextlib import closing
import argparse
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'
RUN = BASE / 'capability-run-02'
HOME = Path('/private/tmp/t081-capability-01/codex-home')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BASE / 'capability-run02-diagnosis-02')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    queries = {
        'state_5.sqlite': [
            'SELECT count(*) FROM threads',
            'SELECT id,source,cwd,has_user_event,cli_version,model,reasoning_effort FROM threads',
        ],
        'logs_2.sqlite': [
            'SELECT count(*),min(ts),max(ts) FROM logs',
            'SELECT level,target,count(*) FROM logs GROUP BY level,target',
            'SELECT count(*) FROM logs WHERE thread_id IS NOT NULL',
            "SELECT count(*) FROM logs WHERE lower(target) LIKE '%tool_call%' OR lower(target) LIKE '%exec_command%'",
        ],
    }
    sql = []
    for name, statements in queries.items():
        path = HOME / name
        before = {p.name: p.stat().st_size for p in HOME.glob(name + '*')}
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
            rows = [{'query': query, 'rows': db.execute(query).fetchall()} for query in statements]
        sql.append({'database': name, 'connection': 'mode=ro', 'files_bytes': before, 'results': rows})
    ptys = list((RUN / 'traces').glob('*/pty.raw'))
    assert len(ptys) == 1
    raw = ptys[0].read_bytes()
    # PTY contains terminal output only. Preserve the existing raw file; a text
    # view strips CSI/OSC formatting without inventing cursor-position spaces.
    text = re.sub(rb'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', b'', raw)
    text = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', text).decode('utf-8')
    (out / 'pty-text.txt').write_text(text, encoding='utf-8')
    events = json.loads((RUN / 'orchestration-events.json').read_text(encoding='utf-8'))['events']
    event_counts = Counter(e['type'] for e in events)
    commands = []
    counts = Counter()
    transcript = RUN / 'commands.jsonl'
    if not transcript.exists():
        pointer = json.loads((RUN / 'commands.jsonl.external.json').read_text(encoding='utf-8'))
        transcript = Path(pointer['archive'])
    with transcript.open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['phase'] != 'finished':
                continue
            argv = row['argv']
            if '--state' in argv:
                command = argv[argv.index('--state') + 2]
                counts[command] += 1
                if command in ('pane_status', 'orchestration_events'):
                    commands.append({'id': row['id'], 'command': command,
                                     'stdout_file': row['stdout_file'], 'exit': row['exit']})
    repo = HOME.parent / 'run-02/repo'
    bare = HOME.parent / 'run-02/local.git'
    refs = []
    for argv in [['git', '-C', str(repo), 'show-ref'], ['git', '-C', str(bare), 'show-ref'],
                 ['git', '-C', str(repo), 'status', '--porcelain=v1']]:
        result = subprocess.run(argv, capture_output=True, text=True, check=False,
                                env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
        assert result.returncode in (0, 1)
        refs.append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    report = {
        'status': 'INCOMPLETE', 'diagnosis_status': 'PASS',
        'scope': '只读证据；不启动模型、daemon，不读取 auth.json，不导出 SQLite 日志正文或令牌',
        'pty_source': str(ptys[0]), 'pty_bytes': len(raw),
        'folder_access_prompt_observed': 'Folder access' in text and bool(re.search(r'Trust\s*this\s*folder\?', text)),
        'trust_prompt_repository': '/private/tmp/t081-capability-01/run-02/repo',
        'configured_trust_text': (HOME / 'config.toml').read_text(encoding='utf-8'),
        'sqlite': sql, 'event_counts': dict(event_counts),
        'turn_events': [{k: e[k] for k in ('seq', 'type', 'launch', 'attempt', 'data')} for e in events
                        if e['type'] in ('turn_submit_intent', 'turn_submitted', 'pane_idle', 'native_record')],
        'turns_consumed': 1, 'turns_limit': 3, 'accounting_source': '主控 #174；不以线程缺失扣回回合',
        'native_sessions_directory_exists': (HOME / 'sessions').exists(),
        'probe_results_exists': (HOME.parent / 'run-02/state/worktrees/t081-capability/T-081-CAP-02-a1/probe-results.json').exists(),
        'command_observation': [
            {'command': command, 'execution': 'INCOMPLETE：未发现工具调用或回执',
             'exit_code': None, 'refusal_text': None}
            for command in ('git update-ref', 'git push')],
        'refs': refs, 'commands_jsonl_bytes': transcript.stat().st_size,
        'command_counts': dict(counts), 'poll_replay_manifest': commands,
        'original_run': json.loads((RUN / 'run.json').read_text(encoding='utf-8')),
        'home_entry_names': sorted(p.name for p in HOME.iterdir()),
        'interpretation': '产品记录的 turn_submitted 是终端发送动作；PTY 显示仍在信任确认。没有能力成功或拒绝证据。',
    }
    assert report['folder_access_prompt_observed']
    assert sql[0]['results'][0]['rows'] == [(0,)]
    (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'diagnosis_status': 'PASS', 'output': str(out),
                      'command_counts': dict(counts), 'threads': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
