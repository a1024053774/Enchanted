"""只重放 runner 的归档收尾，不启动门禁、daemon 或模型。

失败方式：重复写子套件归档；子套件漏归档被静默补建；runner 新归档缺内容；
意外已存在的 runner 归档被覆盖。预期来自单一写入者和保留失败现场的要求。
"""
import argparse
import ast
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from types import SimpleNamespace

import run_t081_bad_worker_suite as runner


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    original = ROOT / 'evidence/2026-10-14-batch14/T-081/full-02/t075-coop'
    child_report = json.loads((original / 'run.json').read_text(encoding='utf-8'))
    if child_report['status'] != 'PASS' or child_report['tests_run'] != 8:
        raise RuntimeError('需要保留的真实 coop 8/8 收据。')
    tree = ast.parse(Path(runner.__file__).read_text(encoding='utf-8'))
    body = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    functions = [node for node in body.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('archive_fixture', 'regression')]
    module = ast.Module(body=functions, type_ignores=[])
    records = []
    root = Path(tempfile.mkdtemp(prefix='t81archive-', dir='/tmp')).resolve()
    for name in ('child-owned', 'child-missing', 'runner-new', 'runner-existing'):
        directory = root / name
        directory.mkdir()
        destination = directory / 't075-coop'
        destination.mkdir()
        fixture = directory / 'fixture'
        fixture.mkdir()
        (fixture / 'sentinel.txt').write_text('independent archive content\n', encoding='utf-8')
        data = child_report if name.startswith('child-') else {'artifact_root': str(fixture)}
        (destination / 'run.json').write_text(json.dumps(data), encoding='utf-8')
        archive = destination / 'fixtures.tar.gz'
        if name == 'child-owned':
            shutil.copyfile(original / 'fixtures.tar.gz', archive)
        elif name == 'runner-existing':
            archive.write_bytes(b'original anomaly; do not replace\n')
        before = archive.read_bytes() if archive.exists() else None
        calls = []
        namespace = dict(vars(runner), ROOT=ROOT, out=directory, report={'steps': []},
                         ensure_frozen=lambda: None,
                         command=lambda argv, **kwargs: (calls.append(list(map(str, argv))) or SimpleNamespace(returncode=0)))
        exec(compile(module, str(runner.__file__), 'exec'), namespace)
        error = None
        try:
            if name.startswith('child-'):
                # The child has already completed in full-02. Replay only its
                # saved receipt and archive at the parent's completion boundary.
                namespace['regression']('t075-coop', 'run_s3_rebased_regression.py', [])
            else:
                namespace['archive_fixture'](data, destination)
        except Exception as caught:
            error = caught
        if name == 'child-owned':
            passed = error is None and archive.read_bytes() == before and len(namespace['report']['steps']) == 1
            expected = '子套件现有归档保留，父流程正常记完该阶段'
        elif name == 'child-missing':
            passed = isinstance(error, RuntimeError) and not archive.exists()
            expected = '子套件缺归档时报错，父流程不补造'
        elif name == 'runner-existing':
            passed = isinstance(error, FileExistsError) and archive.read_bytes() == before
            expected = 'runner 意外已有归档继续独占创建失败并保留原件'
        else:
            passed = error is None
            if passed:
                with tarfile.open(archive, 'r:gz') as stream:
                    passed = stream.extractfile('fixture/sentinel.txt').read() == b'independent archive content\n'
            expected = 'runner 为未归档夹具创建含独立 sentinel 的完整归档'
        records.append({'case': name, 'passed': passed, 'expected': expected,
                        'error': repr(error) if error else None, 'commands_not_executed': calls,
                        'fixture': str(directory)})
    record = {'status': 'PASS' if all(row['passed'] for row in records) else 'INCOMPLETE',
              'scope': '仅 runner 归档边界；不证明门禁或整个 full-03', 'command': sys.argv,
              'source_failure': str(original), 'cases': records, 'real_codex_turns': 0,
              'daemon_started': False}
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
