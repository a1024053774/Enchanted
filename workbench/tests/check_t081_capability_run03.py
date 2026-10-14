"""离线检查：用 run-02 原始响应回放；不启动 PTY、Codex 或 daemon。"""
import argparse
import json
from pathlib import Path
import tempfile

from archive_t081_capability_run02 import archive_file
from capability_poll_evidence import PollEvidence

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'evidence/2026-10-14-batch14/T-081'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('legacy', 'candidate'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    diagnosis = json.loads((BASE / 'capability-run02-diagnosis-02/run.json').read_text(encoding='utf-8'))
    if args.mode == 'legacy':
        oversized = diagnosis['commands_jsonl_bytes'] > 5_000_000
        result = {'status': 'NO_GO' if oversized else 'PASS', 'expected_red': oversized,
                  'failure_id': 'POLL-EVIDENCE-SIZE' if oversized else None,
                  'source': str(BASE / 'capability-run-02/commands.jsonl'),
                  'bytes': diagnosis['commands_jsonl_bytes'], 'limit': 5_000_000,
                  'source_exit': diagnosis['original_run']['error'], 'real_codex_turns': 0}
        code = 1 if oversized else 0
    else:
        polls = PollEvidence(out / 'replayed-polls')
        manifest = diagnosis['poll_replay_manifest']
        expected_events = []
        for index, entry in enumerate(manifest):
            value = json.loads(Path(entry['stdout_file']).read_text(encoding='utf-8'))
            polls.observe(entry['command'], value, now=index / 2)
            if entry['command'] == 'orchestration_events':
                expected_events = value['events']
        files = sorted(polls.output.glob('*.jsonl'))
        rows = [json.loads(line) for path in files for line in path.read_text(encoding='utf-8').splitlines()]
        assert [row['event'] for row in rows if row['kind'] == 'event'] == expected_events, '新增事件必须完整且只出现一次'
        assert any(row.get('reason') == 'change' for row in rows), '状态变化必须被记录'
        assert any(row.get('reason') == 'sample' for row in rows), '重复状态必须有定时采样'
        assert polls.counts == {'pane_status': 319, 'orchestration_events': 319}
        assert sum(path.stat().st_size for path in files) < 100_000, '这批重复响应的保留量应小于 100 KB'
        # A small segment forces real filesystem rotation. Two distinct events
        # and a final state change must survive without duplicates or truncation.
        rotated = PollEvidence(out / 'rotation', segment_bytes=512)
        for index in range(20):
            rotated.observe('pane_status', {'ok': True, 'state': str(index), 'detail': 'x' * 180}, now=index)
        parts = sorted(rotated.output.glob('*.jsonl'))
        assert len(parts) > 1 and max(path.stat().st_size for path in parts) <= 512
        assert len([line for path in parts for line in path.read_text(encoding='utf-8').splitlines()]) == 20
        with tempfile.TemporaryDirectory(prefix='t081-archive-check-') as temporary:
            directory = Path(temporary).resolve()
            source, dest, pointer = [directory / name for name in ('original', 'external/raw', 'pointer.json')]
            raw = bytes(range(256)) * 1025 + b'END'
            source.write_bytes(raw)
            receipt = archive_file(source, dest, pointer, len(raw))
            assert not source.exists() and dest.read_bytes() == raw
            assert json.loads(pointer.read_text(encoding='utf-8'))['bytes'] == len(raw) == receipt['bytes']
            source.write_bytes(b'preserve me')
            try:
                archive_file(source, dest, directory / 'second-pointer', len(b'preserve me'))
            except RuntimeError:
                pass
            else:
                raise AssertionError('已有外置目标必须拒绝覆盖')
            assert source.read_bytes() == b'preserve me' and dest.read_bytes() == raw
        result = {'status': 'PASS', 'scope': '离线原始响应回放、分卷与归档小文件边界；真实信任/回合未验证',
                  'polling': polls.summary(), 'saved_bytes': sum(path.stat().st_size for path in files),
                  'rotation_segments': len(parts), 'archive_bytes_tested': len(raw),
                  'no_overwrite_confirmed': True, 'real_codex_turns': 0, 'fixture_or_home_written': False}
        code = 0
    (out / 'run.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
