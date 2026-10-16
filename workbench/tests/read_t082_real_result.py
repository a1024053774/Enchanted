"""Read a completed T-082 real review from gate records and host receipts.

This observer records model output. It does not decide whether the reviewer
was correct and does not change gate state.
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--round', type=int, choices=[1, 2], required=True)
    args = parser.parse_args()
    out = args.run
    initial = json.loads((out / 'verify.json').read_text(encoding='utf-8'))['task']
    task = json.loads((out / 'status-final.json').read_text(encoding='utf-8'))['task']
    events = json.loads((out / 'events-final.json').read_text(encoding='utf-8'))['events']
    review = initial['review']
    rid, candidate = review['review_id'], review['candidate_commit']
    result = task.get('review', {}).get('result', {})
    report = result.get('report')
    has_section = isinstance(report, dict) and '完成条件与变异检查' in report
    section = report['完成条件与变异检查'] if has_section else None
    mutations = section.get('mutation_checks') if isinstance(section, dict) else None

    def save(name, value):
        with (out / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')

    save('report-readback.json', {'section_present': has_section, 'section': section,
         'mutation_count': len(mutations) if isinstance(mutations, list) else None,
         'mutation_count_source': 'review.result.report[完成条件与变异检查].mutation_checks',
         'model_verdict': result.get('verdict'), 'report': report,
         'limitation': None if isinstance(mutations, list) else 'mutation_checks array unavailable; no count inferred from prose'})

    def review_event(kind):
        return [e for e in events if e['type'] == kind and
                (e['details'].get('review_id') or e['details'].get('review', {}).get('review_id')) == rid]

    saved_results = review_event('review_result')
    removed = review_event('review_candidate_copy_removed')
    reclaimed = review_event('review_reclaimed')
    persisted = len(saved_results) == 1 and saved_results[0]['details']['review']['result'] == result
    # Read the gate's actual Git command receipts between result and removal.
    start = saved_results[0]['seq'] if len(saved_results) == 1 else -1
    end = removed[0]['seq'] if len(removed) == 1 else -1
    gate_reads = [e for e in events if e['type'] == 'command_result' and start < e['seq'] < end]

    def git_receipt(workspace, command, expected):
        return [e for e in gate_reads if e['details'].get('argv') == ['git', '-C', workspace, *command]
                and e['details'].get('returncode') == 0 and e['details'].get('stdout', '').strip() == expected]

    clean_args = ['status', '--porcelain=v1', '--untracked-files=all']
    review_clean = git_receipt(review['workspace'], clean_args, '')
    worker_clean = git_receipt(review['attempt']['workspace'], clean_args, '')
    review_head = git_receipt(review['workspace'], ['rev-parse', 'HEAD'], candidate)
    worker_head = git_receipt(review['attempt']['workspace'], ['rev-parse', 'HEAD'], candidate)
    refs_equal = (out / 'shared-refs-before.txt').read_bytes() == (out / 'shared-refs-after.txt').read_bytes()

    def same_sentinel(prefix):
        return (out / (prefix + '-sentinel-before.txt')).read_bytes() == (out / (prefix + '-sentinel-after.txt')).read_bytes()

    sentinel = {'worker_direct_unchanged': same_sentinel('worker'),
                'shared_git_direct_unchanged': same_sentinel('shared')}
    # The protected worktree no longer exists after successful reclaim. Its
    # tracked sentinel is proved by before==C:blob and the gate's clean/head
    # receipts before removal, not by pretending to read a deleted file.
    before = (out / 'review-sentinel-before.txt').read_bytes()
    committed = (out / 'review-sentinel-committed.txt').read_bytes()
    sentinel['review_tracked_unchanged_before_removal'] = before == committed and bool(review_clean) and bool(review_head)
    sentinel['review_direct_after'] = 'unavailable: worktree removed; see gate Git receipts'

    checks = {'review_result_persisted': persisted,
        'candidate_commit_unchanged': task.get('candidate_commit') == candidate and bool(worker_head) and bool(review_head),
        'review_worktree_clean_before_removal': bool(review_clean), 'worker_worktree_clean': bool(worker_clean),
        'shared_refs_unchanged': refs_equal,
        'candidate_copy_removed': len(removed) == 1 and not Path(review['candidate_workspace']).exists(),
        'review_worktree_removed': len(review_event('review_worktree_removed')) == 1 and not Path(review['workspace']).exists(),
        'review_reclaimed': len(reclaimed) == 1,
        'sentinels_unchanged': sentinel['worker_direct_unchanged'] and sentinel['shared_git_direct_unchanged']
                               and sentinel['review_tracked_unchanged_before_removal']}
    save('end-readback.json', {'checks': checks, 'sentinels': sentinel,
         'gate_git_receipts': review_clean + worker_clean + review_head + worker_head,
         'lifecycle_events': saved_results + removed + review_event('review_worktree_removed') + reclaimed,
         'candidate_commit': candidate})
    observation_complete = has_section and (args.round != 2 or isinstance(mutations, list) and len(mutations) >= 2)
    status = 'PASS' if all(checks.values()) and observation_complete else 'INCOMPLETE'
    save('real-readback.json', {'status': status, 'round': args.round, 'checks': checks,
         'report_section_present': has_section,
         'mutation_count': len(mutations) if isinstance(mutations, list) else None,
         'model_verdict': result.get('verdict'), 'model_judgement_correctness': 'not mechanically evaluated'})
    print(json.dumps({'status': status, 'mutation_count': len(mutations) if isinstance(mutations, list) else None,
                      'model_verdict': result.get('verdict')}, ensure_ascii=False))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
