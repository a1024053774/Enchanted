#!/usr/bin/env python3
"""T-153: real Codex file -> Stop -> CLI -> gate -> review -> scored CAS.

Failure modes: a replay emits another notice; one Stop batch emits more than
one notice; a notice is lost/duplicated in native input; its receipt uses tools;
delivery/trailers disagree with native turn_context; merge/CAS loses host work.
Expectations: T-153, T-118 (record installed version), T-141 (open network),
native-cli-orchestration spec sections 3 and 8 (review, score and provenance).
--mutant changes an isolated source copy, never the checkout. Only named
ContractFailure is business red; setup/CLI/timeout failures are INCOMPLETE.
The outside runner must supply a current authorization for two worker turns
and at most two reviewer turns. No automatic retry or extra turn is granted.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from fixture_artifacts import archive_and_cleanup


ORACLE = '''import json, runpy, subprocess, sys
from pathlib import Path
root=Path(sys.argv[1])
cases=[
 ([{"name":" Alice ","minutes":70},{"name":"张三","minutes":59},{"name":"Alice","minutes":55},{"name":"Bob","minutes":0}],0,
  {"entries":[{"name":"Alice","minutes":125,"duration":"2:05"},{"name":"Bob","minutes":0,"duration":"0:00"},{"name":"张三","minutes":59,"duration":"0:59"}],"total_minutes":184}),
 ([],0,{"entries":[],"total_minutes":0}),
 ([{"name":"A","minutes":-1}],2,{"error":"invalid_minutes"}),
 ([{"name":"A","minutes":True}],2,{"error":"invalid_minutes"}),
 ([{"name":"  ","minutes":1}],2,{"error":"invalid_name"})]
normalize=runpy.run_path(str(root/"src/normalize.py"))["normalize"]
for payload,code,expected in cases:
 if code==0:
  assert normalize(payload)==expected
 else:
  try: normalize(payload)
  except ValueError as error: assert str(error)==expected["error"]
  else: raise AssertionError("invalid input must raise ValueError")
 p=subprocess.run([sys.executable,"-B",str(root/"src/report.py")],input=json.dumps(payload,ensure_ascii=False),text=True,capture_output=True)
 assert p.returncode==code,(payload,p.returncode,p.stdout,p.stderr)
 assert json.loads(p.stdout)==expected,(payload,p.stdout,expected)
print("independent normalization oracle: 5 cases passed")
'''


class ContractFailure(AssertionError):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--turn-authorization', type=Path, required=True)
    parser.add_argument('--setup-only', action='store_true', help='Stop after real card_save/create; do not launch an agent')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=['repeat-feedback'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.summary.exists():
        parser.error('Keep previous evidence; use a new summary path')
    if not args.turn_authorization.is_file():
        parser.error('A current turn authorization file is required')
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='a2a-B-', dir='/tmp')).resolve()
    output = temp / 'raw'; output.mkdir()
    repo, state, isolated = temp / 'repo', temp / 'state', temp / 'codex-home'
    repo.mkdir(); isolated.mkdir(mode=0o700)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.update(GIT_AUTHOR_NAME='B fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='B fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               A2A_OPERATOR_CREDENTIAL=str(temp / 'operator.json'))
    git_env = dict(env, GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0='/dev/null',
                   GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false')
    commands = []; cleanup_pids = set(); started = False
    verdict = {'status': 'INCOMPLETE', 'task': 'T-153-1', 'attempt': 'a1', 'channel': 'B',
               'real_turns_reserved': 0, 'fixture': str(temp), 'raw_artifacts': str(output),
               'command': sys.argv, 'revision': args.revision, 'mutant': args.mutant,
               'turn_authorization': str(args.turn_authorization.resolve()), 'checks': []}
    cli = ['node', root / 'workbench/src/gates/cli.ts', '--state', state]

    def save(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def run(argv, *, check=True, command_env=None, timeout=60):
        p = subprocess.run([str(value) for value in argv], cwd=root, env=command_env or env,
                           capture_output=True, text=True, timeout=timeout)
        commands.append({'argv': [str(value) for value in argv], 'cwd': str(root), 'exit': p.returncode,
                         'stdout': p.stdout, 'stderr': p.stderr, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
        save('commands.json', commands)
        if check and p.returncode: raise RuntimeError(commands[-1])
        return p

    def call(command, *values, check=True):
        p = run([*cli, command, *values], check=check)
        value = json.loads(p.stdout)
        if check and not value.get('ok'): raise RuntimeError(value)
        return value

    def git(*values):
        return run(['git', '-C', repo, *values], command_env=git_env).stdout.strip()

    def check(name, condition):
        verdict['checks'].append({'id': name, 'passed': bool(condition)})
        if not condition:
            raise ContractFailure(name)

    try:
        verdict['candidate_revision'] = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        source = root
        if args.revision or args.mutant:
            source = temp / 'source'
            paths = ['workbench/' + name for name in ('src', 'terminal', 'hooks', 'roles')]
            if args.revision:
                snapshot = temp / 'source.tar'
                run(['git', 'archive', '--output', snapshot, args.revision, *paths])
                run(['tar', '-xf', snapshot, '-C', temp])
                source.mkdir()
                shutil.move(str(temp / 'workbench'), source / 'workbench')
                verdict['source_revision'] = run(['git', 'rev-parse', args.revision]).stdout.strip()
            else:
                for name in paths:
                    shutil.copytree(root / name, source / name, symlinks=True)
                # Fault: every replay can inject another feedback notification.
                path = source / 'workbench/src/daemon.ts'
                old = 'if (!receipt.replayed && !isPendingInboxResult(receipt.result)) receipts.push(receipt);'
                new = 'if (!isPendingInboxResult(receipt.result)) receipts.push(receipt);'
                text = path.read_text(encoding='utf-8')
                if text.count(old) != 1:
                    raise RuntimeError('Mutant anchor must occur exactly once')
                path.write_text(text.replace(old, new), encoding='utf-8')
                save('mutation.json', {'path': str(path), 'before': old, 'after': new})
            (source / 'workbench/node_modules').symlink_to(root / 'workbench/node_modules', target_is_directory=True)
            cli = ['node', source / 'workbench/src/gates/cli.ts', '--state', state]
        git('init', '-b', 'main')
        (repo / 'src').mkdir()
        (repo / 'src/normalize.py').write_text('def normalize(rows):\n    return {}\n', encoding='utf-8')
        (repo / 'src/report.py').write_text('import json\nprint(json.dumps({"stub": True}))\n', encoding='utf-8')
        (repo / '.gitignore').write_text('__pycache__/\n*.pyc\n', encoding='utf-8')
        (repo / 'host.txt').write_text('baseline\n', encoding='utf-8')
        (repo / 'acceptance.py').write_text(ORACLE, encoding='utf-8')
        git('add', '.'); git('commit', '-m', 'B fixture baseline'); baseline = git('rev-parse', 'HEAD')
        oracle = temp / 'oracle.py'; oracle.write_text(ORACLE, encoding='utf-8')
        red = run([sys.executable, '-I', '-B', oracle, repo], check=False)
        if red.returncode == 0: raise RuntimeError('Independent baseline must fail before worker implementation')
        (isolated / 'config.toml').write_text(f'[projects.{json.dumps(str(repo))}]\ntrust_level="trusted"\n', encoding='utf-8')
        (isolated / 'rules').mkdir()
        (isolated / 'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
        limit = 2
        codex = Path(shutil.which('codex')).resolve()
        installed_version = run([codex, '--version']).stdout.strip()
        if not installed_version:
            raise RuntimeError('Installed CLI version must be observable')
        verdict['cli_version'] = installed_version
        config = {'codex_bin': str(codex), 'codex_home': str(isolated),
                  'role_card': str(source / 'workbench/roles/worker.md'),
                  'role_card_revision': run(['git', 'log', '-1', '--format=%H', '--', 'workbench/roles/worker.md']).stdout.strip(),
                  'reviewer_role_card': str(source / 'workbench/roles/reviewer.md'),
                  'reviewer_role_card_revision': run(['git', 'log', '-1', '--format=%H', '--', 'workbench/roles/reviewer.md']).stdout.strip(),
                  'code_revision': verdict.get('source_revision', verdict['candidate_revision']),
                  'hook_authorization': str(args.turn_authorization.resolve()), 'turn_limit': limit,
                  'turn_authorization': str(args.turn_authorization.resolve())}
        save('launch-config.json', config)
        begin = call('daemon_start', '--launch-config', output / 'launch-config.json'); started = True
        cleanup_pids.add(begin['pid'])
        process_ids = {'daemon_pid': begin['pid'], 'daemon_pgid': os.getpgid(begin['pid']), 'daemon_sid': os.getsid(begin['pid']),
                       'caller_pid': os.getpid(), 'caller_pgid': os.getpgrp(), 'caller_sid': os.getsid(0)}
        if not args.setup_only:
            run(['/bin/ps', '-o', 'pid=,ppid=,pgid=,sess=,command=', '-p', str(begin['pid'])])
        assert process_ids['daemon_pid'] == process_ids['daemon_pgid'] == process_ids['daemon_sid']
        assert process_ids['daemon_pgid'] != process_ids['caller_pgid'] and process_ids['daemon_sid'] != process_ids['caller_sid']
        save('daemon-process-readback.json', process_ids)
        ticket = root / '.project-map/tickets/T-153-migrate-worker-delivery.md'
        ready_rev = int(next(line.split(':', 1)[1] for line in ticket.read_text(encoding='utf-8').splitlines() if line.startswith('ready_rev:')))
        task = 'T-153-1'
        card = {'id': task, 'source': {'ticket': str(ticket), 'ready_rev': ready_rev},
                'goal': '这是 T-153 的隔离验收夹具，只实现本卡列出的两个文件；来源ticket仅用于规格版本绑定，不到a2a仓库实现编排系统。'
                        '实现 src/normalize.py 的 normalize(rows) 和 src/report.py。report.py 从 stdin 读取 JSON 数组并只输出一行 JSON。'
                        '每项含 name（字符串）与 minutes（非负整数，bool 不算整数）。name 去掉首尾空白后不得为空。按去空白后的 name 合并 minutes，按 name 升序输出。'
                        '正常退出0，输出 {"entries":[{"name":名字,"minutes":合计整数,"duration":"小时:两位分钟"}],"total_minutes":总数}；空数组输出空entries和0。'
                        'normalize(rows) 返回正常结果字典；非法输入抛 ValueError，消息严格为 invalid_minutes 或 invalid_name。'
                        'report.py 将 minutes 非法转换为退出2、输出 {"error":"invalid_minutes"}；name 非法转换为退出2、输出 {"error":"invalid_name"}。'
                        '只修改这两个源码文件，完成后 git add / git commit。然后运行派发给你的 submit 命令，并加 --request-id delivery。'
                        '为验证重复转交，再将 $A2A_REQUEST_DIR/delivery.json 原样复制为同目录 delivery-copy.json，然后结束回合，不轮询、不重试。'
                        '请求目录中已有的 fixture-* 文件是主控注入的验收夹具，不修改它们。门禁回执只需确认收到并结束，不调用工具、不改文件、不新增请求。',
                'non_goals': ['不修改 oracle、任务合同、host.txt、.gitignore；不访问网络；不启动子agent；请求文件不得进入Git'],
                'paths': {'allow': ['src/normalize.py', 'src/report.py'], 'deny': []},
                'oracle_paths': ['acceptance.py'],
                'completion_conditions': [{'argv': [sys.executable, '-I', '-B', str(oracle), '{worktree}']}],
                'red_commands': [], 'task_type': '后端逻辑', 'repair_target': None, 'complexity': 'M',
                'executor': {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'high'}, 'base_commit': None, 'writer': None}
        save('card.json', card)
        call('card_save', '--task', task, '--project', 'B-fixture', '--card', output / 'card.json', '--expected-version', '0')
        task = call('create', '--task', task, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'B-fixture')['task']['task_id']
        if args.setup_only:
            check('REGISTRATION-FULL-ID', task == 'B-fixture+T-153-1')
            registered = call('status', '--task', task)['task']
            check('REGISTRATION-NO-ATTEMPT', registered['current_attempt'] is None and registered['candidate_commit'] is None)
            save('registration.json', {'task': task, 'project': 'B-fixture', 'real_model_turns': 0})
            verdict.update(status='PASS', phase='registration_only', registered_task=task, real_model_turns=0)
        else:
            shutil.copyfile(Path.home() / '.codex/auth.json', isolated / 'auth.json'); (isolated / 'auth.json').chmod(0o600)
            call('execution_settings_save', '--role', 'reviewer', '--model', 'gpt-6.1-sol', '--effort', 'high', '--fast', 'false')
            # Reserve before dispatch: native readiness now releases automatically (T-127).
            verdict['real_turns_reserved'] = 4
            save('turn-reservation.json', {'worker_max': 2, 'reviewer_max': 2,
                                         'authorization': config['turn_authorization']})
            attempt = call('dispatch', '--task', task, '--runtime-mode', 'workspace-write',
                           '--model', 'gpt-6.1-sol', '--effort', 'high', '--fast', 'false')['attempt']; thread = attempt['thread_id']
            save('attempt.json', attempt)
            pane = call('pane_status', '--thread', thread)
            launch = call('launch_show', '--launch', pane['launch'])['launch']; save('launch-record.json', launch)
            request_dir = Path(launch['request_dir'])
            common = {'schema': 1, 'task': task, 'attempt': attempt['attempt_id'], 'session': attempt['session_id'],
                      'fence': attempt['fence'], 'spec_rev': attempt['spec_rev']}
            injected = {
                'fixture-identity.json': dict(common, request_id='fixture-identity', command='submit', commit=baseline, fence=attempt['fence'] + 1),
                'fixture-incomplete.json': dict(common, request_id='fixture-incomplete', command='submit'),
                'fixture-status.json': dict(common, request_id='fixture-status', command='status'),
                'fixture-issue.json': dict(common, request_id='fixture-issue', command='issue', title='夹具：验证问题上报', body='这是主控注入的非阻塞验收夹具，不是真实缺陷，不要求worker修复。', blocking=False, refs=[]),
            }
            for name, value in injected.items():
                with (request_dir / name).open('x', encoding='utf-8') as stream: stream.write(json.dumps(value, ensure_ascii=False) + '\n')
            save('injected-files.json', {'source': 'executor-test-fixture', 'files': injected})
            # Independent host commit after claim forces a real G/C merge at verify.
            (repo / 'host.txt').write_text('independent G\n', encoding='utf-8')
            git('add', 'host.txt'); git('commit', '-m', 'Independent host G'); G = git('rev-parse', 'refs/heads/main')
            deadline = time.monotonic() + 30
            while True:
                info = call('pane_process_info', '--thread', thread)
                cleanup_pids.update(row['pid'] for row in info['processes'])
                if info.get('leader') and not info.get('failed'): break
                if info.get('failed') or time.monotonic() >= deadline: raise RuntimeError({'foreground_unconfirmed': info})
                time.sleep(0.2)
            save('before-release.json', info)
            deadline = time.monotonic() + 600
            while True:
                pane = call('pane_status', '--thread', thread)
                status = call('status', '--task', task)['task']
                if pane.get('failed'): raise RuntimeError(pane)
                if status['state'] == 'submitted' and pane['state'] == 'idle' and not pane['writing']:
                    observed = call('orchestration_events', '--task', task)['events']
                    completed = {event['data']['record']['payload']['turn_id'] for event in observed
                                 if event['type'] == 'native_record' and event['data']['file'].endswith(pane['native_session'] + '.jsonl')
                                 and event['data']['record']['type'] == 'event_msg' and event['data']['record']['payload']['type'] == 'task_complete'}
                    if len(completed) == limit: break
                if time.monotonic() >= deadline: raise RuntimeError('B真实交付未在期限内结束；不新增回合或重试')
                time.sleep(1)
            if oracle.read_text(encoding='utf-8') != ORACLE: raise RuntimeError('独立oracle被修改')
            verdict['observed_main_turns'] = len(completed)
            C = run(['git', '-C', attempt['workspace'], 'rev-parse', 'HEAD'], command_env=git_env).stdout.strip()
            assert status['candidate_commit'] == C
            assert git('rev-parse', 'refs/heads/main') == G
            # Check feedback before verification creates unrelated reviewer dispatches.
            feedback_events = call('orchestration_events', '--task', task)['events']
            save('worker-feedback-events.json', feedback_events)
            worker_notices = [event for event in feedback_events if event.get('launch') == launch['id']
                              and event['type'] == 'dispatch_queued' and event['data'].get('source') == 'gate']
            check('STOP-BATCH-ONE-NOTICE', len(worker_notices) == 1)
            check('RECEIPT-QUEUE-EMPTY', not pane['queued'])
            verified = call('verify', '--task', task, '--attempt', attempt['attempt_id'])
            verification = verified['verification']
            check('FRESH-REVIEW-STARTED', verified['task']['state'] == 'reviewing')
            review = verified['task']['review']
            review_pane = call('pane_status', '--thread', review['thread_id'])
            review_launch = call('launch_show', '--launch', review_pane['launch'])['launch']
            save('review-launch.json', review_launch)
            check('FRESH-REVIEW-IDENTITY', review_launch['role'] == 'reviewer'
                  and review_launch['id'] != launch['id'] and review['session_id'] != attempt['session_id'])
            deadline = time.monotonic() + 600
            while True:
                reviewed = call('status', '--task', task)['task']
                review_pane = call('pane_status', '--thread', review['thread_id'])
                info = call('pane_process_info', '--thread', review['thread_id'])
                cleanup_pids.update(row['pid'] for row in info['processes'])
                reclaimed = any(event['type'] == 'review_reclaimed' and event['details']['review_id'] == review['review_id']
                                for event in call('events', '--task', task)['events'])
                if reviewed['state'] == 'verified' and reclaimed: break
                if review_pane.get('failed') or reviewed['state'] not in ('reviewing', 'verified'):
                    raise RuntimeError({'review_not_accepted': reviewed, 'pane': review_pane})
                if time.monotonic() >= deadline:
                    raise RuntimeError('Independent review deadline; no retry or additional turn')
                time.sleep(1)
            check('REVIEW-BOUND-TO-CANDIDATE', reviewed['review']['candidate_commit'] == C
                  and reviewed['review']['result']['verdict'] == '可合并')
            check('REVIEW-NATIVE-SESSION-FRESH', reviewed['review']['runtime_identity']['native_session'] != pane['native_session'])
            save('review-result.json', reviewed['review'])
            save('score.json', {'result': '通过', 'boundary_discipline': 3, 'boundary_reason': '只修改卡片内两个源码文件',
                                'engineering_taste': 2, 'engineering_reason': '独立 oracle 与审查通过', 'notes': 'T-153 隔离夹具评分'})
            call('integrate', '--task', task, '--attempt', attempt['attempt_id'], '--score-file', output / 'score.json')
            M = git('rev-parse', 'refs/heads/main')
            assert verification['G'] == G and verification['M'] == M and G != M
            assert git('rev-list', '--parents', '-n', '1', M).split() == [M, G, C]
            assert (repo / 'host.txt').read_text() == 'independent G\n'
            assert oracle.read_text(encoding='utf-8') == ORACLE
            save('git-readback.json', {'B': baseline, 'G': G, 'C': C, 'M': M})
            commit_message = git('show', '-s', '--format=%B', C)
            save('candidate-trailers.json', {'commit': C, 'message': commit_message})
            delivered = call('status', '--task', task)['task']['current_attempt']['delivery']
            turn_contexts = [event['data']['record']['payload'] for event in call('orchestration_events', '--task', task)['events']
                             if event['type'] == 'native_record' and event['data']['file'].endswith(pane['native_session'] + '.jsonl')
                             and event['data']['record']['type'] == 'turn_context'
                             and event['data']['record']['payload'].get('turn_id') == delivered['turn_id']]
            assert turn_contexts, delivered['turn_id']
            turn_context = turn_contexts[-1]
            model = turn_context.get('model') or 'unknown'
            effort = turn_context.get('effort') or turn_context.get('reasoning_effort') or 'unknown'
            assert model != 'unknown' and effort != 'unknown'
            assert delivered['model'] == model and delivered['effort'] == effort
            expected = {'Task': task, 'Attempt': attempt['attempt_id'], 'Session': attempt['session_id'], 'Role': 'worker',
                        'Tool': installed_version, 'Model': model, 'Effort': effort, 'Native-Session': pane['native_session'], 'Launch': launch['id']}
            lines = [line for line in commit_message.splitlines() if line.startswith('A2A-')]
            assert sorted(lines) == sorted('A2A-' + key + ': ' + value for key, value in expected.items())
            events = call('orchestration_events', '--task', task)['events']; save('orchestration-events.json', events)
            gate_events = call('events', '--task', task)['events']; save('gate-events.json', gate_events)
            integrations = [event['details'] for event in gate_events if event['type'] == 'integrated']
            assert len(integrations) == 1
            assert integrations[0]['intent']['G'] == G and integrations[0]['intent']['M'] == M
            assert integrations[0]['readback'] == M
            assert len([event for event in gate_events if event['type'] == 'submitted']) == 1
            stats = git('diff', '--numstat', baseline, C).splitlines()
            measured = {'files': len(stats), 'added': sum(int(line.split('\t')[0]) for line in stats),
                        'deleted': sum(int(line.split('\t')[1]) for line in stats)}
            metric = next(event['details'] for event in gate_events if event['type'] == 'submission_metrics')
            assert all(metric[key] == value for key, value in measured.items())
            save('independent-diff-stat.json', measured)
            for request_id, error in [('fixture-identity', 'relay_identity_mismatch'), ('fixture-incomplete', 'invalid_relay_request')]:
                assert any(event['type'] == 'relay_rejected' and event['data'].get('request_id') == request_id and event['data']['result']['error'] == error for event in events)
            check('DELIVERY-REPLAY', any(event['type'] == 'relay_replayed' and event['data']['key'] == 'id:' + launch['id'] + ':delivery'
                                       and event['data']['result'].get('ok') for event in events))
            assert len([event for event in events if event['type'] == 'relay_processed' and event['data'].get('request_id') == 'delivery']) == 1
            for request_id in ('fixture-status', 'fixture-issue'):
                assert any(event['type'] == 'relay_processed' and event['data'].get('request_id') == request_id for event in events)
            status_receipt = next(event['data']['result'] for event in events if event['type'] == 'relay_processed' and event['data'].get('request_id') == 'fixture-status')
            assert status_receipt['task']['current_attempt']['attempt_id'] == attempt['attempt_id']
            primary = [event['data']['record'] for event in events if event['type'] == 'native_record' and event['data']['file'].endswith(pane['native_session'] + '.jsonl')]
            turns = {event['payload']['turn_id'] for event in primary if event['type'] == 'event_msg' and event['payload']['type'] == 'task_started'}
            verdict['observed_main_turns'] = len(turns)
            assert len(turns) == limit
            contexts = [event['payload'] for event in primary if event['type'] == 'turn_context']
            assert contexts and all(context['model'] == 'gpt-6.1-sol' and context['approval_policy'] == 'never'
                                    and context['sandbox_policy'].get('network_access') is True for context in contexts)
            notices = [event['data'] for event in events if event.get('launch') == launch['id']
                       and event['type'] == 'dispatch_queued' and event['data'].get('source') == 'gate']
            assert len(notices) == 1, 'one Stop batch must produce one gate notice'
            if notices:
                messages = [event['payload'] for event in primary if event['type'] == 'response_item'
                            and event['payload'].get('type') == 'message' and event['payload'].get('role') == 'user'
                            and any(item.get('text') == notices[0]['text'] for item in event['payload'].get('content', []))]
                assert len(messages) == 1, 'native user input must equal the registered gate notice'
                receipt_turn = messages[0]['internal_chat_message_metadata_passthrough']['turn_id']
                starts = [index for index, event in enumerate(primary) if event['type'] == 'event_msg'
                          and event['payload'].get('type') == 'task_started' and event['payload'].get('turn_id') == receipt_turn]
                ends = [index for index, event in enumerate(primary) if event['type'] == 'event_msg'
                        and event['payload'].get('type') == 'task_complete' and event['payload'].get('turn_id') == receipt_turn]
                check('RECEIPT-TURN-BOUNDARIES', len(starts) == len(ends) == 1 and starts[0] < ends[0])
                tools_in_receipt = [event for event in primary[starts[0]:ends[0] + 1] if event['type'] == 'response_item'
                                    and event['payload'].get('type') in ('function_call', 'custom_tool_call')]
                check('RECEIPT-NO-TOOLS', not tools_in_receipt)
            assert not any(event['type'] == 'permission_wait' for event in events)
            assert not pane['queued']
            verdict.update(status='PASS', G=G, M=M, gate_reply='native-message-received-and-receipt-turn-completed')
    except ContractFailure as error:
        verdict.update(status='NO_GO', outcome='contract_failure', failure_id=str(error))
    except (OSError, ValueError, KeyError, TypeError, AssertionError, RuntimeError, subprocess.TimeoutExpired) as error:
        verdict.update(status='INCOMPLETE', outcome='harness_or_unclassified_failure', error=str(error))
    finally:
        if started:
            try:
                if 'thread' in locals():
                    info = call('pane_process_info', '--thread', thread)
                    cleanup_pids.update(row['pid'] for row in info['processes']); save('before-stop-processes.json', info)
                save('all-events-before-stop.json', call('orchestration_events'))
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                verdict['observation_error'] = str(error)
            finally:
                try: save('stop.json', call('daemon_stop', check=False))
                except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error: verdict['stop_error'] = str(error)
        archive_and_cleanup(state, output, isolated, cleanup_pids, run, save, verdict)
        with args.summary.open('x', encoding='utf-8') as stream:
            json.dump(verdict, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
