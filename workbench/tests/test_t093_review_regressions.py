"""Review regressions with synthetic files and intercepted cache writes/signals."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import signal
import sys
import tempfile
import time
import types
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'src/claudeLoginSession.py'
output = Path(sys.argv[1])
assert not output.exists()
spec = importlib.util.spec_from_file_location('review_runtime', SOURCE)
runtime = importlib.util.module_from_spec(spec)
source_text = Path(sys.argv[2]).read_text() if len(sys.argv) > 2 else SOURCE.read_text()
compiled = compile(source_text, str(SOURCE), 'exec')
exec(compiled, vars(runtime))
checks = []


def record(name, action):
    try:
        detail = action()
        checks.append({'check': name, 'status': 'PASS', 'detail': detail})
    except AssertionError as error:
        checks.append({'check': name, 'status': 'FAIL', 'business_failure': str(error)})


def cache_writes():
    attempted = []
    original = importlib.machinery.SourceFileLoader.get_data
    def cache_miss(loader, path):
        if str(path).endswith('.pyc'):
            raise FileNotFoundError(path)
        return original(loader, path)
    def no_write(loader, path, data, **options):
        attempted.append(str(path))
    previous = sys.dont_write_bytecode
    try:
        # Force a cold cache without removing or writing any real cache file.
        with patch.object(importlib.machinery.SourceFileLoader, 'get_data', cache_miss), \
             patch.object(importlib.machinery.SourceFileLoader, 'set_data', no_write):
            sys.dont_write_bytecode = False
            exec(compiled, {'__name__': 'intercepted_review_module', '__file__': str(SOURCE)})
    finally:
        sys.dont_write_bytecode = previous
    assert not attempted, 'bootstrap_must_disable_bytecode_before_local_import'
    return {'cache_write_attempts': len(attempted), 'actual_cache_writes': 0}


def safe_flags():
    assert hasattr(runtime, 'require_safe_python'), 'supported_python_flags_guard_required'
    runtime.require_safe_python()
    rejected = 0
    for missing in ('isolated', 'no_site', 'dont_write_bytecode'):
        flags = dict(isolated=1, no_site=1, dont_write_bytecode=1)
        flags[missing] = 0
        with patch.object(runtime.sys, 'flags', types.SimpleNamespace(**flags)):
            try:
                runtime.require_safe_python()
            except ValueError as error:
                assert str(error) == 'python_isolated_no_site_no_bytecode_required'
                rejected += 1
            else:
                raise AssertionError('unsupported_python_flags_must_be_rejected')
    return {'missing_flag_cases_rejected': rejected}


def unexpected_failure(persists):
    with tempfile.TemporaryDirectory(prefix='t093-review-D-', dir='/private/tmp') as temporary:
        root = Path(temporary)
        private, directory = root / 'private', root / 'receipts'
        for path in (private / 'metadata', directory):
            path.mkdir(parents=True)
        runtime.save(private / 'metadata/before.json', {})
        runtime.save(directory / 'stop.json', {})
        runtime.save(private / 'services.json', {'F': {'pid': 440101, 'pgrp': 440001}})
        c_group = 330001
        alive = {440001, c_group}
        calls = []
        def group_signal(group, kind):
            if group not in alive:
                raise ProcessLookupError()
            if kind:
                calls.append((group, kind))
                if kind == signal.SIGKILL and (group != c_group or not persists):
                    alive.remove(group)
        ticks = iter(range(1000))
        session = {'private_root': str(private), 'metadata_directory': str(directory),
                   'real_home': str(root / 'synthetic-home'), 'c_root_pid': c_group,
                   'deadline': time.time() + 30}
        with patch.object(runtime, 'inventory', side_effect=PermissionError('synthetic denial')), \
             patch.object(runtime.os, 'killpg', side_effect=group_signal), \
             patch.object(runtime.os, 'getpgid', side_effect=lambda pid: {440101: 440001, c_group: c_group}[pid]), \
             patch.object(runtime.signal, 'signal'), patch.object(runtime.signal, 'setitimer'), \
             patch.object(runtime.time, 'sleep'), \
             patch.object(runtime.time, 'monotonic', side_effect=lambda: next(ticks)):
            code = runtime.metadata_service(session)
        receipt = runtime.read(directory / 'removed.json')
        assert code == 2 and receipt['primary_failure'] == 'PermissionError', 'metadata_primary_failure_must_survive_cleanup'
        if persists:
            assert receipt['cleanup_failures'] and not receipt['isolated_home_removed'] and private.exists(), \
                'live_C_group_must_prevent_cleanup_success_receipt'
        else:
            assert c_group not in alive, 'unexpected_failure_must_confirm_C_group_exit'
            assert not receipt['cleanup_failures'] and receipt['isolated_home_removed']
        return {'C_group_persistent': persists, 'primary_failure': receipt['primary_failure'],
                'cleanup_failures': receipt['cleanup_failures'], 'isolated_home_removed': receipt['isolated_home_removed'],
                'C_group_signals': [int(kind) for group, kind in calls if group == c_group]}


record('cold_cache_bootstrap', cache_writes)
record('supported_python_flags', safe_flags)
record('metadata_failure_C_ignores_TERM', lambda: unexpected_failure(False))
record('metadata_failure_C_exit_unconfirmed', lambda: unexpected_failure(True))
status = 'PASS' if all(check['status'] == 'PASS' for check in checks) else 'FAIL'
result = {'status': status, 'scope': 'synthetic files; intercepted cache writes; mocked D signals/time; no auth/network/OS profile',
          'actual_cache_writes': 0, 'actual_process_signals': 0, 'checks': checks}
with output.open('x') as stream:
    json.dump(result, stream, indent=2); stream.write('\n')
print(json.dumps({'status': status, 'checks': len(checks)}))
raise SystemExit(0 if status == 'PASS' else 2)
