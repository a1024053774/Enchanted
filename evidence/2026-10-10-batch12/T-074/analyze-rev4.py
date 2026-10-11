#!/usr/bin/env python3
"""Check the rev-4 contract against frozen native records and raw writes."""
import collections
import datetime as dt
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent

def rows(path):return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
def time(value):return dt.datetime.fromisoformat(value.replace('Z','+00:00'))
def permitted(first_write,submission,stop=None,release=None):
    """Decision 04: an earlier submission blocks B until a later Stop or explicit release."""
    return ((stop is not None and time(submission)<time(stop)<=time(first_write))
            or (release is not None and time(submission)<time(release)<=time(first_write)))

def native(directory,cli):
    if cli=='claude':return rows(directory/'native-transcript-final.jsonl')
    return [r for f in (directory/'native-rollouts').glob('*.jsonl') for r in rows(f)]

def messages(records,cli):
    found=[]
    for r in records:
        if cli=='codex':
            p=r.get('payload',{});meta=p.get('internal_chat_message_metadata_passthrough',{})
            if r['type']=='response_item' and p.get('role')=='user' and 'user.text' in meta.get('content_item_kinds',[]):
                found.append(dict(text=''.join(x['text'] for x in p['content'] if x['type']=='input_text'),native_id=meta['turn_id']))
        elif r.get('type')=='user' and isinstance(r['message']['content'],str) and not r.get('isMeta'):
            found.append(dict(text=r['message']['content'],native_id=r['promptId']))
    return found

prior=json.loads((BASE/'analysis-rev3.json').read_text())
red=[]
for case in prior['races']:
    if case['case']=='before_start':
        accepted=permitted(case['b_first_written_at'],case['a_submitted_at'])
        assert accepted is False
        red.append(dict(label=case['label'],old_b_written=case['b_written'],rev4_contract_accepts=accepted))
