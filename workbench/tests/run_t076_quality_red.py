"""Controller-only T-076-2 stages 1-3. No real model phase exists.

Stage 1 freezes the baseline and harness. Stage 2 records typed contract red.
Stage 3 runs existing-boundary controls and three one-change product mutants.
Absent new reviewer/scoring interfaces remain explicitly unverified.
"""
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
from test_quality_chain_e2e import RED_CASES, CONTROL_CASES

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'a7f4cc3033c16d5888de50d8352da516c941f8e9'
HARNESS = ('run_t076_quality_red.py', 'test_quality_chain_e2e.py', 'quality_chain_host.ts', 'command_evidence.py')
DEFERRED = [
    {'id': 'THIRD-REJECTION', 'reason': 'Three distinct C submissions require the approved repair authorization path; baseline stops at C2. Do not infer the limit from missing first feedback.'},
    {'id': 'REVIEW-WRITER-OR-RESUMED', 'reason': 'Baseline has no review_submit or reviewer launch. Candidate identity and reuse mutants must fail after that interface exists.'},
    {'id': 'REVIEW-CANDIDATE-MISMATCH', 'reason': 'A valid reviewer result is needed before changing only its candidate binding. An unknown-command usage error is not evidence.'},
    {'id': 'REVIEW-NEEDS-FIX', 'reason': 'Requires a valid independent reviewer result. Baseline review-required red proves absence, not findings relay correctness.'},
    {'id': 'SCORE-ONLY-AND-ABANDON', 'reason': 'Baseline unreviewed/unscored integration red proves missing final prerequisites jointly; it does not isolate score validation, abandon, format or recovery.'},
    {'id': 'READONLY-REVIEW-B', 'reason': 'Real P-review probe is not authorized in stages 1-3. No real Codex, auth copy or session hook installation occurs.'},
]


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def extract_owned_archive(archive_path, destination):
    with tarfile.open(archive_path, 'r:gz') as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination not in target.parents:
                raise RuntimeError('Baseline archive path escapes its new fixture.')
            if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                raise RuntimeError('Baseline archive has an unsupported special entry.')
            if member.issym() or member.islnk():
                linked = ((target.parent if member.issym() else destination) / member.linkname).resolve()
                if destination not in linked.parents:
                    raise RuntimeError('Baseline archive link escapes its new fixture.')
        archive.extractall(destination)


