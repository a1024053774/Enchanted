#!/usr/bin/env python3
"""T-091：主控在沙箱外执行的 8 秒预算对照；不运行 Electron。

运行（输出目录必须不存在，批准引用填写本轮值）：
  python3 -B evidence/2026-10-16-batch16/T-091/run_quality_timing.py \
    --source /Users/luckye/Documents/Code/a2a-wt-t091 \
    --output /Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-091/quality-timing-01 \
    --approval-ref '执行主控 T-091 #28：起点和候选各三正例、各三次、同为8秒'

固定比较 44bbb7828 与 3db9b6def，git archive 导出所需受控源码，不建
worktree、不初始化源码副本的 Git，不运行旧包装器的 Git 审计。只直接运行
各版本自己的原 unittest 方法和生命周期适配器。候选进程内移除唯一的
DaemonRun.run_args 覆盖，使两边都调用原 RunCLI.run_args；不改磁盘源码。
实际 run argv 和停机前事件都必须明确为 8 秒，否则数据不收作有效样本。

18 个单方法进程串行，按轮次交替起点/候选顺序，不预热、不重试。每次有
独立 HOME/TMP/state，真实 daemon/Git/门禁和受控 worker/reviewer；原方法
会在它自己新建的分页夹具内 commit、submit、verify、integrate、reclaim。
无供应商 CLI/模型/网络 API/真实登录/auth 副本，无 Electron、读屏或截图。
只读取现有 node_modules，经源码副本的链接使用；不安装依赖、不构建。

每方法总墙钟保护 180 秒（不是修改 run 的8秒期限）；stdout/stderr写外置
文件，合计8 MiB或夹具/报告合计256 MiB时中止。终端最多18条短进度和1条
最终摘要。中止只向本脚本创建的 Python 子进程发 SIGINT，使 finally 执行
原 doCleanups；最多再等90秒，不强杀或接管未知进程。每次核对已登记daemon/
CLI PID退出和临时凭据删除后，复制停止的夹具到外置盘，比较文件数/字节数/
链接目标，保留原目录。收尾不明立即停止后续运行，报告INCOMPLETE及路径。

summary.json 的 PASS 只指18份有效计时和收尾/归档完成，不是原正例全PASS。
原断言失败、异常、deadline、事件耗时及完整方法墙钟分别记录。deadline按
run_finished.outcome/error判，不按耗时>8猜测；事件区间不是完整方法耗时。
三个重复只提供本机此次样本，不自动作因果或可靠性结论。

纯检查：--self-check（只检查事件提取拒错；不启动daemon/CLI/ps）。
可信边界的失败包括：误用30秒、替换原方法、缺失/重复/串错run事件、把环境
错误算超时、把活进程或凭据归档、输出/墙钟失控。任何未知不得补称PASS。
"""
import argparse
import contextlib
import datetime
import inspect
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
import unittest

REVISIONS = {
    'baseline': '44bbb7828459d81fab0d46069a19d3dd515a7732',
    'candidate': '3db9b6def91826d5a52dd02590c559b0c4ce35a0',
}
METHODS = (
    'test_run_entry_point_completes_registered_task',
    'test_transient_tool_activity_keeps_same_thread_owner',
    'test_matching_reclaim_guard_is_idempotent_after_automatic_success',
)
SOURCE_PATHS = (
    'workbench/src', 'workbench/tests', 'acceptance', 'fixtures/pagination',
    '.project-map/specs', 'workbench/package.json', 'workbench/package-lock.json',
    'workbench/.npmrc',
)
VOLUME = Path('/Volumes/WD-Elements')
EXTERNAL = VOLUME / 'a2a-evidence/2026-10-16-batch16/T-091'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def timing(events, task):
    rows = []
    for row in events:
        if row.get('task') == task and row.get('type') in ('run_started', 'run_finished'):
            details = row['details']
            rows.append((row, json.loads(details) if isinstance(details, str) else details))
    starts = [(row, data) for row, data in rows if row['type'] == 'run_started']
    ends = [(row, data) for row, data in rows if row['type'] == 'run_finished']
    if len(starts) != 1 or len(ends) != 1:
        raise ValueError('需要恰好一对原任务run_started/run_finished')
    start, a = starts[0]
    end, b = ends[0]
    if not a.get('run_id') or a['run_id'] != b.get('run_id'):
        raise ValueError('run_id不一致')
    if a.get('task_id') != task or b.get('task_id') != task:
        raise ValueError('事件details的task不一致')
    if a.get('wait_seconds') != 8 or b.get('wait_seconds') != 8:
        raise ValueError('实际事件预算不是8秒')
    elapsed = (datetime.datetime.fromisoformat(end['time'].replace('Z', '+00:00')) -
               datetime.datetime.fromisoformat(start['time'].replace('Z', '+00:00'))).total_seconds()
    if elapsed < 0 or not b.get('outcome') or b['outcome'] == 'running':
        raise ValueError('结束事件或计时无效')
    deadline = b['outcome'] == 'deadline'
    if deadline != (b.get('error') == 'run_deadline'):
        raise ValueError('deadline与run_deadline不一致')
    return dict(run_id=a['run_id'], task=task, wait_seconds=8,
                run_event_elapsed_seconds=elapsed, timed_out=deadline,
                outcome=b['outcome'], phase=b.get('phase'), run_error=b.get('error'),
                start_event=start, finish_event=end)


