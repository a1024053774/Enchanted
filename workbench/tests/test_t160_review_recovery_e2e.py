"""T-160: real daemon, Claude CLI (scripted local Messages), and Electron.

Failure modes, specified before implementation:
1. Fenced JSON is accepted, or its original text is discarded.
2. The issue page does not explain the format error and same-delivery recovery.
3. Explicit recovery cannot start a fresh review of the same candidate/attempt.
4. Recovery silently accepts the failed review or changes the worker delivery.

The oracle comes from T-160: reject fenced output, preserve it, offer recovery.
--revision runs the same check against an earlier source tree. --mutant proves
that accepting fenced output is rejected. This uses no vendor model turns.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

from scripted_claude import Electron, Fixture, prompt_text, quote, working_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', required=True, type=Path)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['accept-fenced'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，使用新 summary 路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision,
                  mutant=args.mutant, checks=[], real_model_turns=0)
    fixture = electron = None
    outputs = {}
    patches = [('src/gates/qualityProtocol.ts', 'value = JSON.parse(raw);',
                'value = JSON.parse(raw.replace(/^```json\\n/, "").replace(/\\n```$/, ""));')] if args.mutant else []

    def plan(body):
        text = prompt_text(body)
        if '审查这一次交付' in text:
            shape = json.loads(text[text.rindex('{\n  "schema": 1'):])
            shape.update(verdict='可合并', findings=[], report={
                '完成条件与变异检查': '脚本化协议夹具；不声称完成真实模型的独立审查。'})
            key = shape['review_id']
            if key not in outputs:
                raw = json.dumps(shape, ensure_ascii=False)
                outputs[key] = '```json\n' + raw + '\n```' if not outputs else raw
            return 'review:' + key, [], outputs[key]
        cwd = working_directory(body)
        submit = re.search(r'显式交付：\n(.+)\n', text).group(1).replace(
            "'FULL_COMMIT_SHA'", '"$(git rev-parse HEAD)"')
        return 'worker', [('Write', dict(file_path=f'{cwd}/answer.txt', content='accepted')),
                          ('Bash', dict(command='git add answer.txt', description='stage')),
                          ('Bash', dict(command='git commit -q -m ' + quote('T160 fixture candidate'), description='commit')),
                          ('Bash', dict(command=submit, description='submit'))], '已交付。'

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    try:
        fixture = Fixture('t160-', plan, revision=args.revision, patches=patches)
        report['fixture'] = str(fixture.dir)
        (fixture.home / '.claude.json').write_text(json.dumps({
            'hasCompletedOnboarding': True, 'theme': 'dark',
            'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}), encoding='utf-8')
        fixture.start(args.claude, {'README.md': 'T-160 fixture\n', 'check.py':
            'from pathlib import Path\nassert Path("answer.txt").read_text() == "accepted"\n'})
        fixture.card('T-1', 'answer.txt', 'check.py')
        dispatched = fixture.request('dispatch', fixture.terminal, task='T-1', runtimeMode='workspace-write')
        check('dispatch', dispatched.get('ok'), dispatched)

        def status():
            return fixture.request('status', fixture.operator, task='demo+T-1')['task']

        def events():
            return fixture.request('events', fixture.operator, task='demo+T-1')['events']

        fixture.wait('交付', lambda: status()['state'] == 'submitted', 180)
        verified = fixture.request('verify', fixture.terminal, task='T-1')
        check('verification_started', verified.get('ok'), verified)
        fixture.wait('审查停止', lambda: status()['state'] in ('paused', 'verified'), 180)
        before = status()
        report['before_recovery'] = before
        check('fenced_output_rejected', before['state'] == 'paused' and before['review']['state'] == 'unknown', before['state'])
        failed = [e for e in events() if e['type'] == 'review_protocol_failed']
        check('raw_preserved', len(failed) == 1 and failed[0]['details']['details']['raw'] == outputs[before['review']['review_id']], failed)
        refused = fixture.request('integrate', fixture.terminal, task='T-1')
        check('failed_review_cannot_integrate', not refused.get('ok'), refused)

        electron = Electron(fixture, 't160-' + fixture.dir.name[5:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('问题页签', "!!document.querySelector('[data-issues-tab]')")
        electron.evaluate("document.querySelector('[data-issues-tab]').click()")
        electron.until('协议问题出现', "!!document.querySelector('.issue-card')")
        page = electron.evaluate("document.querySelector('.issues-page').innerText")
        report['issue_page'] = page
        screenshot = fixture.out / '01-protocol-rejection.png'
        electron.screenshot(screenshot)
        report['screenshot'] = str(screenshot)
        check('recovery_guidance_visible', 'JSON' in page and '为同一次交付新开审查' in page, page)
        # The same public gate entry must recover only the bound delivery.
        recovered = fixture.request('verify', fixture.terminal, task='T-1', attempt=before['current_attempt']['attempt_id'])
        check('explicit_recovery_started', recovered.get('ok'), recovered)
        fixture.wait('新审查通过', lambda: status()['state'] == 'verified', 180)
        after = status()
        report['after_recovery'] = after
        check('same_delivery_new_review', after['candidate_commit'] == before['candidate_commit'] and
              after['current_attempt']['attempt_id'] == before['current_attempt']['attempt_id'] and
              after['review']['review_id'] != before['review']['review_id'], after)
        check('failed_evidence_retained', any(e['type'] == 'review_protocol_failed' and
              e['details']['details']['raw'] == outputs[before['review']['review_id']] for e in events()))
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if fixture:
            report['api_snapshot'] = fixture.api.snapshot()
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except BaseException as error:
                    report['status'] = 'INCOMPLETE'
                    report.setdefault('cleanup_errors', []).append(f'{type(error).__name__}: {error}')
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2, default=str)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
