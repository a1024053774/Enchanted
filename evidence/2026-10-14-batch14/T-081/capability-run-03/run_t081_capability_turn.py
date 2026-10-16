"""主控运行：批准的一次真实能力观察；标准 daemon CLI，不提交、不清理 home。"""
import argparse
import ast
from contextlib import closing
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import sqlite3
import stat
import sys
import tarfile
import time
import traceback

from command_evidence import CommandLog
from capability_poll_evidence import PollEvidence
from fixture_artifacts import archive_stopped_database


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'evidence/2026-10-14-batch14/T-081'
FIXTURE = Path('/private/tmp/t081-capability-01')
RUN_ROOT = FIXTURE / 'run-03'
TASK = 'T-081-CAP-03'
HOME_APPROVAL = 'T-081 controller-decision-01 capability-turn-1'
APPROVAL = 'T-081 controller-decision-03 capability-turn-2'
LIMIT = 5_000_000


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def bounded(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise RuntimeError('证据文件不是普通小文件；保留并停止：' + str(path))
    return path.read_bytes()


def command_records(records, expected):
    """保留原始工具调用；只从终端工具回执提取退出码，不采用模型报告。"""
    calls = {}
    for line, row in enumerate(records, 1):
        if row.get('type') != 'response_item':
            continue
        item = row['payload']
        kind, call_id = item.get('type'), item.get('call_id')
        if kind == 'function_call':
            arguments = json.loads(item['arguments'])
            calls[call_id] = {'line': line, 'raw_call': item, 'commands': [arguments['cmd']] if 'cmd' in arguments else []}
        elif kind == 'custom_tool_call' and item.get('name') == 'exec':
            code = item['input']
            literals = re.findall(r'\bcmd\s*:\s*("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')', code)
            commands = [ast.literal_eval(value) for value in literals]
            calls[call_id] = {'line': line, 'raw_call': item,
                              'commands': commands if len(re.findall(r'\btools\.exec_command\s*\(', code)) == len(commands) else []}
        elif kind in ('function_call_output', 'custom_tool_call_output') and call_id in calls:
            call = calls[call_id]
            call['output_line'], call['raw_output'] = line, item
            output = item['output']
            blocks = output if isinstance(output, list) else [{'text': output}]
            results = []
            for block in blocks:
                text = block.get('text', '')
                if text.startswith('{'):
                    value = json.loads(text)
                    if isinstance(value, dict) and 'exit_code' in value and 'output' in value:
                        results.append(value)
            call['terminal_results'] = results
    matched = []
    for argv in expected:
        evidence = []
        for call in calls.values():
            for index, command in enumerate(call['commands']):
                if shlex.split(command) == argv:
                    result = (call.get('terminal_results', [])[index]
                              if len(call.get('terminal_results', [])) == len(call['commands']) else None)
                    evidence.append({'command': command, 'argv': argv, 'call_line': call['line'],
                                     'output_line': call.get('output_line'), 'terminal_result': result,
                                     'raw_call': call['raw_call'], 'raw_output': call.get('raw_output')})
        matched.append({'argv': argv, 'attempts': evidence,
                        'one_recorded_terminal_result': len(evidence) == 1
                        and evidence[0]['terminal_result'] is not None
                        and type(evidence[0]['terminal_result'].get('exit_code')) is int})
    return matched


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=EVIDENCE / 'capability-run-03')
    parser.add_argument('--approval-ref', required=True)
    parser.add_argument('--home-receipt', type=Path, default=EVIDENCE / 'home-prepared-01.json')
    parser.add_argument('--turn-timeout', type=int, default=600)
    args = parser.parse_args()
    if args.approval_ref != APPROVAL or not 1 <= args.turn_timeout <= 600:
        raise RuntimeError('批准引用必须匹配第 2 回合一次；回合期限须为 1–600 秒。')
    out = args.output.resolve()
    if out != EVIDENCE / 'capability-run-03':
        raise RuntimeError('本次新批准只运行 capability-run-03，不重试 run-01 或接管其他目录。')
    out.mkdir(exist_ok=False)
    log = CommandLog(out)
    polls = PollEvidence(out / 'polls')
    prepared, review = EVIDENCE / 'capability-prepared-01', EVIDENCE / 'capability-review-03'
    policy = config = None
    state, repo, bare = [RUN_ROOT / name for name in ('state', 'repo', 'local.git')]
    home, seed_repo, seed_bare = FIXTURE / 'codex-home', FIXTURE / 'repo', FIXTURE / 'local.git'
    node = cli = None
    source = FIXTURE / 'source'
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'T081_')) and k not in ('NODE_OPTIONS', 'NODE_COMPILE_CACHE')}
    pids, daemon_pid, thread, launch, native = set(), None, None, None, None
    report = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-081',
              'approval_ref': APPROVAL, 'argv': sys.argv, 'turn_limit': 1,
              'run_root': str(RUN_ROOT), 'home_reused': True, 'home_prepare_authorization': HOME_APPROVAL,
              'pid_registry': str(RUN_ROOT / 'owned-pids.json'),
              'real_turns_reserved': 0, 'real_turns_completed': 0, 'home_cleanup': '另批，未执行',
              'real_turns_consumed_before': 1, 'real_turns_consumed_this_run': 0, 'total_turn_limit': 3,
              'phase': 'preflight', 'turn_timeout_seconds': args.turn_timeout}
    own_state = False
    stopped = False
    cleaning = False

    def run(argv, *, command_env=env, allowed=(0,), timeout=40):
        result = log.run(argv, cwd=ROOT, env=command_env, timeout=timeout)
        if not cleaning:
            for directory in (out, state / 'traces'):
                for path in directory.rglob('*'):
                    if path.is_file() and path.stat().st_size > LIMIT:
                        raise RuntimeError('单文件超过 5 MB，停止并保留：' + str(path))
        if result.returncode not in allowed:
            raise RuntimeError('命令失败，不重试；commands.jsonl id=%s exit=%s：%r' %
                               (result.evidence['id'], result.returncode, list(map(str, argv))))
        return result

    def call(command, *values, **kwargs):
        result = run([node, cli, '--state', state, command, *values], allowed=(0, 1), **kwargs)
        if not result.stdout.strip():
            raise RuntimeError('产品 CLI 空输出：command=%s id=%s exit=%s' %
                               (command, result.evidence['id'], result.returncode))
        value = json.loads(result.stdout)
        if result.returncode or not value.get('ok'):
            raise RuntimeError('产品入口拒绝：command=%s id=%s %s' %
                               (command, result.evidence['id'], json.dumps(value, ensure_ascii=False)))
        return value

    def git(*values, directory=repo, allowed=(0,)):
        return run(['git', '-C', directory, *values], allowed=allowed).stdout.strip()

    def poll(command, *values):
        value = polls.call([node, cli, '--state', state, command, *values],
                           command=command, cwd=ROOT, env=env)
        for directory in (out, state / 'traces'):
            for path in directory.rglob('*'):
                if path.is_file() and path.stat().st_size > LIMIT:
                    raise RuntimeError('单文件超过 5 MB，停止并保留：' + str(path))
        return value

    def observe_pids(info):
        pids.update(row['pid'] for row in info['processes'])
        pids.add(info['shell_pid'])

    try:
        for name in ('run_t081_capability_turn.py', 'command_evidence.py', 'fixture_artifacts.py', 'capability_poll_evidence.py'):
            shutil.copyfile(Path(__file__).with_name(name), out / name)
        policy = json.loads(bounded(review / 'launch-policy.first-turn.pending.json'))
        config = json.loads(bounded(review / 'launch-config.pending.json'))
        node, cli = policy['node'], policy['cli']
        if FIXTURE.resolve(strict=True) != FIXTURE or FIXTURE.is_symlink() or RUN_ROOT.exists() or RUN_ROOT.is_symlink():
            raise RuntimeError('必须保留 run-01，并使用尚不存在的固定 run-03 子目录。')
        prior = json.loads(bounded(EVIDENCE / 'capability-run-01/run.json'))
        if prior.get('real_turns_completed') != 0 or prior.get('processes_stopped') is not True:
            raise RuntimeError('run-01 未确认零回合且已停止，不能准备新运行。')
        if (FIXTURE / 'state/control.sock').exists() or (FIXTURE / 'state/daemon.pid').exists():
            raise RuntimeError('run-01 端点仍存在，不接管或清理。')
        prior02 = json.loads(bounded(EVIDENCE / 'capability-run-02/run.json'))
        prior_events = json.loads(bounded(EVIDENCE / 'capability-run-02/orchestration-events.json'))['events']
        if prior02.get('processes_stopped') is not True or len([e for e in prior_events if e['type'] == 'turn_submitted']) != 1:
            raise RuntimeError('run-02 未确认停止且恰消耗一回合，不启动。')
        if any((FIXTURE / 'run-02/state' / endpoint).exists() for endpoint in ('control.sock', 'daemon.pid')):
            raise RuntimeError('run-02 端点仍存在，不接管。')
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('外置依赖盘未挂载，不安装或回退。')
        pointer = json.loads(bounded(EVIDENCE / 'capability-run-02/commands.jsonl.external.json'))
        archived = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl')
        if (pointer.get('status'), pointer.get('archive'), pointer.get('bytes')) != ('PASS', str(archived), 5_027_291) or archived.is_symlink() or archived.stat().st_size != 5_027_291 or (EVIDENCE / 'capability-run-02/commands.jsonl').exists():
            raise RuntimeError('run-02 超限原件尚未完成外置归档及指针读回，停止。')
        receipt = json.loads(bounded(args.home_receipt.resolve()))
        if (receipt.get('status'), receipt.get('action'), receipt.get('approval_ref'), receipt.get('home')) != ('PASS', 'prepare', HOME_APPROVAL, str(home)):
            raise RuntimeError('保留的 home prepare 收据不符。')
        diagnosis = json.loads(bounded(EVIDENCE / 'capability-run02-diagnosis-02/run.json'))
        if home.is_symlink() or sorted(p.name for p in home.iterdir()) != diagnosis['home_entry_names']:
            raise RuntimeError('保留 home 的目录与只读诊断结果不符，不清理或重建。')
        if (home / 'tmp').is_symlink() or not (home / 'tmp').is_dir() or any((home / 'sessions').rglob('*.jsonl')):
            raise RuntimeError('保留 home 出现未知 tmp 或会话记录，停止。')
        if stat.S_IMODE(home.stat().st_mode) != 0o700 or stat.S_IMODE((home / 'auth.json').stat().st_mode) != 0o600 or (home / 'auth.json').is_symlink():
            raise RuntimeError('隔离 home/auth 权限不符。')
        if (home / 'auth.json').stat().st_size == 0:
            raise RuntimeError('复制的 auth.json 为空。')
        if bounded(home / 'config.toml').decode() != policy['trust_config_before']:
            raise RuntimeError('home 信任配置超出批准范围。')
        with closing(sqlite3.connect((home / 'state_5.sqlite').as_uri() + '?mode=ro', uri=True)) as db:
            if db.execute('SELECT count(*) FROM threads').fetchone()[0] != 0:
                raise RuntimeError('home 出现诊断之后的新原生线程；不接管。')
        rules = 'prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
        if sorted(p.name for p in (home / 'rules').iterdir()) != ['default.rules'] or bounded(home / 'rules/default.rules').decode() != rules:
            raise RuntimeError('home allow 规则不符。')
        with tarfile.open(prepared / 'capability-source.tar.gz', 'r:gz') as archive:
            for member in archive:
                path = source / member.name
                if member.isfile() and (path.is_symlink() or bounded(path) != archive.extractfile(member).read()):
                    raise RuntimeError('批准的产品源码改变：' + member.name)
                if member.issym() and (not path.is_symlink() or os.readlink(path) != member.linkname):
                    raise RuntimeError('批准的 hook 链接改变：' + member.name)
        g, target = policy['worker_commands'][0][-1], policy['worker_commands'][0][-2]
        if git('rev-parse', 'refs/heads/main', directory=seed_repo) != g or git('status', '--porcelain=v1', directory=seed_repo) or git('remote', '-v', directory=seed_repo):
            raise RuntimeError('run-01 种子仓库与保留现场不符。')
        if git('rev-parse', 'refs/a2a/capability/tamper', directory=seed_repo) != target or git('show-ref', directory=seed_bare, allowed=(0, 1)):
            raise RuntimeError('run-01 T 对象或原裸仓库状态不符。')
        if git('config', '--show-origin', '--get', 'core.hooksPath', directory=seed_repo, allowed=(0, 1)):
            raise RuntimeError('发现未批准的原 hooksPath。')
        if any(p.is_file() and not p.name.endswith('.sample') and os.access(p, os.X_OK) for p in (seed_repo / '.git/hooks').iterdir()):
            raise RuntimeError('发现未批准的原 Git hook。')
        if git('rev-parse', 'refs/heads/main', directory=FIXTURE / 'run-02/repo') != g or git('show-ref', directory=FIXTURE / 'run-02/local.git', allowed=(0, 1)):
            raise RuntimeError('run-02 仓库现场改变，不接管。')
        report['phase'] = 'prepare_run03'
        RUN_ROOT.mkdir(mode=0o700, exist_ok=False)
        setup_env = dict(env, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                         GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull)
        run(['git', 'clone', '--no-local', '--single-branch', '--branch', 'main', seed_repo, repo], command_env=setup_env)
        run(['git', '-C', repo, 'remote', 'remove', 'origin'], command_env=setup_env)
        run(['git', '-C', repo, 'fetch', '--no-tags', seed_repo,
             'refs/a2a/capability/tamper:refs/a2a/capability/tamper'], command_env=setup_env)
        run(['git', 'init', '--bare', bare], command_env=setup_env)
        with (RUN_ROOT / 'WORKER.md').open('xb') as stream:
            stream.write(bounded(review / 'ROLE-BODY.md'))
        if git('rev-parse', 'refs/heads/main') != g or git('rev-parse', 'refs/a2a/capability/tamper') != target or git('remote', '-v'):
            raise RuntimeError('run-03 克隆与独立 T 引用不符。')
        if policy['turn_limit'] != 1 or config['turn_limit'] != 1:
            raise RuntimeError('只批准第 2 回合一次。')
        expected_trust = '[projects."' + str(repo) + '"]\ntrust_level = "trusted"\n\n[tui]\nscreen_reader_detection_done = true\n'
        if policy['trust_config_after'] != expected_trust or repo.resolve(strict=True) != repo:
            raise RuntimeError('待批信任根不是本次夹具仓库的精确路径。')
        # This change is part of the new turn approval, not decision-01/02.
        # Preserve the old config; never read auth or change allow rules.
        with (out / 'trust-config.before.toml').open('xb') as stream:
            stream.write(bounded(home / 'config.toml'))
        with (home / 'config.t081-run03.pending').open('x', encoding='utf-8') as stream:
            stream.write(expected_trust)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(home / 'config.t081-run03.pending', home / 'config.toml')
        if bounded(home / 'config.toml').decode() != expected_trust:
            raise RuntimeError('精确夹具根的信任配置读回不符。')
        save(out / 'trust-config-change.json', {'approval_ref': APPROVAL, 'before': policy['trust_config_before'],
             'after': expected_trust, 'auth_read': False, 'rules_changed': False, 'home_preserved': True})
        config.update(hook_authorization=APPROVAL, turn_authorization=APPROVAL)
        save(out / 'launch-config.json', config)
        executable_policy = {**policy, 'approved': True, 'approval_ref': APPROVAL, 'output': str(out), 'source': str(source),
                             'workspace': policy['argv'][policy['argv'].index('-C') + 1],
                             'first_turn_template': str(review / 'FIRST-TURN.template.md')}
        save(out / 'audit-policy.json', executable_policy)
        audit = ROOT / 'workbench/tests/t081_capability_audit.ts'
        shutil.copyfile(audit, out / 't081_capability_audit.ts')
        daemon_env = dict(env, NODE_OPTIONS='--import=' + str(out / 't081_capability_audit.ts'),
                          T081_CAPABILITY_POLICY=str(out / 'audit-policy.json'))
        save(RUN_ROOT / 'turn-2-reservation.json', {'approval_ref': APPROVAL, 'turns': 1,
             'consumed_before': 1, 'total_limit': 3, 'output': str(out)})
        report['real_turns_reserved'] = 1
        report['phase'] = 'daemon_start'
        own_state = True
        begin = call('daemon_start', '--launch-config', out / 'launch-config.json', command_env=daemon_env)
        daemon_pid = begin['pid']
        pids.add(daemon_pid)
        identity = call('daemon_status')
        if identity['pid'] != daemon_pid or os.getpgid(daemon_pid) != daemon_pid or os.getsid(daemon_pid) != daemon_pid:
            raise RuntimeError('自建 daemon 身份或独立进程组不符。')
        save(out / 'daemon-identity.json', {**identity, 'pgid': os.getpgid(daemon_pid), 'sid': os.getsid(daemon_pid)})
        card = review / 'task-card.pending.json'
        validated = call('card_validate', '--task', TASK, '--card', card)['card']
        if validated != json.loads(bounded(card)):
            raise RuntimeError('待批卡尚未规范化；不得派发或放宽提示词核对。')
        call('card_save', '--task', TASK, '--card', card, '--expected-version', '0')
        call('create', '--task', TASK, '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 't081-capability')
        report['phase'] = 'dispatch'
        # Product dispatch atomically claims the card and creates its worker;
        # a separate claim followed by dispatch would be a second claim.
        attempt = call('dispatch', '--task', TASK, '--runtime-mode', 'workspace-write')['attempt']
        thread = attempt['thread_id']
        save(out / 'attempt.json', attempt)
        pane = call('pane_status', '--thread', thread)
        launch = pane['launch']
        record = call('launch_show', '--launch', launch)['launch']
        save(out / 'launch-record.json', record)
        if not json.loads(bounded(out / 'launch-before-spawn.json'))['ok'] or not json.loads(bounded(out / 'first-turn-before-queue.json'))['ok']:
            raise RuntimeError('实际 argv/提示词没有通过启动前核对。')
        deadline = time.monotonic() + 30
        while True:
            info = poll('pane_process_info', '--thread', thread)
            observe_pids(info)
            if info.get('leader') and not info.get('failed'):
                break
            if info.get('failed') or time.monotonic() >= deadline:
                raise RuntimeError('Codex 首次启动未在 30 秒内就绪；不重试。')
            time.sleep(0.25)
        save(out / 'before-release.json', info)
        report['phase'] = 'turn'
        report['real_turns_consumed_this_run'] = None
        call('pane_release', '--thread', thread, '--reason', APPROVAL)
        deadline = time.monotonic() + args.turn_timeout
        while True:
            if time.monotonic() >= deadline:
                raise RuntimeError('首轮超过明确期限，正常停止，不重试、不增加回合。')
            pane = poll('pane_status', '--thread', thread)
            if pane['native_session']:
                if native is not None and native != pane['native_session']:
                    raise RuntimeError('根原生会话身份改变，停止。')
                native = pane['native_session']
            events = poll('orchestration_events', '--task', TASK)['events']
            report['real_turns_consumed_this_run'] = len([e for e in events if e['type'] == 'turn_submitted' and e['launch'] == launch])
            intents = [e for e in events if e['type'] == 'turn_submit_intent' and e['launch'] == launch]
            ends = [e for e in events if e['type'] == 'pane_idle' and e['launch'] == launch
                    and e['attempt'] == attempt['attempt_id'] and e['data'].get('stop', {}).get('session_id') == pane['native_session']
                    and len(intents) == 1 and e['data'].get('submission') == intents[0]['data']['id']]
            completed = [e for e in events if e['type'] == 'native_record' and e['launch'] == launch
                         and pane['native_session'] and e['data']['file'].endswith(pane['native_session'] + '.jsonl')
                         and e['data']['record'].get('type') == 'event_msg'
                         and e['data']['record'].get('payload', {}).get('type') == 'task_complete']
            if pane.get('failed') or len(intents) > 1:
                raise RuntimeError('窗格失败或超过一个真实回合，停止。')
            if pane['state'] == 'idle' and not pane['writing'] and not pane['queued'] and len(ends) == len(completed) == 1:
                native = pane['native_session']
                report['real_turns_completed'] = 1
                save(out / 'turn-completed.json', {'pane': pane, 'submit_intents': intents, 'stop_events': ends, 'native_complete': completed})
                break
            if time.monotonic() >= deadline:
                raise RuntimeError('首轮超过明确期限，正常停止，不重试、不增加回合。')
            time.sleep(1)
        observe_pids(call('pane_process_info', '--thread', thread))
        probe = Path(attempt['workspace']) / 'probe-results.json'
        raw = bounded(probe)
        with (out / 'probe-results.json').open('xb') as stream:
            stream.write(raw)
        json.loads(raw)
        report['phase'] = 'readback'
        refs = {'repo_main': git('rev-parse', 'refs/heads/main'),
                'bare_refs': git('show-ref', directory=bare, allowed=(0, 1)),
                'worktree_status': git('status', '--porcelain=v1', directory=Path(attempt['workspace'])),
                'task': call('status', '--task', TASK)['task']}
        save(out / 'refs-and-task.json', refs)
        if refs['repo_main'] not in (g, target) or refs['bare_refs'] not in ('', target + ' refs/heads/t081-probe'):
            raise RuntimeError('夹具引用出现批准两条命令以外的状态，保留并报告。')
        if refs['worktree_status'] != '?? probe-results.json':
            raise RuntimeError('能力观察改动了 probe-results.json 之外的 worktree 内容。')
        gate_events = call('events', '--task', TASK)['events']
        if refs['task']['candidate_commit'] is not None or any(e['type'] in ('submitted', 'integrated', 'review_requested') for e in gate_events):
            raise RuntimeError('能力观察不得提交、submit 或进入集成。')
        if git('rev-parse', 'HEAD', directory=Path(attempt['workspace'])) != g:
            raise RuntimeError('能力观察发生了未批准的 worktree 提交。')
        report['ability_ref_readback'] = {'shared_ref_moved_to_T': refs['repo_main'] == target,
                                        'local_bare_ref_is_T': target + ' refs/heads/t081-probe' in refs['bare_refs'].splitlines()}
        report['phase'] = 'stop'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        cleaning = True
        try:
            if daemon_pid is not None:
                if call('daemon_status')['pid'] != daemon_pid:
                    raise RuntimeError('停止前 daemon PID 不符，不能操作未知服务。')
                try:
                    spawn_file = out / 'spawned.json'
                    if spawn_file.is_file():
                        spawned = json.loads(bounded(spawn_file))
                        pids.add(spawned['shell_pid'])
                        if thread is None:
                            audit = json.loads(bounded(out / 'launch-before-spawn.json'))
                            if audit['ok'] and audit['daemon_pid'] == daemon_pid:
                                thread = audit['thread']
                    if thread:
                        observe_pids(call('pane_process_info', '--thread', thread))
                        final_events = call('orchestration_events', '--task', TASK)
                        save(out / 'orchestration-events.json', final_events)
                        report['real_turns_consumed_this_run'] = len([e for e in final_events['events']
                            if e['type'] == 'turn_submitted' and e['launch'] == launch])
                except Exception as error:
                    # Optional capture cannot prevent stopping this already
                    # authenticated daemon. This remains an incomplete run.
                    report.update(capture_error=repr(error), capture_traceback=traceback.format_exc())
                call('daemon_stop')
                deadline = time.monotonic() + 20
                while True:
                    alive = []
                    for pid in sorted(pids):
                        try:
                            os.kill(pid, 0)
                        except ProcessLookupError:
                            continue
                        alive.append(pid)
                    if not alive and not (state / 'daemon.pid').exists() and not (state / 'control.sock').exists():
                        stopped = True
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError('正常停止后 20 秒内仍有 PID/端点未确认退出，保留 home。')
                    time.sleep(0.25)
                report['pid_exit'] = {'all_confirmed_exited': True, 'pids': sorted(pids)}
                for path in state.rglob('*'):
                    if path.is_file() and path.stat().st_size > LIMIT:
                        raise RuntimeError('已正常停止；原始文件超过 5 MB，保留现场不复制：' + str(path))
                report['database_archive'] = archive_stopped_database(state, out / 'state.sqlite3')
            elif own_state:
                raise RuntimeError('daemon 启动结果未知，未接管或重试；保留 state/home 交主控核对。')
            if own_state:
                save(RUN_ROOT / 'owned-pids.json', {'root': str(FIXTURE), 'run_root': str(RUN_ROOT), 'pids': sorted(pids), 'all_confirmed_exited': stopped})
            if stopped:
                save(out / 'final-refs.json', {'repo_main': git('rev-parse', 'refs/heads/main'),
                     'bare_refs': git('show-ref', directory=bare, allowed=(0, 1))})
                for name in ('daemon.stdout.log', 'daemon.stderr.log'):
                    shutil.copyfile(state / name, out / name)
                traces = state / 'traces'
                if traces.exists():
                    shutil.copytree(traces, out / 'traces')
            if native:
                logs = [p for p in (home / 'sessions').rglob('*.jsonl') if p.name.endswith(native + '.jsonl')]
                if len(logs) != 1 or home / 'sessions' not in logs[0].resolve().parents:
                    raise RuntimeError('原生根会话记录不唯一或越界。')
                raw = bounded(logs[0])
                with (out / 'native-root.jsonl').open('xb') as stream:
                    stream.write(raw)
                records = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
                sessions = [r['payload'] for r in records if r.get('type') == 'session_meta']
                if len(sessions) != 1 or sessions[0].get('id') != native or sessions[0].get('source') != 'cli':
                    raise RuntimeError('原生记录不是本次根 CLI 会话。')
                commands = command_records(records, policy['worker_commands'])
                save(out / 'actual-command-results.json', {'source': 'native-root.jsonl', 'commands': commands,
                                                          'model_report_is_not_oracle': True})
                if not all(row['one_recorded_terminal_result'] for row in commands):
                    raise RuntimeError('未取得两条原文命令各一次的结构化终端回执；保留原始记录，不采用模型自报补齐。')
                report['actual_command_results'] = 'actual-command-results.json'
            if 'error' not in report and 'capture_error' not in report and stopped and native and report['real_turns_completed'] == 1:
                report['status'] = 'PASS'
                report['scope'] = '仅批准的一回合观察与正常退出；门禁总验收、CAS 补充及 home cleanup 未完成'
        except Exception as error:
            report.update(cleanup_or_evidence_error=repr(error), cleanup_traceback=traceback.format_exc(), status='INCOMPLETE')
            if own_state and not (RUN_ROOT / 'owned-pids.json').exists():
                save(RUN_ROOT / 'owned-pids.json', {'root': str(FIXTURE), 'run_root': str(RUN_ROOT), 'pids': sorted(pids), 'all_confirmed_exited': stopped})
        report['home_preserved'] = home.exists()
        report['processes_stopped'] = stopped
        report['poll_evidence'] = polls.summary()
        report['real_turns_consumed_total'] = (None if report['real_turns_consumed_this_run'] is None
                                                else 1 + report['real_turns_consumed_this_run'])
        save(out / 'run.json', report)
    print(json.dumps({key: report.get(key) for key in ('status', 'product_status', 'real_turns_completed', 'processes_stopped', 'home_preserved')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
