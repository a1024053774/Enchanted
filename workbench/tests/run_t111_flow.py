"""T-111: real daemon/SQLite/Electron and old-app red state, no model calls.

Fixture expectations come from T-111. Only stopped, private databases are seeded.
All table/schema/trace values are compared through actual IPC. No screenshots.
"""
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
import time
import traceback
import uuid
from run_t103_picker import Window
from t107_persistence import persistence


def main():
    parser = argparse.ArgumentParser()
    for name in ('source', 'electron-dist', 'summary'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--baseline', default='b1ecd6e9cba23c1bbddb331822b6500a1488e2e9')
    args = parser.parse_args()
    source, output = args.source.resolve(), args.summary.resolve()
    assert not output.exists(), 'Fresh summary required'
    root = Path(tempfile.mkdtemp(prefix='t111-real-', dir='/private/tmp'))
    state = root / 'state'
    runtime = root / 'runtime'
    home = root / 'home'
    home.mkdir()
    dist = args.electron_dist.resolve(strict=True)
    binary = dist / 'Electron.app/Contents/MacOS/Electron'
    assert not str(dist).startswith('/Volumes/') and (dist / 'version').read_text().strip() == '43.4.1'
    assert (source / 'workbench/node_modules').is_dir() and not (source / 'workbench/node_modules').is_symlink()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    for key in ('NODE_OPTIONS', 'ELECTRON_RUN_AS_NODE'):
        env.pop(key, None)
    env.update(HOME=str(home), SHELL='/bin/zsh', ELECTRON_OVERRIDE_DIST_PATH=str(dist), LC_ALL='C',
               TMPDIR='/private/tmp', TMP='/private/tmp', TEMP='/private/tmp', PYTHONDONTWRITEBYTECODE='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    report = dict(status='INCOMPLETE', task='T-111', attempt='a1', model_calls=0, baseline=args.baseline,
                  checks=[], commands=[], limitations=['启动记录和门禁事件为隔离夹具；不证明模型运行或原生 hook 采集。'])
    windows, builds = [], []
    pid, epoch = None, 0

    def run(argv, cwd=source, check=True):
        result = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
        report['commands'].append(dict(argv=list(map(str, argv)), exit=result.returncode))
        if check:
            assert result.returncode == 0, (argv, result.stdout[-3000:], result.stderr[-3000:])
        return result

    def call(command, *fields):
        result = json.loads(run(['node', runtime / 'workbench/src/gates/cli.ts', '--state', state, command, *fields]).stdout)
        assert result['ok'], result
        return result

    def until(read, condition):
        deadline = time.monotonic() + 20
        while True:
            value = read()
            if condition(value):
                return value
            assert time.monotonic() < deadline, value
            time.sleep(.1)

    def start():
        nonlocal pid, epoch
        epoch += 1
        env['A2A_OPERATOR_CREDENTIAL'] = str(root / ('operator-' + str(epoch) + '.json'))
        pid = call('daemon_start')['pid']
        until(lambda: call('pane_layout'), lambda value: not value.get('recovering'))

    def stop():
        nonlocal pid
        if pid is not None:
            call('daemon_stop')
            until(lambda: (state / 'daemon.pid').exists(), lambda value: not value)
            pid = None

    def build(tree, label):
        value = json.loads(run(['node', tree / 'workbench/app/build.mjs', '--slot', 't111-' + label + '-' + uuid.uuid4().hex[:8]]).stdout.splitlines()[-1])
        builds.append(Path(value['out']).parent)
        return Path(value['out'])

    def window(tree, built, label):
        return Window(tree, source / 'workbench/tests/t111_flow_driver.mjs', built, state, root / 'ui', root / label, env,
                      windows, dict(executable=str(binary), dist=str(dist), version='43.4.1'), through_start=False)

    def seed():
        repo = root / 'repo'
        run(['git', '-c', 'core.hooksPath=/dev/null', 'init', '-b', 'main', repo])
        with sqlite3.connect(state / 'state.sqlite3') as db:
            def event(task, attempt, kind, data):
                db.execute('INSERT INTO events(time,task,attempt,type,details) VALUES (?,?,?,?,?)',
                           ('2026-10-20T12:00:00Z', task, attempt, kind, json.dumps(data)))
            def launch(name, role, task, attempt, parent=None, preset=None):
                record = dict(id=name, thread='thread-' + name, role=role, preset=preset, task=task, project='fixture-project',
                              attempt=attempt, cli_version='codex-cli 0.163.0', execution_state='prepared', model_requested='不调用模型')
                if parent is not None:
                    record['parent_launch'] = parent
                db.execute('INSERT INTO launch_records VALUES (?,?,?,?)', (name, task, attempt, json.dumps(record)))
            # The same ticket has an earlier attempt's mechanical rejection.
            event('T-B', 'previous-b', 'claimed', {})
            event('T-B', 'previous-b', 'submitted', {})
            event('T-B', 'previous-b', 'verification_result', dict(verification=dict(verification_id='v-old', state='failed')))
            event('T-B', 'previous-b', 'delivery_rejected', dict(repair=dict(verification_id='v-old', check='completion', count=1)))
            for name, attempt in [('T-A', 'a'), ('T-B', 'b'), ('T-C', 'c'), ('T-D', 'd')]:
                task = dict(task_id=name, project_id='fixture-project', repo=str(repo), title='独立标题 ' + name,
                            spec_rev=1, state='claimed', current_attempt=dict(attempt_id=attempt))
                db.execute('INSERT INTO tasks VALUES (?,?)', (name, json.dumps(task)))
                event(name, attempt, 'claimed', task)
            launch('idea', 'controller', 'T-A', None, preset='ideation')
            launch('executor', 'controller', 'T-A', None, 'idea', 'executor')
            for name in ('worker-1', 'worker-2'):
                launch(name, 'worker', 'T-A', 'a', 'executor')
            launch('reviewer', 'reviewer', 'T-B', 'b', 'executor')
            launch('monitor', 'monitor', 'T-A', 'a', 'executor')
            launch('orphan', 'worker', 'T-A', 'a')
            launch('missing-parent', 'worker', 'T-A', 'a', 'does-not-exist')
            launch('old-attempt', 'worker', 'T-A', 'obsolete', 'executor')
            for index in range(5):
                launch('parallel-' + str(index), 'worker', 'T-C', 'c', 'executor')
            event('T-B', 'b', 'submitted', {})
            event('T-B', 'b', 'verification_intent', {})
            event('T-B', 'b', 'verification_result', dict(verification=dict(state='passed')))
            event('T-B', 'b', 'review_result', dict(review=dict(state='needs_fix')))
            event('T-B', 'b', 'delivery_rejected', dict(repair=dict(check='independent_review', count=1)))
            event('T-B', 'b', 'submitted', {})
            event('T-B', 'b', 'verification_result', dict(verification=dict(verification_id='v-b2', state='passed')))
            event('T-B', 'b', 'review_result', dict(review=dict(state='needs_fix')))
            event('T-B', 'b', 'delivery_rejected', dict(repair=dict(verification_id='v-b2', check='independent_review', count=2)))
            event('T-B', 'b', 'submitted', {})
            event('T-B', 'b', 'verification_result', dict(verification=dict(state='passed')))
            event('T-D', 'd', 'integrated', {})
            # Unrelated refusal and old-attempt success must not imply returns or completion.
            event('T-A', 'a', 'rejected', dict(error='invalid_command'))
            event('T-A', 'obsolete', 'integrated', {})
        trace = state / 'traces/worker-1/pty.raw'
        trace.parent.mkdir(parents=True, exist_ok=True)
        trace.write_text('审查员 正在集成 已完成 (untrusted pane text)\n', encoding='utf-8')

    try:
        revision = run(['git', 'rev-parse', 'HEAD']).stdout.strip()
        report['source_head'] = revision
        report['source_changes'] = run(['git', 'status', '--porcelain', '--untracked-files=all', '--', 'workbench']).stdout.splitlines()
        report['candidate_revision'] = revision if not report['source_changes'] else None
        # A private runtime also isolates dependency permissions from the source.
        shutil.copytree(source / 'workbench/src', runtime / 'workbench/src')
        shutil.copytree(source / 'workbench/node_modules', runtime / 'workbench/node_modules', symlinks=False)
        helper = runtime / 'workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper'
        helper.chmod(0o755)
        start()
        stop()
        seed()
        start()
        baseline = root / 'baseline'
        baseline.mkdir()
        archive = subprocess.check_output(['git', 'archive', args.baseline, 'workbench'], cwd=source, env=env)
        report['commands'].append(dict(argv=['git', 'archive', args.baseline, 'workbench'], exit=0))
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(baseline)
        shutil.copytree(source / 'workbench/node_modules', baseline / 'workbench/node_modules', symlinks=False)
        red = window(baseline, build(baseline, 'red'), 'red')
        red_view = red.call('inspect')
        assert red_view['tabs'] == [], 'Known-bad app unexpectedly provides flow page'
        report['checks'].append(dict(name='真实 Electron 起点缺少流程页，拒绝流程标签合同', status='PASS'))
        red.close()
        built = build(source, 'green')
        green = window(source, built, 'green')
        green.call('tab')
        view = green.wait(lambda value: len(value['lanes']) == 4)
        lanes = {lane['task']: lane for lane in view['lanes']}
        assert lanes['T-A']['stage'] == 'implementation' and lanes['T-B']['stage'] == 'review'
        assert [c['stage'] for c in lanes['T-A']['columns']] == ['implementation', 'delivery', 'checks', 'review', 'integration']
        columns = lanes['T-A']['columns']
        assert all(columns[i]['x'] < columns[i+1]['x'] for i in range(4))
        assert len({column['y'] for column in columns}) == 1 and all(column['width'] >= 200 for column in columns)
        assert lanes['T-A']['y'] < lanes['T-B']['y']
        assert lanes['T-A']['columns'][0]['agents'] == ['worker-1', 'worker-2']
        assert lanes['T-A']['monitors'] == ['monitor']
        assert lanes['T-B']['columns'][3]['agents'] == ['reviewer']
        assert '打回 3 次' in lanes['T-B']['text'], 'Ticket header must display all three rejection facts'
        assert lanes['T-B']['returnLabel'] == '打回 3 次', 'Return diagram must label the total across attempts'
        assert lanes['T-B']['returns'] == [{'from': 'checks', 'count': 1}, {'from': 'review', 'count': 2}], 'Return lines must preserve the mechanical/review counts'
        assert '机械检查打回 1 次' in lanes['T-B']['returnText'] and '审查打回 2 次' in lanes['T-B']['returnText']
        assert lanes['T-B']['returnLinesVisible'] == [True, True], 'Both source return lines must be visible'
        projected = next(lane for lane in green.call('flow')['lanes'] if lane['task'] == 'T-B')
        assert len(projected['returns']) == 3, 'Actual IPC must accumulate rejection facts across attempts'
        assert [item['from'] for item in projected['returns']] == ['checks', 'review', 'review']
        report['multi_return_observed'] = dict(total=3, origins=['checks', 'review', 'review'],
                                             label=lanes['T-B']['returnLabel'], lines=lanes['T-B']['returns'])
        assert lanes['T-A']['returns'] == []
        assert not lanes['T-D']['expanded'] and lanes['T-D']['stage'] == 'integration'
        assert {'orphan','missing-parent','old-attempt'}.issubset(set(view['unassigned']) | {a['id'] for a in green.call('flow')['unassigned']})
        green.call('more', target='unassigned')
        view = green.wait(lambda value: 'old-attempt' in value['unassigned'])
        assert {'orphan','missing-parent','old-attempt'}.issubset(view['unassigned'])
        assert len(lanes['T-C']['columns'][0]['agents']) == 4
        assert next(item for item in view['more'] if item['id']=='T-C-implementation')['text'] == '还有 1 个 ↗'
        green.call('more', target='T-C-implementation')
        view = green.wait(lambda value: len(next(l for l in value['lanes'] if l['task']=='T-C')['columns'][0]['agents']) == 5)
        green.call('toggle', target='T-D')
        green.wait(lambda value: next(l for l in value['lanes'] if l['task']=='T-D')['expanded'])
        green.call('resize', width=900, height=700)
        view = green.wait(lambda value: value['scroll']['total'] > value['scroll']['width'])
        assert not view['bodyOverflow'], view
        assert green.call('scroll') > 0
        # Warm all readers before taking the independent persisted-value snapshot.
        green.call('flow')
        before = persistence(state)
        green.call('flow')
        green.call('flow')
        assert persistence(state) == before, 'Actual flow IPC changed tables/schema/traces'
        report['checks'].append(dict(name='两票并行、阶段、角色胶囊、监视器、跨 attempt 三次打回及来源计数、未归属、折叠展开与窄窗横滚', status='PASS'))
        report['checks'].append(dict(name='真实 flow IPC 所有表/schema/trace 原值不变', status='PASS'))
        green.close()
        stop()
        state = root / 'empty-state'
        start()
        empty = window(source, built, 'empty')
        empty.call('tab')
        empty.wait(lambda value: value['lanes'] == [] and '还没有任务票' in (value.get('text') or ''))
        empty.close()
        stop()
        report['checks'].append(dict(name='无任务票显示空状态', status='PASS'))
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        try:
            for win in windows:
                win.close()
            stop()
            report['cleanup_complete'] = True
        except Exception as error:
            report.update(status='INCOMPLETE', cleanup_complete=False, cleanup_error=repr(error))
        if report['status'] == 'PASS':
            shutil.rmtree(root)
            for directory in builds:
                shutil.rmtree(directory)
        else:
            report.update(retained_fixture=str(root), retained_builds=list(map(str, builds)))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
