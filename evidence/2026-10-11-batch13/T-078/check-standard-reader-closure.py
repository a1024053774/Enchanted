"""Check the reader callers' local imports and exercise the reader from its frozen archive."""
import argparse
import ast
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

SOURCE = Path(__file__).resolve().parents[3]
SEEDS = ['run_t078_p1.py', 't078_09b_phase_driver.py', 't078_09b_i1_permission.py']


def inspect_archive(path):
    with tarfile.open(path) as archive:
        contents = {item.name: archive.extractfile(item).read() for item in archive.getmembers() if item.isfile()}
    required, missing, pending = set(), set(), list(SEEDS)
    while pending:
        name = pending.pop()
        if name in required: continue
        required.add(name)
        relative = 'workbench/tests/' + name
        if relative not in contents:
            missing.add(relative)
            continue
        tree = ast.parse(contents[relative], filename=relative)
        for node in ast.walk(tree):
            imports = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
            for imported in imports:
                dependency = (imported or '').split('.')[0] + '.py'
                if (SOURCE / 'workbench/tests' / dependency).is_file(): pending.append(dependency)
    assert 'p1_output.py' in required
    return contents, sorted(required), sorted(missing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(exist_ok=False)
    contents, required, missing = inspect_archive(args.archive)
    report = {'status': 'INCOMPLETE', 'archive': str(args.archive.resolve()), 'seeds': SEEDS,
              'required_local_modules': required, 'missing_local_dependencies': missing,
              'daemon_starts': 0, 'API_starts': 0, 'native_CLI_starts': 0}
    if not missing:
        with tempfile.TemporaryDirectory(prefix='t078-reader-package-', dir='/private/tmp') as scratch:
            root = Path(scratch)
            for name in required:
                (root / name).write_bytes(contents['workbench/tests/' + name])
            code = """import base64,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import p1_output
assert Path(p1_output.__file__).parent==Path(sys.argv[1])
payload=b'fresh-archive-reader-'+bytes(range(256))*301
calls=[]
def page(offset):
 calls.append(offset);raw=payload[offset:offset+8191]
 return dict(launch='archive-only',start_offset=offset,next_offset=offset+len(raw),total_bytes=len(payload),data_base64=base64.b64encode(raw).decode())
result=p1_output.read_complete_output(page,'archive-only')
assert result['raw']==payload and calls[-1]==len(payload)
print('PASS archive-only import, complete bytes, EOF')
"""
            result = subprocess.run([sys.executable, '-I', '-B', '-c', code, str(root)], capture_output=True, text=True, timeout=15)
            (args.output / 'import.stdout.txt').write_text(result.stdout, encoding='utf-8')
            (args.output / 'import.stderr.txt').write_text(result.stderr, encoding='utf-8')
            assert result.returncode == 0, result.stderr
        # A package that silently drops the helper is the known-bad source boundary.
        mutant = args.output / 'missing-reader.tar.gz'
        with tarfile.open(mutant, 'x:gz') as archive:
            for name, raw in contents.items():
                if name == 'workbench/tests/p1_output.py': continue
                item = tarfile.TarInfo(name); item.size = len(raw); archive.addfile(item, io.BytesIO(raw))
        assert 'workbench/tests/p1_output.py' in inspect_archive(mutant)[2]
        report.update(status='PASS', archive_only_import='PASS', full_bytes_and_EOF='PASS', missing_reader_mutant_rejected=True)
    (args.output / 'result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False)); return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
