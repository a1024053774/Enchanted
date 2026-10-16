"""Reconstruct the T-082 launch-policy red on the unchanged starting gate.

The selected product source owns CLI/daemon/gates/Panes. The existing controlled
host replaces only PTY/process/native observations. No provider executes. Each
case must reach a released, busy reviewer before the new refusal assertion runs.
This is startup-policy evidence, not real sandbox/network enforcement evidence.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import traceback

import test_quality_chain_e2e as chain
import test_task_cards_e2e as base
from test_quality_chain_e2e import ContractFailure, HarnessFailure, save
from test_quality_tracer_e2e import Tracer


START = '451be8462c85fd08b997cb85453188a8e5751c9d'
CASES = ('wrong-workspace', 'network-enabled', 'tmp-writable')


class ParentLaunch(Tracer):
    def configure_host(self, config):
        config['code_revision'] = START

    def observe_parent(self):
        _, candidate = self.good_submission()
        reply = self.gate('verify', '--attempt', self.a['attempt_id'])
        save(self.evidence / 'verify-raw.json', reply)
        if not reply['ok'] or reply['task']['state'] != 'reviewing':
            raise HarnessFailure('Parent did not start review; this is not the required business red.')
        review = reply['task']['review']
        pane = self.gate('pane_status', '--thread', review['thread_id'], task=False)
        launch = next(json.loads(row['data']) for row in self.rows('launch_records')
                      if row['id'] == pane['launch'])
        controlled = json.loads((self.control / (launch['id'] + '.json')).read_text(encoding='utf-8'))
        native_meta = json.loads(Path(controlled['log']).read_text(encoding='utf-8').splitlines()[0])
        argv = launch['argv']
        common = (launch['role'] == 'reviewer' and launch['code_revision'] == START
                  and launch['sandbox'] == 'read-only'
                  and argv[argv.index('--sandbox') + 1] == 'read-only'
                  and argv[argv.index('-C') + 1] == review['workspace']
                  and launch['worktree'] == review['workspace']
                  and controlled['argv'] == launch['shell_argv']
                  and native_meta['payload']['cwd'] == review['workspace']
                  and 'candidate_workspace' not in review)
        violation = {
            'wrong-workspace': common,
            'network-enabled': common and 'sandbox_workspace_write.network_access=true' in argv
                               and 'sandbox_workspace_write.network_access=false' not in argv,
            'tmp-writable': common and 'sandbox_workspace_write.exclude_slash_tmp=false' in argv,
        }[self.case]
        if not violation:
            raise HarnessFailure('Requested launch facts were not materialized: ' + json.dumps(launch))
        release = self.gate('pane_release', '--thread', review['thread_id'],
                            '--reason', 'controlled starting-revision boundary proof', task=False)
        if not release['ok']:
            raise HarnessFailure('Parent reviewer prompt release failed.')
        busy = self.wait_for(lambda: self.gate('pane_status', '--thread', review['thread_id'], task=False),
                             lambda p: p['state'] == 'busy' and p['turn'] == 'fixture-turn-1')
        started = [e for e in self.events() if e['type'] == 'review_started']
        if len(started) != 1 or busy.get('failed') or busy.get('stopped'):
            raise HarnessFailure('Parent reviewer did not reach a healthy controlled turn.')
        save(self.evidence / 'parent-start-readback.json', {
            'starting_revision': START, 'case': self.case, 'candidate': candidate,
            'verify': reply, 'launch': launch, 'controlled_spawn': controlled, 'native_meta': native_meta,
            'release': release, 'busy': busy, 'review_started': started,
            'real_codex_turns': 0, 'native_records_are_synthetic': True,
            'limitation': 'Parent sandbox remains read-only. Explicit network/tmp argv values are accepted at startup; no real egress or tmp writability is asserted.',
        })
        # Same requirement and failure id as the candidate refusal test. Run
        # only after fixture/launch/release observations are complete.
        self.check('T082-LAUNCH-REFUSED', not reply['ok'] and reply.get('error') == 'review_launch_boundary',
                   'reviewer launch outside the approved boundary is rejected by the gate', reply)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fixture-root', type=Path, required=True)
    parser.add_argument('--case', choices=CASES, required=True)
    args = parser.parse_args()
    source, out, fixture = args.source.resolve(), args.output.resolve(), args.fixture_root.resolve()
    if Path('/Volumes/WD-Elements') not in fixture.parents:
        parser.error('Controlled fixtures must be on the approved external disk.')
    fixture.mkdir(exist_ok=False)
    out.mkdir(parents=True, exist_ok=False)
    chain.SOURCE, chain.OUT, chain.DIALECT = source, out, 'current'
    base.GATE, base.ARTIFACT_ROOT = source / 'workbench/src/gates/cli.ts', fixture
    case = ParentLaunch(args.case)
    row = {'case': args.case, 'outcome': 'harness_error', 'assertions': case.assertions}
    request_dirs = []
    cleanup_failures = []
    try:
        case.setUp()
        case.observe_parent()
        row['outcome'] = 'passed'
    except ContractFailure as error:
        row.update(outcome='contract_failure', failure_id=str(error), traceback=traceback.format_exc())
    except Exception as error:
        row.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            if getattr(case, 'state', Path('/nonexistent')).joinpath('state.sqlite3').is_file():
                for item in case.rows('launch_records'):
                    launch = json.loads(item['data'])
                    path = Path(launch['request_dir']).resolve()
                    if (path.parent != Path('/private/tmp') or not path.name.startswith('a2a-requests-')
                            or launch['env']['A2A_STATE'] != str(case.state)):
                        raise HarnessFailure('Unexpected owned request directory.')
                    request_dirs.append(path)
        except Exception as error:
            cleanup_failures.append({'phase': 'request-directory-readback', 'error': repr(error)})
        try:
            cleanup_failures.extend(case.close_fixture())
            if not cleanup_failures:
                for path in request_dirs:
                    shutil.rmtree(path)
                row['request_dirs_removed'] = [str(p) for p in request_dirs]
                row['request_dirs_remaining'] = [str(p) for p in request_dirs if p.exists()]
                if row['request_dirs_remaining']:
                    raise HarnessFailure('Owned request directory remains after cleanup.')
        except Exception as error:
            cleanup_failures.append({'phase': 'close', 'error': repr(error), 'traceback': traceback.format_exc()})
        row['cleanup_failures'] = cleanup_failures
        row.update(commands=case.commands, fixture=str(getattr(case, 'root', fixture)))
        if case.evidence.exists():
            save(case.evidence / 'case.json', row)
        record = {'status': 'PASS' if row['outcome'] == 'passed' and not row['cleanup_failures'] else 'INCOMPLETE',
                  'command': sys.argv, 'source': str(source), 'starting_revision': START,
                  'artifact_root': str(fixture), 'real_codex_turns': 0, 'cases': [row]}
        save(out / 'run.json', record)
    print(json.dumps({'outcome': row['outcome'], 'failure_id': row.get('failure_id'),
                      'cleanup_failures': row['cleanup_failures'], 'real_codex_turns': 0}), flush=True)
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