def child(config_path):
    """只由父脚本创建；原方法、原清理及原断言保持不变。"""
    config = json.loads(Path(config_path).read_text(encoding='utf-8'))
    source, out = Path(config['source']), Path(config['output'])
    os.environ.update(COOP_E2E_ARTIFACT_ROOT=config['artifacts'],
                      COOP_E2E_READBACK_ROOT=str(out / 'readbacks'),
                      COOP_E2E_TRACE=str(out / 'subprocess-trace.json'))
    (out / 'readbacks').mkdir()
    sys.path.insert(0, str(source / 'workbench/tests'))
    record = dict(status='INCOMPLETE', method=config['method'], revision=config['revision'],
                  source=str(source), started=now(), artifacts=[], run_commands=[])
    case = adapter = result = None
    try:
        import daemon_acceptance_adapter as adapter
        cls, original = adapter.DaemonRun, adapter.orchestration.RunCLI
        if getattr(cls, config['method']) is not getattr(original, config['method']):
            raise RuntimeError('适配器替换了原业务方法')
        record['original_method_preserved'] = True
        own = cls.__dict__.get('run_args')
        record['removed_budget_override'] = inspect.getsource(own) if own else None
        if bool(own) != (config['variant'] == 'candidate'):
            raise RuntimeError('冻结版本的预算覆盖形状不符')
        if own:
            delattr(cls, 'run_args')
        if cls.run_args is not original.run_args:
            raise RuntimeError('未使用原始8秒helper')
        record['effective_run_args_source'] = inspect.getsource(cls.run_args)
        case = cls(config['method'])
        started = time.monotonic()
        result = unittest.TextTestRunner(verbosity=2,
            resultclass=adapter.orchestration.EvidenceResult).run(unittest.TestSuite([case]))
        record.update(method_wall_seconds=time.monotonic() - started,
                      tests_run=result.testsRun, failures=len(result.failures),
                      errors=len(result.errors), skipped=len(result.skipped),
                      original_test_status='PASS' if result.wasSuccessful() else 'INCOMPLETE',
                      failures_text=[{'test': test.id(), 'traceback': text} for test, text in result.failures],
                      errors_text=[{'test': test.id(), 'traceback': text} for test, text in result.errors])
        record['status'] = 'PASS'  # 方法执行记录完成；不把原失败上调PASS。
    except BaseException as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        # unittest正常路径已调用；中断时只运行剩余的原cleanup，不重跑业务。
        if case is not None:
            try:
                record['remaining_cleanups_ok'] = case.doCleanups()
            except BaseException as error:
                record['cleanup_error'] = repr(error)
                record['status'] = 'INCOMPLETE'
        if adapter is not None:
            record['artifacts'] = adapter.delivery.ARTIFACTS
            record['run_commands'] = [row for row in adapter.delivery.COMMANDS if row.get('label') == 'coop:run']
            save(out / 'original-observations.json', dict(commands=adapter.delivery.COMMANDS,
                assertions=adapter.recovery.ASSERTIONS, original_results=adapter.orchestration.TEST_RESULTS))
        record['finished'] = now()
        save(out / 'child.run.json', record)
    return 0 if record['status'] == 'PASS' else 2


