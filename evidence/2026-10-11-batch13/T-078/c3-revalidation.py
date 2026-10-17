"""Bind only the new nine-process/caffeinate rehearsal and kernel-path receipts."""
import ast
import json
from pathlib import Path
import subprocess
import tarfile

SOURCE=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
REHEARSAL=BASE/'09c-caffeinate-parity-rehearsal-02'
KERNEL=BASE/'09c-caffeinate-kernel-outside-01/result.json'
BUSINESS='7a6edbff8'
REPAIRS='''p1_simulated_actions.py t078_09b_fake_api.py t078_09b_i1_permission.py t078_09b_rehearsal_host.ts
t078_09b_rehearsal_peer.py t078_09c_driver.py t078_09c_timed_run.py t078_owner_receipt_fixture.py t078_process_tree.py
t078_raw_retention.py t078_rev2_tools_cases.py t078_topology_probe.py test_t078_09c_coordinator_chain.py
test_t078_09c_coordinator_paths.py test_t078_09c_cross_process_clock.py test_t078_09c_permission_display.py
test_t078_09c_real_chain.py test_t078_09c_recorded_entries.py test_t078_09c_timed_guards.py test_t078_a14_rehearsal.py
test_t078_api_ready_atomic.py test_t078_rev2_rehearsal.py test_t078_topology_guards.py test_t078_topology_idle.py
test_t078_topology_probe_entry.py test_t078_caffeinate_topology.py test_t078_caffeinate_kernel.py
test_t078_probe_submission.py test_t078_c3_material_paths.py test_t078_caffeinate_profiles.py
test_t078_child_reaping.py'''.split()
META=[str(BASE.relative_to(SOURCE)/name) for name in ['c3-revalidation.py','freeze-c3.py','prepare-c2-runtime.py',
    '09c-attempt-3-materials-01/i1-prompt.txt','prepare-09b-executable.py']]


def kernel_source_binding(tested):
    """The old OS probe covers these exact functions, not the new waitpid path."""
    raw_path='workbench/tests/t078_raw_retention.py'
    original=subprocess.check_output(['git','show',tested+':'+raw_path],cwd=SOURCE,text=True)
    current=(SOURCE/raw_path).read_text(encoding='utf-8')
    def parts(source):
        module=ast.parse(source);native=next(n for n in module.body if isinstance(n,ast.ClassDef) and n.name=='NativeRuntime')
        nodes=[n for n in module.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
               isinstance(n,ast.FunctionDef) and n.name in ['require','save']]
        nodes += [n for n in native.body if isinstance(n,ast.FunctionDef) and n.name in ['helper_identity','executable_path']]
        assert len([n for n in nodes if isinstance(n,ast.FunctionDef)])==4,'kernel_function_closure_required'
        return [ast.get_source_segment(source,n) for n in nodes]
    assert parts(original)==parts(current),'kernel_probe_function_source_changed'
    test_path='workbench/tests/test_t078_caffeinate_kernel.py'
    assert (SOURCE/test_path).read_bytes()==subprocess.check_output(['git','show',tested+':'+test_path],cwd=SOURCE), 'kernel_probe_source_changed'
    return {'status':'PASS','tested_revision':tested,'test':test_path,
        'exact_functions':['require','save','NativeRuntime.helper_identity','NativeRuntime.executable_path'],
        'imports_unchanged':True,'scope':'exact OS-probe function/test text; later waitpid changes covered by full rehearsal'}


