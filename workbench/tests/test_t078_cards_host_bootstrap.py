"""Probe the actual cards host environment and credential API without a daemon.

Failure modes: no explicit credential; relative/foreign or reused credential;
inherited worker identity; credential creation/readback uses the wrong state.
Host creation is intercepted before spawn. Git baseline setup remains real.
This does not prove socket readiness, managed dispatch or card acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

import test_daemon_gates_e2e as daemon_cards
import test_task_cards_e2e as cards


class CapturedHost(Exception):
    pass


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(exist_ok=False)
    fixtures = Path(tempfile.mkdtemp(prefix='t78cb-', dir='/tmp')).resolve()
    cards.ARTIFACT_ROOT = fixtures
    checks = []
    original = subprocess.Popen
    paths = []
    # Use the same production bootstrap call as daemon_acceptance_host.ts.
    js = """import {mkdirSync,statSync} from 'node:fs';
import {createOperatorCredential,readOperatorCredential} from './workbench/src/credentials.ts';
const state=process.argv[1];mkdirSync(state,{recursive:true});
const path=createOperatorCredential(state),value=readOperatorCredential(state);
console.log(JSON.stringify({path,state:value.state,kind:value.kind,mode:statSync(path).mode&0o777}));
"""
    for index in range(2):
        captured = {}

        def spawn(argv, *values, **kwargs):
            if len(argv) > 1 and Path(argv[1]).name == 'daemon_acceptance_host.ts':
                captured.update(argv=list(map(str, argv)), env=dict(kwargs['env']))
                raise CapturedHost()
            return original(argv, *values, **kwargs)

        case = daemon_cards.DaemonCards('test_card_validation_versions_and_claim_snapshot')
        # A foreign inherited path must not become this fixture's capability.
        with patch.dict(os.environ, {'A2A_OPERATOR_CREDENTIAL': '/tmp/foreign-bootstrap-credential',
                                     'A2A_LAUNCH': 'foreign-launch'}):
            try:
                with patch.object(subprocess, 'Popen', spawn):
                    case.setUp()
            except CapturedHost:
                pass
            finally:
                for name in ('host_stdout', 'host_stderr'):
                    stream = getattr(case, name, None)
                    if stream is not None:
                        stream.close()
        if not captured:
            raise RuntimeError('Actual fixture did not attempt to start its host.')
        env = captured.pop('env')
        credential = env.get('A2A_OPERATOR_CREDENTIAL')
        captured.update(credential_path=credential,
                        inherited_launch_present='A2A_LAUNCH' in env,
                        fixture=str(case.root), state=str(case.state),
                        oracle_paths=case.card['oracle_paths'])
        argv = ['node', '--input-type=module', '-e', js, str(case.state)]
        result = subprocess.run(argv, cwd=cards.ROOT, env=env, capture_output=True, timeout=30)
        (args.output / f'{index}.stdout.bin').write_bytes(result.stdout)
        (args.output / f'{index}.stderr.bin').write_bytes(result.stderr)
        observed = json.loads(result.stdout) if result.returncode == 0 else None
        path = Path(credential) if credential else None
        passed = (result.returncode == 0 and path is not None and path.is_absolute()
                  and path.parent == case.root.resolve() and str(path) not in paths
                  and 'A2A_LAUNCH' not in env and observed['state'] == str(case.state.resolve())
                  and observed['kind'] == 'operator' and observed['mode'] == 0o600)
        if path is not None:
            paths.append(str(path))
        checks.append({'name': f'actual-card-host-bootstrap-{index}', 'status': 'PASS' if passed else 'INCOMPLETE',
                       'captured': captured, 'argv': argv, 'exit_code': result.returncode, 'observed': observed})
        # Remove only the newly created local test capability after readback.
        if observed and path is not None and path.parent == case.root.resolve():
            path.unlink()
    record = {'status': 'PASS' if all(c['status'] == 'PASS' for c in checks) else 'INCOMPLETE',
              'checks': checks, 'fixture_root': str(fixtures), 'commands': cards.COMMANDS,
              'scope': 'Actual DaemonCards setUp environment and production credential API; host spawn intercepted; no socket/PTY/vendor/model',
              'real_model_turns': 0, 'daemon_starts': 0}
    with (args.output / 'results.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'checks': len(checks)}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