assert len(red)==2
sessions=[];all_cases=[]
all_r7=rows(BASE/'r7-injections.jsonl')
rev4=[r for r in all_r7 if r.get('ready_rev')==4]
user_inputs=rows(BASE/'rev4-user-inputs.jsonl')
assert not (BASE/'rev4-stop.json').exists()
for cli in ('codex','claude'):
    label='rev4-'+cli;directory=BASE/label
    manifest=json.loads((directory/'launch.json').read_text())
    records=native(directory,cli);actual=messages(records,cli)
    registrations=rows(directory/'registrations.jsonl');writes=rows(directory/'writes.jsonl')
    gates=rows(directory/'gate-events.jsonl');hooks=rows(directory/'turn-hooks.jsonl')
    case_events=rows(directory/'case-events.jsonl');actions=rows(directory/'user-actions.jsonl')
    observations=[r for r in rev4+user_inputs if r['label']==label]
    assert len(registrations)==18 and len(observations)==18
    assert not (directory/'violations.jsonl').exists()
    for item in registrations:
        obs=next(r for r in observations if r['id']==item['id'])
        exact=[r for r in actual if r['text']==item['registered_text']]
        assert len(exact)==1 and obs['outcome']=='ok' and obs['observed_text']==item['registered_text']
        parts=[w for w in writes if w.get('kind')=='message' and w['id']==item['id']]
        assert len(parts)==2 and [w['part'] for w in parts]==[1,2]
        assert all(w['source']==item['source'] for w in parts)
        assert parts[0]['bytes']=='\x1b[200~'+item['registered_text']+'\x1b[201~' and parts[1]['bytes']=='\r'
        assert time(item['registered_at'])<=time(parts[0]['written_at'])
        assert (time(parts[1]['written_at'])-time(parts[0]['written_at'])).total_seconds()>=.3
        busy=[g for g in gates if g['kind']=='busy' and g.get('item_id')==item['id']]
        assert len(busy)==1 and busy[0]['busy_at']==parts[1]['written_at']
        stop=[g for g in gates if g['kind']=='stop-matched' and g.get('item_id')==item['id']]
        interrupted=item['state']=='gated_after_esc' and item['role']=='A'
        assert len(stop)==(0 if interrupted else 1)
        if stop:
            key='turn_id' if cli=='codex' else 'prompt_id'
            assert stop[0]['event']['payload'][key]==exact[0]['native_id']
            assert time(stop[0]['event']['received_at'])>time(busy[0]['busy_at'])
        if item['source']=='inject' and parts[0]['gate_state']=='busy':
            action=[a for a in actions if a['at']==parts[0]['release_action']]
            assert len(action)==1 and action[0]['queued_id']==item['id'] and action[0]['simulated_by_probe']
        elif item['source']=='inject':assert parts[0]['gate_state']=='idle'
    stops=[h for h in hooks if h['payload']['hook_event_name']=='Stop']
    matched=[g for g in gates if g['kind']=='stop-matched']
    assert len(stops)==len(matched)==16
    assert all(sum(m['event']==h for m in matched)==1 for h in stops)
    for case_id in sorted({r['case_id'] for r in registrations if r['case_id'] and not r['case_id'].startswith('idle-')}):
        a=next(r for r in observations if r['case_id']==case_id and r['role']=='A')
        b=next(r for r in observations if r['case_id']==case_id and r['role']=='B')
        pair=next(c['pair'] for c in case_events if c['case_id']==case_id and c['stage']=='pair-returned')
        assert pair['b_phase']=='queued' and pair['gate']['gate_state']=='busy'
        assert b['queued_at'] and b['queued_ms']>0
        assert b['queued_ms']==round((time(b['first_written_at'])-time(b['queued_at'])).total_seconds()*1000)
        stop=next((g['event']['received_at'] for g in gates if g['kind']=='stop-matched' and g.get('item_id')==a['id']),None)
        assert permitted(b['first_written_at'],a['submitted_at'],stop,b['release_action'])
        result=dict(cli=cli,case_id=case_id,state=b['state'],a_source=a['source'],a_busy_at=a['submitted_at'],
                    stop_received_at=stop,b_registered_at=b['registered_at'],b_first_written_at=b['first_written_at'],
                    b_submitted_at=b['submitted_at'],queued_ms=b['queued_ms'],gate_state_at_write=b['gate_state'],
                    release_action=b['release_action'],native_outcome=b['outcome'])
        if b['state']=='gated_user_submit':assert a['source']=='user_sim'
        if b['state']=='gated_after_esc':
            hold=next(c for c in case_events if c['case_id']==case_id and c['stage']=='after-30s-hold')
            assert hold['hold_seconds']>=30 and hold['status']['gate_state']=='busy' and not hold['b']['written'] and not hold['marker_exists']
            assert time(b['release_action'])>time(hold['at'])
            marker=str(Path(manifest['fixture'])/f'rev4-{case_id}.txt')
            if cli=='codex':
                a_native=next(m['native_id'] for m in actual if m['text']==a['registered_text'])
                closes=[r for r in records if r['type']=='event_msg' and r['payload']['type']=='turn_aborted' and r['payload']['turn_id']==a_native]
                assert len(closes)==1 and time(closes[0]['timestamp'])<time(b['release_action'])
            else:
                calls=[c for r in records if r.get('type')=='assistant' for c in r['message']['content'] if c.get('type')=='tool_use' and marker in json.dumps(c.get('input',{}))]
                assert len(calls)==1
                results=[c for r in records if r.get('type')=='user' and isinstance(r['message']['content'],list) for c in r['message']['content'] if c.get('type')=='tool_result' and c.get('tool_use_id')==calls[0]['id']]
                assert len(results)==1 and results[0]['is_error'] is True
            result['hold_seconds']=hold['hold_seconds'];result['marker_exists']=False
        all_cases.append(result)
    assert sum(r['state']=='gated_idle' and r['role']=='B' for r in registrations)==3
    assert collections.Counter(c['state'] for c in all_cases if c['cli']==cli)=={'gated_race':3,'gated_user_submit':2,'gated_after_esc':2}
    if cli=='codex':
        turns=[r['payload']['turn_id'] for r in records if r['type']=='event_msg' and r['payload']['type']=='task_started']
        models=sorted({r['payload']['model'] for r in records if r['type']=='turn_context'})
        assert models==['gpt-6-astra']
        usage=[r['payload']['info']['total_token_usage'] for r in records if r['type']=='event_msg' and r['payload']['type']=='token_count'][-1]
        cleanup=json.loads((directory/'cleanup.json').read_text());assert cleanup['entire_created_root_removed']
    else:
        turns=sorted({r['promptId'] for r in records if r.get('type')=='user' and r.get('promptId')})
        responses={r['message']['id']:r['message'] for r in records if r.get('type')=='assistant'}
        models=sorted({r['model'] for r in responses.values()});assert models==['claude-haiku-5-5']
        usage=[dict(id=k,model=r['model'],usage=r.get('usage')) for k,r in responses.items()]
        cleanup=json.loads((directory/'archive-final.json').read_text());assert cleanup['owned_processes_present']==[]
    assert len(set(turns))==18
    sessions.append(dict(label=label,cli=cli,native_turns=len(set(turns)),models=models,Stop_events=len(stops),
                         actual_injections=sum(r['source']=='inject' for r in registrations),
                         simulated_user_messages=sum(r['source']=='user_sim' for r in registrations),
                         release_actions=len(actions),all_release_actions_simulated=all(a['simulated_by_probe'] for a in actions),usage=usage))
assert 32+next(s['native_turns'] for s in sessions if s['cli']=='codex')<=55
assert 22+next(s['native_turns'] for s in sessions if s['cli']=='claude')<=40
summary=dict(ready_rev=4,status='PASS',scope='Only decision-04 fixture acceptance; controller review pending',
             counterfactual=red,sessions=sessions,cases=all_cases,r7_new_records=len(rev4),
             codex_total=32+next(s['native_turns'] for s in sessions if s['cli']=='codex'),codex_limit=55,
             claude_total_conservative=22+next(s['native_turns'] for s in sessions if s['cli']=='claude'),claude_limit=40,
             independent_review='Not performed; task card assigns raw-evidence review to controller')
f=BASE/'analysis-rev4.json'
if f.exists():assert json.loads(f.read_text())==summary
else:f.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('sessions','cases')},ensure_ascii=False,indent=2))
