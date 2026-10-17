"""Write unsigned closeout commands; retain all original process bindings."""
import json
from pathlib import Path
import shlex

SOURCE = Path(__file__).resolve().parents[4]
BASE = SOURCE / 'evidence/2026-10-11-batch13/T-078'
DIAG = Path(__file__).resolve().parent
OUT = BASE / '09c-attempt-2-closeout-materials-01'
ROOT = '/private/tmp/t078-2-09c-run-iznfrv18'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    original_path = BASE / '09c-attempt-2-materials-02/owner.json'
    original = json.loads(original_path.read_bytes())
    assert original['root'] == ROOT
    expected = {'daemon': 93964, 'target_shell': 94061, 'target_leader': 94063,
                'ideation_api': 93961, 'executor_api': 93962, 'ideation_shell': 94466,
                'ideation_cli': 94467, 'executor_shell': 95221, 'executor_cli': 95222}
    assert {k: v['pid'] for k, v in original['processes'].items()} == expected
    assert original['scene'] == '09C'
    assert original['source_revision'] == '1dfa09207b34c7ccadfe81cb92a46338fa619526'
    for path in [SOURCE / 'workbench/tests/t078_raw_retention.py', DIAG / 'probe-topology.py',
                 BASE / '09c-c2-preparation-01/timed-01', DIAG / 'forensic-originals']:
        assert path.exists(), path
    # Only the evidence input list changes. Do not re-probe/adopt identities,
    # graph nodes, target, launch, source, or original receipt locations.
    added = [BASE / '09c-c2-preparation-01/timed-01', DIAG / 'forensic-originals',
             DIAG / 'current-topology-01']
    owner = {**original, 'evidence_trees': original['evidence_trees'] + list(map(str, added))}
    assert {k: v for k, v in owner.items() if k != 'evidence_trees'} == {
        k: v for k, v in original.items() if k != 'evidence_trees'}
    OUT.mkdir(exist_ok=False)
    save(OUT / 'capture-owner.json', owner)
    archive = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-attempt-2-raw-01/scene.tar.gz')
    staging = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-078/09c-attempt-2-capture-01')
    readback = BASE / '09c-attempt-2-raw-readback-01'
    approval = {key: owner[key] for key in ['root', 'scene', 'source_revision', 'target_binding', 'processes']}
    approval.update(approved_by=None, approval_ref=None, archive=str(archive), retain_failed_scene=True)
    save(OUT / 'cleanup-approval.json', approval)
    tool = SOURCE / 'workbench/tests/t078_raw_retention.py'
    def command(name, argv, preamble=''):
        with (OUT / name).open('x', encoding='utf-8') as stream:
            stream.write('# 待主控逐步审批；本轮未运行。拓扑未知/不符时保持 BLOCKED。\n')
            stream.write(preamble + shlex.join(list(map(str, argv))) + '\n')
    command('00-PROBE-COMMAND.txt', ['python3', '-B', DIAG / 'probe-topology.py', '--output', DIAG / 'current-topology-01'])
    common = ['python3', '-B', tool, '--owner', OUT / 'capture-owner.json', '--archive', archive]
    command('01-DRY-RUN-COMMAND.txt', common + ['--mode', 'finish', '--approval', OUT / 'cleanup-approval.json',
            '--output', BASE / '09c-attempt-2-cleanup-01-dry-run', '--dry-run'])
    command('02-CAPTURE-COMMAND.txt', common + ['--mode', 'capture', '--output', staging])
    command('03-TAR-READBACK-COMMAND.txt', ['python3', '-B', tool, '--mode', 'readback', '--archive', archive, '--output', readback])
    precheck = f'''set -e
python3 -B - <<'PY'
import json
from pathlib import Path
base=Path({str(BASE)!r})
approval=json.loads((base/'09c-attempt-2-closeout-materials-01/cleanup-approval.json').read_bytes())
review=json.loads((base/'09c-attempt-2-raw-readback-01/failed-scene-review.json').read_bytes())
counts=json.loads((base/'09c-attempt-2-raw-readback-01/readback.json').read_bytes())
assert review['status']=='PASS' and review['scene_status']=='INCOMPLETE'
assert review['archive']==counts['archive']==approval['archive']=={str(archive)!r}
assert review['root']==approval['root']=={ROOT!r}
assert review['source_revision']==approval['source_revision']=={owner['source_revision']!r}
assert review['approved_by']==counts['approved_by']=='executor' and review['approval_ref'] and counts['approval_ref']
assert review['counts']==counts['counts']
assert review['stop_id']=='bfa23030-9da9-413f-87fc-e7cb81317987'
assert review['created_at']=='2026-10-17T01:06:15.258Z'
assert review['original_request_id']=='95058fd0-1e9d-4028-b1c1-f45845dd3584'
assert review['no_ack'] is True and review['C_I2_Enter_count']==0 and review['target_delta_hex']==''
PY
'''
    command('06-FINISH-COMMAND.txt', common + ['--mode', 'finish', '--approval', OUT / 'cleanup-approval.json',
            '--capture-result', staging / 'capture-result.json', '--independent-readback', readback / 'readback.json',
            '--output', BASE / '09c-attempt-2-cleanup-01'], precheck)
    pointer_script = f'''# 主控审阅并签独立读回后运行；不复制HTTP/hook正文进Git。
python3 -B - <<'PY'
import json
from pathlib import Path
archive=Path({str(archive)!r});out=Path({str(OUT)!r})
bundle=json.loads((archive.parent/'bundle.archive.json').read_bytes())
assert bundle['status']==bundle['byte_readback']=='PASS'
assert bundle['root']=={ROOT!r} and bundle['source_revision']=={owner['source_revision']!r}
with (out/'bundle.archive.json').open('xb') as stream:stream.write((archive.parent/'bundle.archive.json').read_bytes())
with (out/'raw-pointers.archive.json').open('x',encoding='utf-8') as stream:
    stream.write(json.dumps({{'archive':str(archive),'pointers_directory':str(archive.parent/'pointers'),'member_prefix':'files/','scene_status':'INCOMPLETE'}},ensure_ascii=False,indent=2)+'\\n')
PY
'''
    with (OUT / '05-SAVE-MANIFEST-COMMAND.txt').open('x', encoding='utf-8') as stream:
        stream.write(pointer_script)
    save(OUT / 'failed-scene-review-template.json', {
        'status': 'INCOMPLETE', 'scene_status': 'INCOMPLETE', 'approved_by': None, 'approval_ref': None,
        'archive': str(archive), 'root': ROOT, 'source_revision': owner['source_revision'],
        'counts': None, 'stop_id': 'bfa23030-9da9-413f-87fc-e7cb81317987',
        'created_at': '2026-10-17T01:06:15.258Z',
        'original_request_id': '95058fd0-1e9d-4028-b1c1-f45845dd3584',
        'no_ack': None, 'C_I2_Enter_count': None, 'target_delta_hex': None,
        'scope': '填写者从tar原件独立核对；所有null必须按事实填写；此草稿不是PASS或签名'})
    save(DIAG / 'closeout-generation.json', {'status': 'PASS', 'kind': 'file generation only',
        'output': str(OUT), 'original_owner_unchanged': True, 'original_process_bindings_unchanged': True,
        'new_evidence_trees': list(map(str, added)), 'future_inputs': [str(added[-1]), str(staging), str(readback)],
        'scene_actions': 0, 'cleanup_execution': 'INCOMPLETE; classification/topology gate unresolved'})
    print(json.dumps({'status': 'PASS', 'output': str(OUT), 'scene_actions': 0}))


if __name__ == '__main__': main()
