"""Reassess saved raw red evidence; never rewrite the original run."""
import json
from pathlib import Path

out=Path(__file__).resolve().parent
run=out/'red02'
event=json.loads((run/'executor-event.json').read_text(encoding='utf-8'))
identity=json.loads((run/'identity.json').read_text(encoding='utf-8'))
delta=json.loads((run/'native-stop-delta.json').read_text(encoding='utf-8'))
checks={
    'credential_issued_to_executor': identity['threads']['executor'] != identity['threads']['ideation'],
    'defect_actor_wrong': event['details']['actor']=='ideation',
    'defect_caller_thread_missing': 'caller_thread' not in event['details'],
    'defect_caller_turn_missing': 'caller_turn' not in event['details'],
    'target_preserved': event['details']['thread']==identity['threads']['worker'],
    'only_gate_interrupt_requested': [e['type'] for e in delta if e['commandId'].startswith('a2a:')]==['thread.turn-interrupt-requested'],
}
with (out/'red02-reassessment.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
        note='PASS denotes defect reproduction, not implementation acceptance; red02 original verdict remains unchanged.'),stream,ensure_ascii=False,indent=2)
print(json.dumps(checks,ensure_ascii=False))
assert all(checks.values())