def command(argv, *, cwd, env, timeout=30):
    p = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, text=True,
                       capture_output=True, timeout=timeout)
    if p.returncode or len(p.stdout) + len(p.stderr) > 1024 * 1024:
        raise RuntimeError(dict(argv=list(map(str, argv)), exit=p.returncode,
                                stdout=p.stdout[:2000], stderr=p.stderr[:2000]))
    return p.stdout


def inventory(root):
    """不跟随链接，不计算校验值。"""
    rows = []
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                target = os.readlink(path)
                rows.append((relative, 'link', len(os.fsencode(target)), target))
            elif path.is_file():
                rows.append((relative, 'file', path.stat().st_size, None))
            elif not path.is_dir():
                raise RuntimeError('夹具含非普通文件：' + str(path))
    return sorted(rows)


def live_bytes(root):
    # 仅用于运行中磁盘额度：文件可能被Git清理，socket不占普通文件字节。
    # 最终归档使用上面的严格inventory，不接受遗留socket或缺失文件。
    total = 0
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in files:
            try:
                info = (Path(parent) / name).lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                total += info.st_size
    return total


def prepare(source, output, env):
    versions = {tool: command([tool, '--version'], cwd=source, env=env)
                for tool in ('node', 'git')}
    if not versions['node'].strip().startswith('v26.5.'):
        raise RuntimeError('要求原回归使用的Node 26.5系列，不自动切换')
    deps = (source / 'workbench/node_modules').resolve(strict=True)
    copies = {}
    for variant, revision in REVISIONS.items():
        resolved = command(['git', 'rev-parse', revision + '^{commit}'], cwd=source, env=env).strip()
        if resolved != revision:
            raise RuntimeError('冻结revision不一致')
        archive = output / (variant + '.sources.tar')
        argv = ['git', 'archive', '--format=tar', revision, '--', *SOURCE_PATHS]
        with archive.open('xb') as stream, (output / (variant + '.archive.stderr')).open('xb') as err:
            subprocess.run(argv, cwd=source, env=env, stdout=stream, stderr=err, check=True, timeout=60)
        copy = output / (variant + '-source')
        copy.mkdir()
        with tarfile.open(archive) as tar:
            for entry in tar.getmembers():
                if (Path(entry.name).is_absolute() or '..' in Path(entry.name).parts or
                        not (entry.isdir() or entry.isfile())):
                    raise RuntimeError('git archive含不允许的条目：' + entry.name)
            tar.extractall(copy)
        (copy / 'workbench/node_modules').symlink_to(deps, target_is_directory=True)
        copies[variant] = copy
        save(output / (variant + '.source.json'), dict(revision=revision, git_archive_argv=argv,
            paths=SOURCE_PATHS, source=str(copy), archive=str(archive), git_worktree_created=False,
            dependency_link=str(deps), source_git_initialized=False))
    for path in ('acceptance/test_run_e2e.py', 'acceptance/test_coop_e2e.py',
                 'acceptance/test_recovery_e2e.py', 'workbench/package-lock.json'):
        if (copies['baseline'] / path).read_bytes() != (copies['candidate'] / path).read_bytes():
            raise RuntimeError('比较两边的原测试或依赖锁不同：' + path)
    if (source / 'workbench/package-lock.json').read_bytes() != (copies['baseline'] / 'workbench/package-lock.json').read_bytes():
        raise RuntimeError('现有依赖对应的锁文件不同')
    save(output / 'environment.json', dict(versions=versions, python=sys.version,
        executable=sys.executable, dependency_link=str(deps), environment=env,
        screen_reads=0, electron_starts=0, vendor_cli_starts=0, supplier_model_turns=0))
    return copies


def absent(pid):
    p = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                       text=True, capture_output=True, timeout=5)
    return dict(pid=pid, argv=p.args, exit=p.returncode, stdout=p.stdout, stderr=p.stderr,
                absent=p.returncode == 1 and not p.stdout.strip() and not p.stderr.strip())


