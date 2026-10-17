"""Run one unchanged acceptance method on two historical trees; no provider CLI/model."""
import argparse
import difflib
import gzip
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
CASE = 'test_submit_requires_clean_head_and_cannot_replace_frozen_candidate'
VERSIONS = [('pre-T082', '150ef6516'), ('main-T082', '0e6c2b833')]
RUNNER = 'workbench/tests/run_s3_rebased_regression.py'
PROTECTED = ['workbench/src', 'workbench/app', 'acceptance', 'fixtures', 'scripts']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE, text=True).strip()


def read_json(path): return json.loads(Path(path).read_bytes())


def project_events(folder):
    matches = []
    for path in sorted((folder / 'readbacks').glob('*.json')):
        value = read_json(path)
        if not value['test'].endswith('.' + CASE): continue
        records = []
        for row in value['tables']['events']:
            if not row['type'].startswith('review_'): continue
            data = json.loads(row['details']); review = data.get('review', {})
            records.append({'seq': row['seq'], 'type': row['type'], 'review_id': data.get('review_id', review.get('review_id')),
                            'candidate': review.get('candidate_commit'), 'shared_refs': review.get('shared_refs'),
                            'phase': data.get('phase'), 'error': data.get('details', {}).get('error')})
        matches.append({'source': str(path), 'review_events': records})
    return matches


