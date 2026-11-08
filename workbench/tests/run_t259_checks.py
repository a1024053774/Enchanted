"""T-259: run the gate/PTY probe on a parent revision or an independent mutant.
Source copies replace only the selected product code. No accepted oracle changes.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from scripted_claude import ROOT, source_tree

CORE = 'src/gates/core.ts'
MUTANTS = {
    'skip-session': [(CORE, 'launch.attempt === attempt.attempt_id && launch.session === attempt.session_id && launch.fence === attempt.fence &&',
                     'launch.attempt === attempt.attempt_id && launch.fence === attempt.fence &&')],
    'ignore-input': [(CORE, '          !this.db.prepare(`SELECT 1 FROM orchestration_events WHERE launch=? AND type IN (',
                     '          !this.db.prepare(`SELECT 1 FROM orchestration_events WHERE 0 AND launch=? AND type IN (')],
    'release-before-archive': [(CORE,
        'if (!preparing && ownsTask && !["accepted", "abandoned", "upgraded"].includes(task.state)) this.invalidate(task, "controller reclaim");',
        'if (ownsTask && !["accepted", "abandoned", "upgraded"].includes(task.state)) this.invalidate(task, "controller reclaim");')],
    'ignore-archive-order': [(CORE, "AND type='pane_archived' AND seq>? LIMIT 1", "AND type='pane_archived' AND ?>=0 LIMIT 1")],
}
SCENARIOS = {'skip-session': 'record-session', 'ignore-input': 'input-intent', 'release-before-archive': 'archive-fails',
             'ignore-archive-order': 'resume-stale-archive'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--revision')
    modes.add_argument('--mutant', choices=list(MUTANTS))
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    summary = args.summary.resolve()
    if summary.exists(): raise SystemExit('preserve existing evidence; choose a new summary')
    fixture = Path(tempfile.mkdtemp(prefix='t259-source-', dir='/private/tmp')) if args.revision or args.mutant else None
    report = None
    try:
        source = source_tree(fixture, args.revision, MUTANTS.get(args.mutant, ())) if fixture else ROOT
        command = ['node', str(Path(__file__).with_name('test_t259_preparing_reclaim.ts')), str(source), str(summary)]
        if args.mutant: command.append(SCENARIOS[args.mutant])
        if args.revision: command.append('stopped')
        done = subprocess.run(command, capture_output=True, text=True, timeout=180)
        report = json.loads(summary.read_text(encoding='utf-8')) if summary.exists() else {'status':'INCOMPLETE'}
        report.update(revision=args.revision, mutant=args.mutant, command=command, exit_code=done.returncode,
                      stdout=done.stdout, stderr=done.stderr)
        if fixture:
            files = [p for p in fixture.rglob('*') if p.is_file() and not p.is_symlink()]
            report['source_cleanup'] = {'directory':str(fixture), 'files':len(files), 'bytes':sum(p.stat().st_size for p in files), 'action':'remove copied source'}
        summary.parent.mkdir(parents=True, exist_ok=True)
        summary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({key:report.get(key) for key in ('status','exit_code','mutant','revision')}, ensure_ascii=False))
        return done.returncode
    finally:
        if fixture and report: shutil.rmtree(fixture)

if __name__ == '__main__':
    raise SystemExit(main())
