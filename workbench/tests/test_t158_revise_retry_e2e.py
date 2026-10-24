"""T-158: explicit reclaim separates retained evidence from path ownership.

Failure modes (written before the test):
1. revise silently adopts a saved card, leaves the old candidate valid, or loses the old attempt ID.
2. dispatch ignores an unreclaimed revoked worker and permits overlapping paths.
3. reclaim targets the new/current attempt instead of the explicitly named historical attempt.
4. a reclaimed attempt still blocks dispatch, including when its dirty worktree must be preserved.
5. help or either role instruction omits the ordered save/revise/old-attempt reclaim/dispatch procedure.
6. the fixture mistakes an in-flight paste (state=idle, empty queue, writing=true) for quiescence.

Oracle: controller #36 / user ruling relayed in 20261024T005556Z-ideation-answer-001:
save v2 -> revise -> reclaim the old attempt -> one dispatch without overlap parameters.
Real daemon/Git/PTY/Electron; real interactive Claude CLI, local scripted Messages endpoint, no vendor model.
--revision selects product sources only. --mutant applies one known-bad product change in a private copy.
--check instructions runs the real help entry without starting a daemon, Electron, or a model endpoint.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import traceback

from scripted_claude import Electron, Fixture, prompt_text, quote, source_tree, working_directory


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = 'workbench/terminal/plugin/enchanted-a2a/skills/a2a/SKILL.md'
WORKER = 'workbench/roles/worker.md'
MODEL = 'claude-haiku-5-5'
MUTANTS = {
    'release-before-reclaim': [('src/gates/core.ts',
        '(a.state !== "revoked" || Boolean(a.thread_id))', 'a.state !== "revoked"')],
    'retain-after-reclaim': [('src/gates/core.ts',
        '!a.reclaimed && a.cleanup?.state !== "removed"', 'a.cleanup?.state !== "removed"')],
    'help-no-reclaim': [('src/terminalCli.ts', 'reclaim', 'reclaiM')],
}


class ContractFailure(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--check', choices=['all', 'flow', 'instructions'], default='all')
    parser.add_argument('--claude', default=shutil.which('claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=MUTANTS)
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve prior evidence; choose a new --summary path'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  product_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  vendor_model_turns=0, checks=[], observed={}, errors=[])
    fixture = electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        return bool(condition)

    def require(name, condition, detail=None):
        if not check(name, condition, detail):
            raise ContractFailure(name)

    def ordered(text):
        # Commands, not an exact prose snapshot; each next operation must be discoverable after the previous one.
        return re.search(r'card_save[\s\S]*?revise[\s\S]*?reclaim[\s\S]*?dispatch', text) is not None

    def instructions(source):
        run = subprocess.run(['node', str(source / 'workbench/src/terminalCli.ts'), 'help'],
                             capture_output=True, text=True, timeout=20,
                             env={k: v for k, v in os.environ.items() if not k.startswith('A2A_')})
        require('help_entry_exits_zero', run.returncode == 0, run.stderr)
        help_text = run.stdout
        controller = (source / CONTROLLER).read_text(encoding='utf-8')
        worker = (source / WORKER).read_text(encoding='utf-8')
        report['observed']['help_stdout'] = help_text
        check('help_has_ordered_revision_retry_steps', ordered(help_text), help_text)
        check('help_names_card_spec_and_old_attempt_parameters',
              all(key in help_text for key in ('card_version', 'spec_rev', 'attempt')),
              'card_version, spec_rev and explicit old attempt are required')
        check('controller_has_ordered_revision_retry_steps', ordered(controller))
        examples = []
        for raw in re.findall(r'`(\{[^`\n]+\})`', controller):
            try:
                examples.append(json.loads(raw))
            except json.JSONDecodeError:
                pass  # The existing score illustration contains ranges, rather than a runnable JSON example.
        revise = [v for v in examples if v.get('command') == 'revise']
        reclaim = [v for v in examples if v.get('command') == 'reclaim']
        check('controller_has_runnable_revise_and_explicit_reclaim_examples',
              any('task' in v and 'spec_rev' in v and 'card_version' in v for v in revise) and
              any('task' in v and isinstance(v.get('attempt'), str) and v['attempt'] for v in reclaim),
              dict(revise=revise, reclaim=reclaim))
        check('worker_has_ordered_steps_and_controller_handoff', ordered(worker) and '执行主控' in worker)

    def plan(body):
        text = prompt_text(body)
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1)
        submit = submit.replace("'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return cwd, [('Write', dict(file_path=f'{cwd}/answer.txt', content='candidate\n')),
                     ('Bash', dict(command='git add answer.txt', description='stage fixture candidate')),
                     ('Bash', dict(command='git commit -q -m ' + quote('T-158 fixture candidate'), description='commit fixture candidate')),
                     ('Bash', dict(command=submit, description='submit fixture candidate'))], '交付已提交。'

    try:
        patches = MUTANTS.get(args.mutant, [])
        if args.check == 'instructions':
            directory = Path(tempfile.mkdtemp(prefix='t158-instructions-', dir='/private/tmp'))
            report['fixture'] = str(directory)
            instructions(source_tree(directory, args.revision, patches))
        else:
            fixture = Fixture('t158-retry-', plan, revision=args.revision, patches=patches)
            report['fixture'] = str(fixture.dir)
            (fixture.home / '.claude.json').write_text(json.dumps({'hasCompletedOnboarding': True, 'theme': 'dark',
                'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
            fixture.start(args.claude, {'README.md': 'T-158 isolated repository\n',
                'check_v1.py': 'raise SystemExit(1)\n',
                'check_v2.py': 'from pathlib import Path\nassert Path("answer.txt").read_text() == "candidate\\n"\n'})
            electron = Electron(fixture, 't158-' + fixture.dir.name)
            electron.until('project visible', '!!document.querySelector(\'[data-project-id="demo"]\')')
            electron.evaluate('document.querySelector(\'[data-project-id="demo"]\').click()')
            task = 'T-158-probe'
            fixture.card(task, 'answer.txt', 'check_v1.py')

            def request(command, **data):
                result = fixture.request(command, fixture.terminal, task=task, **data)
                report['observed'].setdefault('commands', []).append(dict(command=command, input=data, result=result))
                return result

            def status():
                return fixture.request('status', fixture.operator, task='demo+' + task)['task']

            def idle(attempt):
                state = fixture.request('pane_status', fixture.operator, thread=attempt['thread_id'])
                return state if state.get('state') == 'idle' and state.get('writing') is False and not state.get('failed') and not state.get('active') and not state.get('queued') else None

            def wait_idle(label, attempt):
                observed = fixture.wait(label, lambda: idle(attempt), 90)
                report['observed'].setdefault('quiescence', []).append(dict(label=label,
                    at=datetime.now(timezone.utc).isoformat(), pane=observed))
                return observed

            first = request('dispatch', runtimeMode='workspace-write', model=MODEL, effort='low')
            require('initial_dispatch', first.get('ok'), first)
            old = first['attempt']
            fixture.wait('first candidate submitted', lambda: status()['state'] == 'submitted', 180)
            wait_idle('old worker idle after delivery', old)
            rejected = request('verify')
            require('candidate_rejected_before_revision', rejected.get('error') == 'oracle_failed', rejected)
            wait_idle('old worker idle after rejection', old)
            # Dirty retained evidence is a sentinel: path release must depend on reclaim, not worktree deletion.
            sentinel = Path(old['workspace']) / 'uncommitted-evidence.txt'
            sentinel.write_text('T-158 retained evidence\n', encoding='utf-8')
            card_path = fixture.out / f'{task}.json'
            v2 = json.loads(card_path.read_text(encoding='utf-8'))
            v2['oracle_paths'] = ['check_v2.py']
            v2['completion_conditions'] = [dict(argv=['python3', 'check_v2.py'])]
            card_path = fixture.out / 'v2.json'
            card_path.write_text(json.dumps(v2, ensure_ascii=False), encoding='utf-8')
            saved = request('card_save', card=str(card_path), expected_version=1)
            require('save_v2_does_not_adopt_contract', saved.get('ok') and status()['card_version'] == 1, saved)
            revised = request('revise', spec_rev=2, card_version=2)
            require('revise_revokes_candidate_and_keeps_ready_task', revised.get('ok') and
                    revised['task']['current_attempt'] is None and revised['task']['candidate_commit'] is None and
                    revised['task']['card_version'] == 2 and revised['task']['spec_rev'] == 2, revised)
            overlap = request('dispatch', runtimeMode='workspace-write', model=MODEL, effort='low')
            require('unreclaimed_attempt_still_reserves_paths', overlap.get('error') == 'path_overlap' and
                    any(c['attempt'] == old['attempt_id'] for c in overlap.get('details', {}).get('conflicts', [])), overlap)
            wait_idle('old worker quiescent before historical reclaim', old)
            reclaimed = request('reclaim', attempt=old['attempt_id'])
            require('explicit_historical_reclaim_succeeds', reclaimed.get('ok'), reclaimed)
            require('dirty_evidence_preserved_after_reclaim', sentinel.is_file() and
                    sentinel.read_text(encoding='utf-8') == 'T-158 retained evidence\n', str(sentinel))
            second = request('dispatch', runtimeMode='workspace-write', model=MODEL, effort='low')
            require('one_dispatch_after_reclaim_without_overlap_reason', second.get('ok') and
                    second['attempt']['attempt_id'] != old['attempt_id'] and second['attempt']['fence'] == old['fence'] + 1,
                    second)
            new = second['attempt']
            fixture.wait('new candidate submitted', lambda: status()['state'] == 'submitted', 180)
            wait_idle('new worker idle', new)
            require('new_attempt_uses_v2', status()['current_attempt']['spec_rev'] == 2 and status()['card_version'] == 2)
            events = request('events')['events']
            require('old_attempt_reclaimed_event_preserved', any(e['type'] == 'reclaimed' and
                    e['attempt'] == old['attempt_id'] for e in events))
            selector = '[data-task-option="demo+' + task + '"]'
            electron.until('revised task visible', f'!!document.querySelector({json.dumps(selector)})')
            electron.evaluate(f'document.querySelector({json.dumps(selector)}).click()')
            electron.until('revised task selected', f'!!document.querySelector(\'[data-task-id="demo+{task}"]\')')
            screenshot = args.summary.with_name(args.summary.stem + '-retry.png')
            electron.screenshot(screenshot)
            report['observed']['screenshot'] = str(screenshot)
            if args.check == 'all':
                instructions(fixture.source)
        report['status'] = 'PASS' if all(row['passed'] for row in report['checks']) else 'INCOMPLETE'
    except ContractFailure as failure:
        report['target_failure'] = str(failure)
    except Exception:
        report['errors'].append(traceback.format_exc())
    finally:
        try:
            if electron:
                electron.stop()
            if fixture:
                report['observed']['scripted_api'] = fixture.api.snapshot()
                fixture.stop()
        except Exception:
            report['status'] = 'INCOMPLETE'
            report['errors'].append('cleanup: ' + traceback.format_exc())
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary),
        failed=[row['name'] for row in report['checks'] if not row['passed']], errors=report['errors']), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
