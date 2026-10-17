#!/usr/bin/env python3
"""T-089 的真实命令契约验证；外置盘及挂起场景由主控运行。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
COMMAND = ROOT / 'workbench/tests/archive_evidence.py'
EXTERNAL = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-089')


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def snapshot(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob('*') if p.is_file()}


class Checks:
    def __init__(self, root, command, external):
        self.root, self.command, self.external = root, command, external
        self.results = []

    def call(self, label, source, target, *, mount=None, hook=None, timeout=15, keep=()):
        argv = [sys.executable, '-B', str(self.command), str(source), '--mount-point',
                str(mount or ('/Volumes/WD-Elements' if self.external else '/')),
                '--archive-root', str(target), '--timeout', str(timeout)]
        for item in keep:
            argv += ['--keep', item]
        argv += ['--replay', 'python3', 'fixture-producer.py']
        env = dict(os.environ)
        if hook:
            injection = self.root / (label + '-injection')
            injection.mkdir()
            (injection / 'sitecustomize.py').write_text(hook, encoding='utf-8')
            env['PYTHONPATH'] = str(injection)
        start = time.monotonic()
        p = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=timeout + 8)
        row = {'case': label, 'argv': argv, 'exit_code': p.returncode, 'stdout': p.stdout,
               'stderr': p.stderr, 'elapsed_seconds': time.monotonic() - start}
        self.results.append(row)
        return p

    def fixture(self):
        source = self.root / 'fixture/evidence/batch/T-fixture'
        expected = {'run-01/a.txt': b'first\n', 'run-01/nested/b.bin': b'\x00\x01binary\xff',
                    'fixtures/input.json': b'{"raw":true}', 'snapshot.tar.gz': b'archive-bytes',
                    'output.bin': b'raw\x00', 'state.sqlite3': b'sqlite-fixture',
                    'state.sqlite3-wal': b'wal', 'monitor-01.log': b'monitor events\n',
                    'arbitrary-name/run.json': b'{"status":"PASS"}',
                    'arbitrary-name/output.txt': b'raw output'}
        kept = {'RESULTS.md': b'# summary\n', 'run.json': b'{"summary":true}',
                'outside-sandbox.sh': b'echo preserve\n', 'readback-timing-probe.py': b'print(1)\n',
                'controller-decision-01.md': '确认\n'.encode(), 'other.json': b'{}',
                'ordinary.log': b'not a monitor log', 'notes/file.txt': b'untouched',
                'run-kept/input.bin': b'input consumed by a test', 'run-kept/raw.bin': b'keep ancestor'}
        for name, data in {**expected, **kept}.items():
            write(source / name, data)
        (source / 'run-01/empty').mkdir()
        target = self.root / 'archives/fixture'
        p = self.call('fixture', source, target, keep=['run-kept/input.bin'])
        assert p.returncode == 0, p.stderr
        actual = snapshot(source)
        manifests = {name: json.loads(data) for name, data in actual.items() if name.endswith('.archive.json')}
        assert {name: data for name, data in actual.items() if name not in manifests} == kept
        assert snapshot(target) == expected
        assert (target / 'run-01/empty').is_dir()
        assert len(manifests) == 8, list(manifests)
        for name, entry in manifests.items():
            assert {'original', 'archive', 'bytes', 'replay'} <= entry.keys()
            assert set(entry) == {'original', 'archive', 'bytes', 'files', 'replay'}
            assert entry['original'] == str(source / name.removesuffix('.archive.json'))
            archived = Path(entry['archive'])
            assert archived == target / name.removesuffix('.archive.json')
            values = snapshot(archived).values() if archived.is_dir() else [archived.read_bytes()]
            assert entry['bytes'] == sum(len(data) for data in values)
            assert entry['files'] == len(values)
            assert entry['replay'] == ['python3', 'fixture-producer.py']

    def failure(self, label, hook=None, missing=False, collision=False, timeout=15):
        source = self.root / label / 'source'
        write(source / 'a.bin', b'one original')
        write(source / 'b.bin', b'second original')
        before = snapshot(source)
        target = self.root / 'archives' / label
        mount = None
        if missing:
            mount = self.root / 'not-a-mount'
            mount.mkdir()
            target = mount / 'must-not-be-created'
        if collision:
            write(target / 'b.bin', b'existing evidence')
        p = self.call(label, source, target, hook=hook, mount=mount, timeout=timeout)
        assert p.returncode != 0
        assert snapshot(source) == before, 'failure removed or changed an original or published a manifest'
        if missing:
            assert '未挂载' in p.stderr and not target.exists()
        elif collision:
            assert '已存在' in p.stderr and snapshot(target) == {'b.bin': b'existing evidence'}
        elif label == 'truncated':
            assert '字节数不一致' in p.stderr and (target / 'b.bin').stat().st_size < len(before['b.bin'])
        elif label == 'same-size-corruption':
            assert '逐字节比较不一致' in p.stderr
        elif label == 'io-timeout':
            assert '超时' in p.stderr and p.returncode == 1 and (self.root / 'hang-entered').is_file()
            assert self.results[-1]['elapsed_seconds'] < timeout + 5
            pid = int((self.root / 'hang-entered').read_text(encoding='utf-8'))
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError('受控挂起的归档子进程仍存活')

    def reclaim_failure(self, label, hang=False, inspection_error=False):
        source = self.root / label / 'source'
        expected = {'a.bin': b'one original', 'b.bin': b'second original'}
        for name, data in expected.items():
            write(source / name, data)
        target = self.root / 'archives' / label
        marker = self.root / (label + '-pid')
        # Same filesystem boundary as independent-review-01: the first unlink
        # succeeds; the second either stops its process or raises EIO.
        action = ('Path(' + repr(str(marker)) + ').write_text(str(os.getpid()),encoding="utf-8"); '
                  'os.kill(os.getpid(),signal.SIGSTOP)' if hang else
                  'raise OSError(5,"independent simulated unlink I/O error")')
        if inspection_error:
            action = 'Path(' + repr(str(marker)) + ').write_text("metadata error",encoding="utf-8"); ' + action
        hook = ('import os,signal\nfrom pathlib import Path\nold=Path.unlink\n'
                'def changed(self,*args,**kw):\n if self.name=="b.bin": ' + action + '\n'
                ' return old(self,*args,**kw)\nPath.unlink=changed\n')
        if inspection_error:
            hook += ('old_stat=os.lstat\ndef changed_stat(path,*args,**kw):\n'
                     ' if os.fspath(path)==' + repr(str(source / 'b.bin')) + ' and Path('
                     + repr(str(marker)) + ').exists(): raise OSError(5,"remaining metadata unreadable")\n'
                     ' return old_stat(path,*args,**kw)\nos.lstat=changed_stat\n')
        p = self.call(label, source, target, hook=hook, timeout=0.8 if hang else 5)
        assert p.returncode == 1, p.stderr
        assert snapshot(target) == expected
        assert not (source / 'a.bin').exists()
        assert (source / 'b.bin').read_bytes() == expected['b.bin']
        assert '归档已完成并核对、原件回收未完成' in p.stderr, p.stderr
        assert '保留原件与已有副本' not in p.stderr, p.stderr
        state = json.loads(p.stderr)
        assert state['status'] == 'INCOMPLETE' and state['phase'] == 'reclaim'
        assert state['archive_verified'] is True
        if inspection_error:
            assert state['remaining_originals'] == []
            assert list(state['unverified_originals']) == [str(source / 'b.bin')]
            assert 'remaining metadata unreadable' in state['unverified_originals'][str(source / 'b.bin')]
        else:
            assert state['remaining_originals'] == [str(source / 'b.bin')]
            assert state['unverified_originals'] == {}
        for name in expected:
            entry = json.loads((source / (name + '.archive.json')).read_text(encoding='utf-8'))
            assert entry['original'] == str(source / name) and entry['archive'] == str(target / name)
        if hang:
            assert '超时' in state['reason'] and self.results[-1]['elapsed_seconds'] < 5
            try:
                os.kill(int(marker.read_text(encoding='utf-8')), 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError('回收子进程在超时后仍存活')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--command', type=Path, default=COMMAND)
    parser.add_argument('--output', type=Path, required=True, help='只写新文本结果文件')
    parser.add_argument('--external', action='store_true', help='主控运行：真实外置盘及受控挂起')
    parser.add_argument('--fixture-only', action='store_true', help='红态时运行与绿态相同的夹具路径')
    parser.add_argument('--reclaim-error-only', action='store_true', help='不挂起的回收错误红态/绿态')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.external:
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('外置盘未挂载')
        root = EXTERNAL / ('checks-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        root.mkdir(parents=True, exist_ok=False)
    else:
        root = Path(tempfile.mkdtemp(prefix='t089-checks-', dir='/tmp')).resolve()
    tested_command = root / 'tested-source/archive_evidence.py'
    write(tested_command, args.command.read_bytes())
    checks = Checks(root, tested_command, args.external)
    cases = [('fixture', checks.fixture)]
    if args.reclaim_error_only:
        cases = [('delete-error', lambda: checks.reclaim_failure('delete-error'))]
    elif not args.fixture_only:
        cases += [('unmounted', lambda: checks.failure('unmounted', missing=True)),
                  ('existing-target', lambda: checks.failure('existing-target', collision=True))]
        truncated = 'import shutil\norig=shutil.copyfileobj\ndef copy(a,b,*args,**kw):\n orig(a,b,*args,**kw)\n if b.name.endswith("b.bin"): b.truncate(1)\nshutil.copyfileobj=copy\n'
        corrupt = 'import shutil\norig=shutil.copyfileobj\ndef copy(a,b,*args,**kw):\n orig(a,b,*args,**kw)\n if b.name.endswith("b.bin"): b.seek(0); b.write(b"X")\nshutil.copyfileobj=copy\n'
        cases += [('truncated', lambda: checks.failure('truncated', hook=truncated)),
                  ('same-size-corruption', lambda: checks.failure('same-size-corruption', hook=corrupt)),
                  ('delete-error', lambda: checks.reclaim_failure('delete-error')),
                  ('delete-inspection-error', lambda: checks.reclaim_failure('delete-inspection-error', inspection_error=True))]
        if args.external:
            hang = 'import os,signal,shutil\nfrom pathlib import Path\ndef hang(a,b,*args,**kw):\n Path(' + repr(str(root / 'hang-entered')) + ').write_text(str(os.getpid()),encoding="utf-8")\n os.kill(os.getpid(),signal.SIGSTOP)\nshutil.copyfileobj=hang\n'
            cases += [('io-timeout', lambda: checks.failure('io-timeout', hook=hang, timeout=2))]
            cases += [('delete-hang', lambda: checks.reclaim_failure('delete-hang', hang=True))]
    errors = []
    for label, case in cases:
        try:
            case()
        except (AssertionError, OSError, ValueError, subprocess.TimeoutExpired) as error:
            errors.append({'case': label, 'error': repr(error), 'traceback': traceback.format_exc()})
    result = {'status': 'PASS' if not errors else 'INCOMPLETE', 'external': args.external,
              'fixture_root': str(root), 'command': str(args.command), 'tested_command': str(tested_command),
              'cases': checks.results,
              'errors': errors, 'skipped': [] if args.external else ['真实外置盘', '受控挂起（须主控运行 --external）']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('status', 'fixture_root', 'errors', 'skipped')}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
