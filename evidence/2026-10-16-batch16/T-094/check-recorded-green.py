#!/usr/bin/env python3
"""只读核对主控已保存的真实运行，生成精简摘要；不调用 Herdr 或 Codex。"""
import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
ARCHIVE = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-094')
sys.path.insert(0, str(REPO / 'scripts'))
from launch_records import find_launch, validate_launches

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, help='重放时使用不存在的新目录，保护已有摘要')
args = parser.parse_args()
out = args.output.resolve() if args.output else Path(__file__).resolve().parent
if args.output:
    out.mkdir(parents=True, exist_ok=False)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


for label, expected_count in (('green-01', 5), ('unregistered-01', 1)):
    root = ARCHIVE / label
    run = read(root / 'run.json')
    assert len(run['attempts']) == expected_count
    assert run['model_turns'] == 0 and run['violations'] == []
    cases = []
    for attempt in run['attempts']:
        case = root / ('attempt-%02d' % attempt['number'])
        rows = [json.loads(s) for s in (case / 'identity/records/launches.jsonl').read_text(encoding='utf-8').splitlines()]
        row = validate_launches(rows)[rows[-1]['launch_id']]
        assert row == attempt['launch_record']
        calls = [json.loads(s) for s in (case / 'herdr.jsonl').read_text(encoding='utf-8').splitlines()]
        starts = [c for c in calls if c['argv'][:2] == ['agent', 'start']]
        assert len(starts) == 1 and attempt['start_calls'] == 1
        assert not any(c['argv'][:2] == ['agent', 'prompt'] for c in calls)
        assert row['pane'] == attempt['pane_ids'][0]
        assert len(attempt['cleanup']) == 1 and attempt['cleanup'][0]['returncode'] == 0
        exit_code = attempt['launch']['returncode']
        summary = dict(number=attempt['number'], launch_id=row['launch_id'], pane=row['pane'],
                       exit_code=exit_code, phase=row['phase'], start_calls=len(starts),
                       real_agent_start_calls=attempt['real_agent_start_calls'],
                       unmanaged_codex_start_calls=attempt['unmanaged_codex_start_calls'],
                       start_seconds=starts[0]['seconds'], probe_cleanup_exit=0)
        if exit_code:
            assert row['phase'] == 'failed'
            assert row['herdr_stderr'] == starts[0]['stderr']
            assert row['error_code'] == json.loads(row['herdr_stderr'])['error']['code']
            assert row['pane_disposition'] == 'retained_for_controller'
            summary.update(error_code=row['error_code'], herdr_stderr=row['herdr_stderr'],
                           outcome=row['outcome'], pane_disposition=row['pane_disposition'])
        else:
            assert row['phase'] == 'started'
        if label == 'unregistered-01':
            assert exit_code != 0 and row['outcome'] == 'started_unregistered'
            assert row['error_code'] == 'agent_name_not_found'
            info, agent = [v['value'] for v in row['observations']]
            assert any(p['name'] == 'codex' for p in info['foreground_processes'])
            assert agent['agent'] == 'codex' and agent.get('name') is None
            assert attempt['real_agent_start_calls'] == 0 and attempt['unmanaged_codex_start_calls'] == 1
            try:
                find_launch(rows, row['launch_id'])
            except ValueError as error:
                summary['successful_launch_consumer_rejection'] = str(error)
            else:
                raise AssertionError('半成功被当作成功启动')
            summary['injected_error_with_real_unregistered_process'] = True
        cases.append(summary)
    summary = dict(tested_commit=run['commit'], model_turns=0, attempts=cases,
                   successful_starts=sum(c['exit_code'] == 0 for c in cases),
                   failed_starts=sum(c['exit_code'] != 0 for c in cases),
                   checked='原始 JSONL 与保存快照一致、失败诊断、一次 start、探针清理；非全成功结论')
    path = out / (label + '-summary.json')
    with path.open('x', encoding='utf-8') as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    files = [p for p in root.rglob('*') if p.is_file()]
    manifest = dict(original='（由 probe-start.py 直接写入外置盘，无仓库内原始目录）',
                    archive=str(root), files=len(files), bytes=sum(p.stat().st_size for p in files),
                    replay='sh evidence/2026-10-16-batch16/T-094/outside-green.sh（换用新 label 与归档目录以保留旧证据）')
    with (out / (label + '.archive.json')).open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(label, '启动成功', summary['successful_starts'], '启动失败', summary['failed_starts'], '记录核对 PASS')
