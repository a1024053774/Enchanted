#!/usr/bin/env python3
"""T-165 03 离线汇总：只读现有摘要、退出码与 candidate.txt，写一个新结果文件。

不启动 CLI、后台、Electron 或测试，不改输入；输出存在时拒绝覆盖。
保留 RUN-OUTSIDE-03 当时汇总崩溃的事实。两种 checks 格式来自现有测试：
{name, passed: bool} 列表，以及断言通过后才追加名称的字符串列表。
名称列表不代替顶层 PASS、零退出码与无错误条件；所有原反证条件保持。
"""
import json
from pathlib import Path
import sys
import argparse


def normalize_checks(entries):
    if not isinstance(entries, list) or not entries:
        raise ValueError('checks must be a nonempty list')
    if all(isinstance(entry, str) and entry for entry in entries):
        # T-160/T-133 append a name only after its assertion succeeds.
        # Overall status, process exit and errors are still checked below.
        observed = dict.fromkeys(entries, True)
        kind = 'completed_names'
    elif all(isinstance(entry, dict) and isinstance(entry.get('name'), str) and entry['name'] and
             type(entry.get('passed')) is bool for entry in entries):
        observed = {entry['name']: entry['passed'] for entry in entries}
        kind = 'named_results'
    else:
        raise ValueError('checks must contain completed names or named boolean results')
    if len(observed) != len(entries):
        raise ValueError('duplicate check names')
    return observed, kind


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('run_dir', type=Path)
parser.add_argument('--output', type=Path, help='new output path; default RUN_DIR/RESULT.json')
args = parser.parse_args()
root = args.run_dir.resolve()
output = args.output or root / 'RESULT.json'
if output.exists():
    raise FileExistsError('preserve existing output: ' + str(output))
candidate = (root / 'candidate.txt').read_text(encoding='utf-8').strip()
names = ['ordered-1', 'ordered-2', 'ordered-3', 'ordered-baseline', 'unrelated-stop', 'mutant-drop-stop',
         'stop-input-1', 'stop-input-2', 'stop-input-3', 'stop-input-baseline', 'stop-input-bad-caller',
         'stale-baseline', 'stale-recover', 'stale-expired', 'mutant-old-stop', 'mutant-no-reason',
         'mutant-no-recovery', 'split-regression', 'review-regression', 'controller-regression']
stale_failures = {
    'stale-baseline': 'stale_submit_explicitly_refused',
    'mutant-old-stop': 'unmatched_stop_never_enters_execution',
    'mutant-no-reason': 'header_and_sidebar_explain_refusal',
    'mutant-no-recovery': 'recovery_action_exists_but_no_automatic_retry',
}
ordered_failures = {'positive_returns_idle_without_regular_recovery',
                    'intervention_turn_stop_restores_idle', 'queued_native_turn_bound_and_completed'}
checks = []
for name in names:
    path = root / (name + '.json')
    if not path.is_file():
        checks.append(dict(name=name, passed=False, reason='summary absent'))
        continue
    report = json.loads(path.read_text(encoding='utf-8'))
    code = int((root / (name + '.exit')).read_text().strip())
    observed, checks_format = normalize_checks(report.get('checks'))
    failed = {key for key, value in observed.items() if not value}
    clean = not report.get('errors') and not report.get('error')
    if name in ('ordered-baseline', 'mutant-drop-stop'):
        pane = report.get('observed', {}).get('final_pane', {})
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and
                  failed == ordered_failures and observed.get('real_stop_before_native_turn_registration') is True and
                  observed.get('original_stop_submit_accepted') is True and pane.get('state') == 'busy' and
                  pane.get('active') is not None)
        if name == 'ordered-baseline':
            passed = passed and report.get('red_reproduced') is True
    elif name in ('stop-input-baseline', 'stop-input-bad-caller'):
        refused = any(e['type'] == 'relay_rejected' and e['data'].get('result', {}).get('error') == 'worker_not_active'
                      for e in report.get('observed', {}).get('timeline', []))
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and refused and
                  observed.get('original_stop_submit_accepted') is False and
                  observed.get('input_intersects_original_stop_batch') is True and
                  observed.get('input_bytes_unchanged') is True)
    elif name in stale_failures:
        passed = (code == 1 and report.get('status') == 'INCOMPLETE' and clean and
                  observed.get(stale_failures[name]) is False and
                  observed.get('actual_native_new_turn_after_original_stop') is True)
    else:
        passed = code == 0 and report.get('status') == 'PASS' and clean and not failed
        if name == 'unrelated-stop':
            passed = passed and all(observed.get(key) is True for key in (
                'unrelated_stop_remains_unmatched', 'unrelated_stop_never_completes_turn',
                'unrelated_stop_never_transfers_request', 'real_stop_before_native_turn_registration'))
    checks.append(dict(name=name, passed=bool(passed), exit=code, status=report.get('status'),
                       failed_checks=sorted(failed), checks_format=checks_format, check_results=observed,
                       errors=report.get('errors'), error=report.get('error'), summary=str(path),
                       argv=report.get('argv'), revision=report.get('revision'), mutant=report.get('mutant'),
                       fixture=report.get('fixture'), input=report.get('input')))
result = dict(status='PASS' if all(c['passed'] for c in checks) else 'INCOMPLETE', checks=checks,
              scope='20-case T-165 candidate behavior checkpoint; independent acceptance remains separate',
              product_candidate=candidate, run_dir=str(root), vendor_model_turns=0,
              summary_replay_argv=sys.argv, tests_rerun=False,
              prior_aggregate_failure=dict(status='INCOMPLETE', exit=1,
                  reason='original RUN-OUTSIDE-03 aggregator assumed dictionary checks; string-list checks raised TypeError'))
with output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps(dict(status=result['status'], cases=len(checks),
                     passed=sum(check['passed'] for check in checks), output=str(output)), ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