def sample(script, source, variant, method, repeat, output, env):
    short = Path(tempfile.mkdtemp(prefix='t091-t-', dir='/private/tmp')).resolve()
    for name in ('h', 't', 'f'):
        (short / name).mkdir()
    local_env = dict(env, HOME=str(short / 'h'), TMPDIR=str(short / 't'))
    config = dict(source=str(source), variant=variant, revision=REVISIONS[variant],
                  method=method, output=str(output), artifacts=str(short / 'f'))
    save(output / 'config.json', config)
    rec = dict(status='INCOMPLETE', variant=variant, revision=REVISIONS[variant], method=method,
               repeat=repeat, started=now(), fixture=str(short), cleanup_complete=False,
               archive_complete=False, timed_out=None, run_event_elapsed_seconds=None)
    process = None
    try:
        stdout, stderr = output / 'child.stdout.txt', output / 'child.stderr.txt'
        with stdout.open('xb') as out, stderr.open('xb') as err:
            argv = [sys.executable, '-B', str(script), '--child', str(output / 'config.json')]
            rec['argv'] = argv
            process = subprocess.Popen(argv, cwd=source, env=local_env, stdout=out, stderr=err,
                                       start_new_session=True)
            rec['child_pid'] = process.pid
            save(output / 'child-launch.json', dict(argv=argv, pid=process.pid, cwd=str(source),
                started=now(), environment=local_env, owns_new_session=True))
            deadline = time.monotonic() + 180
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    raise RuntimeError('单方法总墙钟保护到期；不是run的8秒deadline')
                if stdout.stat().st_size + stderr.stat().st_size > 8 * 1024 * 1024:
                    raise RuntimeError('单方法stdout/stderr超过8MiB')
                if live_bytes(short) + live_bytes(output) > 256 * 1024 * 1024:
                    raise RuntimeError('单方法夹具/报告超过256MiB')
                time.sleep(1)
            rec['child_exit'] = process.returncode
    except (Exception, KeyboardInterrupt) as error:
        rec.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if process is not None and process.poll() is None:
            # Popen身份属于本脚本；只中断它，不发进程组信号或SIGKILL。
            process.send_signal(signal.SIGINT)
            rec['cleanup_interrupt'] = dict(pid=process.pid, signal='SIGINT', at=now())
            try:
                process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                rec['cleanup_error'] = '原cleanup在90秒内未完成；停止后续运行，交主控核对'
        rec['child_exit'] = None if process is None else process.poll()
        # 只有Python退出后才读取最终状态，不重开停止后的WAL库。
        if process is not None and process.poll() is not None:
            try:
                child_record = json.loads((output / 'child.run.json').read_text(encoding='utf-8'))
                artifacts = child_record['artifacts']
                pids = {d['pid'] for a in artifacts for d in a.get('daemons', []) if d.get('pid')}
                # launch原件覆盖异步CLI；daemon生命周期文件覆盖部分启动失败。
                for path in (short / 'f').rglob('*.launch.json'):
                    row = json.loads(path.read_text(encoding='utf-8'))
                    if row.get('pid'):
                        pids.add(row['pid'])
                for path in (short / 'f').rglob('daemon-lifecycle.jsonl'):
                    for line in path.read_text(encoding='utf-8').splitlines():
                        row = json.loads(line)
                        if row.get('event') == 'test_host_launched':
                            pids.add(row['pid'])
                observations = [absent(pid) for pid in sorted(pids)]
                save(output / 'exit-observations.json', observations)
                if not all(row['absent'] for row in observations):
                    raise RuntimeError('登记的daemon/CLI退出未确认；不归档活夹具')
                if (list(short.rglob('operator-*.credential.json')) or
                        list(short.rglob('daemon.pid')) or list(short.rglob('control.sock'))):
                    raise RuntimeError('原cleanup遗留临时凭据、daemon.pid或socket；不继续')
                rec['cleanup_complete'] = True
                # 先保存停止后夹具。即使事件或原测试结果不完整，也保留现场。
                before = inventory(short)
                destination = output / 'fixture'
                shutil.copytree(short, destination, symlinks=True)
                after = inventory(destination)
                save(output / 'fixture.archive.json', dict(original=str(short), archive=str(destination),
                    files=len(before), bytes=sum(row[2] for row in before), comparison=before == after,
                    original_retained=True, symlink_policy='保留链接本身，不跟随目标',
                    replay='使用同一脚本及新输出目录；源码tar与启动argv在本轮输出中'))
                if before != after:
                    raise RuntimeError('停止后夹具副本文件数/字节数/链接目标不符')
                rec['archive_complete'] = True
                if child_record['status'] != 'PASS' or child_record['tests_run'] != 1 or child_record['skipped']:
                    raise RuntimeError('原方法执行记录不完整；见child.run.json')
                if len(artifacts) != 1:
                    raise RuntimeError('需要一个原方法夹具')
                artifact = artifacts[0]
                readback = Path(artifact['state_readback'])
                snapshot = json.loads(readback.read_text(encoding='utf-8'))
                if snapshot['test'] != artifact['test'] or snapshot['database'] != str(Path(artifact['state'], 'state.sqlite3').resolve()):
                    raise RuntimeError('停机前读回不属于本夹具')
                runs = child_record['run_commands']
                if len(runs) != 1 or runs[0]['argv'].count('--wait-seconds') != 1:
                    raise RuntimeError('缺少唯一的实际run argv')
                argv = runs[0]['argv']
                if argv[argv.index('--wait-seconds') + 1] != '8':
                    raise RuntimeError('实际CLI预算不是8秒')
                rec.update(timing(snapshot['tables']['events'], artifact['task']),
                           actual_run_argv=argv, readback=str(readback),
                           original_test_status=child_record['original_test_status'],
                           tests_run=child_record['tests_run'], failures=child_record['failures'],
                           errors=child_record['errors'], skipped=child_record['skipped'],
                           method_wall_seconds=child_record['method_wall_seconds'])
                # 环境异常和非deadline的原断言失败不能作为有效对照PASS。
                if child_record['errors'] or (child_record['failures'] and not rec['timed_out']):
                    raise RuntimeError('原测试有异常或非deadline失败；计时仍保留，不上调PASS')
                if 'error' not in rec and rec['child_exit'] == 0:
                    rec['status'] = 'PASS'
            except Exception as error:
                rec.update(collection_error=repr(error), collection_traceback=traceback.format_exc())
        rec['finished'] = now()
        save(output / 'sample.json', rec)
    return rec


