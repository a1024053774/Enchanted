#!/usr/bin/env python3
"""主控运行：只复现 ACK 后修复回合与 idle 轮询竞争；不修产品或夹具。"""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback

from run_red_outside import unpack_source

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = 'cdf8fe9b0eebfacf9f8d2ffeff3aecebf1e6eb37'
CASE = 'red_run_reject_preserves_worker'
LIMIT = 5_000_000
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(('A2A_', 'CODEX_', 'GIT_', 'COOP_', 'ELECTRON_'))}
ENV.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def sizes(out):
    large = [{'path': str(p), 'bytes': p.stat().st_size} for p in out.rglob('*')
             if p.is_file() and p.stat().st_size > LIMIT]
    if large:
        raise RuntimeError('单文件超过 5 MB；停止并保留现场：' + json.dumps(large))


def run(out, label, argv, timeout=90):
    sizes(out)
    row = {'argv': list(map(str, argv)), 'cwd': str(ROOT)}
    save(out / (label + '.start.json'), row)
    with (out / (label + '.stdout.bin')).open('xb') as stdout, \
            (out / (label + '.stderr.bin')).open('xb') as stderr:
        process = subprocess.run(row['argv'], cwd=ROOT, env=ENV, stdout=stdout,
                                 stderr=stderr, timeout=timeout)
    row['exit'] = process.returncode
    save(out / (label + '.command.json'), row)
    sizes(out)
    return row


def child(source, output):
    sys.path.insert(0, str(source / 'workbench/tests'))
    import test_quality_chain_e2e as quality

    class OrderedProbe(quality.QualityCase):
        def stop_turn(self, *, turn=None):
            pane = self.gate('pane_status', '--thread', self.a['thread_id'], task=False)
            if pane['turn'] == 'fixture-turn-2':
                # Hold the controlled ACK turn until the real run has queued its
                # completion failure. This is the ordering observed in final-02.
                # No signal, verdict, queue, or product state is substituted.
                deadline = time.monotonic() + 5
                while True:
                    current = self.cli('status')['task']
                    repair = current.get('repair')
                    messages = self.gate_messages()
                    repairs = [m for m in messages if (m['data'].get('context') or {}).get('kind') == 'quality-repair']
                    if repair and repairs:
                        pane = self.gate('pane_status', '--thread', self.a['thread_id'], task=False)
                        message = repairs[-1]
                        context = message['data']['context']
                        valid = (repair['check'] == 'completion' and repair['count'] == 1
                                 and repair['stopped'] is False and repair['failure']['error'] == 'oracle_failed'
                                 and context['rejection_id'] == repair['id'] and message['launch'] == self.launch
                                 and pane['state'] == 'busy' and pane['turn'] == 'fixture-turn-2'
                                 and message['id'] in pane['queued'])
                        quality.save(self.evidence / 'ack-repair-barrier.json', {
                            'matched': valid, 'task': self.task, 'attempt': self.a,
                            'repair': repair, 'message': message, 'pane': pane,
                            'ordering': 'completion rejection and repair queued before ACK Stop'})
                        if not valid:
                            raise quality.HarnessFailure('Probe did not reproduce the final-02 ACK/repair ordering.')
                        break
                    if time.monotonic() >= deadline:
                        raise quality.HarnessFailure('Probe did not observe a real completion rejection before ACK Stop.')
                    time.sleep(0.03)
            return super().stop_turn(turn=turn)

        def process(self, *args, **kwargs):
            sizes(output.parent)
            result = super().process(*args, **kwargs)
            sizes(output.parent)
            return result

    return quality.run_cases(source, output, [CASE], case_type=OrderedProbe, dialect='current')


