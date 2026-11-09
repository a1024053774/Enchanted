"""Read-only provenance audit, plus disposable-copy mutation replay.

No Git metadata or external state is changed. Runtime evidence is attributed to
the prior controller execution; local startup failures never count as kills.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
MATERIAL = Path('/private/tmp/a2a-requests-LKaPQG/review-materials.md')
REPO = '/Users/luckye/Documents/Code/a2a'
OLD = '6e92ec6f0d0b59423f5f1bcb85cc39174da70bf5'
SOURCE = 'e18e5207de94fd6ea56be9868de45c18c1f2991f'
CANDIDATE = '6e1fde0a28a13b7cfd2d2f7b42d6363ffda2fa67'
MERGE = '5ba4e68e9038e7bf4c01c2d1028b2917807c144b'
BASE = '62faa87b9424e48a4739920b53920d111a057486'
ANCESTOR = '3647a07bdacb514cdc303965be8c52b84d9356b2'
PREFIX = 'evidence/2026-11-08-batch34/T-262/worker/'
REVIEW = PREFIX + 'recovery-a3/sources/review-01/'
PRODUCTS = ['workbench/app/RecordsPage.tsx', 'workbench/app/records.css',
            'workbench/tests/test_t262_records_e2e.py']
EXPECTED = {
    'no-sort': '每区最新在前，同时间按记录身份稳定排列',
    'receipt-task': '任务筛选同时约束双区',
    'ignore-session': '同一 launch 的输入与回执一起筛选',
    'no-full-receipt': '完整回执与原始存储一致',
}


def git(*args):
    return subprocess.check_output(['git', '-C', REPO, *args])


def save(name, data):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    text = MATERIAL.read_bytes().decode('utf-8', errors='strict')
    blocks = text.split('候选改动：\n', 1)[1].split('机械验收：\n', 1)[0].split('diff --git ')[1:]
    added = {}
    for block in blocks:
        lines = block.split('\n')
        path = lines[0].split(' b/', 1)[1]
        if 'new file mode ' not in block:
            continue
        contents = []
        in_hunk = False
        for line in lines[1:]:
            if line.startswith('@@ '):
                in_hunk = True
            elif in_hunk and line.startswith('+'):
                contents.append(line[1:])
        ending = '\n' if contents and '\\ No newline at end of file' not in lines else ''
        added[path] = ('\n'.join(contents) + ending).encode('utf-8')
    for path, data in added.items():
        assert data == git('show', CANDIDATE + ':' + path), path
    product_checks = []
    for path in PRODUCTS:
        local = (ROOT / path).read_bytes()
        for ref in [OLD, SOURCE, CANDIDATE, MERGE]:
            assert local == git('show', ref + ':' + path), (ref, path)
        product_checks.append(dict(path=path, bytes=len(local), equal_refs=[OLD, SOURCE, CANDIDATE, MERGE]))
    assert not git('diff', ANCESTOR, BASE, '--', *PRODUCTS)
    old_worker = git('ls-tree', '-r', '--name-only', SOURCE, '--', PREFIX).decode().splitlines()
    assert len(old_worker) == 123
    for path in old_worker:
        assert added[path] == git('show', SOURCE + ':' + path), path
    original_worker = git('ls-tree', '-r', '--name-only', OLD, '--', PREFIX).decode().splitlines()
    for path in original_worker:
        assert added[path] == git('show', OLD + ':' + path), path
    assert {p for p in added if p.startswith(PREFIX)} - set(old_worker) == {PREFIX + 'recovery-a4/RESULTS.md'}
    oracle_paths = ['REVIEW.md', 'acceptance/', '.project-map/tickets/T-262-records-grouping-order.md',
                    'workbench/tests/test_t179_receipt_summary_e2e.py',
                    'workbench/tests/test_t133_t134_records_metrics_e2e.py']
    assert not git('diff', BASE, CANDIDATE, '--', *oracle_paths)
    mechanical = json.loads(text.split('机械验收：\n', 1)[1].split('上一轮问题清单：\n', 1)[0])
    assert mechanical['C'] == CANDIDATE and mechanical['M'] == MERGE
    result = mechanical['result']
    current = json.loads(result['stdout'])
    assert result['exit'] == 0 and current['status'] == 'PASS' and not current['failed']
    assert len(current['checks']) == 38 and current['base'] == MERGE
    assert current['cleanup']['removed'] and not current.get('error')
    assert all(c['expected'] == c['actual'] for c in current['checks'])
    summary = json.loads(added[REVIEW + 'external-01/summary.json'])
    assert summary['candidate'] == OLD
    assert summary['source_restored_byte_for_byte']
    external = []
    for case in ['candidate', *EXPECTED]:
        raw = json.loads(added[REVIEW + 'external-01/' + case + '.json'])
        overview = next(r for r in summary['results'] if r['case'] == case)
        assert raw['base'] == OLD and not raw.get('error') and not raw.get('cleanup_error')
        assert raw['diagnostics']['before_cleanup']['process_started']
        assert raw['electron_start']['cwd'] == summary['workspace']
        assert raw['cleanup']['removed'] and raw['core_cleanup']['exit'] == 0
        assert json.loads(raw['core_cleanup']['stdout'])['stopped']
        failed = [r['name'] for r in raw['failed']]
        assert failed == overview['failed']
        if case == 'candidate':
            assert overview['exit'] == 0 and raw['status'] == 'PASS' and len(raw['checks']) == 38 and not failed
            signal = None
        else:
            assert overview['exit'] == 1 and raw['status'] == 'FAIL' and EXPECTED[case] in failed
            signal = next(r for r in raw['failed'] if r['name'] == EXPECTED[case])
            assert signal['actual'] != signal['expected']
        external.append(dict(case=case, command=overview['command'], cwd=summary['workspace'],
                             status=raw['status'], exit=overview['exit'], failed=failed, signal=signal))
    save('evidence-check.json', dict(status='PASS', material_utf8=True, diff_blocks=len(blocks),
         added_files_compared=len(added), products=product_checks, worker_preserved=len(old_worker),
         old_worker_preserved=len(original_worker), frozen_unchanged=oracle_paths,
         current_mechanical=dict(candidate=CANDIDATE, merge=MERGE, status=current['status'],
                                 checks=len(current['checks']), exit=result['exit'], base=current['base']),
         external_attribution='独立审查员构造，主控外部执行；本轮审查员读取原始报告并核对字节',
         external=external))
    page = ROOT / PRODUCTS[0]
    original = page.read_bytes()
    assert original == added[REVIEW + 'RecordsPage.original.tsx']
    save('mutation-expectations.json', EXPECTED)
    mutations = []
    try:
        for case, expected in EXPECTED.items():
            patch = added[REVIEW + case + '.diff']
            with (OUT / (case + '.diff')).open('xb') as stream:
                stream.write(patch)
            lines = patch.decode('utf-8').splitlines()
            removed = [line[1:] for line in lines if line.startswith('-') and not line.startswith('---')]
            inserted = [line[1:] for line in lines if line.startswith('+') and not line.startswith('+++')]
            assert len(removed) == len(inserted) == 1
            before, after = removed[0].encode(), inserted[0].encode()
            assert original.count(before) == 1
            mutant = original.replace(before, after)
            page.write_bytes(mutant)
            assert page.read_bytes() == mutant and mutant != original
            # The original entry point exits at git rev-parse before creating any
            # fixture in this Git-free review copy; do not bypass this boundary.
            command = ['/usr/bin/python3', 'workbench/tests/test_t262_records_e2e.py']
            run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            with (OUT / (case + '.stdout')).open('x') as stream:
                stream.write(run.stdout)
            with (OUT / (case + '.stderr')).open('x') as stream:
                stream.write(run.stderr)
            assert run.returncode != 0 and 'not a git repository' in run.stderr
            mutations.append(dict(case=case, removed=removed[0], inserted=inserted[0], command=command,
                                  local_exit=run.returncode, local_status='INCOMPLETE',
                                  local_reason='git rev-parse HEAD fails before business checks',
                                  independent_expectation=expected,
                                  external_business_result=next(x for x in external if x['case'] == case)))
            page.write_bytes(original)
    finally:
        page.write_bytes(original)
    assert page.read_bytes() == original
    save('mutation-recheck.json', dict(status='PASS', scope='同字节候选的四个既有补丁及已归档外部业务检出核对',
                                      local_execution='INCOMPLETE', source_restored=True, mutations=mutations))
    print(json.dumps(dict(status='PASS', artifacts=str(OUT), products_equal=True,
                         archived_worker_preserved=len(old_worker), current_checks=38,
                         external_mutants_rejected=4, local_mutant_runs='INCOMPLETE: no .git',
                         source_restored=True), ensure_ascii=False))


if __name__ == '__main__':
    main()
