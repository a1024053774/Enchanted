"""T-244：hc 固定值改变时，仍在运行的 core 照样能起新终端；新固定值装进自己的目录，不沿用旧二进制。
真实后台、私有 hc core 与终端；不运行 CLI，不联网。

“新固定值”：把同一个官方包重新打包（文件相同、版本仍是 0.1.15、SHA-256 不同），放进另一个缓存目录，并在后台源码副本里
改掉固定值的 SHA-256。

失败方式（先列再写）：
1. 新固定值的后台把新版本写到 core 正在用的文件上（换了 inode），core 之后起的 holder 构建号对不上，新终端报 `no holder`。
2. 新固定值的后台沿用旧固定值的二进制。
3. 后台重启时换掉了 core（core 的 pid 变了），这个场景就没有测到“仍在运行的 core”。
4. 新终端交给了仍在运行的旧 holder，core 没有新起 holder，1 就测不到。一个 holder 托管多个终端，终端都退出后它仍常驻
   （本测试第一次运行实测），所以先让终端都退出，再结束这个空 holder（核对它是夹具里的进程），core 的下一个终端只能从文件
   新起 holder。

--revision 在该版本的隔离源码上跑（修前应失败于 1）。
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from scripted_claude import Fixture, hc_binary, source_tree  # noqa: E402

PIN = "  sha256: '47eba8367e0626a1efced8795fcb03d5434b2541c5a84d78c50cc02c8fb49fc8',"
ARCHIVE = 'herdr-core-0.1.15-macos-aarch64.tar.gz'
FILES = ['herdr-core', 'LICENSE', 'THIRD-PARTY-NOTICES']


def repacked(cache, target):
    """The pinned archive's files packed again: another digest for the same release."""
    work = target / 'unpacked'
    work.mkdir(parents=True)
    subprocess.run(['/usr/bin/tar', '-xzf', str(cache / ARCHIVE), '-C', str(work), *FILES], check=True)
    with tarfile.open(target / ARCHIVE, 'w:gz') as archive:
        for name in FILES:
            archive.add(work / name, arcname=name)
    shutil.rmtree(work)
    digest = hashlib.sha256((target / ARCHIVE).read_bytes()).hexdigest()
    assert digest != PIN.split("'")[1]
    return digest


def core_status(state, env, binary):
    identity = json.loads((state / 'hc-runtime.json').read_text(encoding='utf-8'))
    private = dict(env, HC_SESSION=identity['session'], HC_SOCKET=identity['socket'],
                   XDG_STATE_HOME=str(state / 'hc/state'), XDG_CONFIG_HOME=str(state / 'hc/config'))
    run = subprocess.run([str(binary), '--json', 'server', 'status'], env=private, capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stderr
    return json.loads(run.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    cache = Path(os.environ.get('ENCHANTED_HC_CACHE_DIR', str(ROOT.parent / 'hc-cache')))
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, checks=[])
    fixture = Fixture('t244-', [], revision=args.revision)
    report['fixture'] = str(fixture.dir)

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def terminal_works(label):
        launch = fixture.run_cli('shell_start', '--project', fixture.project, '--cwd', str(fixture.repo))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=fixture.project)
        assert window['ok'], window
        marker = fixture.out / f'{label}.txt'
        sent = fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- {label} > {marker}\r')
        assert sent['ok'], sent
        fixture.wait(f'{label} 终端执行命令', lambda: marker.exists() and marker.read_text().strip() == label, 30)
        return window['identity']

    try:
        fixture.start(shutil.which('claude') or str(Path.home() / '.local/bin/claude'), {'README.md': 'demo\n'})
        first = hc_binary(fixture.state)
        first_inode = first.stat().st_ino
        core = core_status(fixture.state, fixture.env, first)
        report.update(first_install=str(first), first_inode=first_inode, core=core)
        window = terminal_works('before')
        # 4: end every terminal so the core has no holder left; the next terminal makes it start one from the file.
        reopened = fixture.request('window_open', fixture.operator, launch=fixture.terminal_launch, project=fixture.project)
        for identity, sequence in ((window, 2), (reopened['identity'], 1)):  # each window counts its own inputs
            ended = fixture.request('window_input', identity, sequence=sequence, request_id=str(uuid.uuid4()), data='exit\r')
            assert ended['ok'], ended
        fixture.wait('终端都已退出', lambda: core_status(fixture.state, fixture.env, first)['live'] == 0, 30)
        holders = core_status(fixture.state, fixture.env, first)['holders']
        report['empty_holders'] = holders
        assert len(holders) == 1 and holders[0]['terminals'] == 0, holders
        owner = subprocess.run(['/bin/ps', '-E', '-ww', '-p', str(holders[0]['pid']), '-o', 'command='], capture_output=True, text=True).stdout
        assert str(fixture.state) in owner, ('holder 不是夹具的进程', owner)
        os.kill(holders[0]['pid'], 9)
        fixture.wait('core 没有 holder', lambda: not core_status(fixture.state, fixture.env, first)['holders'], 30)
        check('no_holder_before_pin_change', True)

        fixture.run_cli('daemon_stop')
        fixture.running = False
        fixture.wait('后台退出', lambda: not (fixture.state / 'daemon.pid').exists(), 20)
        check('core_survives_daemon_stop', core_status(fixture.state, fixture.env, first)['pid'] == core['pid'])

        digest = repacked(cache, fixture.dir / 'cache-b')
        (fixture.dir / 'pin-b').mkdir()
        source_b = source_tree(fixture.dir / 'pin-b', args.revision, [('src/hcDistribution.mjs', PIN, PIN.replace(PIN.split("'")[1], digest))])
        fixture.cli = source_b / 'workbench/src/gates/cli.ts'
        fixture.env['ENCHANTED_HC_CACHE_DIR'] = str(fixture.dir / 'cache-b')
        report['pin_b'] = digest
        # Each daemon start writes a new operator credential (as t123 restarts do).
        credential = fixture.dir / 'operator.json'
        credential.rename(fixture.dir / f'operator-{uuid.uuid4().hex[:8]}.json')
        fixture.run_cli('daemon_start', '--launch-config', str(fixture.dir / 'launch-config.json'))
        fixture.running = True
        fixture.operator = json.loads(credential.read_text(encoding='utf-8'))
        fixture.wait('后台恢复结束', lambda: fixture.request('pane_layout').get('recovering') is False, 10)
        check('same_core_after_pin_change', core_status(fixture.state, fixture.env, first)['pid'] == core['pid'])

        # 1: a new terminal of the running core.
        try:
            terminal_works('after')
        except AssertionError as error:
            report['after_error'] = str(error)
            raise
        check('new_terminal_after_pin_change', True)
        # 2: the new pin has an install of its own, not the old binary.
        installs = sorted(str(path) for path in fixture.state.glob('hc/herdr-core-*/herdr-core'))
        report['installs'] = installs
        check('new_pin_installed_apart', len(installs) == 2 and str(first) in installs, installs)
        check('running_core_file_untouched', first.stat().st_ino == first_inode)
        command = subprocess.check_output(['/bin/ps', '-p', str(core['pid']), '-o', 'comm='], text=True).strip()
        check('core_runs_first_install', Path(command).resolve() == first.resolve(), command)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(status='INCOMPLETE', error=f'{type(error).__name__}: {error}')
    finally:
        try:
            fixture.stop()
            report['core_cleanup'] = fixture.core_cleanup
        except AssertionError as error:
            report.update(status='INCOMPLETE', residue=str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if report['status'] == 'PASS':
            shutil.rmtree(fixture.dir)
    print(json.dumps({'status': report['status'], 'checks': report['checks'], 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
