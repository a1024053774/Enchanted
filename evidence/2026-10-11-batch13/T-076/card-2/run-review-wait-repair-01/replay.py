"""Offline replay of the requested -> running wait, with a virtual clock.

Failure modes: advancing on intent only; waiting past the deadline; ignoring
unknown/failed state; adopting another attempt/C/reviewer; accepting missing
running identity. No backend, processes, sockets, Git writes or model calls.
"""
import argparse
import copy
import datetime
import difflib
import gzip
import json
from pathlib import Path
import runpy

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent; card = here.parent; root = card.parents[3]
out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
saved = card / 'outside-legacy-green-05/run'
def read(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else json.loads(gzip.decompress(path.with_name(path.name+'.gz').read_bytes()))
tables = read(saved / 'state-readback.json')[0]['tables']
events = [{**row, 'details': json.loads(row['details'])} for row in tables['events']]
requested_event = next(e for e in events if e['type'] == 'review_requested')
started_event = next(e for e in events if e['type'] == 'review_started')
requested = requested_event['details']['task']; running = started_event['details']['task']
attempt = requested['current_attempt']; candidate = requested['candidate_commit']; task = requested['task_id']
assert requested['review']['state'] == 'requested' and requested['review']['launch_id'] is None
assert running['review']['state'] == 'running' and running['review']['launch_id'] and running['review']['runtime_identity']
assert requested['review']['review_id'] == running['review']['review_id']
delta = (datetime.datetime.fromisoformat(started_event['time'].replace('Z','+00:00')) -
         datetime.datetime.fromisoformat(requested_event['time'].replace('Z','+00:00'))).total_seconds()
assert 0 < delta < 12


class Clock:
    def __init__(self): self.now = 0
    def monotonic(self): return self.now
    def sleep(self, seconds): self.now += seconds


def probe(path, states):
    cls = runpy.run_path(str(path))['QualityDriver']; clock = Clock()
    cls.finalize_run.__globals__['time'] = clock
    class Actor(cls):
        def __init__(self):
            self.index = 0; self.observed = None; self.actions = []; self.timeouts = []
        def command(self, command, *args, **kwargs):
            if command == 'status':
                assert args == ('--task', task)
                if 'timeout' in kwargs:
                    assert 0 < kwargs['timeout'] <= 12
                    self.timeouts.append(kwargs['timeout'])
                clock.now += 0.05
                self.observed = copy.deepcopy(states[min(self.index, len(states)-1)]); self.index += 1
                return {'ok': True, 'task': self.observed}
            assert command == 'integrate' and self.actions == ['review']
            self.actions.append('integrate'); return {'ok': True}
        def complete_review(self, selected_task, selected_attempt, selected_candidate):
            assert selected_task == task and selected_attempt == attempt and selected_candidate == candidate
            if self.observed['review']['state'] != 'running':
                raise RuntimeError('Reviewer action before running readiness.')
            self.actions.append('review')
        def score_file(self, selected_attempt):
            assert selected_attempt == attempt
            return '/offline-only-score.json'
    actor = Actor(); error = None
    try: actor.finalize_run(task, attempt, candidate)
    except RuntimeError as failure: error = str(failure)
    return {'error': error, 'status_reads': actor.index, 'actions': actor.actions,
            'virtual_seconds': clock.now, 'status_timeouts': actor.timeouts}


before = here / 'legacy_quality_driver.py.before'; after = root / 'workbench/tests/legacy_quality_driver.py'
old = probe(before, [requested, requested, running])
assert old['error'] == 'Reviewer action before running readiness.' and not old['actions']
green = probe(after, [requested, requested, running])
assert green['error'] is None and green['actions'] == ['review','integrate'] and green['status_reads'] == 3
checks = {}
for name in ('paused', 'unknown', 'changed-attempt', 'changed-candidate', 'changed-reviewer', 'missing-identity', 'deadline'):
    bad = copy.deepcopy(running)
    if name == 'paused': bad['state'] = 'paused'
    elif name == 'unknown': bad['review']['state'] = 'unknown'
    elif name == 'changed-attempt': bad['current_attempt']['attempt_id'] = 'another-attempt'
    elif name == 'changed-candidate': bad['candidate_commit'] = 'a' * 40
    elif name == 'changed-reviewer': bad['review']['review_id'] = 'another-review'
    elif name == 'missing-identity': bad['review']['launch_id'] = None
    elif name == 'deadline': bad = copy.deepcopy(requested)
    value = probe(after, [requested, bad])
    assert value['error'] and not value['actions']
    if name == 'deadline': assert 12 <= value['virtual_seconds'] < 12.1
    else: assert value['status_reads'] == 2
    checks[name] = value
record = dict(status='PASS', product_status='INCOMPLETE', real_codex_turns=0,
              scope='offline fixture readiness replay only; complete_review and integrate are observed callbacks, not product calls',
              source=str(saved), review_id=requested['review']['review_id'],
              requested={'seq':requested_event['seq'],'time':requested_event['time']},
              running={'seq':started_event['seq'],'time':started_event['time']}, elapsed_seconds=delta,
              before=old, repaired=green, negative_checks=checks)
with (out/'run.json').open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
with (out/'fixture-fix.diff').open('x',encoding='utf-8') as stream:
    stream.writelines(difflib.unified_diff(before.read_text(encoding='utf-8').splitlines(True),
                      after.read_text(encoding='utf-8').splitlines(True),fromfile='before/legacy_quality_driver.py',tofile='after/legacy_quality_driver.py'))
print(json.dumps({k:record[k] for k in ('status','product_status','elapsed_seconds')}))
