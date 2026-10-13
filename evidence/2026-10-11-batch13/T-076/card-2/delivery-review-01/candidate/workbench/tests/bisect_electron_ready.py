"""Three controlled driver variants; no daemon, model, or product mutation.

First remove the whenReady wrapper, then stop awaiting window readiness during
entry-module evaluation, then restore the wrapper. All variants use the same
Electron binary, product build, environment policy, pipes, and process session.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time


WRAPPER = '''const whenReady = app.whenReady.bind(app);
app.whenReady = (...args) => {
  stage('when_ready_called');
  const promise = whenReady(...args);
  void promise.then(() => stage('when_ready_resolved'), (error) => stage('when_ready_rejected', { error: String(error) }));
  return promise;
};
'''
WAIT = "  const window = await run({ state: values.state, task: values.task, launch: values.launch, userData: values['user-data'] });\n"


def release_window_wait(source):
    assert source.count(WAIT) == 1
    start = source.index(WAIT)
    end = source.rindex('\n}\nawait main().catch(fatal);')
    body = '\n'.join('  ' + line if line else line for line in source[start + len(WAIT):end].split('\n'))
    return (source[:start] + "  void run({ state: values.state, task: values.task, launch: values.launch, userData: values['user-data'] }).then(async (window) => {\n"
            + body + '\n  }).catch(fatal);' + source[end:])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--old-driver', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='a4ready-', dir='/tmp')).resolve()
    scripts = Path(tempfile.mkdtemp(prefix='ready-bisect-', dir=source / 'workbench/tests'))
    baseline = args.old_driver.read_text(encoding='utf-8')
    assert baseline.count(WRAPPER) == 1
    without_wrapper = baseline.replace(WRAPPER, '')
    candidate = release_window_wait(baseline)
    assert candidate == (source / 'workbench/tests/electron_driver.mjs').read_text(encoding='utf-8'), 'C must be the actual candidate driver'
    cases = [('a-no-wrapper', without_wrapper, False),
             ('b-release-window-wait', release_window_wait(without_wrapper), True),
             ('c-restore-wrapper', candidate, True)]
    relative = (source / 'workbench/node_modules/electron/path.txt').read_text().strip()
    executable = (source / 'workbench/node_modules/electron/dist' / relative).resolve(strict=True)
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env.pop('ELECTRON_RUN_AS_NODE', None)
    # Match the window harness's fixed, non-secret fixture overrides in every case.
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_COUNT='2',
               GIT_CONFIG_KEY_0='core.hooksPath', GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign', GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T0754 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T0754 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
               A2A_BUILD_VOLUME='/Volumes/WD-Elements')
    results = []
    verdict = {'status': 'INCOMPLETE', 'argv': sys.argv, 'fixture': str(fixture), 'cases': results,
               'claim': '仅诊断真实 Electron 的 ready 阻塞；不证明完整窗口、PTY 或门禁验收', 'model_turns': 0}

    def stages(path):
        if not path.exists():
            return []
        # A concurrently appended final line may be incomplete. Preserve it on
        # disk and use only complete records for this bounded observation.
        return [json.loads(line) for line in path.read_bytes().splitlines(keepends=True) if line.endswith(b'\n')]

    def save():
        (output / 'results.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    try:
        for label, code, expect_window in cases:
            case = output / label; case.mkdir()
            script = scripts / (label + '.mjs'); script.write_text(code, encoding='utf-8')
            (case / 'driver.mjs').write_text(code, encoding='utf-8')
            trace = case / 'stages.jsonl'
            argv = [str(executable), str(script), '--build', str(args.build.resolve()), '--state', str(fixture / label / 'state'),
                    '--task', 'ready-probe', '--user-data', str(fixture / label / 'ui'), '--output', str(case)]
            stdout = (case / 'stdout.bin').open('xb'); stderr = (case / 'stderr.bin').open('xb')
            process = subprocess.Popen(argv, cwd=source, env={**env, 'A2A_ELECTRON_DIAGNOSTICS': str(trace)},
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       bufsize=0, start_new_session=True)
            record = {'label': label, 'argv': argv, 'pid': process.pid, 'expected_window': expect_window,
                      'diagnostic_environment': {'A2A_ELECTRON_DIAGNOSTICS': str(trace)}}
            results.append(record)
            selector = selectors.DefaultSelector()

            def drain(wait):
                for key, _mask in selector.select(wait):
                    data = os.read(key.fileobj.fileno(), 65536)
                    if data:
                        key.data.write(data); key.data.flush()
                    else:
                        selector.unregister(key.fileobj)

            began = time.monotonic()
            try:
                for stream, destination in [(process.stdout, stdout), (process.stderr, stderr)]:
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_READ, destination)
                save()
                while True:
                    drain(0.02)
                    events = stages(trace)
                    observed = any(event['stage'] == 'window_created' and event['app_ready'] for event in events)
                    if observed or process.poll() is not None or time.monotonic() - began >= 8:
                        break
                record.update(window_observed=observed, observation_seconds=time.monotonic() - began,
                              reached_deadline=not observed and process.poll() is None,
                              stages_before_cleanup=[event['stage'] for event in events])
            finally:
                if process.poll() is None:
                    try:
                        group = os.getpgid(process.pid)
                        assert group == process.pid, 'Refuse to signal any group not created by this probe'
                        record.update(cleanup_signal='SIGKILL', owned_pgid=group)
                        os.killpg(group, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # A natural exit raced cleanup; wait still confirms this owned child.
                record['exit'] = process.wait(timeout=5)
                deadline = time.monotonic() + 2
                while selector.get_map() and time.monotonic() < deadline:
                    drain(0.02)
                record['output_drained'] = not selector.get_map()
                selector.close(); process.stdin.close(); process.stdout.close(); process.stderr.close()
                stdout.close(); stderr.close()
                save()
            events = stages(trace)
            started = next((event for event in events if event['stage'] == 'product_run_started'), None)
            record['paths_configured_before_ready'] = bool(started and started['app_ready'] is False)
            record['matches_expected'] = (record['window_observed'] == expect_window
                and record['output_drained'] and record['paths_configured_before_ready']
                and not any(event['stage'] == 'fatal' for event in events)
                and (expect_window or record['reached_deadline'])
                and (label != 'c-restore-wrapper' or any(event['stage'] == 'when_ready_resolved' for event in events)))
            record['status'] = 'PASS' if record['matches_expected'] else 'INCOMPLETE'
            save()
        if all(record['matches_expected'] for record in results):
            verdict['status'] = 'PASS'
            verdict['inference'] = '去掉 whenReady 包装仍阻塞；解除模块求值对窗口就绪的等待后通过；恢复包装仍通过。此对照定位到驱动的等待链，产品构建保持原样。'
        else:
            verdict['error'] = '三组对照不支持预期因果关系；保留全部结果，不继续窗口验收。'
    except Exception as error:
        verdict['error'] = repr(error)
    finally:
        save()
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if verdict['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
