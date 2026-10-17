"""Probe the actual quality host bootstrap before the socket boundary.

Failure modes: missing/foreign/reused operator path, absent credential creation
in the actual TypeScript host, wrong state/mode, and missing failure-log copies.
The QualityCase setup and host entry are real; only serve is replaced before
socket/PTY creation. This does not prove reviewer launch or end-check behavior.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import run_t082_boundary as boundary
import test_quality_chain_e2e as quality

ROOT = Path(__file__).resolve().parents[2]


class CapturedHost(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(exist_ok=False)
    checks = []
    # Only the daemon's serve export is intercepted. The actual host still
    # loads its config/PTY installer and creates/reads a real local capability.
    probe = out / 'host-probe.mjs'
    probe.write_text('''import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
import {statSync} from 'node:fs';
import {join} from 'node:path';
const [source,state,control,ready]=process.argv.slice(2);
const credentialURL=pathToFileURL(join(source,'workbench/src/credentials.ts')).href;
const daemonURL=pathToFileURL(join(source,'workbench/src/daemon.ts')).href;
registerHooks({load(url,context,next){
 if(url!==daemonURL)return next(url,context);
 return {format:'module',shortCircuit:true,source:`
  import {readOperatorCredential} from ${JSON.stringify(credentialURL)};
  import {statSync} from 'node:fs';
  export async function serve(root){
   const value=readOperatorCredential(root),path=process.env.A2A_OPERATOR_CREDENTIAL;
   console.log(JSON.stringify({probe:'before-socket',path:path??null,kind:value?.kind??null,
    state:value?.state??null,mode:value?(statSync(path).mode&0o777):null}));
  }`};
}});
process.argv=[process.execPath,join(source,'workbench/tests/quality_chain_host.ts'),source,state,control,ready];
await import(pathToFileURL(process.argv[1]).href);
''', encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='t078-quality-bootstrap-', dir='/private/tmp') as temporary:
        fixtures = Path(temporary).resolve(); (fixtures / 'cases').mkdir()
        quality.SOURCE, quality.OUT = ROOT, out
        quality.base.ARTIFACT_ROOT = fixtures / 'cases'
        case = quality.QualityCase('bootstrap-probe')
        real_popen = subprocess.Popen
        captured = []

        def intercept(argv, *values, **kwargs):
            if len(argv) > 1 and Path(argv[1]).name == 'quality_chain_host.ts':
                captured.append({'argv': list(map(str, argv)), 'env': dict(kwargs['env'])})
                raise CapturedHost()
            return real_popen(argv, *values, **kwargs)

        try:
            for generation in [1, 2]:
                with patch.dict(os.environ, {'A2A_OPERATOR_CREDENTIAL': '/private/tmp/foreign-quality-capability',
                                             'A2A_LAUNCH': 'foreign-worker-launch'}):
                    try:
                        with patch.object(subprocess, 'Popen', intercept):
                            case.setUp() if generation == 1 else case.start_host()
                    except CapturedHost:
                        pass
                assert len(captured) == generation, 'Actual host spawn was not captured'
                item = captured[-1]; env = item['env']; path = env.get('A2A_OPERATOR_CREDENTIAL')
                command = ['node', str(probe), *item['argv'][2:]]
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=20)
                (out / f'bootstrap-{generation}.stdout.bin').write_bytes(result.stdout)
                (out / f'bootstrap-{generation}.stderr.bin').write_bytes(result.stderr)
                observed = json.loads(result.stdout) if result.returncode == 0 else None
                expected_path = case.root / f'operator-{generation:02d}.credential.json'
                passed = (result.returncode == 0 and path == str(expected_path)
                          and observed == {'probe': 'before-socket', 'path': str(expected_path),
                              'kind': 'operator', 'state': str(case.state.resolve()), 'mode': 0o600}
                          and 'A2A_LAUNCH' not in env)
                checks.append({'name': f'actual-quality-host-generation-{generation}',
                    'status': 'PASS' if passed else 'INCOMPLETE', 'command': command,
                    'credential_path': path, 'expected_path': str(expected_path), 'exit_code': result.returncode,
                    'observed': observed, 'inherited_launch_present': 'A2A_LAUNCH' in env})
        finally:
            case.close_fixture()
            # The no-socket probe exited normally. No local capability may be
            # copied into evidence or outlive this disposable fixture.
            remaining = list(case.root.glob('operator-*.credential.json'))
            checks.append({'name': 'capabilities-removed-before-archive',
                           'status': 'PASS' if not remaining else 'INCOMPLETE',
                           'remaining_paths': list(map(str, remaining))})
        fake = out / 'log-copy-probe'; fake.mkdir()

        def failed_case(argv, **kwargs):
            target = fake / 'failed'; evidence = target / 'tracer_review_copy'; evidence.mkdir(parents=True)
            (evidence / 'host-01.stderr.bin').write_bytes(b'Error: operator_credential_required\n')
            (evidence / 'host-01.stdout.bin').write_bytes(b'')
            (target / 'run.json').write_text(json.dumps({'status': 'INCOMPLETE', 'cases': [{'case': 'tracer_review_copy', 'outcome': 'harness_error'}]}) + '\n', encoding='utf-8')
            return subprocess.CompletedProcess(argv, 1, '', '')

        with patch.object(subprocess, 'run', failed_case):
            copied = boundary.run_case(ROOT, fake, 'tracer_review_copy', 'failed')
        logs = copied.get('host_diagnostics', [])
        passed = (len(logs) == 1 and Path(logs[0]['stderr']).read_bytes() == b'Error: operator_credential_required\n')
        checks.append({'name': 'failed-run-copies-host-stderr', 'status': 'PASS' if passed else 'INCOMPLETE', 'host_diagnostics': logs})
    record = {'status': 'PASS' if all(row['status'] == 'PASS' for row in checks) else 'INCOMPLETE',
              'checks': checks, 'daemon_starts': 0, 'real_model_turns': 0, 'scratch_removed': True,
              'scope': 'Actual QualityCase setup and TypeScript host; serve intercepted before socket; failure-copy probe only'}
    with (out / 'results.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
