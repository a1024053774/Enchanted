"""T-212 边界：真实 daemon/shell 入口，不调用模型。

失败方式：损坏缓存被忽略或下载覆盖；只检查 core socket 而漏算 holder 后缀；
core 私有 XDG 覆盖泄漏进终端；用户原值/空值/未设置的区别丢失；继承 HC_*；
访问用户 core；hc 私有 registry 或 bearer token 被复制进证据。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import traceback
import uuid

from hc_evidence import assert_public_evidence, private_tokens, user_core_snapshot
from test_t212_shell_hc_e2e import stop_private_core

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=['leak-xdg'])
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='t212-boundaries-', dir='/private/tmp'))
    source = ROOT
    if args.mutant:
        source = root / 'source'
        for part in ('src', 'terminal', 'hooks', 'roles'):
            shutil.copytree(ROOT / 'workbench' / part, source / 'workbench' / part, symlinks=True)
        subprocess.run(['/bin/cp', '-cR', str(ROOT / 'workbench/node_modules'), str(source / 'workbench/node_modules')], check=True)
        path = source / 'workbench/src/panes.ts'
        text = path.read_text(encoding='utf-8')
        old = '["/usr/bin/env", ...xdg, ...originals, record.shell, ...record.shell_argv]'
        assert text.count(old) == 1
        path.write_text(text.replace(old, '[record.shell, ...record.shell_argv]'), encoding='utf-8')
    before = user_core_snapshot()
    report = dict(status='INCOMPLETE', command=[__file__, *os.sys.argv[1:]], fixture=str(root), cases=[], commands=[])
    tokens = set()
    try:
        for case in ('xdg-unset', 'xdg-values', 'xdg-empty', 'corrupt-cache', 'long-holder-socket'):
            fixture = root / case; fixture.mkdir()
            state, home, cwd = [fixture / name for name in ('state', 'home', 'project')]
            for directory in (state, home, cwd): directory.mkdir()
            (home / '.zshrc').write_text("PS1='BOUNDARY% '\n", encoding='utf-8')
            env = {key: os.environ[key] for key in ('PATH', 'LANG') if key in os.environ}
            env.update(HOME=str(home), SHELL='/bin/zsh', TMPDIR='/private/tmp',
                A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'), HC_SCOPE='inherited-must-disappear',
                HC_SESSION='default', HC_SOCKET=str(fixture / 'never-connect.sock'))
            if args.mutant:
                env['ENCHANTED_HC_CACHE_DIR'] = str(ROOT.parent / 'hc-cache')
            expected = {}
            if case == 'xdg-values':
                expected = dict(XDG_STATE_HOME=str(fixture / '用户状态'), XDG_CONFIG_HOME=str(fixture / '用户配置'))
                config = Path(expected['XDG_CONFIG_HOME']) / 'herdr-core'; config.mkdir(parents=True)
                (config / 'config.toml').write_text('invalid = [ deliberately broken\n', encoding='utf-8')
            elif case == 'xdg-empty': expected = dict(XDG_STATE_HOME='', XDG_CONFIG_HOME='')
            env.update(expected)
            if case == 'corrupt-cache':
                cache = fixture / 'cache'; cache.mkdir()
                archive = ROOT.parent / 'hc-cache/herdr-core-0.1.15-macos-aarch64.tar.gz'
                data = bytearray(archive.read_bytes()); data[0] ^= 1
                (cache / archive.name).write_bytes(data)
                env['ENCHANTED_HC_CACHE_DIR'] = str(cache)
            if case == 'long-holder-socket':
                # Core path itself fits; its holder.<8 hex>.sock endpoint does not.
                stem = str(fixture) + '/'
                socket = stem + 's' * (98-len(stem.encode())-5) + '.sock'
                assert len(socket.encode()) == 98
                (state / 'hc-runtime.json').write_text(json.dumps(dict(session='enchanted-'+str(uuid.uuid4()), socket=socket)))
            running = False
            result = dict(case=case, status='INCOMPLETE')

            def cli(*arguments):
                argv = ['node', str(source / 'workbench/src/gates/cli.ts'), '--state', str(state), *arguments]
                run = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=40, start_new_session=True)
                report['commands'].append(dict(argv=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr))
                return run

            try:
                start = cli('daemon_start')
                if case == 'corrupt-cache':
                    assert start.returncode != 0
                    error = (state / 'daemon.stderr.log').read_text()
                    assert 'SHA-256 mismatch' in error, error
                    assert not (state / 'hc/bin/herdr-core').exists(), 'corrupt cache silently replaced'
                    assert not (state / 'control.sock').exists(), 'failed runtime published a ready daemon'
                    result.update(status='PASS', error='hc archive SHA-256 mismatch', fallback_binary_created=False)
                    continue
                if case == 'long-holder-socket':
                    assert start.returncode != 0
                    error = (state / 'daemon.stderr.log').read_text()
                    assert 'including holder suffix exceeds 103 bytes' in error, error
                    assert not Path(socket).exists()
                    result.update(status='PASS', core_socket_bytes=98, error='including holder suffix exceeds 103 bytes')
                    continue
                assert start.returncode == 0, start.stdout
                running = True
                end = time.monotonic()+20
                while True:
                    layout = cli('pane_layout')
                    if json.loads(layout.stdout).get('recovering') is False: break
                    assert time.monotonic()<end
                    time.sleep(.1)
                opened = cli('shell_start', '--project', 'boundaries', '--cwd', str(cwd))
                assert opened.returncode == 0, opened.stdout
                launch = json.loads(opened.stdout)['launch']
                script = cwd / 'environment.mjs'
                script.write_text("import{writeFileSync}from'node:fs';const e=process.env;writeFileSync('environment.json',JSON.stringify({xdg:Object.fromEntries(['XDG_STATE_HOME','XDG_CONFIG_HOME'].map(k=>[k,{set:Object.hasOwn(e,k),value:e[k]??null}])),session:e.HC_SESSION,socket:e.HC_SOCKET,scope:e.HC_SCOPE}));", encoding='utf-8')
                # The existing window input public endpoint, via the same raw transport as UI tests.
                import socket as net
                def request(command, identity, **data):
                    with net.socket(net.AF_UNIX) as conn:
                        conn.settimeout(15); conn.connect(str(state / 'control.sock'))
                        conn.sendall((json.dumps(dict(id=str(uuid.uuid4()),identity=identity,input=dict(command=command,**data)))+'\n').encode())
                        data=b''
                        while b'\n' not in data: data+=conn.recv(65536)
                    return json.loads(data.split(b'\n')[0])
                operator=json.loads((fixture/'operator.json').read_text())
                window=request('window_open',operator,launch=launch['id'],project='boundaries')['identity']
                sent=request('window_input',window,sequence=1,request_id=str(uuid.uuid4()),data=f"node '{script}'\r")
                assert sent['ok'],sent
                end=time.monotonic()+15
                while not (cwd/'environment.json').exists():
                    assert time.monotonic()<end,'terminal environment not returned';time.sleep(.05)
                observed=json.loads((cwd/'environment.json').read_text())
                for key in ('XDG_STATE_HOME','XDG_CONFIG_HOME'):
                    assert observed['xdg'][key]==dict(set=key in expected,value=expected.get(key)),observed
                identity=json.loads((state/'hc-runtime.json').read_text())
                assert observed['session']==identity['session']!='default'
                assert observed['socket']==identity['socket'] and observed['scope']!='inherited-must-disappear'
                private=state/'hc/state/herdr-core'/identity['session']
                assert private.stat().st_mode & 0o777 == 0o700
                result.update(status='PASS',observed=observed,private_state_mode='0700')
            finally:
                tokens.update(private_tokens(state))
                if running:
                    stopped=cli('daemon_stop'); assert stopped.returncode==0,stopped.stdout
                    end=time.monotonic()+15
                    while (state/'control.sock').exists():
                        assert time.monotonic()<end;time.sleep(.05)
                    if case!='corrupt-cache':
                        cleanup=stop_private_core(fixture,env); assert cleanup['exit']==0,cleanup
                        result['core_cleanup']=cleanup
                report['cases'].append(result)
        after=user_core_snapshot()
        assert before==after,'user core directory or processes changed'
        report.update(status='PASS',user_core=dict(before=before,after=after))
    except Exception as error:
        report.update(error=str(error),traceback=traceback.format_exc())
    (args.output/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report['evidence_boundary']=assert_public_evidence(args.output,tokens)
    if report['status']=='PASS':
        shutil.rmtree(root)
        report['successful_fixture_removed']=not root.exists()
    (args.output/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],cases=report['cases'],error=report.get('error')),ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
