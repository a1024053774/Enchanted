"""Execute one preapproved 09C timed segment through existing gate/window tools."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import tarfile
import time
import traceback

import t078_09c_driver as c
from electron_client import ElectronClient
from p1_output import read_complete_output, validate_capture
from t078_09b_i1_driver import gate
from t078_09b_phase_driver import phase_events
from t078_09b_phase_registry import rows
from t078_raw_retention import read_json, save, require, NativeRuntime, check_identities

SOURCE = Path(__file__).resolve().parents[2]
TESTS = SOURCE / 'workbench/tests'


def expected_stop_command(plan, stop):
    argv = [plan['node'], str(Path(plan['source']) / 'workbench/src/gates/cli.ts'), 'stop',
            '--thread', plan['target_binding']['thread_id'], '--stop-id', stop['id']]
    return argv, shlex.join(argv)


def verify_template(plan, stage, dispatch, template, original, capture, start):
    binding = template['binding']; inp = plan['roles']['ideation']
    stop, request, _ = c.original_send(plan)
    expected_stop = {'id': stop['id'], 'created_at': stop['created_at'], 'request_id': request['request_id']}
    require(start['stop'] == expected_stop, 'timed_original_clock_stop_changed')
    argv, command = expected_stop_command(plan, stop)
    expected = {'source_revision': plan['source_revision'], 'package': plan['package'],
                'launch': inp['launch'], 'session': inp['session'], 'thread': inp['thread'],
                'dispatch': dispatch['dispatch']['id'], 'global_seq': dispatch['dispatch']['seq'],
                'prompt_id': dispatch['permission_event']['data']['prompt_id'],
                'permission_seq': dispatch['permission_event']['seq'],
                'tool_use_id': dispatch['dispatch']['tool_use']['id'], 'stop': expected_stop,
                'target': plan['target_identity'], 'command': command, 'argv': argv}
    c.validate_binding(binding)
    require(all(binding[k] == v for k, v in expected.items()), 'timed_exact_permission_binding_mismatch')
    require(dispatch['stage'] == template['stage'] == stage, 'timed_stage_mismatch')
    require(dispatch['permission_event']['data']['tool_input'] == {'command': command}, 'timed_hook_command_mismatch')
    require(dispatch['dispatch']['tool_use']['input'] == {'command': command} and
            shlex.split(command) == argv, 'timed_command_has_unapproved_arguments')
    require(template['key'] == 'Enter' and template['selected_line'] == '❯ 1. Yes' and
            template['selected_label'] == 'Yes' and template['max_writes'] == 1 and
            template['source'] == 'test-simulated-user', 'timed_one_time_Yes_required')
    validate_capture(original, capture)


class Timed:
    def __init__(self, args, output):
        self.args, self.output = args, output
        self.plan = read_json(args.plan); self.root = Path(self.plan['root'])
        self.p1 = args.ideation.resolve(); self.executor = args.executor.resolve()
        self.inp = read_json(self.p1 / 'input.json')
        self.policy = read_json(args.preapproval); self.steps = []; self.child = None; self.child_files = ExitStack()

    def check_policy(self):
        p = self.policy; plan = self.plan; ready = read_json(self.args.stage_a / 'readiness.json')
        require(Path(ready['root']).resolve()==self.root.resolve() and
                self.args.plan.resolve()==self.root/'protocol-plan.json','timed_original_root_plan_required')
        packet=Path(plan['package']);static=read_json(packet/'static-check.json')
        require(static['revision']==plan['source_revision'],'timed_original_source_revision')
        with tarfile.open(packet/'sources.tar.gz') as archive:
            require(set(archive.getnames())==set(static['source_paths']),'timed_frozen_closure_members')
            for relative in static['source_paths']:
                require(archive.extractfile(relative).read()==(SOURCE/relative).read_bytes(), 'timed_frozen_source_changed:'+relative)
        require(p['approved_by'] == 'executor' and p['approval_ref'] == self.args.signature_ref and
                bool(self.args.signature_ref.strip()), 'timed_preapproval_signature_required')
        require(p['scene'] == plan['scene'] == '09C' and p['role'] == 'ideation' and
                p['source'] == 'test-simulated-user' and p['max_Enter_per_stage'] == 1,
                'timed_preapproval_scope')
        require(p['stages'] == ['C-I2', 'C-I3'] and p['stop_binding'] == 'actual original C-I1 queued request -> Stop/relay entry only',
                'timed_preapproval_stop_rule')
        require(p['source_revision'] == plan['source_revision'] == ready['source_revision'] and
                p['package'] == plan['package'] and p['target_binding'] == plan['target_binding'] == ready['target_binding'],
                'timed_preapproval_source_target')
        require(p['launch'] == self.inp['launch'] == plan['roles']['ideation']['launch'] and
                p['session'] == self.inp['session'] and p['thread'] == self.inp['thread'], 'timed_preapproval_role')
        owner = read_json(plan['owner_file']); check_identities(owner, NativeRuntime(owner))
        require(owner['source_revision'] == plan['source_revision'] and owner['claim_binding'] == plan['target_binding'],
                'timed_original_owner_required')
        require(read_json(self.executor / 'input.json') == plan['roles']['executor'], 'timed_executor_input_changed')
        require(self.inp == plan['roles']['ideation'], 'timed_ideation_input_changed')
        require(self.args.build.is_dir(), 'timed_prebuilt_Electron_required')

    def time_check(self):
        path = Path(self.plan['clock_origin_file'])
        return c.timing(read_json(path), c.Clock()) if path.is_file() else None

    def run(self, label, argv):
        sample = self.time_check()
        timeout = 60 if sample is None else min(45, max(.1, (150000 - sample['wall_age_ms']) / 1000))
        command = list(map(str, argv)); record = {'step': label, 'argv': command, 'before': sample}
        self.steps.append(record); save(self.output / (label + '-command.json'), record)
        result = subprocess.run(command, cwd=SOURCE, capture_output=True, timeout=timeout)
        for suffix, raw in [('.stdout.bin', result.stdout), ('.stderr.bin', result.stderr)]:
            with (self.output / (label + suffix)).open('xb') as stream: stream.write(raw)
        require(result.returncode == 0, {'reason': 'timed_step_failed', 'step': label, 'exit': result.returncode})
        self.time_check()

    def phase_argv(self, stage, mode, label):
        p1 = self.executor if stage == 'C-E1' else self.p1
        folder = p1 / 'phases' / stage
        return [sys.executable, '-B', TESTS / 't078_09c_driver.py', '--plan', self.args.plan, '--stage', stage,
                '--approval', folder / 'approval.json', '--mode', mode, '--output', folder / label]

    def observe(self, stage):
        deadline = time.monotonic() + 20
        while True:
            self.time_check()
            bound = [read_json(p) for p in (self.root / 'roles/ideation').glob('bound-*.json') if read_json(p).get('phase') == stage]
            require(len(bound) <= 1, 'timed_duplicate_phase')
            if bound:
                events, _, prompt = phase_events(self.plan, self.inp, bound[0]['id'])
                waits = [e for e in events if e['type'] == 'permission_wait' and e['data'].get('prompt_id') == prompt]
                if waits: break
            require(time.monotonic() < deadline, 'timed_actual_permission_deadline')
            time.sleep(.05)
        self.run(stage + '-observe', self.phase_argv(stage, 'observe', 'dispatch-01'))
        folder = self.p1 / 'phases' / stage; dispatch = read_json(folder / 'dispatch-01/result.json')
        binding = read_json(self.p1 / 'launch-binding.json')
        label = 'c2-ideation-' + stage + '-permission-screen-01'
        self.run(stage + '-screen', [sys.executable, '-B', TESTS / 'run_t078_p1.py', '--materials', self.p1,
            '--reuse-stage-a', '--launch-label', binding['launch_label'], '--phase', 'screen', '--label', label,
            '--screen-id', 'ideation-' + stage + '-permission'])
        raw = (self.p1 / label / 'screen.bin').read_bytes(); meta = read_json(self.p1 / label / 'screen.json')
        validate_capture(raw, meta['capture'])
        require(raw == Path(dispatch['permission_screen']).read_bytes(), 'timed_full_screen_cmp_failed')
        save(self.output / (stage + '-cmp.json'), {'status': 'PASS', 'bytes': len(raw), 'capture': meta['capture'],
             'reference': dispatch['permission_screen'], 'observed': str(self.p1 / label / 'screen.bin')})
        return dispatch, raw

    def permission_argv(self, stage, label, check=False):
        folder = self.p1 / 'phases' / stage
        binding = read_json(self.p1 / 'launch-binding.json')
        argv = [sys.executable, '-B', TESTS / 't078_09b_i1_permission.py', '--materials', self.p1, '--p1', self.p1,
             '--stage', stage, '--stage-a', self.args.stage_a, '--dispatch-result', folder / 'dispatch-01/result.json',
             '--process-manifest', binding['process_manifest'], '--approval', folder / 'permission-approval-01.json',
             '--output', folder / label]
        return argv + (['--check-only'] if check else [])

    def early(self):
        stage = 'C-I2'; folder = self.p1 / 'phases' / stage
        dispatch, original = self.observe(stage)
        self.run('C-I2-prepare', [sys.executable, '-B', Path(self.plan['package']).parent / 'prepare-a14.py',
             '--mode', 'permission', '--p1', self.p1, '--result', folder / 'dispatch-01/result.json',
             '--output', folder / 'permission-approval-01.json'])
        env = {**os.environ, 'PATH': '/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin',
               'HOME': str(self.root / 'manager-home'), 'TMPDIR': str(self.root / 'tmp'),
               'A2A_OPERATOR_CREDENTIAL': str(self.root / 'operator.json'), 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
        result_dir = folder / 'execute-02'; result_dir.mkdir(exist_ok=False)
        client = ElectronClient(SOURCE, self.args.build, self.root / 'state', self.inp['task'],
                  self.root / 'electron-home', folder / 'execute-02-electron', env, launch=self.inp['launch'])
        try:
            client.wait(lambda v: v.get('launch') == self.inp['launch'] and v.get('thread') == self.inp['thread'] and
                 v.get('active_dispatch') == dispatch['dispatch']['id'] and v.get('input_enabled') is True and
                 re.search(r'^\s*❯\s+1\. Yes\s*$', v.get('terminal', ''), re.M) is not None)
            runtime = c.NativePermission(self.plan, stage, client); actual = runtime.actual()
            start = read_json(self.plan['clock_origin_file'])
            template = {'stage': stage, 'source': 'test-simulated-user', 'key': 'Enter', 'selected_line': '❯ 1. Yes',
                'selected_label': 'Yes', 'max_writes': 1, 'binding': actual['binding'], 'screen_file': dispatch['permission_screen'],
                'screen_capture': dispatch['permission_screen_capture'], 'intent_file': str(self.root / 'permission-intents' / (dispatch['dispatch']['id'] + '.json')),
                'approved_by': 'executor', 'approval_ref': self.args.signature_ref}
            verify_template(self.plan, stage, dispatch, template, original, template['screen_capture'], start)
            c.validate_permission(template, actual, original, template['screen_capture'])
            require(read_complete_output(runtime.fetch_page, self.inp['launch'])['raw'] == original, 'timed_C_I2_screen_changed')
            save(folder / 'preapproved-template.json', {'policy': self.policy, 'actual_template': template})
            approval = read_json(folder / 'permission-approval-01.json')
            require(approval['approved_by'] is None and approval['approval_ref'] is None, 'timed_C_I2_draft_already_signed')
            approval.update(approved_by='executor', approval_ref=self.args.signature_ref)
            pending = folder / 'permission-signed-pending.json'; save(pending, approval)
            # Keep the unsigned original as evidence; the check uses this signed file.
            os.link(pending, folder / 'permission-signed.json')
            argv = self.permission_argv(stage, 'permission-check-01', True)
            argv[argv.index('--approval') + 1] = folder / 'permission-signed.json'
            self.run('C-I2-check', argv)
            actual = runtime.actual(); c.validate_permission(template, actual, original, template['screen_capture'])
            require(read_complete_output(runtime.fetch_page, self.inp['launch'])['raw'] == original, 'timed_C_I2_screen_changed_before_Enter')
            require(c.timing(start, c.Clock())['wall_age_ms'] < 90000, 'timed_C_I2_early_cutoff')
            save(template['intent_file'], {'stage': stage, 'binding': template['binding'], 'signature_ref': self.args.signature_ref})
            receipt = runtime.enter(template)
            require(receipt['form'] == 'action' and receipt['data'] == '\r' and receipt['intent_count'] == receipt['written_count'] == 1 and
                    receipt['new_turn_intents'] == 0, 'timed_C_I2_control_receipt')
            save(result_dir / 'Enter.json', receipt)
            settled = c.settle_stage(self.plan, self.inp, stage, result_dir)
            save(result_dir / 'result.json', settled)
        except Exception as error:
            save(result_dir / 'result.json', {'status':'INCOMPLETE','error':repr(error),'traceback':traceback.format_exc()})
            raise
        finally: client.close()
        self.run('C-I2-collect', self.phase_argv(stage, 'collect', 'collect-01'))

    def late(self):
        dispatch, original = self.observe('C-I3'); folder = self.p1 / 'phases/C-I3'
        argv = self.phase_argv('C-I3', 'permission', 'execute-02') + ['--build', self.args.build]
        stdout = self.child_files.enter_context((self.output / 'C-I3-driver.stdout.bin').open('xb'))
        stderr = self.child_files.enter_context((self.output / 'C-I3-driver.stderr.bin').open('xb'))
        save(self.output / 'C-I3-driver-command.json', {'argv': list(map(str, argv))})
        self.child = subprocess.Popen(list(map(str, argv)), cwd=SOURCE, stdout=stdout, stderr=stderr, start_new_session=True)
        review = folder / 'execute-02-review'
        while not (review / 'template.json').is_file():
            sample = self.time_check(); require(self.child.poll() is None, 'timed_C_I3_driver_exited_before_template')
            require(sample['wall_age_ms'] < 130000, 'timed_C_I3_template_deadline'); time.sleep(.05)
        template = read_json(review / 'template.json'); raw = (review / 'screen.bin').read_bytes()
        start = read_json(self.plan['clock_origin_file'])
        verify_template(self.plan, 'C-I3', dispatch, template, raw, template['screen_capture'], start)
        current = read_complete_output(lambda offset: gate(self.root, 'pane_output', '--launch', self.inp['launch'], '--offset', str(offset)), self.inp['launch'])
        require(raw == original == current['raw'], 'timed_C_I3_original_complete_screen_cmp_failed')
        require(template['approved_by'] is None and template['approval_ref'] is None, 'timed_C_I3_template_already_signed')
        draft = {**template, 'approved_by': 'executor', 'approval_ref': self.args.signature_ref}
        save(review / 'approval-draft.json', draft)
        require({k:v for k,v in draft.items() if k not in ('approved_by','approval_ref')} ==
                {k:v for k,v in template.items() if k not in ('approved_by','approval_ref')}, 'timed_C_I3_signed_content_changed')
        pending = review / 'approved-publication.json'
        with pending.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(draft, ensure_ascii=False, indent=2) + '\n'); stream.flush(); os.fsync(stream.fileno())
        os.link(pending, review / 'approved.json')
        sample = self.time_check()
        self.child.wait(timeout=max(.1, (150000-sample['wall_age_ms'])/1000))
        require(self.child.returncode == 0, 'timed_C_I3_conditional_driver_failed')
        require(read_json(folder / 'execute-02/result.json')['status'] == 'PASS', 'timed_C_I3_result_required')

    def execute(self):
        self.check_policy()
        # All future destinations are checked before the first Enter. Their
        # owning entries still create each directory exclusively before binding it.
        for stage in ['C-I1','C-I2','C-I3','C-I4','C-E1']:
            p1 = self.executor if stage == 'C-E1' else self.p1
            require(read_json(p1/'phases'/stage/'armed-01/result.json')['status'] == 'ARMED', 'timed_all_phases_must_be_armed')
        destinations = [self.p1/'phases/C-I1/permission-check-timed-01', self.p1/'phases/C-I1/execute-02']
        for stage in ['C-I2','C-I3']:
            destinations += [self.p1/'phases'/stage/name for name in ['dispatch-01','execute-02','execute-02-review','permission-check-01']]
            destinations += [self.p1/('c2-ideation-'+stage+'-permission-screen-01')]
        destinations += [self.p1/'phases/C-I2'/name for name in ['permission-approval-01.json','permission-signed-pending.json',
            'permission-signed.json','preapproved-template.json','execute-02-electron']]
        destinations += [Path(self.plan['continued_demand_file'])]
        destinations += [self.p1/'phases/C-I2/collect-01', self.p1/'phases/C-I4/collect-01', self.executor/'phases/C-E1/collect-01']
        require(all(not p.exists() for p in destinations), 'timed_output_exists_no_Enter')
        require(not Path(self.plan['clock_origin_file']).exists(), 'timed_C_I1_already_settled_no_repeat')
        save(self.output/'preflight.json', {'status':'PASS','policy':self.policy,'future_outputs':list(map(str,destinations))})
        self.run('C-I1-check', self.permission_argv('C-I1','permission-check-timed-01',True))
        self.run('C-I1-Enter', self.permission_argv('C-I1','execute-02'))
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location('timed_demand', Path(self.plan['package']).parent/'prepare-rev2-owner.py')
        module = module_from_spec(spec); spec.loader.exec_module(module)
        module.demand(argparse.Namespace(result=self.p1/'phases/C-I1/execute-02/settlement.json',
             approval=self.p1/'phases/C-I1/approval.json', output=Path(self.plan['continued_demand_file'])))
        self.early(); self.late()
        for stage in ['C-I4','C-E1']: self.run(stage+'-collect', self.phase_argv(stage,'collect','collect-01'))
        posts = {role:len(list((self.root/'roles'/role/'http-exchanges').glob('*.request.bin'))) for role in ['ideation','executor']}
        require(posts == {'ideation':7,'executor':1}, 'timed_actual_POST_budget')
        events = rows(self.root,'orchestration_events')
        roots = {role:sum(e['type']=='turn_submitted' and e['launch']==self.plan['roles'][role]['launch'] for e in events)
                 for role in ['ideation','executor']}
        require(roots == {'ideation':4,'executor':1}, 'timed_actual_root_budget')
        sample = self.time_check()
        return {'status':'PASS','POST':posts,'roots':roots,'observed_time':sample,'signature_ref':self.args.signature_ref,
                'models':0,'cleanup':'NOT_RUN; live owner remains for raw retention and separate approved cleanup'}

    def close(self):
        if self.child is not None and self.child.poll() is None:
            # Interrupt only this runner's conditional harness process. Its
            # finally closes its Electron client; never signal a role or target.
            self.child.send_signal(signal.SIGINT); self.child.wait(timeout=10)
        self.child_files.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['plan','stage-a','ideation','executor','build','preapproval','output']:
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--signature-ref', required=True)
    args = parser.parse_args(); output = args.output.resolve()
    # This is outside the exception handler: a duplicate invocation cannot bind
    # or overwrite the original result and cannot start a process or key path.
    output.mkdir(parents=True, exist_ok=False)
    runner = None; result = {'status':'INCOMPLETE','steps':[]}
    try:
        runner = Timed(args, output); result.update(runner.execute())
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if runner is not None:
            result['steps'] = runner.steps
            try: runner.close()
            except Exception as error: result.update(status='INCOMPLETE', close_error=repr(error))
        save(output/'result.json', result)
    print(json.dumps({'status':result['status'],'output':str(output)}))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