def receipts():
    assert (REHEARSAL/'result.json').is_file() and KERNEL.is_file(),'C3_new_rehearsal_and_kernel_receipts_required'
    result=json.loads((REHEARSAL/'result.json').read_bytes());kernel=json.loads(KERNEL.read_bytes())
    assert result['status']=='PASS' and result['POST']=={'ideation':7,'executor':1} and result['roots']=={'ideation':4,'executor':1}
    assert 120000<result['scene_age_ms']<150000 and 120000<result['completion_age_ms']<150000
    assert result['real_model_turns']==result['vendor_CLIs']==0 and result['coordinator_execution_count']==1 and result['duplicate_refusal']=='PASS'
    assert result['cleanup']['status']=='PASS' and result['cleanup']['scratch_removed'] is True and result['cleanup']['post_stop_SQLite_reads']==0
    assert kernel['status']=='PASS' and kernel['role_CLIs']==kernel['model_turns']==0 and len(kernel['checks'])==2
    assert kernel['checks'][0]['kernel_executable']=='/usr/bin/caffeinate' and kernel['checks'][0]['expected_system_binary'] is True
    assert kernel['checks'][1]['kernel_executable']!='/usr/bin/caffeinate' and kernel['checks'][1]['expected_system_binary'] is False
    revision=result['source_revision']
    for tested in [revision,kernel['source_revision']]:
        subprocess.run(['git','merge-base','--is-ancestor',tested,'HEAD'],cwd=SOURCE,check=True)
    # Only receipt selection/freeze metadata changes after the actual run.
    # All runtime tools, product, acceptance and other producers stay exact.
    assert not subprocess.check_output(['git','diff',revision,'--','workbench','acceptance','scripts',
        *[str(BASE/name) for name in ['prepare-a14.py','prepare-rev2-owner.py','prepare-c2-runtime.py','run-09b.py','prepare-09b-executable.py']]],cwd=SOURCE),'C3_tools_changed_since_external_run'
    kernel_source_binding(kernel['source_revision'])
    with tarfile.open(REHEARSAL/'flow/retention-archive/scene.tar.gz') as tar:
        def load(name):return json.loads(tar.extractfile(name).read())
        identity=load('identity-receipts.json');snapshot=load('snapshot.json')
        records=[row for row in snapshot['records'] if row['source'].endswith('/startup-topology/helpers.json')]
        assert len(records)==1,'original_startup_topology_receipt_required'
        topology=load('files/'+records[0]['logical'])
    required={'daemon','target_shell','target_leader','ideation_shell','ideation_cli','executor_shell','executor_cli','ideation_api','executor_api'}
    assert set(identity['processes'])==required and topology['owner_process_count']==9
    assert identity['source_revision']==snapshot['source_revision']==revision,'rehearsal_archive_revision_required'
    helpers=topology['allowed_helpers'];assert len(helpers)==2 and {h['role'] for h in helpers}=={'ideation','executor'}
    for helper in helpers:
        assert helper['executable']=='/usr/bin/caffeinate' and helper['command']=='caffeinate -i -t 300'
        assert helper['ppid']==identity['processes'][helper['role']+'_cli']['pid'] and helper['pid'] not in {p['pid'] for p in identity['processes'].values()}
    duplicate=json.loads((REHEARSAL/'flow/coordinator-duplicate-refusal/result.json').read_bytes())
    assert duplicate['status']=='PASS' and all(duplicate[k]==0 for k in ['gate_event_delta','POST_delta','key_delta','result_overwrites'])
    flow=json.loads((REHEARSAL/'flow/flow-readback.json').read_bytes())
    assert flow['status']=='PASS' and flow['target_delta_hex']=='1b' and flow['no_ack'] is True and len(flow['control_events'])==3
    assert 120000<flow['independent_emergency_age_ms']<150000 and flow['independent_control_segment_seconds']>120
    for label in ['daemon','ideation_api','executor_api']:
        child=json.loads((REHEARSAL/'flow/cleanup-standard/child-waits'/(label.replace('_','-')+'.json')).read_bytes())
        assert child['status']=='REAPED' and type(child['exit_code']) is int and child['pid']==identity['processes'][label]['pid']
        assert child['creator_pid']==identity['process_graph'][label]['ppid'],'original_rehearsal_parent_required'
    waits=sorted((REHEARSAL/'flow/cleanup-standard/exit-observations').glob('wait-*'))
    assert len(waits)==4,'original_exit_wait_receipts_required'
    final=json.loads((waits[-1]/'result.json').read_bytes())
    assert final['status']=='PASS' and final['remaining']==[] and set(final['labels'])==required,'all_nine_actual_exits_required'
    for wait in waits:
        observed=json.loads((wait/'result.json').read_bytes());assert observed['status']=='PASS' and observed['remaining']==[]
        sample=json.loads((wait/f"sample-{observed['samples']:04d}.json").read_bytes())
        assert {p['label'] for p in sample['probes']}==set(observed['labels'])
        assert all(p['pid']==identity['processes'][p['label']]['pid'] and p['exit']==1 and not p['stdout'].strip() and
                   not p['stderr'].strip() for p in sample['probes']),'actual_ps_absence_required'
    return result


def validate(static,approval):
    result=receipts();revision=result['source_revision']
    expected=str(REHEARSAL/'result.json')
    assert static.get('harness_rehearsal')==approval.get('harness_rehearsal')==expected
    assert static.get('harness_profile')==approval.get('harness_profile')=='c3-caffeinate-v1'
    assert static.get('runtime_source_revision')==approval.get('runtime_source_revision')==revision
    assert static.get('harness_kernel_check')==approval.get('harness_kernel_check')==str(KERNEL),'C3_kernel_receipt_required'
    coordinator=BASE/'09c-coordinator-rehearsal-01/real-chain-outside-01/result.json'
    assert static.get('coordinator_rehearsal')==approval.get('coordinator_rehearsal')==str(coordinator),'C3_coordinator_receipt_required'
    prior=json.loads(coordinator.read_bytes())
    assert prior['status']=='PASS' and prior['POST']=={'ideation':7,'executor':1} and prior['roots']=={'ideation':4,'executor':1}
    assert 120000<prior['scene_age_ms']<150000 and prior['coordinator_execution_count']==1 and prior['duplicate_refusal']=='PASS'
    repairs=['workbench/tests/'+name for name in REPAIRS]
    changes=subprocess.check_output(['git','diff','--name-only',BUSINESS,'--','workbench','acceptance','scripts'],cwd=SOURCE,text=True).splitlines()
    assert set(changes)==set(repairs),('unexpected_C3_delta',changes)
    assert not subprocess.check_output(['git','diff',BUSINESS,'--','workbench/src','workbench/app','acceptance'],cwd=SOURCE)
    exclusions=repairs+META
    assert static.get('harness_delta_paths')==approval.get('harness_delta_paths')==exclusions
    return exclusions,{'status':'PASS','rehearsal':expected,'kernel_receipt':str(KERNEL),'coordinator_rehearsal':str(coordinator),
        'kernel_source_binding':kernel_source_binding(json.loads(KERNEL.read_bytes())['source_revision']),'revision':revision,
        'meaning':'original product regressions plus exact repaired tools, real nine-process topology/kernel-helper/archive lifecycle; no REHEARSAL bypass'}