def verify_archive(root, archive_path):
    """Verify original fixture bytes before removing this run's short /tmp root."""
    paths = [root]
    for parent, directories, files in os.walk(root, followlinks=False):
        paths += [Path(parent) / name for name in directories + files]
    with tarfile.open(archive_path) as archive:
        members = {item.name: item for item in archive.getmembers()}
        assert len(members) == len(paths)
        for path in paths:
            name = str(path.relative_to(root.parent)); member = members[name]; mode = path.lstat().st_mode
            if stat.S_ISLNK(mode): assert member.issym() and member.linkname == os.readlink(path)
            elif stat.S_ISDIR(mode): assert member.isdir()
            elif stat.S_ISREG(mode): assert member.isfile() and archive.extractfile(member).read() == path.read_bytes()
            else: raise RuntimeError('unsupported fixture archive member: ' + str(path))
    return len(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true'); args = parser.parse_args(); out = args.output.resolve()
    assert out.parent == BASE and not out.exists()
    revisions = [(name, git('rev-parse', revision)) for name, revision in VERSIONS]
    assert not git('diff', revisions[0][1], revisions[1][1], '--', 'acceptance/test_coop_e2e.py')
    overlay = (SOURCE / RUNNER).read_bytes()
    for _, revision in revisions:
        for relative in [RUNNER, 'acceptance/test_coop_e2e.py', 'workbench/tests/legacy_quality_driver.py',
                         'workbench/tests/daemon_acceptance_adapter.py', 'workbench/src/gates/core.ts']:
            subprocess.check_output(['git', 'cat-file', '-e', revision + ':' + relative], cwd=SOURCE)
    assert (SOURCE / 'workbench/node_modules').is_dir()
    if args.check_only:
        print(json.dumps({'status': 'PASS', 'scope': 'Git object and dependency-path checks only; no clone/host/test',
              'revisions': revisions, 'case': CASE, 'acceptance_same_bytes': True,
              'overlay': RUNNER + ' only: current case-selection/evidence runner, not business assertions',
              'vendor_CLI_starts': 0, 'model_turns': 0})); return 0
    assert not git('diff', 'HEAD', '--', *PROTECTED, RUNNER)
    out.mkdir(exist_ok=False)
    scratch = Path(tempfile.mkdtemp(prefix='t078-f4-cmp-', dir='/private/tmp')).resolve()
    env = {key: value for key, value in os.environ.items() if not key.startswith(('A2A_', 'GIT_', 'COOP_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_', 'OPENAI_', 'NODE_COMPILE_CACHE'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1')
    record = {'status': 'INCOMPLETE', 'scope': 'Cross-version diagnostic capture, not product acceptance or a fix',
              'case': CASE, 'scratch': str(scratch), 'scratch_removed': False, 'cases': [],
              'real_model_turns': 0, 'vendor_CLI_starts': 0, 'source_unchanged': True}
    def save(): (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    def command(argv, cwd=SOURCE, timeout=60):
        return subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=True)
    save()
    try:
        for name, revision in revisions:
            folder = out / name; folder.mkdir(); checkout = scratch / name
            command(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--shared', '--no-checkout', SOURCE, checkout])
            command(['git', '-C', checkout, 'sparse-checkout', 'init', '--cone'])
            command(['git', '-C', checkout, 'sparse-checkout', 'set', 'workbench', 'acceptance', 'fixtures', 'scripts', '.project-map'])
            command(['git', '-C', checkout, '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', revision])
            assert command(['git', '-C', checkout, 'rev-parse', 'HEAD']).stdout.strip() == revision
            # Only disposable source dependency directories are linked. No dist/build outputs are linked or built.
            modules = checkout / 'workbench/node_modules'; assert not modules.exists()
            modules.symlink_to((SOURCE / 'workbench/node_modules').resolve(), target_is_directory=True)
            original = (checkout / RUNNER).read_bytes()
            (folder / 'historical-runner.py').write_bytes(original)
            (folder / 'runner-overlay.py').write_bytes(overlay)
            (folder / 'runner-overlay.diff').write_text(''.join(difflib.unified_diff(original.decode().splitlines(True), overlay.decode().splitlines(True), fromfile=revision + '/' + RUNNER, tofile='current-runner-only')), encoding='utf-8')
            (checkout / RUNNER).write_bytes(overlay)
            assert not command(['git', '-C', checkout, 'diff', '--name-only', revision, '--', *PROTECTED]).stdout.strip()
            assert command(['git', '-C', checkout, 'diff', '--name-only', revision, '--', 'workbench/tests']).stdout.splitlines() == [RUNNER]
            child_out = folder / 'case'
            argv = [sys.executable, '-B', str(checkout / RUNNER), '--suite', 'coop', '--case', CASE, '--revision', revision, '--output', str(child_out)]
            row = {'name': name, 'revision': revision, 'argv': argv, 'timeout_seconds': 180, 'status': 'INCOMPLETE',
                   'fixture_overlay': [RUNNER], 'acceptance_or_product_changes': []}
            record['cases'].append(row); save(); started = time.time()
            with (folder / 'stdout.bin').open('xb') as stdout, (folder / 'stderr.bin').open('xb') as stderr:
                child = subprocess.Popen(argv, cwd=checkout, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
                row['runner_pid'] = child.pid; save()
                code = child.wait(timeout=180)
            row['exit_code'] = code; result = read_json(child_out / 'run.json')
            assert result['tests_run'] == 1 and result['selected_case'] == CASE and result['skipped'] == 0
            assert code in [0, 1] and not result['collection_errors']
            row.update(test_status=result['status'], failures=result['failures'], errors=result['errors'],
                       error_text=result['error_text'], saved_review_events=project_events(child_out))
            artifacts = json.loads(gzip.decompress((child_out / 'artifacts.json.gz').read_bytes()))
            for artifact in artifacts:
                for generation in artifact['daemons']:
                    assert generation.get('confirmed_exited'), 'host exit unknown; retain scratch, no cleanup'
                    observed = subprocess.run(['/bin/ps', '-p', str(generation['pid']), '-o', 'pid='], capture_output=True, text=True)
                    assert observed.returncode == 1 and not observed.stdout.strip(), 'PID still exists; retain all roots'
            fixture = Path(result['artifact_root']).resolve()
            assert fixture.parent == Path('/private/tmp') and fixture.name.startswith('s3f-') and not fixture.is_symlink()
            assert fixture.stat().st_ctime >= started - 2 and artifacts and all(Path(item['root']).is_relative_to(fixture) for item in artifacts)
            members = verify_archive(fixture, child_out / 'fixtures.tar.gz')
            shutil.rmtree(fixture); row.update(fixture_root_removed=True, verified_archive_members=members)
            assert not command(['git', '-C', checkout, 'diff', '--name-only', revision, '--', *PROTECTED]).stdout.strip()
            assert command(['git', '-C', checkout, 'diff', '--name-only', revision, '--', 'workbench/tests']).stdout.splitlines() == [RUNNER]
            row['status'] = 'CAPTURED'; save()
        shutil.rmtree(scratch); record.update(status='PASS', scratch_removed=True,
            verdict='Both single-case outcomes captured; inspect each test_status/error/event. This PASS is not a business PASS.')
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc(), scratch_retained=scratch.exists(),
                      action='stop; no retry, signal, reset, or deletion of unconfirmed fixture')
    save(); print(json.dumps({key: record.get(key) for key in ['status', 'output', 'scratch_removed', 'error']}, ensure_ascii=False))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