def run(args):
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if not os.path.ismount(VOLUME) or not output.is_relative_to(EXTERNAL.resolve()) or output == EXTERNAL.resolve():
        raise RuntimeError('需要挂载的T-091外置新输出目录')
    output.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    frozen_script = output / script.name
    shutil.copyfile(script, frozen_script)
    script = frozen_script
    isolation = Path(tempfile.mkdtemp(prefix='t091-t-pre-', dir='/private/tmp')).resolve()
    (isolation / 'h').mkdir(); (isolation / 't').mkdir()
    env = {key: os.environ[key] for key in ('PATH', 'USER', 'LOGNAME') if key in os.environ}
    env.update(HOME=str(isolation / 'h'), TMPDIR=str(isolation / 't'), LANG='en_US.UTF-8', LC_ALL='C',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0',
               PYTHONDONTWRITEBYTECODE='1')
    record = dict(status='INCOMPLETE', task='T-091', attempt='a1', approval_ref=args.approval_ref,
                  worker='s16-t091', ticket_ready_rev=1,
                  worker_launch='launch-71afbd1600cb451a9d9354aa7768e72b',
                  worker_session='d4277ace-1dde-425b-99b8-8988f1df751f',
                  worker_native_session='01a14a05-4472-70e1-af77-58414340c1ee',
                  started=now(), argv=sys.argv, revisions=REVISIONS, repeat_count=3, wait_seconds=8,
                  expected_samples=18, samples=[], electron_starts=0, screen_reads=0,
                  captures=0, vendor_cli_starts=0, supplier_model_turns=0,
                  new_codex_sessions=0, max_concurrent_sample_processes=1,
                  limitations=['三个重复为本机此次对照，不自动给出因果或可靠性结论。',
                               'PASS指计时收尾完成；原方法结果单列，deadline失败不补成原测试PASS。'])
    try:
        copies = prepare(source, output, env)
        ordinal = 0
        for repeat in range(1, 4):
            for method_index, method in enumerate(METHODS):
                order = ('baseline', 'candidate') if (repeat + method_index) % 2 else ('candidate', 'baseline')
                for variant in order:
                    ordinal += 1
                    child_out = output / ('%02d-%s-r%d-m%d' % (ordinal, variant, repeat, method_index + 1))
                    child_out.mkdir()
                    result = sample(script, copies[variant], variant, method, repeat, child_out, env)
                    record['samples'].append(result)
                    with (output / 'progress.jsonl').open('a', encoding='utf-8') as log:
                        log.write(json.dumps(result, ensure_ascii=False) + '\n')
                    print('%02d/18 %s r%d m%d %s deadline=%s event_seconds=%s' % (
                        ordinal, variant, repeat, method_index + 1, result['status'],
                        result['timed_out'], result['run_event_elapsed_seconds']), flush=True)
                    if (not result['cleanup_complete'] or not result['archive_complete'] or
                            'error' in result or result['timed_out'] is None):
                        raise RuntimeError('本次收尾/归档或执行保护失败，停止后续样本：' + str(child_out))
        record['comparison'] = [{
            'variant': variant, 'revision': REVISIONS[variant], 'method': method,
            'observations': len(rows), 'valid_measurements': sum(r['status'] == 'PASS' for r in rows),
            'deadline_count': sum(r['timed_out'] is True for r in rows),
            'event_seconds': [r['run_event_elapsed_seconds'] for r in rows],
            'original_test_statuses': [r.get('original_test_status', 'INCOMPLETE') for r in rows],
        } for variant in REVISIONS for method in METHODS
          for rows in [[r for r in record['samples'] if r['variant'] == variant and r['method'] == method]]]
        record['cleanup_complete'] = all(r['cleanup_complete'] for r in record['samples'])
        record['archive_complete'] = all(r['archive_complete'] for r in record['samples'])
        if len(record['samples']) == 18 and all(r['status'] == 'PASS' for r in record['samples']):
            record['status'] = 'PASS'
    except (Exception, KeyboardInterrupt) as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        # 预检环境没有后台进程；保留新HOME/TMP原件并把小副本归档。
        try:
            destination = output / 'preflight-environment'
            shutil.copytree(isolation, destination, symlinks=True)
            before, after = inventory(isolation), inventory(destination)
            save(output / 'preflight-environment.archive.json', dict(original=str(isolation),
                archive=str(destination), files=len(before), bytes=sum(r[2] for r in before),
                comparison=before == after, original_retained=True))
            if before != after:
                raise RuntimeError('预检环境副本不一致')
        except Exception as error:
            record.update(status='INCOMPLETE', archive_complete=False,
                          preflight_archive_error=repr(error))
        record.update(finished=now(), preflight_environment=str(isolation), originals_retained=True)
        record.setdefault('cleanup_complete', all(r['cleanup_complete'] for r in record['samples']))
        record.setdefault('archive_complete', False)
        save(output / 'summary.json', record)
        print(json.dumps(dict(status=record['status'], samples=len(record['samples']),
                              output=str(output), error=record.get('error')), ensure_ascii=False), flush=True)
    return 0 if record['status'] == 'PASS' else 1


