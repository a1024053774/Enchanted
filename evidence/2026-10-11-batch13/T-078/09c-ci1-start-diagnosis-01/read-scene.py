"""只读本次 START 失败现场；只允许 pane_status/pane_output 与 SELECT。"""
from contextlib import closing
import json
from pathlib import Path
import signal
import sqlite3
import sys
import traceback

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
SOURCE = BASE.parents[2]
sys.path.insert(0, str(SOURCE / 'workbench/tests'))
from p1_output import read_complete_output
from t078_09b_i1_driver import gate


def load(path):
    return json.loads(Path(path).read_bytes())


def save(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    assert not (OUT / 'result.json').exists()
    def timeout(*_): raise TimeoutError('read_only_scene_timeout_20s')
    signal.signal(signal.SIGALRM, timeout); signal.alarm(20)
    result = {'status': 'INCOMPLETE', 'scope': 'SELECT + readonly pane_status/pane_output; no dispatch/release/key/Stop',
              'business_actions': 0, 'keys': 0, 'HTTP_requests_sent_by_reader': 0}
    try:
        ready = load(BASE / '09c-stage-a-01/readiness.json'); root = Path(ready['root'])
        p1s = {role: BASE / ('09c-c1-b1-' + role + '-p1-01') for role in ['ideation','executor']}
        inputs = {role: load(p1 / 'input.json') for role,p1 in p1s.items()}
        inp = inputs['ideation']; plan = load(root / 'protocol-plan.json')
        assert plan['root'] == str(root) and plan['roles'] == inputs
        failed = load(p1s['ideation'] / 'phases/C-I1/start-01/result.json')
        assert failed['status'] == 'INCOMPLETE' and 'initial_release_only' in failed['error']
        with closing(sqlite3.connect((root / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            db.execute('BEGIN')
            dispatches = [dict(row) for row in db.execute('SELECT * FROM dispatch_records WHERE launch=?', (inp['launch'],))]
            events = [dict(row) for row in db.execute('SELECT seq,time,type,launch,data FROM orchestration_events WHERE launch IN (?,?) ORDER BY seq', tuple(v['launch'] for v in inputs.values()))]
            inbox = [json.loads(row['data']) for row in db.execute('SELECT data FROM inbox_records')]
        for event in events: event['data'] = json.loads(event['data'])
        releases = [row for row in events if row['type'] == 'executor_action' and row['data'].get('action') == 'initial_release']
        assert len(releases) == 2 and {row['launch'] for row in releases} == {v['launch'] for v in inputs.values()}
        assert len(dispatches) == 1
        dispatch = dispatches[0]; stored = json.loads(dispatch['data'])
        relevant = [row for row in events if row['data'].get('dispatch') == dispatch['id'] or
                    (row['type'] == 'dispatch_queued' and row['data'].get('id') == dispatch['id']) or
                    row['type'] in ['turn_start_signal','permission_wait','turn_end_signal','pane_idle']]
        queued = [row for row in relevant if row['type'] == 'dispatch_queued']; assert len(queued) == 1
        actual = queued[0]['data']
        assert stored['text'] == plan['i1_prompt'].rstrip('\r\n')
        assert actual['text'] == '⟦主控 #' + str(dispatch['seq']) + '⟧\n' + stored['text']
        submits = [row for row in relevant if row['type'] == 'turn_submitted']; assert len(submits) == 1
        starts = [row for row in relevant if row['type'] == 'turn_start_signal']; assert len(starts) == 1
        waits = [row for row in relevant if row['type'] == 'permission_wait']; assert len(waits) == 1
        assert starts[0]['data']['prompt'] == actual['text']
        assert waits[0]['data']['prompt_id'] == starts[0]['data']['prompt_id']
        panes = {role: gate(root, 'pane_status', '--thread', value['thread']) for role,value in inputs.items()}
        assert panes['ideation']['state'] == 'busy' and panes['ideation']['active']['dispatch'] == dispatch['id']
        assert panes['ideation']['queued'] == [] and panes['ideation']['failed'] is None
        assert panes['executor']['state'] == 'idle' and panes['executor']['active'] is None and panes['executor']['queued'] == []
        screen = read_complete_output(lambda offset: gate(root,'pane_output','--launch',inp['launch'],'--offset',str(offset)), inp['launch'])
        with (OUT / 'current-permission-screen.bin').open('xb') as stream: stream.write(screen['raw'])
        save('current-permission-capture.json', screen['capture'])
        save('pane-status.json', panes)
        save('registered-dispatch.json', {'stored_row': dispatch, 'dispatch_event': queued[0]})
        save('relevant-events.json', {'initial_releases': releases, 'dispatch_through_permission': relevant})
        counts = {}
        for role in inputs:
            folder = root / 'roles' / role
            def lines(name):
                p = folder / name
                return [json.loads(line) for line in p.read_bytes().splitlines() if line.strip()] if p.exists() else []
            requests, responses = lines('requests.ndjson'), lines('responses.ndjson')
            counts[role] = {'request_records':len(requests), 'response_records':len(responses),
                            'HTTP_POST_files':len(list((folder/'http-exchanges').glob('*.request.bin'))),
                            'request_phases':[{k:item.get(k) for k in ['phase','message_kind','dispatch_id','error']} for item in requests]}
        assert counts['ideation']['HTTP_POST_files'] == 1 and counts['executor']['HTTP_POST_files'] == 0
        assert counts['ideation']['request_phases'] == [{'phase':'C-I1','message_kind':'tool_use','dispatch_id':dispatch['id'],'error':None}]
        stops = [entry for entry in inbox if entry.get('kind')=='stop' and 'input:'+plan['synthetic_input_id'] in entry.get('refs',[])]
        assert not stops and not Path(plan['clock_origin_file']).exists()
        assert (root/plan['target_bytes']).read_bytes() == bytes.fromhex(plan['target_baseline_hex'])
        assert not [row for row in relevant if row['type'] in ['turn_end_signal','pane_idle']]
        result.update(status='PASS', source_revision=ready['source_revision'], root=str(root),
            original_start_result=str(p1s['ideation']/'phases/C-I1/start-01/result.json'),
            registered_dispatch=dispatch['id'], global_seq=dispatch['seq'],
            event_order={kind:[row['seq'] for row in relevant if row['type']==kind] for kind in ['dispatch_queued','paste_intent','paste_written','turn_submit_intent','turn_submitted','turn_start_signal','permission_wait']},
            initial_release_events=[{'seq':row['seq'],'launch':row['launch']} for row in releases],
            current_state='ideation busy, same active dispatch, queue empty; executor idle',
            screen_bytes=len(screen['raw']), screen_complete=True, counts=counts,
            actual_stop_entries=0, clock_origin_exists=False, target_delta_hex='',
            I_budget={'used_roots':1,'used_POST':1,'remaining_roots':3,'remaining_POST':6},
            E_budget={'used_roots':0,'used_POST':0,'remaining_roots':1,'remaining_POST':1},
            continuation='observe original C-I1 permission only; never repeat START/dispatch/initialize/release',
            driver_source_changed=False, scene_rebuild_required=False)
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc())
    finally: signal.alarm(0)
    save('result.json', result)
    print(json.dumps({k:result[k] for k in ['status','registered_dispatch','global_seq','screen_bytes','error'] if k in result},ensure_ascii=False))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
