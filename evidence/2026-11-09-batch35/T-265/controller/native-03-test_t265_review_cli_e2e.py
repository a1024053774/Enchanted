"""T-265：主控外部运行的真实交互 Codex 材料投递探针。

真实 createReview/dispatch 生成输入，PTY 执行原生 Codex；不启动 Claude/额外 agent、
后台、hc 或 Electron，不操作正式实例。进程创建边界替换为夹具，原生 argv 在这里
显式给出；无 hook、无 MCP，不把该探针冒充 Stop/review_submit 门禁的端到端验收。
父版须在原生输入上限拒绝且没有开始回合；候选须开始回合，由 CLI 的沙箱工具执行
材料中的命令，完整读取 UTF-8 字节，读出头/中/尾随机标记，同时证明材料不能写。
默认依次运行父版与候选，一轮各一次；没有自动重试。--describe 不启动 CLI。
"""
import argparse
import errno
import json
import os
from pathlib import Path
import pty
import re
import select
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import fcntl
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASE = '80a6304225cdd567737362dd045dabf97a625c56'
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'

CAPTURE = r'''
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import { registerHooks } from 'node:module';
const m = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (m.parent_source) registerHooks({load(url, context, next) {
  const loaded = next(url, context);
  return url === pathToFileURL(m.source + '/workbench/src/panes.ts').href
    ? {...loaded, source: fs.readFileSync(m.parent_source, 'utf8')} : loaded;
}});
const {Panes} = await import(pathToFileURL(m.source + '/workbench/src/panes.ts'));
const pane = {record: {id: m.launch, role: 'reviewer', cli: 'Codex', request_dir: m.requests,
  role_text: m.role}, queue: [], failed: null, stopped: false};
const host = {config: {reviewer_role_card: 'fixture', reviewer_role_card_revision: 'T265'},
  async createPane() {}, get() {return pane;}, parentLaunch: {getStore() {}},
  store: {register: (launch, text) => ({launch, text}), event() {}},
  dispatch: Panes.prototype.dispatch, async drain(p) {
    if (p.queue.length !== 1) throw new Error('one dispatch required');
    fs.writeFileSync(m.entry, p.queue[0].text, {flag: 'wx', encoding: 'utf8'});
  }};
await Panes.prototype.createReview.call(host, {card: {executor: {cli: 'Codex'}}},
  {attempt: {}, session_id: m.session, thread_id: m.launch, candidate_workspace: m.candidate},
  fs.readFileSync(m.prompt, 'utf8'), {schema: 1, review_id: m.review, session: m.session});
'''

# Executed by the native CLI's tool, never by this host. Expected values are not
# passed to this program. O_WRONLY probes authorization without modifying evidence.
PROBE = r'''
import json, os, sys
from pathlib import Path
p = Path(sys.argv[1])
b = p.read_bytes()
s = b.decode('utf-8')
try:
    fd = os.open(p, os.O_WRONLY | os.O_APPEND)
except OSError as e:
    writable, write_error = False, e.errno
else:
    os.close(fd)
    writable, write_error = True, None
result = dict(bytes=len(b), characters=len(s),
              diff_rows=s.count('DIFF_ROW 中文🧭\n'),
              verification_rows=s.count('VERIFY_ROW café é\n'),
              markers=[line for line in s.splitlines() if line.startswith('SENTINEL_')],
              materials_writable=writable, write_error=write_error)
Path('native-read.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
'''


def argv_for(binary, candidate):
    return [binary, '--no-daemon', '--no-alt-screen', '-C', str(candidate), '-a', 'never',
            '--sandbox', 'workspace-write', '-m', 'gpt-6-astra',
            '-c', 'model_reasoning_effort="xhigh"', '-c', 'service_tier="default"',
            '-c', 'check_for_update_on_startup=false', '-c', 'notice.hide_rate_limit_model_nudge=true',
            '-c', 'sandbox_workspace_write.network_access=true',
            '-c', 'sandbox_workspace_write.writable_roots=[]',
            '-c', 'sandbox_workspace_write.exclude_slash_tmp=true',
            '-c', 'sandbox_workspace_write.exclude_tmpdir_env_var=true']


def save(path, data):
    with path.open('x', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2)
        out.write('\n')