def observation(output, source):
    report = json.loads((output / 'run.json').read_text(encoding='utf-8'))
    case = report['cases'][0]
    directory = output / CASE
    barrier = json.loads((directory / 'ack-repair-barrier.json').read_text(encoding='utf-8'))
    tables = json.loads((directory / 'database-readback.json').read_text(encoding='utf-8'))['tables']
    task = json.loads(tables['tasks'][0]['data'])
    repair = task.get('repair')
    last = next(command for command in reversed(case['commands']) if 'pane_status' in command['argv'])
    pane = json.loads(Path(last['stdout']).read_text(encoding='utf-8'))
    rejected = [row for row in tables['events'] if row['type'] == 'delivery_rejected']
    completed = [json.loads(row['details']) for row in tables['events'] if row['type'] == 'completion_check']
    idles = [row for row in tables['orchestration_events'] if row['type'] == 'pane_idle'
             and json.loads(row['data']).get('stop', {}).get('turn_id') == 'fixture-turn-2']
    submitted = [row for row in tables['orchestration_events'] if row['type'] == 'turn_submitted'
                 and json.loads(row['data']).get('dispatch') == barrier['message']['id']]
    refs = json.loads((directory / 'git-readback.json').read_text(encoding='utf-8'))['refs'].splitlines()
    expected = (case['outcome'] == 'harness_error'
                and case.get('error', '').startswith("HarnessFailure('Controlled pane did not reach its expected boundary:")
                and not case['cleanup_failures'] and barrier['matched'] is True
                and len(rejected) == 1 and completed and completed[-1]['passed'] is False
                and repair == barrier['repair'] and len(idles) == len(submitted) == 1
                and idles[0]['seq'] < submitted[0]['seq']
                and pane['state'] == 'busy' and pane['lifecycle'] == 'running'
                and pane['turn'] == 'fixture-turn-3' and pane['failed'] is None
                and pane['stopped'] is False and pane['queued'] == []
                and pane['active']['dispatch'] == barrier['message']['id']
                and task['current_attempt']['attempt_id'] == barrier['attempt']['attempt_id']
                and task['current_attempt']['reclaimed'] is False
                and task['base_commit'] + ' refs/heads/main' in refs
                and not any(row['type'] == 'integrated' for row in tables['events']))
    result = {'status': 'PASS' if expected else 'INCOMPLETE',
              'scope': 'same fixture boundary reproduced; not a product acceptance verdict',
              'source': str(source), 'case_outcome': case['outcome'], 'error': case.get('error'),
              'pane': pane, 'repair': repair, 'ack_idle_events': idles,
              'turn3_events': submitted, 'fixture': case['fixture'], 'report': str(output / 'run.json')}
    save(output / 'observation.json', result)
    with tarfile.open(output / 'fixtures.tar.gz', 'x:gz') as stream:
        stream.add(report['artifact_root'], arcname=Path(report['artifact_root']).name)
    sizes(output.parent)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.source:
        return child(args.source.resolve(), args.output.resolve())
    out = args.output.resolve()
    if out.parent != HERE:
        raise RuntimeError('输出必须是 T-080 证据根的一个新子目录。')
    out.mkdir(exist_ok=False)
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-080',
              'command': sys.argv, 'baseline': BASE, 'real_model_calls': 0,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'observations': []}
    try:
        if sys.version_info[:2] != (3, 9) or not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('需要本机 Python 3.9 及已挂载外置盘；不安装或回退。')
        for label, argv in [('node', ['node', '--version']), ('head', ['git', 'rev-parse', 'HEAD']),
                            ('status', ['git', 'status', '--porcelain=v1', '--untracked-files=all']),
                            ('diff', ['git', 'diff', '--binary', BASE])]:
            if run(out, label, argv)['exit']:
                raise RuntimeError('预检查失败：' + label)
        if not (out / 'node.stdout.bin').read_text().startswith('v26.5.'):
            raise RuntimeError('需要已安装的 Node 26.5。')
        if (out / 'head.stdout.bin').read_text().strip() != BASE:
            raise RuntimeError('worker HEAD 已变；停止报告。')
        dependencies = ROOT / 'workbench/node_modules'
        if not dependencies.is_dir() or not os.access(dependencies / 'node-pty/prebuilds/darwin-arm64/spawn-helper', os.X_OK):
            raise RuntimeError('已安装依赖或 spawn-helper 执行权限缺失。')
        fixture = Path(tempfile.mkdtemp(prefix='t80p-', dir='/tmp')).resolve()
        paths = ['workbench/src', 'workbench/tests', 'workbench/hooks/hook.py',
                 'workbench/package.json', 'workbench/package-lock.json', 'workbench/LICENSE.synara']
        archive = out / 'baseline-source.tar.gz'
        if run(out, 'freeze-base', ['git', 'archive', '--format=tar.gz', '--output', archive, BASE, *paths])['exit']:
            raise RuntimeError('无法冻结 cdf8fe9b 原产品。')
        baseline = fixture / 'baseline'
        baseline.mkdir()
        with tarfile.open(archive, 'r:gz') as stream:
            unpack_source(stream, baseline)
        candidate = fixture / 'candidate'
        ignore = shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store')
        for path in paths:
            original = ROOT / path
            target = candidate / path
            if original.is_dir():
                shutil.copytree(original, target, ignore=ignore, symlinks=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, target)
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as stream:
            for path in paths:
                stream.add(candidate / path, arcname=path)
        same = {}
        for path in ['workbench/tests/test_quality_chain_e2e.py', 'workbench/tests/quality_chain_host.ts',
                     'workbench/tests/controlled_quality_pty.ts', 'workbench/src/panes.ts', 'workbench/src/daemon.ts']:
            same[path] = (baseline / path).read_bytes() == (candidate / path).read_bytes()
        run_start, run_end = '  private async run(args: A2AGateRequest)', '  private inboxRecords()'
        code = [(s / 'workbench/src/gates/core.ts').read_text(encoding='utf-8') for s in (baseline, candidate)]
        same['core.ts run method'] = code[0][code[0].index(run_start):code[0].index(run_end)] == code[1][code[1].index(run_start):code[1].index(run_end)]
        save(out / 'source-manifest.json', {'baseline': str(baseline), 'candidate': str(candidate),
             'baseline_revision': BASE, 'unchanged': same, 'paths': paths,
             'card_fixtures': 'each source uses its own valid card format; no production compatibility path',
             'scheduling': 'repair queued before controlled ACK Stop, matching final-02'})
        if not all(same.values()):
            raise RuntimeError('run 或受控边界与 cdf8fe9b 不同；停止报告，不预设归因。')
        for label, source in [('baseline', baseline), ('candidate', candidate)]:
            (source / 'workbench/node_modules').symlink_to(dependencies.resolve(), target_is_directory=True)
            result = run(out, label, [sys.executable, '-B', Path(__file__).resolve(),
                                      '--source', source, '--output', out / label])
            observed = observation(out / label, source)
            record['observations'].append({'label': label, 'exit': result['exit'], **observed})
            if result['exit'] != 1 or observed['status'] != 'PASS':
                raise RuntimeError('最小对照没有复现同一边界；停止，不重试、不修正预期。')
        record.update(status='PASS', finding='Both products reached the same queued repair and failed the unchanged idle polling boundary.')
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'result.json', record)
    print(json.dumps({'status': record['status'], 'product_status': 'INCOMPLETE', 'report': str(out / 'result.json')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
