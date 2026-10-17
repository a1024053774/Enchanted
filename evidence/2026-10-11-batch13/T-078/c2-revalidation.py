"""Bind the reviewed 09C tool repairs to the completed real-chain rehearsal."""
import json
from pathlib import Path
import subprocess

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
REHEARSAL = BASE / '09c-coordinator-rehearsal-01/real-chain-outside-01'
REPAIR_REVISION = 'dc15dc3f0169f8689c5cded440676031cfa48bf5'
BUSINESS_REVISION = '7a6edbff87df85077b3a05d38f3cfd5654cde9c1'
REPAIRS = ['t078_09b_fake_api.py','t078_09b_i1_permission.py','t078_09b_rehearsal_host.ts',
    't078_09b_rehearsal_peer.py','t078_09c_driver.py','t078_rev2_tools_cases.py',
    'test_t078_09c_cross_process_clock.py','test_t078_09c_permission_display.py','test_t078_09c_real_chain.py',
    'test_t078_09c_recorded_entries.py','test_t078_api_ready_atomic.py','test_t078_rev2_rehearsal.py',
    't078_09c_timed_run.py','test_t078_09c_timed_guards.py',
    'test_t078_09c_coordinator_chain.py','test_t078_09c_coordinator_paths.py']
NEW_FILES = [
    str(BASE.relative_to(SOURCE)/'c2-revalidation.py'),str(BASE.relative_to(SOURCE)/'prepare-c2-runtime.py'),
    str(BASE.relative_to(SOURCE)/'freeze-c2.py'),str(BASE.relative_to(SOURCE)/'09c-attempt-2-materials-02/i1-prompt.txt')]


def validate(static, approval):
    expected = str(REHEARSAL / 'result.json')
    assert static.get('harness_rehearsal') == approval.get('harness_rehearsal') == expected, 'C2_rehearsal_receipt_required'
    assert static.get('runtime_source_revision') == approval.get('runtime_source_revision') == REPAIR_REVISION, 'C2_rehearsed_runtime_revision_required'
    result = json.loads((REHEARSAL / 'result.json').read_bytes())
    assert result['status'] == 'PASS' and result['source_revision'] == REPAIR_REVISION
    assert result['POST'] == {'ideation':7,'executor':1} and result['roots'] == {'ideation':4,'executor':1}
    assert 120000 < result['scene_age_ms'] < 150000 and result['real_model_turns'] == result['vendor_CLIs'] == 0
    assert 120000 < result['completion_age_ms'] < 150000 and result['coordinator_execution_count'] == 1 and result['duplicate_refusal'] == 'PASS'
    duplicate = json.loads((REHEARSAL/'flow/coordinator-duplicate-refusal/result.json').read_bytes())
    assert duplicate['status'] == 'PASS' and duplicate['complete_coordinator_executions'] == duplicate['refused_duplicate_invocations'] == 1
    assert duplicate['expected_exit'] == duplicate['actual_exit'] == 1 and duplicate['original_files_byte_compared'] > 0
    assert all(duplicate[name] == 0 for name in ['gate_event_delta','POST_delta','key_delta','result_overwrites'])
    assert result['cleanup']['status'] == 'PASS' and result['cleanup']['scratch_removed'] is True and result['cleanup']['post_stop_SQLite_reads'] == 0
    flow = json.loads((REHEARSAL / 'flow/flow-readback.json').read_bytes())
    assert flow['status'] == 'PASS' and flow['target_delta_hex'] == '1b' and flow['no_ack'] is True
    assert 120000 < flow['independent_emergency_age_ms'] < 150000 and flow['independent_control_segment_seconds'] > 120
    assert len(flow['permissions']) == len(flow['control_events']) == 3
    origin = json.loads((REHEARSAL / 'flow/clock-origin.json').read_bytes())
    assert origin['observer_pid'] and origin['mono_ms'] > 0 and origin['stop']['id'] == flow['stop']['id']
    # Existing repair code must still be exactly what the completed rehearsal ran.
    repairs = ['workbench/tests/' + name for name in REPAIRS]
    for path in repairs:
        assert (SOURCE/path).read_bytes() == subprocess.check_output(['git','show',REPAIR_REVISION+':'+path],cwd=SOURCE), ('rehearsed repair changed',path)
    changed = subprocess.check_output(['git','diff','--name-only',BUSINESS_REVISION,'--','workbench','acceptance','scripts'],cwd=SOURCE,text=True).splitlines()
    assert set(changed) == set(repairs), ('unexpected C2 source delta',changed)
    assert not subprocess.check_output(['git','diff',REPAIR_REVISION,'--','workbench','acceptance','scripts'],cwd=SOURCE), 'C2_runtime_differs_from_completed_coordinator_rehearsal'
    exclusions = repairs + NEW_FILES + [str(BASE.relative_to(SOURCE)/'prepare-09b-executable.py')]
    assert static.get('harness_delta_paths') == approval.get('harness_delta_paths') == exclusions
    return exclusions, {'status':'PASS','rehearsal':expected,'revision':REPAIR_REVISION,
        'business_revision':BUSINESS_REVISION,'runtime_source_revision':REPAIR_REVISION,
        'new_timed_coordinator':'real CLI rehearsal PASS; execution 1; duplicate refused without effects',
        'meaning':'four original product regressions + exact dc15 runtime + completed real coordinator chain; metadata-only binding update'}
