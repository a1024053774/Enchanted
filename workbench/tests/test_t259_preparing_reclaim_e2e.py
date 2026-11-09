"""T-259 through the real daemon socket and CLI, before/after a normal daemon restart.
The only injected fault is one runtime identity read after real PTY creation. CLI is a compiled
waiting executable; no model calls. Expected contract is the ticket: live/unknown refuses,
owned stopped unsent preparation reclaims, then the same task can be dispatched again.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
from scripted_claude import Fixture, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision')
    parser.add_argument('--archive-gap', action='store_true', help='interrupt after durable archive and restart before retry')
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    assert not args.summary.exists(), 'preserve existing evidence'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, checks=[], errors=[], observed={}, model_calls=0)
    fixture = None
    hosts = []
    logs = []
    def record(name, ok, detail=None): report['checks'].append(dict(name=name, passed=bool(ok), detail=detail))
    try:
        fixture = Fixture('t259-e2e-', lambda _: (_ for _ in ()).throw(AssertionError('no model requests allowed')), revision=args.revision)
        report['fixture'] = str(fixture.dir)
        fake = fixture.dir / 'waiting-cli'
        fake.with_suffix('.c').write_text('#include <stdio.h>\n#include <string.h>\n#include <unistd.h>\nint main(int n,char**a){if(n==2&&!strcmp(a[1],"--version")){puts("t259-fixture 1");return 0;}for(;;)pause();}\n', encoding='utf-8')
        subprocess.run(['/usr/bin/cc', str(fake.with_suffix('.c')), '-o', str(fake)], check=True)
        home = fixture.home / '.codex'; home.mkdir()
        run_cli = fixture.run_cli
        def start_host():
            path = fixture.dir / 'launch-config.json'
            config = json.loads(path.read_text(encoding='utf-8'))
            config.update(codex_bin=str(fake), codex_home=str(home))
            path.write_text(json.dumps(config), encoding='utf-8')
            ready = fixture.dir / f'ready-{len(hosts)}.json'
            log = (fixture.out / f'host-{len(hosts)}.log').open('w'); logs.append(log)
            host = subprocess.Popen(['node', str(Path(__file__).with_name('t259_preparing_host.ts')), str(fixture.source),
                str(fixture.state), str(path), str(ready), 'archive-gap' if args.archive_gap else 'normal'], env=fixture.env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            hosts.append(host)
            def ready_or_exit():
                assert host.poll() is None, 'fixture host exited before readiness; see host log'
                return ready.exists()
            fixture.wait('isolated daemon readiness', ready_or_exit, 25)
            fixture.running = True
            return json.loads(ready.read_text(encoding='utf-8'))
        def cli(*argv): return start_host() if argv[0] == 'daemon_start' else run_cli(*argv)
        fixture.run_cli = cli
        fixture.start('/usr/bin/false', {'note.txt':'original\n', 'check.py':'raise SystemExit(0)\n'})
        fixture.card('T-259', 'note.txt', 'check.py', executor=dict(cli='Codex', model='fixture', effort='high'))
        task = 'demo+T-259'
        dispatch = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
        attempt = fixture.request('status', fixture.operator, task=task)['task']['current_attempt']
        report['observed']['dispatch'] = dispatch
        report['observed']['attempt'] = attempt
        record('dispatch_failed_after_creation_before_binding', dispatch.get('error') == 'gate_failure' and attempt['runtime_identity'] is None and attempt['state']=='preparing')
        fixture.wait('real foreground CLI observed', lambda: fixture.request('pane_process_info', thread=attempt['thread_id']).get('leader'), 20)
        live = fixture.request('reclaim', fixture.terminal, task=task, attempt=attempt['attempt_id'])
        record('running_preparation_still_refused', not live.get('ok'), live)
        # Production daemon_stop terminates the fixture worker; its ordinary terminal/core survives.
        run_cli('daemon_stop'); fixture.running = False
        hosts[-1].wait(timeout=15)
        record('first_daemon_exited', hosts[-1].returncode == 0)
        start_host()
        fixture.wait('restart recovery complete', lambda: fixture.request('pane_layout').get('recovering') is False, 20)
        stopped = fixture.request('pane_status', thread=attempt['thread_id'])
        report['observed']['after_restart'] = stopped
        record('old_worker_confirmed_stopped', stopped.get('stopped') is True)
        if args.archive_gap:
            first = fixture.request('reclaim', fixture.operator, task=task, attempt=attempt['attempt_id'])
            report['observed']['archive_gap'] = first
            record('archive_gap_interrupted', first.get('error') == 'gate_failure')
            archived = [e for e in fixture.request('orchestration_events', task=task)['events'] if e['type']=='pane_archived']
            record('archive_completed_before_interruption', len(archived)==1 and archived[0]['attempt']==attempt['attempt_id'])
            run_cli('daemon_stop'); fixture.running=False
            hosts[-1].wait(timeout=15)
            start_host()
            fixture.wait('archive-gap recovery complete', lambda: fixture.request('pane_layout').get('recovering') is False, 20)
        reclaimed = fixture.request('reclaim', fixture.operator, task=task, attempt=attempt['attempt_id'])
        report['observed']['reclaim'] = reclaimed
        record('stopped_unsent_preparation_reclaimed', reclaimed.get('ok'), reclaimed)
        after = fixture.request('status', fixture.operator, task=task)['task']
        record('old_path_released_after_reclaim', after['state']=='ready' and after['current_attempt'] is None and not Path(attempt['workspace']).exists())
        if reclaimed.get('ok'):
            again = fixture.request('reclaim', fixture.operator, task=task, attempt=attempt['attempt_id'])
            record('repeat_reclaim_succeeds_without_input', again.get('ok'))
            redispatched = fixture.request('dispatch', fixture.terminal, task=task, runtimeMode='workspace-write')
            current = fixture.request('status', fixture.operator, task=task)['task']['current_attempt']
            report['observed']['redispatch'] = redispatched
            record('same_task_gets_new_attempt', redispatched.get('error')=='gate_failure' and current and current['attempt_id'] != attempt['attempt_id'] and current['fence']==attempt['fence']+1)
        events = fixture.request('orchestration_events', task=task)['events']
        report['observed']['events'] = [dict(seq=e['seq'], type=e['type'], attempt=e['attempt']) for e in events]
        record('no_task_bytes_or_turns', not any(e['type'] in ['dispatch_queued','paste_intent','turn_submit_intent','turn_submitted','terminal_input_write_intent'] for e in events))
        report['status'] = 'PASS' if all(c['passed'] for c in report['checks']) else 'FAIL'
    except Exception as error:
        report['errors'].append(dict(error=str(error), stack=traceback.format_exc()))
    finally:
        if fixture:
            try:
                fixture.stop()
                for host in hosts:
                    if host.poll() is None: host.wait(timeout=15)
                report['core_cleanup'] = fixture.core_cleanup
            except Exception as error:
                report['status']='INCOMPLETE'; report['errors'].append(dict(cleanup=str(error)))
            for log in logs: log.close()
            report['host_logs'] = [p.read_text(encoding='utf-8')[-5000:] for p in fixture.out.glob('host-*.log')]
            files=[p for p in fixture.dir.rglob('*') if p.is_file() and not p.is_symlink()]
            report['cleanup'] = dict(directory=str(fixture.dir), files=len(files), bytes=sum(p.stat().st_size for p in files))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if fixture and not any('cleanup' in e for e in report['errors']): shutil.rmtree(fixture.dir)
    print(json.dumps(dict(status=report['status'], failed=[c['name'] for c in report['checks'] if not c['passed']], errors=report['errors'],summary=str(args.summary)),ensure_ascii=False))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
