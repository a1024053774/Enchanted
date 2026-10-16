"""Extract T-082's completed real turn without running commands as reviewer.

Read-only sources: persisted Stop event, the archived native transcript, and
fixture sentinels. Host readbacks are marked with their collection time.
"""
import argparse
import datetime
import gzip
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--rollout', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)

    def save(name, value):
        with (args.output / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')

    events = json.loads((args.run / 'events-last.json').read_text(encoding='utf-8'))['events']
    failed = [event for event in events if event['type'] == 'review_protocol_failed']
    assert len(failed) == 1
    payload = json.loads(failed[0]['details']['details']['raw'])
    binding = json.loads((args.run / 'binding.json').read_text(encoding='utf-8'))
    review = binding['review']
    worker = Path(review['attempt']['workspace'])
    protected = Path(review['workspace'])
    copy = Path(review['candidate_workspace'])
    repo = Path(binding['task']['repo'])
    report = payload['report']
    save('report-from-rejected-stop.json', report)

    with gzip.open(args.rollout, 'rt', encoding='utf-8') as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    selected = []
    probes = {}
    markers = {}
    mutations = []
    for number, row in enumerate(rows, 1):
        value = row.get('payload', {})
        if row['type'] != 'response_item' or value.get('type') != 'custom_tool_call_output':
            continue
        for block in value.get('output', []):
            if block.get('type') != 'input_text':
                continue
            try:
                output = json.loads(block['text'])
            except ValueError:
                continue
            text = output.get('output') if isinstance(output, dict) else None
            if not isinstance(text, str) or not any(word in text for word in
                    ('T082_PROBE', 'T082_DENY', 'baseline_completion')):
                continue
            name = f'native-tool-output-line-{number}.txt'
            (args.output / name).write_text(text, encoding='utf-8')
            source = {'line': number, 'call_id': value.get('call_id'), 'file': name,
                      'tool_exit': output.get('exit_code')}
            selected.append(source)
            for line in text.splitlines():
                try:
                    item = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(item, dict):
                    continue
                if 'target' in item and 'returncode' in item:
                    probes[item['target']] = {**item, 'source': source}
                if item.get('command') == ['./test-command.sh']:
                    markers['candidate_test'] = {**item, 'source': source}
                if item.get('command') == 'write t082-reviewer-write.txt':
                    markers['candidate_write'] = {**item, 'source': source}
                if 'mutation' in item or 'mutant' in item or str(item.get('check', '')).startswith('M'):
                    mutations.append({**item, 'source': source})

    sentinel_rows = []
    for label, path, before in [
        ('review', protected / 'src/t082-worker-sentinel.txt', 'review-sentinel-before.txt'),
        ('worker', worker / 'src/t082-worker-sentinel.txt', 'worker-sentinel-before.txt'),
        ('shared_git', repo / '.git/t082-shared-sentinel', 'shared-sentinel-before.txt'),
    ]:
        expected = (args.run / before).read_bytes()
        try:
            observed = path.read_bytes()
            value = {'content': observed.decode('utf-8'), 'unchanged': observed == expected}
        except OSError as error:
            value = {'unavailable': str(error), 'unchanged': None}
        sentinel_rows.append({'target': label, 'path': str(path), 'before_source': before,
                              'before': expected.decode('utf-8'), **value})

    native_turns = {row['payload']['turn_id'] for row in rows if row['type'] == 'event_msg'
                    and row['payload'].get('type') == 'task_started'}
    contexts = [row['payload'] for row in rows if row['type'] == 'turn_context']
    status = json.loads((args.run / 'status-last.json').read_text(encoding='utf-8'))['task']
    save('boundary-readback.json', {
        'collection_time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'sources': {'events': str(args.run / 'events-last.json'), 'rollout': str(args.rollout)},
        'observation_type': 'tool outputs during real turn plus later read-only host sentinel reads',
        'selected_native_outputs': selected, 'tool_probes': probes, 'candidate_positive_controls': markers,
        'sentinels': sentinel_rows, 'native_main_turns': len(native_turns),
        'model_context': [{key: ctx.get(key) for key in ('model', 'effort', 'sandbox_policy', 'approval_policy')}
                          for ctx in contexts],
        'candidate_commit_before': review['candidate_commit'], 'candidate_commit_at_last_status': status['candidate_commit'],
        'worker_head_file': (repo / '.git/worktrees' / worker.name / 'HEAD').read_text(encoding='utf-8'),
        'review_head_file': (repo / '.git/worktrees' / protected.name / 'HEAD').read_text(encoding='utf-8'),
        'protected_probe_files_exist': {str(path): path.exists() for path in
            (protected / 't082-reviewer-write.txt', worker / 't082-reviewer-write.txt', repo / '.git/t082-reviewer-write.txt')},
        'candidate_probe_file': {'exists': (copy / 't082-reviewer-write.txt').exists(),
                                 'content': (copy / 't082-reviewer-write.txt').read_text(encoding='utf-8')
                                            if (copy / 't082-reviewer-write.txt').exists() else None},
        'candidate_copy_exists': copy.exists(), 'review_worktree_exists': protected.exists(),
        'review_result_events': sum(e['type'] == 'review_result' for e in events),
        'review_cleanup_events': [e['type'] for e in events if e['type'] in
            ('review_reclaimed', 'review_candidate_copy_removed', 'review_worktree_removed')],
        'limitations': ['protocol rejection prevented the product end-boundary check and cleanup',
                        'current sentinel reads are later host readbacks, not gate end-time checks',
                        'worker/review Git clean status and refs comparison require independent Git readback'],
    })
    print(json.dumps({'output': str(args.output), 'probes': sorted(probes),
                      'sentinels_unchanged': all(s.get('unchanged') for s in sentinel_rows),
                      'real_main_turns': len(native_turns)}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
