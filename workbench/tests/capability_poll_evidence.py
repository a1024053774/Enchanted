"""能力夹具的轮询记录：事件一次写入，状态变化与定时采样分卷保存。"""
import json
from pathlib import Path
import subprocess
import time


class PollEvidence:
    def __init__(self, output, *, sample_seconds=30, segment_bytes=1_000_000):
        self.output = Path(output)
        self.output.mkdir(exist_ok=False)
        self.sample_seconds, self.segment_bytes = sample_seconds, segment_bytes
        self.index, self.size = 0, 0
        self.states, self.samples, self.counts = {}, {}, {}
        self.last_seq, self.event_count, self.written = -1, 0, 0

    def write(self, row):
        raw = (json.dumps(row, ensure_ascii=False) + '\n').encode('utf-8')
        if len(raw) > self.segment_bytes:
            raise RuntimeError('单条轮询证据超过分卷上限；停止，不截断。')
        if self.index == 0 or self.size + len(raw) > self.segment_bytes:
            self.index += 1
            self.size = 0
            (self.output / f'{self.index:04d}.jsonl').touch(exist_ok=False)
        with (self.output / f'{self.index:04d}.jsonl').open('ab') as stream:
            stream.write(raw)
        self.size += len(raw)
        self.written += 1

    def observe(self, command, value, *, now):
        self.counts[command] = self.counts.get(command, 0) + 1
        if command == 'orchestration_events':
            events = value['events']
            seqs = [row['seq'] for row in events]
            if seqs != sorted(set(seqs)) or len(events) < self.event_count or (seqs and seqs[-1] < self.last_seq):
                raise RuntimeError('轮询事件顺序或数量回退；停止，不补写或重试。')
            for event in events:
                if event['seq'] > self.last_seq:
                    self.write({'kind': 'event', 'observed_monotonic': now, 'event': event})
            self.last_seq = seqs[-1] if seqs else self.last_seq
            self.event_count = len(events)
            state = {'count': len(events), 'last_seq': self.last_seq}
        else:
            state = value
        reason = ('initial' if command not in self.states else
                  'change' if state != self.states[command] else
                  'sample' if now - self.samples[command] >= self.sample_seconds else None)
        if reason:
            self.write({'kind': 'state', 'reason': reason, 'command': command,
                        'observed_monotonic': now, 'poll_number': self.counts[command], 'value': state})
            self.samples[command] = now
            self.states[command] = state
        return value

    def call(self, argv, *, command, cwd, env, timeout=40):
        if command not in self.counts:
            self.write({'kind': 'poll_command', 'command': command, 'argv': list(map(str, argv)),
                        'cwd': str(cwd), 'timeout': timeout})
        try:
            result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, timeout=timeout, capture_output=True)
        except (OSError, subprocess.TimeoutExpired) as error:
            self.write({'kind': 'poll_error', 'command': command, 'error': repr(error)})
            raise
        if len(result.stdout) + len(result.stderr) > self.segment_bytes:
            raise RuntimeError('单次轮询响应超过 1 MB；停止，未写入大文件。')
        try:
            value = json.loads(result.stdout)
        except (ValueError, UnicodeError):
            value = None
        if result.returncode or not isinstance(value, dict) or not value.get('ok'):
            self.write({'kind': 'poll_error', 'command': command, 'exit': result.returncode,
                        'stdout': result.stdout.decode('utf-8', 'replace'),
                        'stderr': result.stderr.decode('utf-8', 'replace')})
            raise RuntimeError('轮询命令失败；原文见 polls 分卷，不重试。')
        now = time.monotonic()
        if result.stderr:
            self.observe(command + ':stderr', {'stderr': result.stderr.decode('utf-8', 'replace')}, now=now)
        return self.observe(command, value, now=now)

    def summary(self):
        return {'poll_counts': self.counts, 'unique_events': self.event_count,
                'written_records': self.written, 'segments': self.index,
                'segment_limit_bytes': self.segment_bytes, 'sample_seconds': self.sample_seconds}
