#!/usr/bin/env python3
"""只在一次性副本归档 T-086，并核对代码中的 evidence 引用范围。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
PRIMARY = Path('/Users/luckye/Documents/Code/a2a')
RELATIVE = 'evidence/2026-10-15-batch15/T-086'
EXTERNAL = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089')
# This inventory comes from inspecting the direct read sites, not from the
# archive implementation. Other matches create outputs or document provenance.
READERS = {
    'workbench/tests/test_command_evidence.py': 'T-075/card-4/offline-trace 的 commands.jsonl 与两份 .bin',
    'workbench/tests/run_daemon_acceptance.py': 'T-075/card-5 三个小文件、T-075/run-acceptance.py；T-076/card-2 两个小文件',
    'workbench/tests/audit_legacy_scope.py': 'T-076/card-2/legacy-acceptance-hunks.diff',
    'workbench/tests/test_worktree_lifecycle_e2e.py': 'T-077 的 PLAN、决定01/02、outside-sandbox.sh；baseline 模式另读 outside-red-01/sources.tar.gz',
    'workbench/tests/prepare_s3_baseline.py': '旧 T-077 checkout 的 outside-red-01/run.json 和 sources.tar.gz',
    'workbench/tests/run_t076_green.py': 'T-076 consistency 数据库目录；T-075/card-4/outside-live-04/lifecycle',
    'workbench/tests/run_t076_legacy_green.py': 'T-076/card-2/legacy-acceptance-hunks.diff；T-075 lifecycle',
    'workbench/tests/test_t081_archive_ownership.py': 'T-081/full-02/t075-coop/run.json 和 fixtures.tar.gz',
    'workbench/tests/run_t081_bad_worker_suite.py': 'T-081/full-03/t076-wide/run.json；T-077/controlled-trailer-input.json',
    'workbench/tests/run_t081_capability_turn.py': 'T-081 的 prepared/review/receipt、run-01/02/03、finding 与 native-root；旧归档仍要求外置盘',
    'workbench/tests/t081_capability_home.py': 'T-081/capability-run-02/03/04 的 run.json；夹具 owned-pids',
    'workbench/tests/diagnose_t081_capability_run02.py': 'T-081/capability-run-02 的 pty、events、commands、run.json',
    'workbench/tests/check_t081_capability_paths.py': 'T-081/capability-run-02 的 commands、run.json',
    'workbench/tests/check_t081_capability_run03.py': 'T-081/capability-run-02 的 commands 与 run-03 的 run.json',
    'workbench/tests/collect_t081_closeout.py': 'T-081/full-04、capability 与补充验收 JSON',
    'workbench/tests/commit_t081_duplicate_fix.py': 'T-081/duplicate-conflict-01 的 run/review 记录和 source_snapshot 路径',
    'workbench/tests/test_t082_review_boundary_e2e.py': 'T-082/protocol-red-green-01/real-review-submit.json',
    'workbench/tests/archive_t081_capability_run02.py': 'T-081/capability-run-02/commands.jsonl，归档命令读取原件',
    'workbench/tests/commit_t081_closeout.py': 'T-081/cas-01、home-cleanup-01、closeout-final-01 的结果',
    'workbench/tests/prepare_t081_capability_run02.ts': 'T-081/capability-review-01 的 policy、task-card、role、config；prepared 的 hooks',
    'workbench/tests/prepare_t081_capability_run03.ts': 'T-081/capability-review-02、run02-diagnosis-02、prepared 的 hooks',
    'workbench/tests/prepare_t081_capability_run04.ts': 'T-081/capability-review-03、run03-finding-01、prepared 的 hooks',
    'workbench/tests/run_p_review.py': 'T-076/card-2/p-review-02 的 policy、角色、批准材料与 source snapshot',
    'workbench/tests/run_t076_quality_real.py': 'T-076/card-2/real-delivery-02 的 policy、脚本与归档；p-review-readback-01.json',
    'workbench/tests/run_t076_quality_widen.py': 'T-076/card-2/outside-focused-tracer-01/run.json 与 candidate-source.tar.gz',
    'workbench/tests/run_t081_duplicate_case.py': 'T-081/full-04/green-trailer_duplicate/trailer_duplicate/observation.json',
    'workbench/tests/test_t081_capability_audit.ts': 'T-081/capability-review-04 的 policy 与 FIRST-TURN.template.md',
}
SAMPLES = [
    'evidence/2026-10-10-batch12/T-075/card-5/controller-decision-01.md',
    'evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh',
    'evidence/2026-10-10-batch12/T-075/card-5/readback-timing-probe.py',
]


def files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def reference_audit():
    rows = []
    for folder in ('workbench/tests', 'acceptance'):
        for path in sorted((PRIMARY / folder).rglob('*')):
            if path.suffix not in ('.py', '.ts', '.mjs', '.js'):
                continue
            source = path.read_text(encoding='utf-8')
            hits = [{'line': n, 'text': text.strip()} for n, text in enumerate(source.splitlines(), 1)
                    if 'evidence/' in text or 'T-086' in text or '/ "evidence"' in text]
            if not hits:
                continue
            name = str(path.relative_to(PRIMARY))
            # Output receipts are read in the same invocation; those are new
            # caller-owned paths. Fixed historical input readers are listed above.
            kind = '历史输入' if name in READERS else '输出、同次运行读回或记录引用'
            rows.append({'file': name, 'kind': kind, 'input': READERS.get(name, ''), 'sites': hits,
                         'references_t086': 'T-086' in source,
                         'result': 'INCOMPLETE' if 'T-086' in source else 'PASS',
                         'claim': '固定输入属于其他 ticket，或在本次运行生成；不在 T-086 副本搬迁集合内'})
    missing = sorted(set(READERS) - {row['file'] for row in rows})
    if missing:
        raise RuntimeError('已审查 reader 没被扫描到：' + str(missing))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--external', action='store_true', help='主控运行：写入本票外置盘测试目录')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.external:
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('外置盘未挂载')
        area = EXTERNAL / ('replay-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        area.mkdir(parents=True, exist_ok=False)
    else:
        area = Path(tempfile.mkdtemp(prefix='t089-replay-', dir='/tmp')).resolve()
    source = area / 'copy' / RELATIVE
    original = ROOT / RELATIVE
    before = files(original)
    shutil.copytree(original, source, symlinks=True)
    assert files(source) == before
    target = area / 'archives/2026-10-15-batch15/T-086'
    argv = [sys.executable, '-B', str(ROOT / 'workbench/tests/archive_evidence.py'), str(source),
            '--mount-point', '/Volumes/WD-Elements' if args.external else '/', '--archive-root', str(target),
            '--timeout', '120', '--replay', 'python3', str(Path(__file__).resolve()), '--output', str(args.output)]
    command = subprocess.run(argv, capture_output=True, text=True, timeout=130)
    errors = []
    manifests = []
    if command.returncode:
        errors.append(command.stderr)
    else:
        manifests = json.loads(command.stdout)['archives']
        restored = files(source)
        for entry in manifests:
            archived, path = Path(entry['archive']), Path(entry['original'])
            name = str(path.relative_to(source))
            assert entry['bytes'] == sum(len(data) for data in (files(archived).values() if archived.is_dir() else [archived.read_bytes()]))
            del restored[name + '.archive.json']
            if archived.is_dir():
                restored.update({name + '/' + key: data for key, data in files(archived).items()})
            else:
                restored[name] = archived.read_bytes()
        if restored != before:
            errors.append('通过清单重建的所有相对文件名和字节与原件不一致')
    if files(original) != before:
        errors.append('仓库 T-086 原件被改动')
    readers = reference_audit()
    if any(row['result'] != 'PASS' for row in readers):
        errors.append('有代码直接引用 T-086；需逐路径复核')
    samples = []
    sample_root = area / 'samples/evidence/2026-10-10-batch12/T-075'
    for name in SAMPLES:
        data = (PRIMARY / name).read_bytes()
        copy = sample_root / Path(name).relative_to('evidence/2026-10-10-batch12/T-075')
        copy.parent.mkdir(parents=True, exist_ok=True)
        copy.write_bytes(data)
        samples.append({'original': name, 'copy': str(copy), 'bytes': len(data)})
    sample_command = argv[:3] + [str(sample_root), '--mount-point', argv[5], '--archive-root', str(area / 'archives/samples'),
                                 '--timeout', '15', '--replay', 'python3', 'run_daemon_acceptance.py']
    p = subprocess.run(sample_command, capture_output=True, text=True, timeout=23)
    if p.returncode or any(Path(row['copy']).read_bytes() != (PRIMARY / row['original']).read_bytes() for row in samples):
        errors.append('三个真实输入小文件没有原样保留：' + p.stderr)
    result = {'status': 'PASS' if not errors else 'INCOMPLETE', 'external': args.external,
              'area': str(area), 'source': str(source), 'archive': str(target), 'argv': argv,
              'exit_code': command.returncode, 'stderr': command.stderr, 'errors': errors,
              'original_files': len(before), 'original_bytes': sum(map(len, before.values())),
              'archived_items': len(manifests), 'archived_bytes': sum(entry['bytes'] for entry in manifests),
              'remaining_files': len(files(source)), 'original_unchanged': files(original) == before,
              'manifest_paths': [str(Path(entry['original']).with_name(Path(entry['original']).name + '.archive.json')) for entry in manifests],
              'samples': samples, 'sample_argv': sample_command, 'sample_exit_code': p.returncode,
              'references': readers,
              'limitation': '逐项结论仅证明 evidence 引用不在本次 T-086 搬迁集合；没有重跑各历史业务验收，也不外推其他批次可直接归档'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'original_files', 'original_bytes', 'archived_items', 'archived_bytes', 'remaining_files', 'errors')}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
