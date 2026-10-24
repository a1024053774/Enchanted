"""T-160 real Haiku review output, three fresh reviews through native CLI/gates/Electron.

Failure modes: a reviewer does not start with Haiku; output is accepted without a
valid protocol result; invalid output loses its original text or offers no recovery;
the three reviews reuse a session; real-turn usage exceeds nine; isolated login
preflight fails. No scripted model response, automatic retry, or auto recovery.
Login failures: missing/expired exact credentials, retaining refreshToken, a
non-private credential copy, or a copy left behind after owned processes stop.

Three independent tasks use real workers (at most two turns each, including the
delivery acknowledgement) and one real reviewer turn each: total ceiling nine.
Each oracle requires a file and its independently specified exact content, so a
reviewer can exercise deletion and wrong-content mutations. This measures protocol
adherence, not the correctness of the model's engineering judgement.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from scripted_claude import Electron, Fixture

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'claude-haiku-5-5'


def credentials(real_home, destination):
    # Same access-token-only preparation as T-163, using the product's private
    # reader (its stdout is captured in memory, never written to our report).
    sys.path.insert(0, str(ROOT / 'workbench/src'))
    from claudeLoginFiles import read_auth
    source = real_home / '.claude/.credentials.json'
    kind = 'file' if source.is_file() and not source.is_symlink() else 'macos-keychain'
    oauth = read_auth(str(real_home), kind)['claudeAiOauth']
    if oauth['expiresAt'] <= (time.time() + 600) * 1000:
        raise RuntimeError('登录即将过期；不刷新或启动模型')
    access_only = {key: value for key, value in oauth.items() if key != 'refreshToken'}
    with os.fdopen(os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w', encoding='utf-8') as stream:
        json.dump({'claudeAiOauth': access_only}, stream)
    return access_only['accessToken'], kind


class RealFixture(Fixture):
    def run_cli(self, *arguments):
        if arguments[0] == 'daemon_start':
            path = self.dir / 'launch-config.json'
            config = json.loads(path.read_text(encoding='utf-8'))
            revision = self.tested_revision
            config.update(turn_limit=2, code_revision=revision, source_snapshot=str(self.source),
                role_card_revision=revision, reviewer_role_card_revision=revision, monitor_role_card_revision=revision,
                hook_authorization='T-160-1/a1 controller #46; per-session native Claude hooks',
                turn_authorization='T-160 controller #46: three reviews, nine real turns total')
            path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
        return super().run_cli(*arguments)

    def turns(self):
        return [e for e in self.request('orchestration_events')['events'] if e['type'] == 'turn_start_signal']

    def wait(self, label, predicate, timeout=90):
        def guarded():
            count = len(self.turns())
            assert count <= 9, f'真实回合超过上限：{count}'
            return predicate()
        return super().wait(label, guarded, timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['reuse-review-id'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], trials=[], real_turn_limit=9,
                  model=MODEL, real_turns_observed=0)
    fixture = electron = None
    secret = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def no_scripted_model(body):
        raise AssertionError('真实运行不能请求脚本化模型接口')

    try:
        patches = [('src/gates/core.ts', 'const reviewId = randomUUID();', 'const reviewId = "t160-reused-review";')] if args.mutant else []
        fixture = RealFixture('t160-real-', no_scripted_model, revision=args.revision, patches=patches)
        fixture.tested_revision = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', args.revision or 'HEAD'], text=True).strip()
        report['fixture'] = str(fixture.dir)
        for key in ('ANTHROPIC_BASE_URL', 'ANTHROPIC_AUTH_TOKEN'):
            fixture.env.pop(key, None)
        fixture.env.update({key: os.environ[key] for key in ('USER', 'LOGNAME') if key in os.environ})
        # Managed Panes does not pass CLAUDE_CONFIG_DIR. Its actual default is
        # HOME/.claude; use that identical location for both preflight and CLI.
        private_config = fixture.home / '.claude'
        private_config.mkdir(exist_ok=True, mode=0o700)
        config = {'hasCompletedOnboarding': True, 'theme': 'dark',
                  'projects': {str(fixture.repo): {'hasTrustDialogAccepted': True}}}
        original = Path.home() / '.claude.json'
        if original.is_file():
            metadata = json.loads(original.read_text(encoding='utf-8'))
            if 'oauthAccount' in metadata:
                config['oauthAccount'] = metadata['oauthAccount']
        (fixture.home / '.claude.json').write_text(json.dumps(config), encoding='utf-8')
        (fixture.home / '.claude.json').chmod(0o600)
        secret, kind = credentials(Path.home(), private_config / '.credentials.json')
        report['login_preparation'] = dict(source=kind, config=str(private_config), refresh_token_copied=False,
                                           credential_mode=oct((private_config / '.credentials.json').stat().st_mode & 0o777))
        auth = subprocess.run([args.claude, 'auth', 'status', '--json'], env=fixture.env,
                              capture_output=True, text=True, timeout=30)
        # Do not write account identifiers or credential material to evidence.
        login = json.loads(auth.stdout)
        report['auth'] = dict(returncode=auth.returncode, loggedIn=login.get('loggedIn'), authMethod=login.get('authMethod'))
        check('isolated_login_ready', auth.returncode == 0 and login.get('loggedIn') is True, report['auth'])
        files = {'README.md': 'T-160 一次性协议验收项目。每个任务只新增对应 answer-N.txt，内容为 value-N，无换行。\n'}
        for i in range(1, 4):
            files[f'check_{i}.py'] = (f'from pathlib import Path\np=Path("answer-{i}.txt")\n'
                                     f'assert p.is_file(), "missing file"\nassert p.read_text()=="value-{i}", "wrong content"\n')
        fixture.start(args.claude, files)
        electron = Electron(fixture, 't160-real-' + fixture.dir.name[10:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('问题页签', "!!document.querySelector('[data-issues-tab]')")
        electron.evaluate("document.querySelector('[data-issues-tab]').click()")
        for i in range(1, 4):
            task = f'T-{i}'
            check(f'{task}_budget_reserved', len(fixture.turns()) <= 3 * (i - 1), len(fixture.turns()))
            with (fixture.out / 'turn-budget.jsonl').open('a', encoding='utf-8') as ledger:
                ledger.write(json.dumps(dict(task=task, reserved=3, observed=len(fixture.turns()), limit=9)) + '\n')
            card = dict(id=task, source=None, goal=f'只新增 answer-{i}.txt，内容精确为 value-{i}，无换行。运行 check_{i}.py 后提交并显式交付。',
                        non_goals=['不改已有文件或验收文件', '不开子 agent，不另起模型进程；收到门禁回执只确认，不继续改动'], paths=dict(allow=[f'answer-{i}.txt'], deny=[]),
                        oracle_paths=[f'check_{i}.py'], completion_conditions=[dict(argv=['python3', f'check_{i}.py'])],
                        red_commands=[], task_type='测试', repair_target=None, complexity='S',
                        executor=dict(cli='Claude Code', model=MODEL, effort='low'), base_commit=None, writer=None)
            card_path = fixture.out / f'{task}.json'
            card_path.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            saved = fixture.request('card_save', fixture.terminal, task=task, card=str(card_path), expected_version=0)
            check(f'{task}_card_saved', saved.get('ok'), saved)
            created = fixture.request('create', fixture.terminal, task=task, project='demo', repo=str(fixture.repo), branch='refs/heads/main', card_version=1)
            check(f'{task}_created', created.get('ok'), created)
            launched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            check(f'{task}_dispatched', launched.get('ok'), launched)

            def status():
                return fixture.request('status', fixture.operator, task='demo+' + task)['task']

            fixture.wait('真实 worker 交付', lambda: status()['state'] == 'submitted', 600)
            worker = status()['current_attempt']
            fixture.wait('真实 worker 完成 ACK', lambda: (lambda p: p['state'] == 'idle' and not p['queued'] and not p['active'])(
                fixture.request('pane_status', fixture.operator, thread=worker['thread_id'])), 180)
            verified = fixture.request('verify', fixture.terminal, task=task, attempt=worker['attempt_id'])
            check(f'{task}_review_started', verified.get('ok'), verified)
            fixture.wait('真实审查结果', lambda: status().get('review', {}).get('state') in ('passed', 'needs_fix', 'unknown'), 600)
            current = status()
            review = current['review']
            trial = dict(task=task, attempt=worker['attempt_id'], candidate=current['candidate_commit'], review=review)
            report['trials'].append(trial)
            launch = fixture.request('launch_show', fixture.operator, launch=review['launch_id'])['launch']
            trial['launch'] = {key: launch.get(key) for key in ('id', 'argv', 'cli_version', 'model_requested', 'effort_requested', 'role_card_revision')}
            check(f'{task}_haiku_reviewer', launch['cli'] == 'Claude Code' and launch['model_requested'] == MODEL and
                  launch['argv'][launch['argv'].index('--model') + 1] == MODEL, trial['launch'])
            facts = [e['data'] for e in fixture.request('orchestration_events')['events']
                     if e['type'] == 'native_turn_facts' and e['launch'] == review['launch_id']]
            trial['native_turn_facts'] = facts
            check(f'{task}_observed_haiku', facts and isinstance(facts[-1].get('model'), str) and facts[-1]['model'].startswith(MODEL), facts)
            events = fixture.request('events', fixture.operator, task='demo+' + task)['events']
            if review['state'] in ('passed', 'needs_fix'):
                result = [e for e in events if e['type'] == 'review_result' and e['details']['review']['review_id'] == review['review_id']]
                check(f'{task}_protocol_accepted', len(result) == 1 and review.get('result', {}).get('verdict') in ('可合并', '需修复'), result)
            else:
                failed = [e for e in events if e['type'] == 'review_protocol_failed' and e['details']['review']['review_id'] == review['review_id']]
                trial['protocol_failure'] = failed
                check(f'{task}_invalid_output_retained', len(failed) == 1 and isinstance(failed[0]['details']['details'].get('raw'), str), failed)
                electron.until('真实格式错误的恢复入口', f"!!document.querySelector('[data-restart-review=\"{review['review_id']}\"]')", 30)
                check(f'{task}_recoverable_rejection', current['state'] == 'paused')
                electron.screenshot(fixture.out / f'0{i}-real-rejected.png')
            check(f'{task}_bounded_turns', len(fixture.turns()) <= 3 * i, len(fixture.turns()))
        check('three_fresh_reviews', len({t['review']['session_id'] for t in report['trials']}) == 3 and
              len({t['review']['review_id'] for t in report['trials']}) == 3 and
              len({t['review']['launch_id'] for t in report['trials']}) == 3)
        check('no_scripted_model_calls', fixture.api.snapshot()['main'] == 0, fixture.api.snapshot())
        report['status'] = 'PASS'
    except BaseException as error:
        detail = f'{type(error).__name__}: {error}'
        report['error'] = detail.replace(secret, '[REDACTED]') if secret else detail
    finally:
        if fixture and fixture.running:
            try:
                turns = fixture.turns()
                report['real_turns_observed'] = len(turns)
                report['turns'] = [dict(seq=e['seq'], launch=e['launch'], session=e['data'].get('session_id'),
                                        prompt=e['data'].get('prompt_id')) for e in turns]
            except BaseException as error:
                report['status'] = 'INCOMPLETE'
                report['turn_observation_error'] = str(error)
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except BaseException as error:
                    report['status'] = 'INCOMPLETE'
                    report.setdefault('cleanup_errors', []).append(str(error))
        # Preserve native evidence, then remove the complete private HOME:
        # the CLI may have made credential backups alongside the known file.
        if fixture and not report.get('cleanup_errors'):
            try:
                native = fixture.home / '.claude/projects'
                saved = []
                for path in sorted(native.rglob('*.jsonl')):
                    destination = fixture.out / 'native' / path.relative_to(native)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    raw = path.read_text(encoding='utf-8')
                    with destination.open('x', encoding='utf-8') as stream:
                        stream.write(raw.replace(secret, '[REDACTED]') if secret else raw)
                    saved.append(str(destination))
                report['native_transcripts'] = saved
                shutil.rmtree(fixture.home)
                report['copied_login_removed'] = not fixture.home.exists()
            except BaseException:
                report['status'] = 'INCOMPLETE'
                report.setdefault('cleanup_errors', []).append('native evidence or private HOME cleanup failed; preserve instance')
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as stream:
            encoded = json.dumps(report, ensure_ascii=False, indent=2)
            stream.write(encoded.replace(secret, '[REDACTED]') if secret else encoded)
            stream.write('\n')
    print(json.dumps(dict(status=report['status'], summary=str(args.summary), turns=report['real_turns_observed'], error=report.get('error')), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
