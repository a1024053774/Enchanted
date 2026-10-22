"""真实 daemon/CLI/PTY/Electron；仅本地固定 Responses API，不调用模型。Python 3.9。"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from run_t103_picker import Window
from t108_cleanup import observe, stop_owned
from t112_archive import extract_baseline
from diagnose_t112_reviewer import BINARY, run_reviewer_case
from t112_native_api import request_source, message_events


def closed_fixture_launches(root):
    # The Node producer has exited and closed every connection. Its final
    # checkpoint removes WAL/SHM; immutable avoids recreating those side files
    # during Python's read-only open. Never use this for the live daemon store.
    database = root / 'state.sqlite3'
    assert database.is_file(), 'Closed fixture database is missing'
    assert not any(Path(str(database) + suffix).exists() for suffix in ('-wal', '-shm')), 'Closed fixture still has WAL/SHM'
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
        return [json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records')]


def main():
    parser = argparse.ArgumentParser()
    for key in ('source', 'electron-dist', 'summary'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--baseline', default='e3102389eda8952ea92cae4b373e14eaff898314')
    # A fixed binary on purpose: the baseline revision predates T-118 and refuses any other
    # Codex version, so its red result needs this one (T-122 regress-t112-native-08). The
    # product itself records the version and refuses none (T-118).
    parser.add_argument('--codex', type=Path, default=Path('/Users/luckye/.codex/packages/app-server-daemon/releases/0.162.1-aarch64-apple-darwin/bin/codex'))
    args = parser.parse_args()
    source, summary = args.source.resolve(), args.summary.resolve()
    assert not summary.exists(), 'Preserve earlier evidence; choose a fresh summary'
    root = Path(tempfile.mkdtemp(prefix='t112-native-', dir='/private/tmp')).resolve()
    report = dict(status='INCOMPLETE', task='T-112', attempt='a1', baseline=args.baseline, fixture=str(root),
                  acceptance_revision='bc4306abdaca2e3cd08cd4f2b05b78a10c5215db',
                  acceptance_ruling='改验收，原样传递即可 (Recommended)',
                  model_calls_by_fixture=0, vendor_egress_observed=None,
                  egress_limitation='No system-wide egress monitor; fixture endpoints are credential-free loopback only',
                  commands=[], cases=[], checks=[], cleanup=[])
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_'))}
    for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
        env.pop(key, None)
    manager = root / 'manager-home'; manager.mkdir()
    env.update(HOME=str(manager), LC_ALL='C', PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='T112 fixture', GIT_AUTHOR_EMAIL='t112@example.invalid', GIT_COMMITTER_NAME='T112 fixture', GIT_COMMITTER_EMAIL='t112@example.invalid')
    requests, title_requests, api_errors, windows, builds, owners = [], [], [], [], [], []
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
            try:
                raw = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
                assert self.path in ('/v1/responses', '/responses'), self.path
                with (root / 'fake-api-requests.jsonl').open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps({'path': self.path, 'raw_body': raw}, ensure_ascii=False) + '\n')
                body = json.loads(raw)
                kind = request_source(body)
                if kind == 'thread_title':
                    title_requests.append(body)
                    assert len(title_requests) <= 12, 'Unexpected extra title inputs'
                    reply = json.dumps({'title': 'T112 local fixture'})
                else:
                    assert kind == 'user', 'Unexpected native thread source: ' + kind
                    requests.append(body)
                    assert len(requests) <= 12, 'Unexpected extra inputs'
                    reply = 'T112_LOCAL_FIXED_RESPONSE'
                self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for sequence, (name, payload) in enumerate(message_events(reply, body['model'])):
                    self.wfile.write(('event: ' + name + '\ndata: ' + json.dumps(dict(type=name, sequence_number=sequence, **payload)) + '\n\n').encode())
                self.wfile.flush()
            except Exception as error:
                api_errors.append({'path': self.path, 'error': str(error)})
                self.send_error(500)

    try:
        report['source_head'] = run(['git', 'rev-parse', 'HEAD']).strip()
        report['source_changes'] = run(['git', 'status', '--porcelain', '--untracked-files=all', '--',
            'workbench/src', 'workbench/app', 'workbench/tests', 'scripts/launch-worker']).splitlines()
        assert not report['source_changes'], 'Commit the candidate with RUN-OUTSIDE-COMMIT-01.sh before native acceptance'
        search_summary = root / 'repository-search.json'
        run(['python3', '-B', source / 'evidence/2026-10-20-batch18/T-112/SEARCH-REPO-08.py', '--source', source, '--summary', search_summary])
        report['repository_search'] = json.loads(search_summary.read_text(encoding='utf-8'))
        report['checks'].append('repository_model_effort_search_recorded')
        assert run([args.codex, '--version']).strip() == 'codex-cli 0.162.1'
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = False
        threading.Thread(target=server.serve_forever, daemon=True).start()
        # Private copies only. Controlled internal Git links stay unchanged;
        # no new links into another checkout and no chmod in a shared checkout.
        candidate, baseline = root / 'candidate', root / 'baseline'
        report['snapshot_commands'] = []
        for revision, tree in [(report['source_head'], candidate), (args.baseline, baseline)]:
            command = ['git', 'archive', revision, 'workbench']
            archive = subprocess.check_output(command, cwd=source, env=env)
            extract_baseline(archive, tree)
            report['snapshot_commands'].append(dict(argv=command, destination=str(tree)))
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
                # Codex resolves a Git worktree's trust against its repository;
                # trusting the unrelated fixture ancestor left a startup dialog.
                '[projects.' + json.dumps(str(repo)) + ']\ntrust_level = "trusted"\n', encoding='utf-8')
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

        def launch(expected, fields=()):
            value = call('dispatch', '--task', 'T112-fixture', '--runtime-mode', 'workspace-write', *fields)
            if active['label'] == 'red':
                assert not value['ok'] and value['error'] == 'worker_executor_mismatch', value
                report['cases'].append(dict(label='baseline_high', status='EXPECTED_RED', observed=value))
                return
            with sqlite3.connect('file:' + str(active['state'] / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                records = [json.loads(row[0]) for row in db.execute('SELECT data FROM launch_records')]
            record = next(row for row in records if row['role'] == 'worker')
            case_result = dict(label=active['label'], status='INCOMPLETE', launch=record, expected=expected)
            report['cases'].append(case_result)
            assert record['model_requested'] == expected['model'] and record['effort_requested'] == expected['effort'], record
            assert record['argv'][record['argv'].index('-m') + 1] == expected['model']
            assert 'model_reasoning_effort=' + json.dumps(expected['effort']) in record['argv']
            assert 'service_tier=' + json.dumps('fast' if expected['fast'] else 'default') in record['argv']
            def events():
                with sqlite3.connect('file:' + str(active['state'] / 'state.sqlite3') + '?mode=ro', uri=True) as db:
                    return [{'type': t, 'data': json.loads(d)} for t, d in db.execute('SELECT type,data FROM orchestration_events ORDER BY seq')]
            assert value['ok'], value
            case_result['dispatch'] = value
            foreground = until(lambda: call('pane_process_info', '--thread', record['thread']), lambda row: row.get('leader') and not row.get('failed'), 'foreground native CLI process')
            native = observe(foreground['leader']); assert native and str(args.codex.resolve()) in native['command']; owners.append(native)
            before = len(requests)
            case_result['pre_release'] = dict(process_info=foreground, api_requests=before,
                isolated_config=(Path(record['env']['CODEX_HOME']) / 'config.toml').read_text(encoding='utf-8'))
            # Since T-127 the daemon releases the first input itself after Codex's "Open restricted" screen.
            released = until(events, lambda rows: any(row['type'] == 'codex_restricted_opened' for row in rows), 'restricted folder opened by the daemon')
            case_result['release'] = [row for row in released if row['type'].startswith('codex_restricted')]
            until(lambda: len(requests), lambda count: count > before, 'first user request received by local fake API')
            assert not api_errors, api_errors
            request = requests[before]
            case_result['first_api_request'] = dict(index=before, thread_source=request_source(request),
                model=request['model'], reasoning=request.get('reasoning'), service_tier=request.get('service_tier'))
            info = until(lambda: call('pane_process_info', '--thread', record['thread']), lambda row: row.get('leader') and row.get('native_session') and not row.get('failed'), 'native CLI identity after first input')
            assert info['leader'] == foreground['leader'], 'Native CLI leader changed during first input'
            until(events, lambda rows: any(row['type'] == 'pane_idle' for row in rows), 'native matched Stop', 45)
            assert request['model'] == expected['model'] and request.get('reasoning', {}).get('effort') == expected['effort'], request
            assert not any(row['type'] == 'launch_failed' for row in events()), 'a2a must not reject the supplied value'
            case_result.update(status='PASS', native_identity=info, native_process=native,
                request={'model': request['model'], 'reasoning': request.get('reasoning'), 'service_tier': request.get('service_tier')})

        start(baseline, 'red'); launch(None); stop()
        report['checks'].append('baseline_real_dispatch_high_refused')
        # Same real reviewer constructor, PTY, hooks and native receipt used by
        # REVIEWER-DIAG-04. Change effort to low; mutate only the parent write root.
        assert args.codex.resolve() == BINARY, 'Reviewer and worker must use the same pinned binary'
        good = run_reviewer_case(source, candidate, root / 'reviewer-changed-effort-good', report['source_head'], env, report)
        assert good['candidate_write'] and good['boundary_oracle_passed'] and not good['unsafe_write_observed'], 'Changed-effort reviewer must preserve the external file'
        bad = run_reviewer_case(source, candidate, root / 'reviewer-changed-effort-bad', report['source_head'], env, report, bad=True)
        assert bad['candidate_write'] and bad['unsafe_write_observed'] and not bad['boundary_oracle_passed'], 'The same oracle must reject the parent-writable configuration'
        for case in (good, bad):
            assert case['launch']['effort_requested'] == 'low'
            assert not case.get('cleanup_errors') and case['cleanup'] and all(row['status'] == 'exited' for row in case['cleanup']), 'Reviewer cleanup must finish before the next case'
        report['checks'].append('changed_reviewer_effort_native_sandbox_good_and_bad_control')
        start(candidate, 'factory')
        report['factory_settings'] = call('execution_settings')['settings']
        assert report['factory_settings']['worker'] == dict(model='gpt-6.1-sol', effort='high', fast=False)
        launch(dict(model='gpt-6.1-sol', effort='high', fast=False)); stop()
        case = start(candidate, 'ui-settings')
        built = json.loads(run(['node', candidate / 'workbench/app/build.mjs', '--slot', 't112-' + uuid.uuid4().hex[:8]]).splitlines()[-1]); builds.append(Path(built['out']).parent)
        window = Window(candidate, candidate / 'workbench/tests/t112_settings_driver.mjs', Path(built['out']), active['state'], case / 'ui', case / 'window', env,
                        windows, dict(executable=str(binary), dist=str(dist), version='43.4.1'), through_start=False)
        initial_view = window.wait(lambda row: row['ready'])
        report['ui_settings'] = dict(argv=window.argv, native_electron=window.ready, before=initial_view)
        assert initial_view['settings']['worker'] == dict(model='gpt-6.1-sol', effort='high', fast=False)
        window.call('save', role='worker', model='gpt-6.1-sol', effort='low', fast=False)
        view = window.wait(lambda row: row.get('message') == '已保存，下次启动生效')
        report['ui_settings']['after'] = view
        assert view['settings']['worker']['effort'] == view['form']['effort'] == 'low', view
        window.close(); launch(dict(model='gpt-6.1-sol', effort='low', fast=False)); stop()
        report['checks'].append('real_dom_save_changes_next_native_dispatch')
        start(candidate, 'override')
        assert call('execution_settings_save', '--role', 'worker', '--model', 't112-saved-unselected-model', '--effort', 'medium', '--fast', 'false')['ok']
        report['override_saved_settings'] = call('execution_settings')['settings']['worker']
        assert report['override_saved_settings'] == dict(model='t112-saved-unselected-model', effort='medium', fast=False)
        launch(dict(model='gpt-6.1-sol', effort='xhigh', fast=True), ('--model', 'gpt-6.1-sol', '--effort', 'xhigh', '--fast', 'true')); stop()
        start(candidate, 'invalid'); launch(dict(model='gpt-6.1-sol', effort='unsupported-t112', fast=False), ('--effort', 'unsupported-t112')); stop()
        report['checks'].extend(['high_xhigh_low_reach_native_cli', 'override_beats_saved_medium', 'fast_argv_explicit', 'unknown_effort_unchanged_in_launch_argv_record_and_first_request'])
        assert not api_errors, api_errors
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
        report['api_errors'] = api_errors
        if api_errors:
            report['status'] = 'INCOMPLETE'
        for case in report['cases']:
            if 'bad_parent_writable' in case and (case.get('cleanup_errors') or not case.get('cleanup') or any(row['status'] != 'exited' for row in case['cleanup'])):
                report['status'] = 'INCOMPLETE'
                report.setdefault('cleanup_errors', []).append({'case': case['label'], 'reason': 'reviewer_cleanup_not_confirmed'})
        for build in builds:
            shutil.rmtree(build)
        report['fake_api_requests'] = len(requests)
        report['fake_title_requests'] = len(title_requests)
        if report['status'] != 'PASS':
            report['terminal_diagnostics'] = [dict(path=str(file), tail=file.read_bytes()[-3000:].decode('utf-8', errors='replace'))
                for file in root.glob('*/state/traces/*/pty.raw')]
        if not report.get('cleanup_errors'):
            try:
                shutil.rmtree(root)
                report['fixture_removed'] = not root.exists()
            except OSError as error:
                report['status'] = 'INCOMPLETE'; report['cleanup_errors'] = [str(error)]
        else:
            report['fixture_retained_reason'] = 'owned_process_cleanup_incomplete'
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': report['status'], 'summary': str(summary)}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
