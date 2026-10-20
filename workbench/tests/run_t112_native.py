"""真实 daemon/CLI/PTY/Electron；仅本地固定 Responses API，不调用模型。Python 3.9。"""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from run_t103_picker import Window
from t108_cleanup import observe, stop_owned


def main():
    parser = argparse.ArgumentParser()
    for key in ('source', 'electron-dist', 'summary'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--baseline', default='e3102389eda8952ea92cae4b373e14eaff898314')
    parser.add_argument('--codex', type=Path, default=Path('/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex'))
    args = parser.parse_args()
    source, summary = args.source.resolve(), args.summary.resolve()
    assert not summary.exists(), 'Preserve earlier evidence; choose a fresh summary'
    root = Path(tempfile.mkdtemp(prefix='t112-native-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', task='T-112', attempt='a1', baseline=args.baseline, fixture=str(root),
                  model_calls=0, vendor_calls=0, commands=[], cases=[], checks=[], cleanup=[])
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
        env.pop(key, None)
    manager = root / 'manager-home'; manager.mkdir()
    env.update(HOME=str(manager), LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='T112 fixture', GIT_AUTHOR_EMAIL='t112@example.invalid', GIT_COMMITTER_NAME='T112 fixture', GIT_COMMITTER_EMAIL='t112@example.invalid')
    requests, windows, builds, owners = [], [], [], []
    active = None
    server = None

    def run(argv, cwd=source, timeout=180, accepted_exits=(0,)):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=result.returncode, stdout=result.stdout[-6000:], stderr=result.stderr[-2000:]))
        assert result.returncode in accepted_exits, report['commands'][-1]
        return result.stdout

    def until(read, predicate, label, seconds=30):
        end = time.monotonic() + seconds
        while True:
            value = read()
            if predicate(value):
                return value
            assert time.monotonic() < end, (label, value)
            time.sleep(.1)

    def call(command, *fields):
        # A gate refusal is JSON with exit 1. Keep it available to the specific
        # positive/negative oracle instead of treating every refusal as setup failure.
        return json.loads(run(['node', active['tree'] / 'workbench/src/gates/cli.ts', '--state', active['state'], command, *fields], accepted_exits=(0, 1)))

    def stop():
        nonlocal active
        if active:
            value = call('daemon_stop'); assert value['ok'], value
            until(lambda: observe(active['pid']), lambda row: row is None or row['stat'].startswith('Z'), 'owned daemon exit')
            active = None

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            assert self.path in ('/v1/models', '/models'), self.path
            payload = json.dumps({'object': 'list', 'data': [{'id': 'gpt-6.1-sol', 'object': 'model', 'owned_by': 'fixture'}]}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(payload)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert self.path in ('/v1/responses', '/responses'), self.path
            requests.append(body)
            with (root / 'fake-api-requests.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(body, ensure_ascii=False) + '\n')
            assert len(requests) <= 12, 'Unexpected extra inputs'
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
            item = {'id': 'msg_fixture', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                    'content': [{'type': 'output_text', 'text': 'T112_LOCAL_FIXED_RESPONSE', 'annotations': []}]}
            response = {'id': 'resp_' + uuid.uuid4().hex, 'object': 'response', 'status': 'completed', 'model': body['model'],
                        'output': [item], 'usage': {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}}
            events = [('response.created', {'response': dict(response, status='in_progress', output=[])}),
                      ('response.output_item.added', {'output_index': 0, 'item': dict(item, status='in_progress', content=[])}),
                      ('response.content_part.added', {'item_id': item['id'], 'output_index': 0, 'content_index': 0, 'part': {'type': 'output_text', 'text': '', 'annotations': []}}),
                      ('response.output_text.delta', {'item_id': item['id'], 'output_index': 0, 'content_index': 0, 'delta': 'T112_LOCAL_FIXED_RESPONSE'}),
                      ('response.output_item.done', {'output_index': 0, 'item': item}), ('response.completed', {'response': response})]
            for name, payload in events:
                self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, **payload)) + '\n\n').encode())
            self.wfile.flush()

    try:
        report['source_head'] = run(['git', 'rev-parse', 'HEAD']).strip()
        report['source_changes'] = run(['git', 'status', '--porcelain', '--untracked-files=all', '--',
            'workbench/src', 'workbench/app', 'workbench/tests', 'scripts/launch-worker']).splitlines()
        assert not report['source_changes'], 'Commit the candidate with RUN-OUTSIDE-COMMIT-01.sh before native acceptance'
        assert run([args.codex, '--version']).strip() == 'codex-cli 0.162.1'
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        # Private copies only. No links and no chmod in any shared checkout.
        candidate, baseline = root / 'candidate', root / 'baseline'
        shutil.copytree(source / 'workbench', candidate / 'workbench', ignore=shutil.ignore_patterns('node_modules'))
        archive = subprocess.check_output(['git', 'archive', args.baseline, 'workbench'], cwd=source, env=env)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                assert not member.issym() and not member.islnk() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                if member.isdir():
                    (baseline / member.name).mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target = baseline / member.name; target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read()); target.chmod(member.mode)
        shutil.copytree(source / 'workbench/node_modules', root / 'node_modules', symlinks=False,
                        ignore=shutil.ignore_patterns('.bin', 'win32-*', 'linux-*'))
        (root / 'node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper').chmod(0o755)
        dist = args.electron_dist.resolve(strict=True)
        binary = dist / 'Electron.app/Contents/MacOS/Electron'
        assert not str(binary).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
        env['ELECTRON_OVERRIDE_DIST_PATH'] = str(dist)

        def start(tree, label):
            nonlocal active
            case = root / label; case.mkdir()
            repo, state, home = case / 'repo', case / 'state', case / 'codex-home'
            home.mkdir(); role = case / 'role.md'; role.write_text('只回答固定文本，不运行工具，不交付或修改文件。\n', encoding='utf-8')
            # The provider has no credentials and can address only this bound fake API.
            (home / 'config.toml').write_text('model_provider = "t112_fixture"\ncli_auth_credentials_store = "file"\n'
                '[model_providers.t112_fixture]\nname = "T112 local fixture"\nbase_url = "http://127.0.0.1:' + str(server.server_port) + '/v1"\n'
                'wire_api = "responses"\nrequires_openai_auth = false\n'
                '[projects.' + json.dumps(str(root)) + ']\ntrust_level = "trusted"\n', encoding='utf-8')
            config = case / 'launch.json'
            config.write_text(json.dumps(dict(codex_bin=str(args.codex.resolve()), codex_home=str(home), role_card=str(role),
                role_card_revision='T112/a1', code_revision=report['source_head'], hook_authorization='T112 explicit local fake API fixture', turn_limit=1)), encoding='utf-8')
            env['A2A_OPERATOR_CREDENTIAL'] = str(case / 'operator.json')
            active = dict(tree=tree, state=state, label=label)
            value = call('daemon_start', '--launch-config', config); assert value['ok'], value
            active['pid'] = value['pid']; owner = observe(value['pid']); assert owner and str(state) in owner['command']; owners.append(owner)
            until(lambda: call('pane_layout'), lambda row: not row.get('recovering'), 'daemon recovery')
            run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
            (repo / 'oracle.txt').write_text('protected fixture\n', encoding='utf-8')
            run(['git', '-C', repo, 'add', '.']); run(['git', '-c', 'core.hooksPath=/dev/null', '-C', repo, 'commit', '-m', 'fixture'])
            card = dict(id='T112-fixture', source=None, goal='模型设置原生验证', non_goals=['交付与集成'], paths={'allow': ['.'], 'deny': []},
                oracle_paths=['oracle.txt'], completion_conditions=[{'argv': ['/usr/bin/false']}], red_commands=[], task_type='后端逻辑', repair_target=None,
                complexity='L', executor={'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'high'}, base_commit=None, writer=None)
            card_file = case / 'card.json'; card_file.write_text(json.dumps(card, ensure_ascii=False), encoding='utf-8')
            assert call('card_save', '--task', card['id'], '--card', card_file, '--expected-version', '0')['ok']
            assert call('create', '--task', card['id'], '--repo', repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'T112-project')['ok']
            return case

        def launch(expected, fields=(), invalid=False):
            value = call('dispatch', '--task', 'T112-fixture', '--runtime-mode', 'workspace-write', *fields)
            if active['label'] == 'red':
                assert not value['ok'] and value['error'] == 'worker_executor_mismatch', value
                report['cases'].append(dict(label='baseline_high', status='EXPECTED_RED', observed=value))
                return
            with sqlite3.connect('file:' + str(active['state'] / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                records = [json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records')]
            record = next(row for row in records if row['role'] == 'worker')
            assert record['model_requested'] == expected['model'] and record['effort_requested'] == expected['effort'], record
            assert record['argv'][record['argv'].index('-m') + 1] == expected['model']
            assert 'model_reasoning_effort=' + json.dumps(expected['effort']) in record['argv']
            assert 'service_tier=' + json.dumps('fast' if expected['fast'] else 'default') in record['argv']
            def events():
                with sqlite3.connect('file:' + str(active['state'] / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                    return [{'type': t, 'data': json.loads(d)} for t, d in db.execute('SELECT type,data FROM orchestration_events ORDER BY seq')]
            if invalid:
                rows = until(events, lambda rows: any(row['type'] == 'launch_failed' for row in rows), 'CLI rejects unsupported effort')
                trace = (active['state'] / 'traces' / record['id'] / 'pty.raw').read_text(errors='replace')
                assert 'unsupported-t112' in trace and ('invalid' in trace.lower() or 'unknown' in trace.lower()), trace
                report['cases'].append(dict(label='invalid_effort', status='PASS', dispatch=value, launch=record, failure=[r for r in rows if r['type'] == 'launch_failed'], cli_error=trace[-3000:]))
            else:
                assert value['ok'], value
                info = until(lambda: call('pane_process_info', '--thread', record['thread']), lambda row: row.get('leader') and row.get('native_session'), 'real native CLI identity')
                native = observe(info['leader']); assert native and str(args.codex.resolve()) in native['command']; owners.append(native)
                before = len(requests)
                released = call('pane_release', '--thread', record['thread'], '--reason', 'T112 local fake API verification'); assert released['ok'], released
                until(lambda: len(requests), lambda count: count > before, 'local fake API turn')
                until(events, lambda rows: any(row['type'] == 'pane_idle' for row in rows), 'native matched Stop', 45)
                request = requests[before]
                assert request['model'] == expected['model'] and request.get('reasoning', {}).get('effort') == expected['effort'], request
                report['cases'].append(dict(label=active['label'], status='PASS', launch=record, native_identity=info,
                    request={'model': request['model'], 'reasoning': request.get('reasoning'), 'service_tier': request.get('service_tier')}))

        start(baseline, 'red'); launch(None); stop()
        report['checks'].append('baseline_real_dispatch_high_refused')
        # Native sandbox counterexample uses the actual reviewer argv produced
        # by Panes at a changed effort. The contract supplies PTY only; the
        # following subprocess enforces the real macOS write boundary.
        env['T112_FIXTURE_PREFIX'] = str(root / 'review-policy-')
        policy_file = root / 'policy-contract.json'
        run(['node', candidate / 'workbench/tests/test_t112_execution.mjs', policy_file])
        policy = json.loads(policy_file.read_text())
        policy_root = Path(policy['fixture'])
        with sqlite3.connect('file:' + str(policy_root / 'state.sqlite3') + '?mode=ro', uri=True) as db:
            review = next(json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records') if json.loads(row[0])['role'] == 'reviewer')
        assert review['effort_requested'] == 'low'
        prefix = [str(args.codex), 'sandbox', '--permission-profile', ':workspace', '--cd', review['worktree']]
        for index, argument in enumerate(review['argv']):
            if argument == '-c' and not review['argv'][index + 1].startswith('hooks.'):
                prefix += ['-c', review['argv'][index + 1]]
        protected = policy_root / 'protected.txt'; protected.write_text('unchanged\n', encoding='utf-8')
        writable = Path(review['worktree']) / 'candidate-probe.txt'
        probe = 'from pathlib import Path; Path(' + repr(str(writable)) + ').write_text("candidate-only"); Path(' + repr(str(protected)) + ').write_text("forbidden")'
        command = prefix + ['--', '/usr/bin/python3', '-I', '-S', '-B', '-c', probe]
        result = subprocess.run(command, cwd=review['worktree'], env={**env, 'CODEX_HOME': review['env']['CODEX_HOME']}, capture_output=True, text=True, timeout=30)
        report['commands'].append(dict(argv=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
        assert writable.read_text() == 'candidate-only', 'Sandbox setup failure cannot count as read-only evidence'
        assert result.returncode != 0 and protected.read_text() == 'unchanged\n' and 'PermissionError' in result.stderr
        report['checks'].append('changed_reviewer_effort_native_sandbox_denies_protected_write_allows_candidate_copy')
        start(candidate, 'factory'); launch(dict(model='gpt-6.1-sol', effort='high', fast=False)); stop()
        case = start(candidate, 'ui-settings')
        built = json.loads(run(['node', candidate / 'workbench/app/build.mjs', '--slot', 't112-' + uuid.uuid4().hex[:8]]).splitlines()[-1]); builds.append(Path(built['out']).parent)
        window = Window(candidate, candidate / 'workbench/tests/t112_settings_driver.mjs', Path(built['out']), active['state'], case / 'ui', case / 'window', env,
                        windows, dict(executable=str(binary), dist=str(dist), version='43.4.1'), through_start=False)
        window.wait(lambda row: row['ready'])
        window.call('save', role='worker', model='gpt-6.1-sol', effort='low', fast=False)
        view = window.wait(lambda row: row.get('message') == '已保存，下次启动生效')
        assert view['settings']['worker']['effort'] == 'low', view
        window.close(); launch(dict(model='gpt-6.1-sol', effort='low', fast=False)); stop()
        report['checks'].append('real_dom_save_changes_next_native_dispatch')
        start(candidate, 'override')
        assert call('execution_settings_save', '--role', 'worker', '--effort', 'medium')['ok']
        launch(dict(model='gpt-6.1-sol', effort='xhigh', fast=True), ('--model', 'gpt-6.1-sol', '--effort', 'xhigh', '--fast', 'true')); stop()
        start(candidate, 'invalid'); launch(dict(model='gpt-6.1-sol', effort='unsupported-t112', fast=False), ('--effort', 'unsupported-t112'), True); stop()
        report['checks'].extend(['high_xhigh_low_reach_native_cli', 'override_beats_saved_medium', 'fast_argv_explicit', 'invalid_effort_native_error_and_launch_failure'])
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    finally:
        for window in windows:
            try:
                window.close()
            except Exception as error:
                report['status'] = 'INCOMPLETE'; report.setdefault('cleanup_errors', []).append(str(error))
        if active:
            try:
                stop()
            except Exception as error:
                report['status'] = 'INCOMPLETE'; report.setdefault('cleanup_errors', []).append(str(error))
        for owner in reversed(owners):
            try:
                report['cleanup'].append(stop_owned(owner))
            except Exception as error:
                report['status'] = 'INCOMPLETE'; report.setdefault('cleanup_errors', []).append(str(error))
        if server:
            server.shutdown(); server.server_close()
        for build in builds:
            shutil.rmtree(build)
        report['fake_api_requests'] = len(requests)
        # Preserve raw fixtures outside Git; never fall back when the archive disk is absent.
        try:
            disk = Path('/Volumes/WD-Elements'); assert disk.is_mount(), 'Evidence archive disk is not mounted'
            target = disk / 'a2a-evidence/2026-10-20-batch18/T-112' / root.name
            target.parent.mkdir(parents=True, exist_ok=True); assert not target.exists()
            before = [p for p in root.rglob('*') if p.is_file()]
            count, size = len(before), sum(p.stat().st_size for p in before)
            shutil.copytree(root, target)
            after = [p for p in target.rglob('*') if p.is_file()]
            assert len(after) == count and sum(p.stat().st_size for p in after) == size
            manifest = dict(original=str(root), archive=str(target), files=count, bytes=size, replay=report['commands'])
            summary.with_suffix('.archive.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            shutil.rmtree(root)
        except Exception as error:
            report['status'] = 'INCOMPLETE'; report['archive_error'] = str(error)
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': report['status'], 'summary': str(summary)}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
