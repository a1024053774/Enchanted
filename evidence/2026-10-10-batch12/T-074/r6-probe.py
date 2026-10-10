#!/usr/bin/env python3
"""Trigger and observe only the fixture-scoped approval experiment."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import sqlite3

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('runner', BASE / 'round2-runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

def snapshot(label, trial, stage, marker):
    out = BASE / label
    manifest = json.loads((out / 'launch.json').read_text(encoding='utf-8'))
    status = runner.probe.control(label, {'op': 'status'})
    logs = sqlite3.connect('file:' + manifest['codex_home'] + '/logs_2.sqlite?mode=ro', uri=True)
    logs.row_factory = sqlite3.Row
    outgoing = [dict(row) for row in logs.execute('SELECT id,ts,ts_nanos,level,target,feedback_log_body FROM logs WHERE target="codex_app_server::outgoing_message" ORDER BY id')]
    logs.close()
    controls = [json.loads(line) for line in (out / 'terminal-controls.jsonl').read_text(encoding='utf-8').splitlines()]
    notify = [json.loads(line) for line in (out / 'notify.jsonl').read_text(encoding='utf-8').splitlines()] if (out / 'notify.jsonl').exists() else []
    native = [json.loads(line) for line in (out / 'native-events.jsonl').read_text(encoding='utf-8').splitlines()]
    record = dict(trial=trial, stage=stage, captured_at=runner.stamp(), status=status,
                  marker_file=str(marker), marker_exists=marker.exists(),
                  marker_text=marker.read_text(encoding='utf-8') if marker.exists() else None,
                  osc9=[r for r in controls if r['kind']=='OSC' and r['value'].startswith('9;')],
                  notify=notify, native_tail=native[-14:], outgoing_tail=outgoing[-25:])
    runner.append(out / 'r6-snapshots.jsonl', record)
    return record

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('trial', type=int)
    parser.add_argument('sequence', type=int)
    args = parser.parse_args()
    out = BASE / args.label
    manifest = json.loads((out / 'launch.json').read_text(encoding='utf-8'))
    marker = Path(manifest['fixture']) / ('approval-marker-' + str(args.trial) + '.txt')
    if marker.exists():
        raise SystemExit('Marker preexists; refuse contaminated experiment')
    script = 'from pathlib import Path; Path(' + repr(str(marker)) + ').write_text(' + repr('T074 approval trial ' + str(args.trial)) + ', encoding="utf-8")'
    command = shlex.join(['python3', '-c', script])
    text = f'⟦主控 #{args.sequence}⟧ R6 真实批准探针 {args.trial}。只允许这一条命令：{command}。请用 exec_command 明确传 sandbox_permissions="require_escalated" 和 justification="T074：只写隔离夹具标记，请求人工批准以观测信号"。即使夹具可写，也要显式请求升级；不要改用普通写入或 apply_patch，不执行其他命令。等待批准；如果被拒绝或取消，只回复已取消，不重试。'
    runner.append(out / 'r6-stimuli.jsonl', dict(trial=args.trial, registered_at=runner.stamp(),
                    marker_file=str(marker), marker_preexists=False, exact_requested_command=command,
                    requested_permissions='require_escalated', stimulus_text=text))
    runner.inject(args.label, 'M3', 'idle', text, 'r6-stimulus')
    runner.wait_state(args.label, 'awaiting_approval')
    record = snapshot(args.label, args.trial, 'approval-before-injection', marker)
    print(json.dumps(dict(trial=args.trial, state=record['status']['state'],
                          marker_exists=record['marker_exists'], captured_at=record['captured_at'],
                          osc9=record['osc9']), ensure_ascii=False), flush=True)
    runner.inject(args.label, 'M3', 'awaiting_approval',
                  f'⟦主控 #{args.sequence + 1}⟧ 这是新的用户消息，不是批准：请不要执行标记命令，只记录本条文字。',
                  'coverage-approval', str(marker))
    record = snapshot(args.label, args.trial, 'approval-after-injection', marker)
    print(json.dumps(dict(trial=args.trial, state=record['status']['state'],
                          marker_exists=record['marker_exists'], captured_at=record['captured_at']), ensure_ascii=False), flush=True)