def rollout(home):
    rows = []
    for path in (home / 'sessions').rglob('rollout-*.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # A writer's unfinished last line is not a completed event.
    return rows


def error_record(error):
    return dict(type=type(error).__name__, message=str(error), errno=getattr(error, 'errno', None),
                traceback=''.join(traceback.format_exception(type(error), error, error.__traceback__)))


def native_events(rows):
    return [row for row in rows if row.get('type') in ('session_meta', 'turn_context') or
            row.get('payload', {}).get('type') in ('task_started', 'task_complete', 'custom_tool_call',
                                                  'custom_tool_call_output', 'function_call', 'function_call_output')]


def stop_owned(child, diagnostic):
    if child is None:
        return dict(complete=True, reason='Popen did not return a child handle')
    if type(child.pid) is not int or child.pid <= 0 or child.pid != diagnostic.get('pid') or child.pid == os.getpid():
        raise RuntimeError('invalid owned child PID; no signal sent')
    # poll/wait use this Popen's waitpid handle. An exited child needs no signal.
    if child.poll() is not None:
        return dict(complete=True, reaped=True, exit_code=child.wait(timeout=0), signals=[])
    if diagnostic.get('pgid') != child.pid:
        raise RuntimeError('creation did not establish an owned process group; no signal sent')
    signals = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        pgid = os.getpgid(child.pid)
        if pgid != child.pid or pgid != diagnostic.get('pgid') or pgid == os.getpgrp():
            raise RuntimeError('owned child process group changed or unverified; no signal sent')
        diagnostic.setdefault('signal_attempts', []).append(dict(pid=child.pid, pgid=pgid, signal=int(sig)))
        os.killpg(pgid, sig)
        signals.append(int(sig))
        try:
            code = child.wait(timeout=3)
            return dict(complete=True, reaped=True, exit_code=code, signals=signals)
        except subprocess.TimeoutExpired:
            if sig == signal.SIGKILL:
                raise
    raise AssertionError('unreachable cleanup state')


def interact(argv, env, entry, home, timeout, parent, *, evidence, name, diagnostic):
    child = fd = slave = None
    primary = None
    diagnostic.update(pid=None, pgid=None, created=False, cleanup=dict(complete=False))

    def note(stage):
        diagnostic['stage'] = stage
        with (evidence / (name + '-process.jsonl')).open('a', encoding='utf-8') as out:
            out.write(json.dumps(dict(time=time.time(), **diagnostic), ensure_ascii=False) + '\n')

    raw, sent, pasted, submit_queued = bytearray(), False, False, False
    pending, paste_finished = b'', None
    pending_action, choice_at = None, None
    restricted_queued, native_ready = False, False
    diagnostic.update(restricted_choice_observed=False, restricted_key_written=False,
                      native_ready_observed=False, entry_paste_written=False, sent=False)
    last_output_at = time.monotonic()
    deadline = time.monotonic() + timeout
    terminal = (evidence / (name + '-terminal.txt')).open('xb')
    try:
        note('opening-pty')
        fd, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 45, 160, 0, 0))
        # Same native PTY creation as t141_probe_codex_start.py, with a Popen
        # handle so exec/setup errors cannot continue as a second Python driver.
        def control_terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        note('creating-child')
        child = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, env=env,
                                 preexec_fn=control_terminal)
        diagnostic.update(pid=child.pid, created=True)
        note('child-created')
        if type(child.pid) is not int or child.pid <= 0 or child.pid == os.getpid():
            raise RuntimeError('invalid child PID returned by Popen')
        diagnostic['creation_exit_code'] = child.poll()
        if diagnostic['creation_exit_code'] is None:
            diagnostic['pgid'] = os.getpgid(child.pid)
        note('child-identity-observed')
        os.close(slave); slave = None
        os.set_blocking(fd, False)
        note('reading-terminal')
        while time.monotonic() < deadline:
            readable, writable, _ = select.select([fd], [fd] if pending else [], [], .1)
            if writable:
                pending = pending[os.write(fd, pending[:16384]):]
                if not pending and pending_action:
                    if pending_action == 'restricted-key':
                        diagnostic['restricted_key_written'] = True
                        note('restricted-key-written')
                    elif pending_action == 'entry-paste':
                        diagnostic['entry_paste_written'] = True
                        note('entry-paste-written')
                    elif pending_action == 'entry-submit':
                        sent = diagnostic['sent'] = True
                        note('task-submitted')
                    pending_action = None
            if readable:
                try:
                    chunk = os.read(fd, 65536)
                except OSError as error:
                    if error.errno == errno.EIO:
                        break
                    raise
                if not chunk:
                    break
                raw.extend(chunk)
                terminal.write(chunk); terminal.flush()
                last_output_at = time.monotonic()
                for query, reply in [(b'\x1b[6n', b'\x1b[1;1R'),
                                     (b'\x1b]10;?', b'\x1b]10;rgb:ffff/ffff/ffff\x1b\\'),
                                     (b'\x1b]11;?', b'\x1b]11;rgb:0000/0000/0000\x1b\\')]:
                    if query in chunk:
                        pending += reply
            screen = raw.decode('utf-8', errors='replace')
            # Match the product's openCodexRestricted: strip ANSI/whitespace,
            # observe the selected restricted choice, wait for 800ms quiet (5s cap),
            # send one CR. A native ready packet, not the key, admits the task.
            if not native_ready:
                compact = re.sub(r'\s+', '', re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*?(?:\x07|\x1b\\)', '', screen))[-4096:]
                if 'Trustandcontinue' in compact:
                    raise RuntimeError('trust choice not answered')
                selected = '›1.Openrestricted' in compact and compact.rfind('›1.Openrestricted') == compact.rfind('›')
                if choice_at is None and selected:
                    choice_at = time.monotonic()
                    diagnostic['restricted_choice_observed'] = True
                    note('restricted-choice-observed')
                if re.search(r'\x1b\]7501;state=idle:app=codex(?:\x07|\x1b\\)', screen):
                    native_ready = diagnostic['native_ready_observed'] = True
                    note('native-ready-observed')
                elif selected and choice_at is not None and not restricted_queued and not pending and (
                        time.monotonic() - last_output_at >= .8 or time.monotonic() - choice_at >= 5):
                    pending = b'\r'
                    pending_action = 'restricted-key'
                    restricted_queued = True
                    note('restricted-key-queued')
            if not pasted and native_ready and not pending:
                # Bracketed paste, exactly the native interactive entry; never exec/headless.
                pending += b'\x1b[200~' + entry.encode('utf-8') + b'\x1b[201~'
                pending_action = 'entry-paste'
                pasted = True
                note('pasting-entry')
            if pasted and not pending and paste_finished is None:
                paste_finished = time.monotonic()
            if not submit_queued and paste_finished is not None and time.monotonic() - paste_finished >= .5:
                pending += b'\r'
                pending_action = 'entry-submit'
                submit_queued = True
                note('submit-queued')
            if sent:
                if parent and 'Message exceeds the maximum length of 1048576 characters' in screen:
                    break
                if not parent and any(row.get('type') == 'event_msg' and
                                      row.get('payload', {}).get('type') == 'task_complete' for row in rollout(home)):
                    break
        diagnostic.update(sent=sent, terminal_bytes=len(raw),
                          interaction_exit_code=child.poll(), deadline_reached=time.monotonic() >= deadline)
        note('interaction-ended')
        result = dict(sent=sent, terminal=raw.decode('utf-8', errors='replace'), rows=rollout(home))
    except BaseException as error:
        primary = error
        diagnostic['error_stage'] = diagnostic['stage']
        diagnostic['error'] = error_record(error)
        raise
    finally:
        # Preserve the original interaction and native facts before any signal.
        try:
            terminal.flush(); os.fsync(terminal.fileno())
            note('before-cleanup')
            save(evidence / (name + '-before-cleanup-native-events.json'), native_events(rollout(home)))
        except Exception as error:
            diagnostic.setdefault('diagnostic_errors', []).append(error_record(error))
        try:
            diagnostic['cleanup'] = stop_owned(child, diagnostic)
        except Exception as error:
            # EPERM is a failed cleanup, never ignored or followed by a different
            # signal/permission path. The caller retains the fixture for inspection.
            diagnostic['cleanup'] = dict(complete=False, error=error_record(error))
        for descriptor in (slave, fd):
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError as error:
                    diagnostic.setdefault('diagnostic_errors', []).append(error_record(error))
        try:
            terminal.close()
        except OSError as error:
            diagnostic.setdefault('diagnostic_errors', []).append(error_record(error))
        try:
            note('cleanup-finished')
            save(evidence / (name + '-native-events.json'), native_events(rollout(home)))
            save(evidence / (name + '-process.json'), diagnostic)
        except Exception as error:
            diagnostic.setdefault('diagnostic_errors', []).append(error_record(error))
        if primary is None and (not diagnostic['cleanup']['complete'] or diagnostic.get('diagnostic_errors')):
            raise RuntimeError('native cleanup/diagnostics incomplete; see process evidence')
    return result


def case(args, root, name, evidence, report):
    directory = root / name
    directory.mkdir()
    requests, candidate, home = [directory / part for part in ('requests', 'candidate', 'codex-home')]
    for path in (requests, candidate, home):
        path.mkdir(mode=0o700)
    # Like the gate's candidate copy, this directory has no .git metadata.
    (candidate / '.a2a-tmp').mkdir()
    probe = directory / 'probe.py'; probe.write_text(PROBE, encoding='utf-8')
    material = requests / 'review-materials.md'
    command = shlex.join(['/usr/bin/python3', str(probe), str(material)])
    role = ('这是 T-265 隔离材料读取验证，不做代码审查或交付。先读完材料，再执行这条核对命令：\n' + command +
            '\n命令读取全部字节并输出计数、随机标记和材料写权限。不要修改核对脚本，不重造输出，不申请权限，不调用其他 agent。运行后直接报告结果并结束。')
    markers = [f'SENTINEL_{position}_{uuid.uuid4().hex}' for position in ('HEAD', 'MIDDLE', 'TAIL')]
    prompt = (markers[0] + '\n任务卡：独立材料读取探针\n候选改动：\n' + 'DIFF_ROW 中文🧭\n' * 55000 +
              markers[1] + '\n机械验收：\n' + 'VERIFY_ROW café é\n' * 50000 +
              '\n上一轮问题清单：[]\n' + markers[2] + '\n提交方式：报告核对结果，结束本回合。')
    prompt_path = directory / 'prompt.txt'; prompt_path.write_text(prompt, encoding='utf-8')
    original = (role + '\n\n' + prompt).encode('utf-8')
    assert len(original.decode('utf-8')) > 1048576
    manifest = dict(source=str(ROOT), launch=str(uuid.uuid4()), session=str(uuid.uuid4()), review=str(uuid.uuid4()),
                    requests=str(requests), candidate=str(candidate), role=role, prompt=str(prompt_path),
                    entry=str(directory / 'entry.txt'))
    if name == 'parent':
        parent = directory / 'parent-panes.ts'
        parent.write_bytes(subprocess.check_output(['git', 'show', args.parent + ':workbench/src/panes.ts'], cwd=ROOT))
        manifest['parent_source'] = str(parent)
    save(directory / 'capture.json', manifest)
    capture = directory / 'capture.mjs'; capture.write_text(CAPTURE, encoding='utf-8')
    subprocess.run([args.node, str(capture), str(directory / 'capture.json')], check=True, timeout=30)
    entry = Path(manifest['entry']).read_text(encoding='utf-8')
    if name == 'candidate':
        assert len(entry) < 4096 and material.read_bytes() == original
    else:
        assert entry.encode('utf-8') == original
    # The only copied user file is auth.json; neither config nor hooks are copied.
    shutil.copy2(args.auth, home / 'auth.json')
    (home / 'config.toml').write_text('cli_auth_credentials_store = "file"\n' +
        f'[projects.{json.dumps(str(candidate))}]\ntrust_level = "untrusted"\n', encoding='utf-8')
    rules = home / 'rules'; rules.mkdir()
    (rules / 'default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                       'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding='utf-8')
    native_home = directory / 'home'; native_home.mkdir()
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL') if key in os.environ}
    env.update(HOME=str(native_home), CODEX_HOME=str(home), TERM='xterm-256color', SHELL='/bin/zsh',
               TMPDIR=str(candidate / '.a2a-tmp') + '/')
    argv = argv_for(args.codex, candidate)
    report.update(argv=argv, hooks=[], entry_characters=len(entry), material_bytes=len(original),
                  identity={key: manifest[key] for key in ('launch', 'review', 'session', 'requests')})
    save(evidence / (name + '-launch.json'), report)
    report['process'] = {}
    result = interact(argv, env, entry, home, args.timeout, name == 'parent', evidence=evidence, name=name,
                      diagnostic=report['process'])
    # Keep relevant native facts/tool results, not copied auth/config or huge prompt echoes.
    observed = native_events(result['rows'])
    types = [row.get('payload', {}).get('type') for row in result['rows'] if row.get('type') == 'event_msg']
    report.update(sent=result['sent'], native_started='task_started' in types, native_completed='task_complete' in types)
    if name == 'parent':
        report['rejected'] = 'Message exceeds the maximum length of 1048576 characters' in result['terminal']
        assert report['sent'] and report['rejected'] and not report['native_started'], report
    else:
        read = json.loads((candidate / 'native-read.json').read_text(encoding='utf-8'))
        report['read'] = read
        expected = dict(bytes=len(original), characters=len(original.decode('utf-8')), diff_rows=55000,
                        verification_rows=50000, markers=markers, materials_writable=False)
        assert report['sent'] and report['native_started'] and report['native_completed'], report
        assert {key: read[key] for key in expected} == expected, read
        assert read['write_error'] in (errno.EPERM, errno.EACCES), read
        assert material.read_bytes() == original
        assert any(str(probe) in json.dumps(row, ensure_ascii=False) for row in observed
                   if row.get('payload', {}).get('type') in ('custom_tool_call', 'function_call')), 'native tool did not execute probe'
    report['status'] = 'PASS'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--codex', default=shutil.which('codex'))
    parser.add_argument('--node', default=NODE)
    parser.add_argument('--auth', type=Path, default=Path.home() / '.codex/auth.json')
    parser.add_argument('--parent', default=BASE)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--describe', action='store_true')
    args = parser.parse_args()
    if args.describe:
        print(json.dumps(dict(argv=argv_for(args.codex or '<codex>', Path('<fixture>/candidate')),
                              hooks=[], scope=__doc__, cleanup='persist terminal/native events first; poll/reap Popen child; signal only its verified PGID; preserve failed fixture'), ensure_ascii=False, indent=2))
        return 0
    assert args.codex and args.summary and not args.summary.exists(), '需要真实 codex 与全新 summary 路径'
    args.codex = str(Path(args.codex).resolve())
    evidence = args.summary.parent / (args.summary.stem + '-artifacts')
    evidence.mkdir(parents=True, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='t265-cli-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', command=sys.argv, fixture=str(root), cases=[])
    try:
        report.update(code_revision=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                      native_version=subprocess.check_output([args.codex, '--version'], text=True).strip())
        for name in ('parent', 'candidate'):
            current = dict(name=name, status='INCOMPLETE')
            report['cases'].append(current)
            case(args, root, name, evidence, current)
        report['status'] = 'PASS'
    except BaseException as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        files = [path for path in root.rglob('*') if path.is_file()]
        report['cleanup'] = dict(directory=str(root), files=len(files), bytes=sum(path.stat().st_size for path in files),
                                 removed=False, result='尚未清理')
        save(evidence / 'before-fixture-cleanup.json', report)
        try:
            if report['status'] == 'PASS':
                shutil.rmtree(root)
                report['cleanup'].update(removed=not root.exists(), result='夹具已删除；原生文本证据保留')
            else:
                # With confirmed native exit, remove copied credentials but keep
                # the failed fixture. An unconfirmed child retains its home too.
                removed_homes = []
                for current in report['cases']:
                    if not current.get('process') or current['process'].get('cleanup', {}).get('complete'):
                        home = root / current['name'] / 'codex-home'
                        if home.exists():
                            shutil.rmtree(home); removed_homes.append(str(home))
                report['cleanup'].update(result='INCOMPLETE：保留失败夹具；未确认退出的子进程目录不删除',
                                         removed_codex_homes=removed_homes)
        except Exception as error:
            report['status'] = 'INCOMPLETE'
            report['cleanup'].update(result='INCOMPLETE：清理失败', error=error_record(error))
        save(args.summary, report)
    print(json.dumps(dict(status=report['status'], summary=str(args.summary)), ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
