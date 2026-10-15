"""Controller-only focused tracer checks and counterfactuals. No real Codex."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback

from command_evidence import CommandLog
from run_t076_quality_red import archive_directory
from test_quality_tracer_e2e import CASES

ROOT = Path(__file__).resolve().parents[2]


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-076-2', 'ready_rev': 1,
              'scope': 'first controlled tracer slice, not full T-076 acceptance', 'argv': sys.argv,
              'real_codex_turns': 0, 'steps': [], 'artifacts': [], 'remaining': [
                  'widened red/rule and terminal score acceptance in its separate phase', 'reviewer failure-path red and green evidence',
                  'score recovery failure injection and full 8/9/18 migration/regression',
                  'real read-only P-review probe and real model end-to-end delivery',
                  'T-077 lifecycle/R8 joint verification and fresh-context delivery review'],
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    artifacts = []
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk not mounted. Do not install or use an internal cache.')
        node = commands.run(['node', '--version'], cwd=ROOT, env=env)
        if node.returncode or not node.stdout.strip().startswith('v26.5.'):
            raise RuntimeError('Approved Node 26.5 runtime unavailable.')
        checkout = commands.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env)
        diff = commands.run(['git', 'diff', '--', 'workbench/src', 'workbench/hooks', 'workbench/tests', 'workbench/README.md'], cwd=ROOT, env=env)
        unchanged = commands.run(['git', 'diff', 'a7f4cc3033c16d5888de50d8352da516c941f8e9', '--',
                                 'acceptance/test_coop_e2e.py', 'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py'], cwd=ROOT, env=env)
        if any(p.returncode for p in (checkout, diff, unchanged)) or unchanged.stdout:
            raise RuntimeError('Source audit failed or original acceptance assertions changed.')
        fixture = Path(tempfile.mkdtemp(prefix='q76green-', dir='/tmp')).resolve()
        source = fixture / 'source'
        shutil.copytree(ROOT / 'workbench', source / 'workbench', symlinks=True,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
        (source / 'workbench/node_modules').symlink_to((ROOT / 'workbench/node_modules').resolve(), target_is_directory=True)
        with tarfile.open(out / 'candidate-source.tar.gz', 'x:gz') as archive:
            archive.add(source / 'workbench', arcname='workbench')
        save(out / 'source-manifest.json', {'source': str(source), 'head': checkout.stdout.strip(),
             'tracked_diff': diff.stdout, 'candidate_archive': str(out / 'candidate-source.tar.gz'),
             'includes_untracked_harness_and_product_files': True,
             'dependencies': str((ROOT / 'workbench/node_modules').resolve())})

        def run_suite(name, selected_source, *, cases=None, controls=False):
            target = out / name
            script = 'test_quality_chain_e2e.py' if controls else 'test_quality_tracer_e2e.py'
            argv = [sys.executable, '-B', source / 'workbench/tests' / script, '--source', selected_source, '--output', target]
            if controls:
                argv.extend(['--group', 'controls'])
            for case in cases or []:
                argv.extend(['--case', case])
            result = commands.run(argv, cwd=source, env=env, timeout=300,
                                  stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            report_path = target / 'run.json'
            report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else None
            step = {'name': name, 'command': result.evidence, 'exit': result.returncode,
                    'report_path': str(report_path), 'report': report}
            record['steps'].append(step)
            save(out / (name + '.receipt.json'), step)
            if report:
                artifacts.append(Path(report['artifact_root']))
            if not report or any(row['outcome'] == 'harness_error' or row['cleanup_failures'] for row in report['cases']):
                raise RuntimeError('Unexpected fixture/protocol failure; preserve and ask controller: ' + name)
            return result, report

        # Run the first full slice before widening the controlled cases.
        for name, cases in [('tracer', ['tracer_success']), ('protocol-controls', CASES[1:])]:
            result, report = run_suite(name, source, cases=cases)
            if result.returncode or report['status'] != 'PASS' or [r['case'] for r in report['cases']] != cases:
                raise RuntimeError('Candidate behavior failed; no automatic repair/retry: ' + name)
        result, report = run_suite('existing-boundary-controls', source, controls=True)
        if result.returncode or report['status'] != 'PASS' or len(report['cases']) != 8:
            raise RuntimeError('An existing boundary regressed; stop before mutants.')

        # The canonical Herdr validator is read only. The candidate never writes
        # records/scores.jsonl or imports live scores as part of this phase.
        score_file = out / 'tracer/tracer_success/score-payload.json'
        validation = commands.run([sys.executable, '-B', '-c',
            'import json,runpy,sys; sys.path.insert(0,sys.argv[1]); '
            'm=runpy.run_path(sys.argv[1]+"/score",run_name="fixture_validator"); '
            'm["validate_scores"]([json.load(open(sys.argv[2],encoding="utf-8"))]); print("schema-1 payload accepted")',
            ROOT / 'scripts', score_file], cwd=source, env=env)
        if validation.returncode:
            raise RuntimeError('Canonical score format validation failed.')

        mutations = [
            ('wrong-c-accepted', 'tracer_wrong_candidate', 'TRACER-REVIEW-CANDIDATE', 'gates/core.ts',
             'args.candidate_commit === task.candidate_commit && args.candidate_commit === review.candidate_commit,',
             'true, // Test mutant: omit candidate binding'),
            ('old-native-accepted', 'tracer_reused_native', 'TRACER-REVIEW-REUSE', 'gates/core.ts',
             'requireGate(!reused, "review_native_session_reused");',
             'requireGate(true, "review_native_session_reused");'),
            ('third-rejection-keeps-writing', 'tracer_third_rejection', 'TRACER-THIRD-STOP', 'gates/core.ts',
             'stopped: count >= 3, failure', 'stopped: count > 3, failure'),
            ('markdown-extracted', 'tracer_malformed_review', 'TRACER-REVIEW-STRICT-JSON', 'gates/qualityProtocol.ts',
             'try { value = JSON.parse(raw); }',
             'try { value = JSON.parse(raw.startsWith("```json\\n") ? raw.slice(8, -4) : raw); }'),
            ('score-invented', 'tracer_score_required', 'TRACER-SCORE-REQUIRED', 'gates/core.ts',
             'requireGate(path, "score_required");',
             'if (!path) return {result:"通过",boundary_discipline:3,boundary_reason:"mutant",engineering_taste:3,engineering_reason:"mutant",notes:""};'),
            ('score-fields-unchecked', 'tracer_score_required', 'TRACER-SCORE-FIELDS', 'gates/qualityProtocol.ts',
             'export function executorScore(value: unknown, command: "integrate" | "abandon" = "integrate"): Record<string, unknown> {',
             'export function executorScore(value: unknown, command: "integrate" | "abandon" = "integrate"): Record<string, unknown> { return value as Record<string, unknown>;'),
            ('reviewer-readonly', 'tracer_success', 'TRACER-REVIEW-COPY-ARGV', 'panes.ts',
             'const sandboxMode = review ? "workspace-write" : "workspace-write";',
             'const sandboxMode = review ? "read-only" : "workspace-write";'),
            ('prior-turn-score-facts', 'tracer_missing_delivery_context', 'TRACER-DELIVERY-CONTEXT', 'panes.ts',
             'pane.model = "unknown"; pane.effort = "unknown";', '// Test mutant: retain the prior turn facts'),
            ('identity-refusals-not-scored', 'tracer_identity_score', 'TRACER-SCORE', 'gates/core.ts',
             'rejections.identity_version = identityRejections;', 'rejections.identity_version = 0;'),
        ]
        for name, case, failure_id, relative, before, after in mutations:
            mutant = fixture / name
            shutil.copytree(source, mutant, symlinks=True)
            path = mutant / 'workbench/src' / relative
            text = path.read_text(encoding='utf-8')
            if text.count(before) != 1:
                raise RuntimeError('Mutation target is not unique: ' + name)
            path.write_text(text.replace(before, after), encoding='utf-8')
            save(out / (name + '.mutation.json'), {'source': str(source), 'mutant': str(mutant),
                 'path': relative, 'before': before, 'after': after, 'expected_failure': failure_id})
            syntax = commands.run(['node', '--check', path], cwd=mutant, env=env)
            if syntax.returncode:
                raise RuntimeError('Mutant has a syntax error, not business evidence: ' + name)
            result, report = run_suite(name, mutant, cases=[case])
            row = report['cases'][0]
            if result.returncode != 1 or row['outcome'] != 'contract_failure' or row.get('failure_id') != failure_id:
                raise RuntimeError('Mutant was not detected at its specified business boundary: ' + name)
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        for index, path in enumerate(artifacts):
            try:
                target = out / ('fixture-%02d.tar.gz' % index)
                record['artifacts'].append({'fixture': str(path), 'archive': archive_directory(path, target, out.name)})
            except Exception as error:
                record.update(status='INCOMPLETE', archive_error=repr(error))
        record['oversize_files'] = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
        print(json.dumps({k: record[k] for k in ('status', 'product_status', 'real_codex_turns', 'scope')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
