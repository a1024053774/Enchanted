"""重放历史弱验收反例；不启动后台、Electron 或模型。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from test_t163_controller_e2e import oracle_probe  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，选新路径'
    out = Path(tempfile.mkdtemp(prefix='t163-oracle-known-bad-', dir='/private/tmp'))
    legacy = ROOT / 'evidence/2026-10-23-batch24/T-155/fixture-inputs'
    shutil.copy2(legacy / 'check_pantry_summary.py', out / 'check_pantry.py')
    shutil.copy2(legacy / 'check_shopping_list.py', out / 'check_shopping.py')
    report = dict(status='INCOMPLETE', scope='仅验证测试能抓住历史弱验收；不是本票真实模型红态',
                  fixture=str(out), argv=sys.argv, checks=[])
    oracle_probe(SimpleNamespace(out=out, env=dict(os.environ)), report)
    failed = {check['name'] for check in report['checks'] if not check['passed']}
    # Independent counterexamples: both historical checkers ignore meaning; the summary checker swaps k/q.
    expected = {'summary-wrong-numbers', 'summary-inverted', 'shopping-inverted', 'shopping-grouped'}
    assert expected <= failed, (expected, failed)
    assert all(check['passed'] for check in report['checks'] if check['expected_accept']), report
    report.update(status='PASS', rejected_weak_checker_claims=sorted(failed), expected_counterexamples=sorted(expected))
    with args.summary.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), rejected=sorted(failed))))


if __name__ == '__main__':
    main()
