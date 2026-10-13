"""Offline adapter replay, using saved verify/verified/accepted snapshots.

Failure categories: duplicate review effects on a reread; adopting a changed
attempt/C/review; retrying an incomplete follow-up; driving review for refusal.
Only the process-result reader and status transport are replaced. No backend,
socket, ps, provider, signals, Git mutations or product state writes occur.
"""
import argparse
import ast
import copy
import difflib
import gzip
import json
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent; card = here.parent; root = card.parents[3]
out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
saved = card / 'outside-legacy-green-04'
report = json.loads((saved / 'recovery/run.json').read_text(encoding='utf-8'))
artifact = next(a for a in report['artifacts'] if a['test'].endswith('.test_live_integrate_excludes_verify_and_integrate'))
snapshot = next(s for s in json.loads((saved / 'recovery/state-readback.json').read_text(encoding='utf-8')) if s['test'] == artifact['test'])
tables = snapshot['tables']; accepted = json.loads(tables['tasks'][0]['data'])
events = [{**e, 'details': json.loads(e['details'])} for e in tables['events']]
reviews = [e for e in events if e['type'] == 'review_result']
assert len(reviews) == 1 and accepted['state'] == 'accepted'
verified = reviews[0]['details']['task']
assert verified['state'] == 'verified' and verified['review']['review_id'] == accepted['review']['review_id']
assert len([e for e in events if e['type'] == 'review_reclaimed']) == 1
assert len([e for e in events if e['type'] == 'integrated']) == len([e for e in events if e['type'] == 'score_recorded']) == 1
commands = [c for c in report['commands'] if c.get('cwd') == artifact['root'] and c.get('label') == 'coop:verify']
success = next(c for c in commands if c['exit_code'] == 0 and json.loads(c['stdout']).get('task', {}).get('state') == 'reviewing')
refused = next(c for c in commands if c['exit_code'] == 1 and json.loads(c['stdout']).get('error') == 'operation_busy')
QualityDriver = runpy.run_path(str(root / 'workbench/tests/legacy_quality_driver.py'))['QualityDriver']


class FixtureError(RuntimeError):
    pass


class ReceiptReader:
    def complete(self, handle, timeout=12):
        self.reads += 1
        return self.receipt


class StatusOnlyDriver(QualityDriver):
    def __init__(self):
        self.current = copy.deepcopy(verified); self.commands = []; self.records = []

    def command(self, *args, **kwargs):
        assert args == ('status', '--task', accepted['task_id']) and not kwargs
        self.commands.append(list(args))
        return {'ok': True, 'task': copy.deepcopy(self.current)}

    def record(self, phase, **data):
        self.records.append({'phase': phase, **data})


def adapter(source):
    tree = ast.parse(source)
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'DaemonLifecycle')
    method = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == 'complete')
    owner = ast.ClassDef(name='Adapter', bases=[ast.Name(id='ReceiptReader', ctx=ast.Load())],
                        keywords=[], body=[method], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[owner], type_ignores=[]))
    namespace = {'ReceiptReader': ReceiptReader, 'json': json, 'recovery': SimpleNamespace(FixtureError=FixtureError)}
    exec(compile(module, 'exact-adapter-complete-method', 'exec'), namespace)
    return namespace['Adapter']


def instance(cls, row=success):
    value = cls(); value.reads = 0; value.lifecycle_events = []; value.quality = StatusOnlyDriver()
    value.receipt = subprocess.CompletedProcess(row['argv'], row['exit_code'], row['stdout'], row['stderr'])
    value.lifecycle = lambda event, **data: value.lifecycle_events.append({'event': event, **data})
    return value


before = (here / 'daemon_acceptance_adapter.py.before').read_text(encoding='utf-8')
after = (root / 'workbench/tests/daemon_acceptance_adapter.py').read_text(encoding='utf-8')
Old, New = adapter(before), adapter(after)
old = instance(Old); handle = {'command': 'verify'}
old.complete(handle); old.quality.current = copy.deepcopy(accepted)
try:
    old.complete(handle)
    raise AssertionError('Old adapter did not reproduce the saved cleanup error.')
