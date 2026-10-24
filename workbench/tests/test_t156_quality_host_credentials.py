"""Check the shared QualityCase's operator credentials before the socket boundary.

Migrated from test_t078_quality_host_bootstrap.py (T-156-2). The independent
expectations are two fixture-owned paths, kind=operator, this fixture's resolved
state, exact 0600, no inherited A2A_LAUNCH, and removal by close_fixture.
Failure modes include absent creation, foreign/reused paths, wrong kind/state/
mode, unreadable credentials, inherited launch identity, and incomplete cleanup.
The real setup and TypeScript host run; only daemon.serve is replaced before
socket/PTY creation. This does not prove daemon or native CLI behavior.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import test_quality_chain_e2e as quality

ROOT = Path(__file__).resolve().parents[2]


class CapturedHost(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(exist_ok=False)
    checks = []

    def check(name, expected, actual):
        checks.append({'name': name, 'status': 'PASS' if actual == expected else 'INCOMPLETE',
                       'expected': expected, 'actual': actual})

    # Report only non-secret metadata, before the real reader can reject a bad
    # credential. This distinguishes kind/state/mode failures from missing files.
    probe = out / 'host-probe.mjs'
    probe.write_text('''import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
const [source,state,control,ready]=process.argv.slice(2);
const credentialURL=pathToFileURL(join(source,'workbench/src/credentials.ts')).href;
const daemonURL=pathToFileURL(join(source,'workbench/src/daemon.ts')).href;
registerHooks({load(url,context,next){
 if(url!==daemonURL)return next(url,context);
 return {format:'module',shortCircuit:true,source:`
  import {readOperatorCredential} from ${JSON.stringify(credentialURL)};
  import {existsSync,readFileSync,statSync} from 'node:fs';
  export async function serve(root){
   const path=process.env.A2A_OPERATOR_CREDENTIAL,exists=!!path&&existsSync(path);
   const value=exists?JSON.parse(readFileSync(path,'utf8')):null;
   console.log(JSON.stringify({probe:'before-socket',path:path??null,exists,
    kind:value?.kind??null,state:value?.state??null,mode:exists?(statSync(path).mode&0o777):null}));
   const credential=readOperatorCredential(root);
   console.log(JSON.stringify({probe:'credential-readable',readable:!!credential}));
  }`};
}});
process.argv=[process.execPath,join(source,'workbench/tests/quality_chain_host.ts'),source,state,control,ready];
await import(pathToFileURL(process.argv[1]).href);
''', encoding='utf-8')
    hosts = []
    with tempfile.TemporaryDirectory(prefix='t156-quality-credentials-', dir='/private/tmp') as temporary:
        fixtures = Path(temporary).resolve()
        (fixtures / 'cases').mkdir()
        quality.SOURCE, quality.OUT = ROOT, out
        quality.base.ARTIFACT_ROOT = fixtures / 'cases'
        case = quality.QualityCase('credentials-probe')
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
                item = captured[-1]
                env = item['env']
                command = ['node', str(probe), *item['argv'][2:]]
                result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=20)
                (out / f'bootstrap-{generation}.stdout.bin').write_bytes(result.stdout)
                (out / f'bootstrap-{generation}.stderr.bin').write_bytes(result.stderr)
                observations = [json.loads(line) for line in result.stdout.splitlines()]
                metadata = next((row for row in observations if row.get('probe') == 'before-socket'), {})
                readable = {'probe': 'credential-readable', 'readable': True} in observations
                hosts.append({'generation': generation, 'command': command, 'exit_code': result.returncode,
                              'observations': observations})
                prefix = f'generation-{generation}'
                expected_path = str(case.root / f'operator-{generation:02d}.credential.json')
                check(prefix + '-spawn-path', expected_path, env.get('A2A_OPERATOR_CREDENTIAL'))
                check(prefix + '-host-path', expected_path, metadata.get('path'))
                check(prefix + '-created', True, metadata.get('exists'))
                check(prefix + '-kind', 'operator', metadata.get('kind'))
                check(prefix + '-state', str(case.state.resolve()), metadata.get('state'))
                check(prefix + '-mode', 0o600, metadata.get('mode'))
                check(prefix + '-readable', True, result.returncode == 0 and readable)
                check(prefix + '-launch-filtered', False, 'A2A_LAUNCH' in env)
        finally:
            cleanup_failures = case.close_fixture()
            remaining = list(case.root.glob('operator-*.credential.json'))
            check('cleanup-failures', [], cleanup_failures)
            check('capabilities-removed-before-archive', [], list(map(str, remaining)))
            # TemporaryDirectory removes only this disposable fixture, after
            # metadata and cleanup failures have been recorded without tokens.
    record = {'status': 'PASS' if all(row['status'] == 'PASS' for row in checks) else 'INCOMPLETE',
              'checks': checks, 'hosts': hosts, 'daemon_starts': 0, 'real_model_turns': 0,
              'scratch_removed': not fixtures.exists(),
              'scope': 'Actual QualityCase setup and TypeScript host; serve intercepted before socket'}
    with (out / 'results.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