def self_check():
    import copy
    rows = [dict(task='t', type='run_started', time='2026-10-17T00:00:00.000Z',
                 details=json.dumps(dict(task_id='t', run_id='r', wait_seconds=8))),
            dict(task='t', type='run_finished', time='2026-10-17T00:00:09.250Z',
                 details=json.dumps(dict(task_id='t', run_id='r', wait_seconds=8,
                                         outcome='deadline', error='run_deadline')))]
    assert timing(rows, 't')['timed_out'] is True
    assert timing(rows, 't')['run_event_elapsed_seconds'] == 9.25
    complete = copy.deepcopy(rows)
    complete[1]['time'] = '2026-10-17T00:00:06.000Z'
    complete[1]['details'] = json.dumps(dict(task_id='t', run_id='r', wait_seconds=8, outcome='completed'))
    assert timing(complete, 't')['timed_out'] is False
    assert timing(complete, 't')['run_event_elapsed_seconds'] == 6
    bad = [rows[:1], rows + rows[1:]]
    for field, value in (('wait_seconds', 30), ('run_id', 'other'), ('task_id', 'foreign'), ('error', 'other')):
        mutated = copy.deepcopy(rows)
        data = json.loads(mutated[1]['details']); data[field] = value
        mutated[1]['details'] = json.dumps(data); bad.append(mutated)
    for value in bad:
        try:
            timing(value, 't')
        except ValueError:
            pass
        else:
            raise AssertionError('无效事件/30秒输入未被拒绝')
    print('PASS：2个计时正例、6个缺失/重复/串身份/30秒/错误分类拒绝；未实跑。')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--approval-ref')
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--child', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        sys.exit(child(args.child))
    if args.self_check:
        sys.exit(self_check())
    if not args.output or not args.approval_ref:
        parser.error('需要--output和本轮--approval-ref')
    sys.exit(run(args))
