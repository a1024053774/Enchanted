#!/usr/bin/env python3
"""Check remaining entry arguments and offline boundaries; start no daemon."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
E = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from command_evidence import CommandLog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    log = CommandLog(out)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    rows = []

    def call(name, argv, report=None):
        result = log.run(argv, cwd=ROOT, env=env, timeout=45)
        row = {'name': name, 'argv': list(map(str, argv)), 'exit': result.returncode}
        if report is not None:
            data = json.loads(report.read_text(encoding='utf-8'))
            row.update(report=str(report), result=data.get('status', 'PASS' if data.get('failure') is None else 'INCOMPLETE'))
        rows.append(row)
        if result.returncode or row.get('result', 'PASS') != 'PASS':
            raise RuntimeError('Preflight failed without retry: ' + name)

    record = {'status': 'INCOMPLETE', 'scope': 'entry help/syntax and offline request/Panes boundaries; not daemon E2E',
              'real_codex_turns': 0, 'argv': sys.argv, 'steps': rows}
    try:
        for name in ('test_relay_conflict_e2e.py', 'test_conflict_trailer_proofs.py', 'test_multiturn_identity_e2e.py',
                     'test_startup_shutdown_e2e.py', 'test_quality_tracer_e2e.py', 'test_quality_widen_e2e.py',
                     'test_quality_chain_e2e.py', 'test_quality_legacy_e2e.py', 'test_relay_cli.py'):
            call('help-' + name, [sys.executable, '-B', ROOT / 'workbench/tests' / name, '--help'])
        for name in ('test_relay_core.ts', 'test_relay_scope.ts', 'test_native_final_read.ts',
                     'test_pane_dispatch_state.ts', 'test_conflict_panes.ts', 'relay_conflict_host.ts',
                     'trailer_conflict_host.ts', 'startup_shutdown_host.ts', 'multiturn_identity_host.ts', 'controlled_quality_pty.ts'):
            call('syntax-' + name, ['node', '--check', ROOT / 'workbench/tests' / name])
        call('relay-core', ['node', ROOT / 'workbench/tests/test_relay_core.ts', out / 'relay-core'], out / 'relay-core/results.json')
        call('relay-cli', [sys.executable, '-B', ROOT / 'workbench/tests/test_relay_cli.py', '--output', out / 'relay-cli'], out / 'relay-cli/results.json')
        call('relay-scope', ['node', ROOT / 'workbench/tests/test_relay_scope.ts', ROOT / 'workbench/src/relay.ts', out / 'relay-scope'], out / 'relay-scope/run.json')
        call('relay-global-mutant', [sys.executable, '-B', E / 'check-relay-mutants.py', '--mutant', 'global-lookup',
             '--output', out / 'relay-global-mutant'], out / 'relay-global-mutant/run.json')
        for name, script in [('native-final', 'test_native_final_read.ts'), ('dispatch-state', 'test_pane_dispatch_state.ts')]:
            call(name, ['node', ROOT / 'workbench/tests' / script, out / name], out / name / 'results.json')
        call('panes', ['node', ROOT / 'workbench/tests/test_conflict_panes.ts', '--product', ROOT,
             '--output', out / 'panes.json'], out / 'panes.json')
        record['status'] = 'PASS'
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        record['error'] = repr(error)
    record['files_over_5mb'] = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
    if record['files_over_5mb']: record['status'] = 'INCOMPLETE'
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'steps', 'files_over_5mb')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