except RuntimeError as error:
    assert str(error).startswith('Expected a running independent reviewer:')
    old_error = str(error).split(':', 1)[0]
assert len(old.quality.commands) == 2
new = instance(New); handle = {'command': 'verify'}
first = new.complete(handle); new.quality.current = copy.deepcopy(accepted)
second = new.complete(handle)
assert first.stdout == second.stdout == success['stdout'] and first.returncode == second.returncode == 0
assert len(new.quality.commands) == 1 and handle['quality_review_followup']['phase'] == 'completed'
assert new.lifecycle_events[-1]['event'] == 'review_driver_receipt_replayed'

# Binding changes must refuse a reread without another reviewer action.
for field in ('candidate_commit', 'attempt_id', 'review_id'):
    changed = json.loads(success['stdout'])
    if field == 'candidate_commit': changed['task'][field] = 'a' * 40
    elif field == 'attempt_id': changed['task']['current_attempt'][field] = 'foreign-attempt'
    else: changed['task']['review'][field] = 'foreign-review'
    new.receipt = subprocess.CompletedProcess(success['argv'], 0, json.dumps(changed), '')
    try:
        new.complete(handle); raise AssertionError('Changed receipt was adopted: ' + field)
    except FixtureError: pass
assert len(new.quality.commands) == 1

failed = instance(New); pending = {'command': 'verify'}; attempts = []
def fail_once(*args):
    attempts.append(args); raise RuntimeError('deliberate fixture follow-up failure')
failed.quality.complete_review = fail_once
try: failed.complete(pending)
except RuntimeError as error: assert str(error) == 'deliberate fixture follow-up failure'
assert len(attempts) == 1 and pending['quality_review_followup']['phase'] == 'started'
try: failed.complete(pending); raise AssertionError('Incomplete follow-up was retried.')
except FixtureError: pass
assert len(attempts) == 1
denied = instance(New, refused); busy = {'command': 'verify'}
denied.complete(busy); denied.complete(busy)
assert not denied.quality.commands and 'quality_review_followup' not in busy

with (out / 'fixture-fix.diff').open('x', encoding='utf-8') as stream:
    stream.writelines(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                       fromfile='before/daemon_acceptance_adapter.py', tofile='after/daemon_acceptance_adapter.py'))
coop = json.loads(gzip.decompress((saved / 'coop/run.json.gz').read_bytes()))
record = dict(status='PASS', product_status='INCOMPLETE', real_codex_turns=0,
              scope='offline saved-receipt replay, not a new Recovery E2E run', source=str(saved),
              task=accepted['task_id'], attempt=accepted['current_attempt']['attempt_id'], candidate=accepted['candidate_commit'],
              review_id=accepted['review']['review_id'], actual_task_state=accepted['state'],
              lifecycle_events=[{'seq': e['seq'], 'type': e['type']} for e in events if e['type'] in ('review_result','review_reclaimed','integrated','score_recorded')],
              old={'error': old_error, 'driver_status_reads': len(old.quality.commands)},
              repaired={'driver_status_reads': len(new.quality.commands), 'same_raw_receipt': True,
                        'changed_binding_refused': ['candidate', 'attempt', 'review'], 'incomplete_followup_not_retried': True,
                        'busy_verify_no_followup': True, 'fixture_events': new.lifecycle_events},
              prior_coop={k: coop[k] for k in ('status','tests_run','failures','errors','skipped')},
              prior_recovery={k: report[k] for k in ('status','tests_run','failures','errors','skipped')})
with (out / 'run.json').open('x', encoding='utf-8') as stream: json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({k: record[k] for k in ('status','product_status','scope')}))
