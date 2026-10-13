"""Read the saved probe receipts and append one budget audit, never a reservation."""
import argparse
import fcntl
import gzip
import json
from pathlib import Path
import tarfile

CARD = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise RuntimeError('Preserve existing readback; choose another output.')
    root = CARD / 'outside-p-review-02'
    read = lambda name: json.loads((root / name).read_text(encoding='utf-8'))
    run, task, probe, binding = read('run.json'), read('task-result.json'), read('sentinel-result.json'), read('binding.json')
    rows = read('events-after-stop.json')
    native = [r['data']['record'] for r in rows if r['type'] == 'native_record']
    starts = [r['payload']['turn_id'] for r in native if r['type'] == 'event_msg' and r['payload'].get('type') == 'task_started']
    ends = [r['payload']['turn_id'] for r in native if r['type'] == 'event_msg' and r['payload'].get('type') == 'task_complete']
    metas = [r['payload'] for r in native if r['type'] == 'session_meta']
    contexts = [r['payload'] for r in native if r['type'] == 'turn_context']
    assert run['status'] == 'PASS' and run['observed_main_turns'] == 1 and run['home_removed'] is True
    assert len(starts) == len(ends) == len(metas) == 1 and starts == ends and metas[0]['source'] == 'cli'
    assert contexts and all(c['model'] == 'gpt-6.1-sol' and c['effort'] == 'xhigh' and c['approval_policy'] == 'never'
                            and c['sandbox_policy']['type'] == 'read-only' for c in contexts)
    assert probe['parsed']['denied'] is True and probe['parsed']['errno'] == 1 and probe['parsed']['write_attempts'] == 1
    sentinel = b'T076-P-review immutable sentinel\n'
    path = 'archive/state/verification/review-' + run['review_id'] + '/sentinel.txt'
    with tarfile.open(root / 'fixture-artifacts.tar.gz', 'r:gz') as archive:
        assert archive.extractfile(path).read() == sentinel
        assert archive.extractfile('archive/repo/sentinel.txt').read() == sentinel
        assert archive.extractfile('archive/host-control/sentinel.txt').read() != sentinel
    commands = [json.loads(l) for l in gzip.decompress((root / 'commands.jsonl.gz').read_bytes()).decode('utf-8').splitlines()]
    status = [r for r in commands if r['phase'] == 'finished' and r['argv'] == ['git', 'status', '--porcelain']][-1]
    ref = [r for r in commands if r['phase'] == 'finished' and r['argv'] == ['git', 'rev-parse', 'refs/heads/main']][-1]
    assert status['exit'] == ref['exit'] == 0 and status['stdout'] == '' and ref['stdout'].strip() == binding['B']
    assert task['state'] == 'verified' and task['review']['state'] == 'passed'
    assert task['review']['candidate_commit'] == run['C'] and task['review']['result']['verdict'] == '可合并'
    assert task['review']['result']['findings'] == []
    assert any(e['type'] == 'relay_processed' for e in rows) and any(e['type'] == 'review_reclaimed' for e in read('gate-events.json'))
    assert not Path('/private/tmp/a2a-t076-p-review-02/reviewer-home').exists()
    assert not any(p.is_file() and p.stat().st_size > 5 * 1024 * 1024 for p in root.rglob('*'))
    audit = dict(kind='readback', slot=1, audit='worker-p-review-02-01', accounted_total=1, budget_limit=8,
                 observed_main_turns=1, status='PASS', evidence=str(root), home_removed=True)
    with (CARD / 'real-turn-budget.jsonl').open('a+', encoding='utf-8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX); stream.seek(0)
        entries = [json.loads(l) for l in stream if l.strip()]
        assert sum(r['reserved'] for r in entries if r['kind'] == 'reservation') == 1
        assert [r['observed_main_turns'] for r in entries if r['kind'] == 'observation'] == [1]
        if not any(r.get('audit') == audit['audit'] for r in entries):
            stream.seek(0, 2); stream.write(json.dumps(audit) + '\n'); stream.flush()
    report = dict(status='PASS', product_status='INCOMPLETE', accounted_total=1, budget_limit=8, B=binding['B'], C=run['C'],
                  native_session=metas[0]['id'], turn=starts[0], model='gpt-6.1-sol', effort='xhigh', sandbox='read-only',
                  sentinel_errno=1, git_clean=True, project_ref_unchanged=True, home_removed=True, argv=__import__('sys').argv)
    with args.output.open('x', encoding='utf-8') as stream: json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps(report))


if __name__ == '__main__': main()