def archive_directory(path, target, label):
    with tarfile.open(target, 'x:gz') as archive:
        archive.add(path, arcname=path.name)
    if target.stat().st_size > 5 * 1024 * 1024:
        external = Path('/Volumes/WD-Elements/a2a-evidence/2026-10-11-batch13/T-076/card-2') / label
        external.mkdir(parents=True, exist_ok=True)
        archived = external / target.name
        with target.open('rb') as source, archived.open('xb') as dest:
            shutil.copyfileobj(source, dest)
        # Byte comparison verifies this one newly made archive copy. No hash or
        # source directory is altered, and earlier artifacts are never removed.
        if target.read_bytes() != archived.read_bytes():
            raise RuntimeError('External archive byte readback differs.')
        save(target.with_suffix(target.suffix + '.pointer.json'), {'archive': str(archived), 'bytes': archived.stat().st_size})
        target.unlink()
        return str(archived)
    return str(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['stage-1', 'stage-2', 'stage-3'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base_out = args.output.resolve()
    if args.stage == 'stage-1':
        base_out.mkdir(parents=True, exist_ok=False)
    elif not base_out.is_dir():
        raise RuntimeError('Run stage-1 with this new label first.')
    out = base_out / args.stage
    out.mkdir(exist_ok=False)
    commands = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'task': 'T-076-2',
              'ready_rev': 1, 'baseline': BASELINE, 'stage': args.stage, 'argv': sys.argv,
              'real_codex_turns': 0, 'steps': [], 'deferred_contracts': DEFERRED,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    child_artifacts = []
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk is not mounted; no build/cache fallback or installation.')
        node = commands.run(['node', '--version'], cwd=ROOT, env=env)
        if node.returncode or not node.stdout.strip().startswith('v26.5.'):
            raise RuntimeError('This frozen fixture requires the approved Node 26.5 series.')
        if args.stage == 'stage-1':
            for argv in (['git', '--version'], [sys.executable, '--version'], ['git', 'rev-parse', 'HEAD'],
                         ['git', 'status', '--short'], ['git', 'diff', BASELINE, '--', 'workbench/src', 'workbench/hooks'],
                         ['git', 'diff', BASELINE, '--', 'acceptance/test_coop_e2e.py',
                          'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py']):
                p = commands.run(argv, cwd=ROOT, env=env)
                if p.returncode:
                    raise RuntimeError('Read-only preflight command failed.')
                if argv[:2] == ['git', 'diff'] and p.stdout:
                    raise RuntimeError('Baseline product/acceptance paths changed; preserve diff and ask controller before running this prepared stage.')
            temporary = Path(tempfile.mkdtemp(prefix='q76src-', dir='/tmp')).resolve()
            source = temporary / 'source'
            source.mkdir()
            archive = out / 'baseline-source.tar.gz'
            p = commands.run(['git', 'archive', '--format=tar.gz', BASELINE, 'workbench'], cwd=ROOT,
                             env=env, stdout_file=archive)
            if p.returncode:
                raise RuntimeError('Could not freeze the pinned baseline.')
            extract_owned_archive(archive, source)
            dependencies = (ROOT / 'workbench/node_modules').resolve()
            if not dependencies.is_dir():
                raise RuntimeError('Existing dependencies are unavailable; this script never installs.')
            (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
            for name in HARNESS:
                target = source / 'workbench/tests' / name
                if target.exists():
                    # Only baseline's identical command_evidence helper already
                    # exists. Refuse a changed helper instead of replacing it.
                    if target.read_bytes() != (ROOT / 'workbench/tests' / name).read_bytes():
                        raise RuntimeError('Frozen baseline helper differs from the prepared harness: ' + name)
                else:
                    with target.open('xb') as stream:
                        stream.write((ROOT / 'workbench/tests' / name).read_bytes())
            with tarfile.open(out / 'harness-source.tar.gz', 'x:gz') as saved:
                for name in HARNESS:
                    saved.add(source / 'workbench/tests' / name, arcname='workbench/tests/' + name)
            npm = source / 'workbench/package.json'
            metadata = json.loads(npm.read_text(encoding='utf-8'))
            probe = commands.run(['node', '--input-type=module', '-e',
                'import {createRequire} from "node:module"; const r=createRequire(process.argv[1]); '
                'for(const n of ["node-pty","effect"]){console.log(JSON.stringify({name:n,path:r.resolve(n)}));}', str(npm)], cwd=source, env=env)
            if probe.returncode:
                raise RuntimeError('Pinned source dependencies cannot be resolved.')
            save(base_out / 'preparation.json', {'baseline': BASELINE, 'source': str(source),
                 'dependencies': str(dependencies), 'dependency_versions_requested': metadata['dependencies'],
                 'harness': list(HARNESS), 'real_codex_turns': 0, 'source_archive': str(archive),
                 'no_auth_copy': True, 'no_real_codex_version_probe': True})
            save(out / 'deferred-contracts.json', DEFERRED)
            record.update(status='PASS', source=str(source), scope='preparation only; no business test has run')
        else:
            prep = json.loads((base_out / 'preparation.json').read_text(encoding='utf-8'))
            source = Path(prep['source'])
            if prep['baseline'] != BASELINE or not source.is_dir():
                raise RuntimeError('Prepared baseline identity/path is unavailable; no automatic reconstruction.')
            for name in HARNESS:
                if (ROOT / 'workbench/tests' / name).read_bytes() != (source / 'workbench/tests' / name).read_bytes():
                    raise RuntimeError('Harness changed after stage-1; use a new label instead of mixing evidence.')
            prerequisite = base_out / ('stage-1' if args.stage == 'stage-2' else 'stage-2') / 'run.json'
            if json.loads(prerequisite.read_text(encoding='utf-8'))['status'] != 'PASS':
                raise RuntimeError('Previous stage is not complete; controller disposition required.')

            def child(name, selected_source, group, case=None):
                target = out / name
                argv = [sys.executable, '-B', source / 'workbench/tests/test_quality_chain_e2e.py',
                        '--source', selected_source, '--output', target, '--group', group, '--card-dialect', 'legacy']
                if case:
                    argv.extend(['--case', case])
                result = commands.run(argv, cwd=source, env=env, timeout=300,
                                      stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
                report_path = target / 'run.json'
                value = json.loads(report_path.read_text(encoding='utf-8')) if report_path.is_file() else None
                step = {'name': name, 'exit': result.returncode, 'result_path': str(report_path),
                        'command': result.evidence, 'report': value}
                record['steps'].append(step)
                save(out / (name + '.receipt.json'), step)
                if value:
                    child_artifacts.append(Path(value['artifact_root']))
                if value is None or any(row['outcome'] == 'harness_error' or row['cleanup_failures'] for row in value['cases']):
                    raise RuntimeError('Fixture/product protocol error: preserve original output, stop, and report to controller: ' + name)
                if value['planned_cases'] != [row['case'] for row in value['cases']]:
                    raise RuntimeError('Suite did not run every planned case: ' + name)
                return result, value

            if args.stage == 'stage-2':
                result, report = child('baseline-contracts', source, 'red')
                actual = {row['case']: row for row in report['cases']}
                expected = list(RED_CASES)
                if (result.returncode != 1 or list(actual) != expected or any(
                    actual[name]['outcome'] != 'contract_failure' or actual[name].get('failure_id') != RED_CASES[name]
                    for name in expected)):
                    raise RuntimeError('Baseline did not fail at exactly the independently declared business assertions.')
                record.update(status='PASS', scope='expected contract red captured; not product acceptance',
                              expected_red_ids=RED_CASES)
            else:
                result, report = child('baseline-controls', source, 'controls')
                if result.returncode or report['status'] != 'PASS' or len(report['cases']) != len(CONTROL_CASES):
                    raise RuntimeError('Existing-boundary controls did not pass; do not run mutants.')
                mutations = [
                    ('fence-disabled', 'control_fence', 'CONTROL-FENCE',
                     'requireGate(args.fence === attempt.fence, "stale_fence");',
                     'requireGate(true, "stale_fence");'),
                    ('candidate-freeze-disabled', 'control_frozen_candidate', 'CONTROL-FROZEN',
                     '!task.candidate_commit || task.candidate_commit === commit,', 'true, // T-076-2 test mutant: candidate guard removed'),
                    ('path-guard-disabled', 'control_paths', 'CONTROL-PATH',
                     'requireGate(forbidden.length === 0, "path_boundary_failed", { forbidden });',
                     'requireGate(true, "path_boundary_failed", { forbidden });'),
                ]
                for name, case, failure_id, old, new in mutations:
                    mutant = source.parent / name
                    shutil.copytree(source, mutant, symlinks=True)
                    file = mutant / 'workbench/src/gates/core.ts'
                    content = file.read_text(encoding='utf-8')
                    if content.count(old) != 1:
                        raise RuntimeError('Mutation target is not unique in pinned baseline: ' + name)
                    file.write_text(content.replace(old, new), encoding='utf-8')
                    save(out / (name + '.mutation.json'), {'source': str(source), 'mutant': str(mutant),
                         'file': 'workbench/src/gates/core.ts', 'before': old, 'after': new,
                         'case': case, 'expected_failure_id': failure_id, 'production_checkout_edited': False})
                    result, report = child(name, mutant, 'controls', case)
                    row = report['cases'][0]
                    if result.returncode != 1 or row['outcome'] != 'contract_failure' or row.get('failure_id') != failure_id:
                        raise RuntimeError('Known-bad product mutant was not caught by its business assertion: ' + name)
                record.update(status='PASS', scope='existing-boundary controls and three explicit product mutants; new review/score/limit cases remain deferred')
    except Exception as error:
        record.update(status='INCOMPLETE', error=repr(error), traceback=traceback.format_exc())
    finally:
        record['artifacts'] = []
        for index, path in enumerate(child_artifacts):
            try:
                target = out / ('fixture-%02d.tar.gz' % index)
                record['artifacts'].append({'fixture': str(path), 'archive': archive_directory(path, target, base_out.name + '-' + args.stage)})
            except Exception as error:
                record.update(status='INCOMPLETE', archive_error=repr(error))
        record['oversize_files'] = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
        # Raw outputs are preserved even if large. This list prevents them from
        # silently entering Git; the controller receives it with the stage report.
        record['ended_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save(out / 'run.json', record)
        print(json.dumps({k: record[k] for k in ('status', 'product_status', 'stage', 'real_codex_turns')}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
