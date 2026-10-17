"""File-only checks for the #368 diagnostic/recovery handoff. No process probe."""
import ast
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3]


def load():
    spec = importlib.util.spec_from_file_location('parity_recovery', HERE / 'recover.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main():
    checks = []; recovery = load(); owner, prior, helpers = recovery.inputs()
    assert recovery.SOURCE == SOURCE
    for path in HERE.iterdir():
        if path.is_file() and path.suffix in ('.py', '.json', '.md', '.txt'):
            text = path.read_text(encoding='utf-8'); assert not text.startswith('\ufeff')
            if path.suffix == '.py': ast.parse(text, filename=str(path))
    checks.append('UTF-8/no BOM and Python AST')
    approval = recovery.raw.read_json(HERE / 'approval.json')
    assert approval['approved_by'] is None and approval['approval_ref'] is None
    try: recovery.signed(approval, owner)
    except ValueError as error: assert str(error) == 'signed_recovery_approval_required'
    else: raise AssertionError('unsigned cleanup accepted')
    signed = {**approval, 'approved_by': 'executor', 'approval_ref': 'UNIT ONLY never executed'}
    recovery.signed(signed, owner)
    for changed in [dict(signed, root='/private/tmp/another-scene'), dict(signed, processes={}),
                    dict(signed, source_revision='0' * 40), dict(signed, daemon_stop_allowed=True),
                    dict(signed, operation='kill_anything'), dict(signed, archive='/private/tmp/wrong.tar.gz')]:
        try: recovery.signed(changed, owner)
        except ValueError: pass
        else: raise AssertionError('wrong recovery approval accepted')
    checks.append('unsigned and six mismatched approvals rejected; exact signed fixture accepted (no actions)')
    # Exercise the actual identity guard with a clearly labelled ps transport
    # fixture. It is not OS absence evidence and never calls kill or a daemon.
    original_ps = recovery.ps
    def fake_ps(pid, *_):
        label = next((key for key, value in owner['processes'].items() if value['pid'] == pid), None)
        if label in recovery.APIS:
            return {'identity': owner['processes'][label], 'ppid': 1, 'pgid': pid, 'stat': 'S'}
        return None
    recovery.ps = fake_ps
    recovery.identities(owner, HERE, 'UNIT', recovery.APIS)
    cases = ['PID_reused', 'argv_changed', 'parent_changed', 'zombie', 'managed_still_present', 'helper_still_present']
    for case in cases:
        def bad_ps(pid, *args):
            value = fake_ps(pid, *args)
            if pid == recovery.EXPECTED['ideation_api']:
                value = {**value, 'identity': dict(value['identity'])}
                if case == 'PID_reused': value['identity']['started'] = 'Sat Oct 17 00:00:00 2026'
                if case == 'argv_changed': value['identity']['command'] += ' --other'
                if case == 'parent_changed': value['ppid'] = 999
                if case == 'zombie': value['stat'] = 'Z'
            if (case == 'managed_still_present' and pid == recovery.EXPECTED['daemon']) or (case == 'helper_still_present' and pid == recovery.HELPERS[0]):
                return {'identity': {'pid': pid}, 'ppid': 1, 'pgid': pid, 'stat': 'S'}
            return value
        recovery.ps = bad_ps
        try: recovery.identities(owner, HERE, 'UNIT', recovery.APIS)
        except ValueError: pass
        else: raise AssertionError('bad identity accepted:' + case)
    recovery.ps = original_ps
    checks.append({'ps_transport_only': cases, 'all_rejected': True})
    # Actual tar reader counterexample on an in-memory transport; no fixture or
    # original archive is rewritten.
    from unittest.mock import patch
    import tarfile
    inventory = recovery.raw.read_json(recovery.FLOW / 'retention-archive/bundle.archive.json')['inventory']
    assert recovery.raw.verify_archive(recovery.STAGE, recovery.OLD_ARCHIVE) == inventory
    extract = tarfile.TarFile.extractfile
    class ChangedBytes:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return b'CORRUPTED ARCHIVE TRANSPORT'
    def corrupt(tar, member):
        if member.name == 'snapshot.json': return ChangedBytes()
        return extract(tar, member)
    with patch.object(tarfile.TarFile, 'extractfile', corrupt):
        try: recovery.raw.verify_archive(recovery.STAGE, recovery.OLD_ARCHIVE)
        except ValueError as error: assert str(error) == 'archive_bytes_mismatch:snapshot.json'
        else: raise AssertionError('corrupt archive bytes accepted')
    checks.append('actual tar byte comparison PASS; corrupt snapshot transport rejected before lifecycle')
    commands = []
    for path in sorted(HERE.glob('0*-*.txt')):
        argv = shlex.split(path.read_text(encoding='utf-8'))
        assert argv[0:2] == ['python3', '-B'] and Path(argv[2]).is_file()
        commands.append({'file': path.name, 'entrypoint_exists': argv[2],
                         'output_not_created': not Path(argv[argv.index('--output') + 1]).exists()})
        assert commands[-1]['output_not_created']
    # A dry file preflight executes no ps and no recovery mode.
    command = ['python3', '-B', str(HERE / 'recover.py'), '--mode', 'inspect', '--output',
               str(recovery.BASE / '09c-parity-recovery-inspect-01'), '--check-only']
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    output = {'status': 'PASS', 'checks': checks, 'commands': commands,
              'check_only': {'argv': command, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr},
              'scene_signals': 0, 'scene_keys': 0, 'scene_processes_started': 0, 'SQLite_reads': 0,
              'limitations': 'ps transport tests and file readback only; live identities, child-exit probe and recovery NOT RUN'}
    recovery.raw.save(HERE / 'file-check.json', output)
    print(json.dumps(output, ensure_ascii=False)); return 0


if __name__ == '__main__': raise SystemExit(main())
