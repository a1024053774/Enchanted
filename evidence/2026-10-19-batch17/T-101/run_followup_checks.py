#!/usr/bin/env python3
"""主控 #7 追加要求：真实 Git/文件系统和已安装 filter-repo 的隔离验证。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_local_checks as fixture


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def modules():
    slim = load(HERE / 'slim_history.py', 'followup_slim')
    sys.modules['slim_history'] = slim
    migration = load(HERE / 'migrate_hashes.py', 'followup_migration')
    sys.modules['migrate_hashes'] = migration
    installer = load(HERE / 'install_publish.py', 'followup_install')
    return slim, migration, installer


def check_archive(root, legacy=False):
    root.mkdir()
    shim = (HERE / 'slim_history.py').read_text(encoding='utf-8')
    shim += '\nHERE=Path(' + repr(str(root)) + ')\nARCHIVES=HERE/"archive"\nmounted=lambda *args: None\n'
    (root / 'slim_history.py').write_text(shim, encoding='utf-8')
    script = root / 'RUN-OUTSIDE-07-archive-local.sh'
    if legacy:
        script.write_bytes(fixture.command(['git', 'show', 'b9efd67b9:evidence/2026-10-19-batch17/T-101/RUN-OUTSIDE-07-archive-local.sh'], HERE))
    else:
        script.write_bytes((HERE / script.name).read_bytes())
        shutil.copyfile(HERE / 'archive_local.py', root / 'archive_local.py')
    valid = root / 'a2a-t101-valid'
    valid.mkdir()
    (valid / 'input.txt').write_bytes(b'original fixture bytes\n')
    for name, source in [('local-checks-a', root / 'a2a-t101-missing'), ('local-checks-z', valid)]:
        (root / (name + '.json')).write_text(json.dumps({'artifact_root': str(source)}), encoding='utf-8')
    command = ['sh', str(script)]
    result = subprocess.run(command, capture_output=True, env=fixture.env())
    (root / 'first.stdout').write_bytes(result.stdout)
    (root / 'first.stderr').write_bytes(result.stderr)
    assert result.returncode == 0, 'missing source aborted the complete batch'
    target = root / 'archive/local-preparation/local-checks-z/input.txt'
    assert target.read_bytes() == b'original fixture bytes\n'
    assert not (root / 'local-checks-a.archive.json').exists(), 'missing source received a false archive manifest'
    missing = list(root.glob('local-checks-a.missing-*.json'))
    assert len(missing) == 1 and json.loads(missing[0].read_text())['status'] == 'INCOMPLETE'
    summary = [json.loads(p.read_text()) for p in root.glob('archive-local-*.json')]
    assert len(summary) == 1 and summary[0]['status'] == 'INCOMPLETE'
    assert {r['result'] for r in summary[0]['results']} == {'source_not_found', 'archived'}
    result = subprocess.run(command, capture_output=True, env=fixture.env())
    assert result.returncode == 0, 'partial rerun overwrote or rejected a verified archive'
    target.write_bytes(b'changed size')
    result = subprocess.run(command, capture_output=True, env=fixture.env())
    assert result.returncode != 0, 'corrupt existing archive was silently accepted'
    assert (valid / 'input.txt').read_bytes() == b'original fixture bytes\n'


def check_trial(root):
    root.mkdir()
    slim, migration, installer = modules()
    source = root / 'source'
    fixture.repo(source)
    for branch in ('exec/t103', 'exec/t104'):
        fixture.command(['git', 'branch', branch], source)
        work = root / branch.split('/')[1]
        fixture.command(['git', 'worktree', 'add', str(work), branch], source)
        (work / 'pending.txt').write_bytes(b'worker dirty original\n')
    for name in ('dispatch.jsonl', 'launches.jsonl', 'controller-poll.log'):
        (source / name).write_bytes(b'preexisting dirty bytes\n')
    inbox = source / '.project-map/inbox/pending.md'
    inbox.parent.mkdir(parents=True)
    inbox.write_bytes(b'untracked inbox\n')
    slim.SOURCE = source
    original_git = slim.git
    def advancing_git(repo, *args):
        result = original_git(repo, *args)
        if args[:2] == ('bundle', 'create'):
            # 固定 bundle 之后，真实 worker 分支提交并追加主仓库日志。
            worker = root / 't103'
            fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', 'pending.txt'], worker)
            fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'parallel advance'], worker)
            with (source / 'dispatch.jsonl').open('ab') as handle:
                handle.write(b'concurrent append\n')
        return result
    slim.git = advancing_git
    run = root / 'trial'
    slim.trial_backup(run)
    data = slim.read(run / 'backup.json')
    assert data['status'] == 'INCOMPLETE' and data['mode'] == 'trial'
    assert slim.read(run / 'trial-observations.json')['live_changed'] is True
    assert original_git(run / 'repository', 'rev-parse', 'refs/heads/exec/t103') != original_git(source, 'rev-parse', 'refs/heads/exec/t103')
    assert (source / 'dispatch.jsonl').read_bytes() == b'preexisting dirty bytes\nconcurrent append\n'
    assert inbox.read_bytes() == b'untracked inbox\n'
    assert (root / 't104/pending.txt').read_bytes() == b'worker dirty original\n'
    assert not (run / 'worktree-1').exists(), 'trial pretended to copy live working trees'
    for phase in (slim.verify, installer.install, installer.publish):
        try:
            phase(run)
        except ValueError as error:
            assert '试跑' in str(error)
        else:
            raise AssertionError('trial reached a formal phase')
    try:
        migration.migrate(run, None, True)
    except ValueError as error:
        assert '试跑' in str(error)
    else:
        raise AssertionError('trial reached migration phase')


def check_migration(root, empty_mutant=False):
    root.mkdir()
    slim, migration, _ = modules()
    source = root / 'source'
    fixture.repo(source)
    (source / 'payload.txt').write_bytes(b'independent expected input\n')
    raw = source / 'evidence/run/raw.bin'
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b'raw evidence fixture')
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'input with evidence'], source)
    old = fixture.command(['git', 'rev-parse', 'HEAD'], source).decode().strip()
    caller = 'workbench/tests/test_literal.py'
    code = ("import subprocess,sys\nfrom pathlib import Path\nrevisions=[%r,%r]\n"
            "for revision in revisions:\n value=subprocess.check_output(['git','show',revision+':payload.txt'])\n"
            " assert value==b'independent expected input\\n'\n"
            "Path(sys.argv[1]).write_text('PASS\\n',encoding='utf-8')\n" % (old[:9], old)).encode()
    (source / caller).parent.mkdir(parents=True)
    (source / caller).write_bytes(code.replace(b'\n', b'\r\n'))
    for name in ('.project-map/tickets/record.md', 'evidence/record.txt', 'records/record.txt'):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(old + '\n', encoding='utf-8')
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'hash literal callers'], source)
    run = root / 'run'
    run.mkdir()
    shutil.copytree(source, run / 'repository')
    candidate = run / 'candidate.git'
    fixture.command(['git', 'clone', '--mirror', '--no-local', str(source), str(candidate)])
    tool = Path('/Volumes/WD-Elements/a2a-backup-pre-slim/tools/bin/git-filter-repo')
    assert tool.is_file(), 'installed filter-repo unavailable; do not claim actual rewrite proof'
    fixture.command([str(tool), '--invert-paths', '--path', 'evidence/run/raw.bin', '--prune-empty', 'never',
                     '--prune-degenerate', 'never', '--preserve-commit-hashes', '--replace-refs', 'delete-no-add'], candidate)
    work = run / 'prepared'
    fixture.command(['git', 'worktree', 'add', str(work), 'main'], candidate)
    slim.save(run / 'backup.json', {'mode': 'formal-fixture', 'status': 'PASS', 'note': '隔离迁移测试收据，不是真实仓库备份'})
    mapping = migration.read_mapping(candidate / 'filter-repo/commit-map')
    assert mapping[old] != old
    if empty_mutant:
        migration.replace_literals = lambda raw, mapping: (raw, [])
    migration.migrate(run, None, True)
    config = root / 'suites.json'
    suite = {'argv': ['python3', '-B', caller, '{output}/result.txt'], 'timeout_seconds': 30, 'covers': []}
    slim.save(config, {'no_models': True, 'suites': [suite]})
    if not empty_mutant:
        try:
            migration.migrate(run, config)
        except ValueError as error:
            assert '缺少相关套件覆盖' in str(error)
        else:
            raise AssertionError('missing suite coverage accepted')
        assert not (run / 'hash-migration-intent.json').exists()
    suite['covers'] = [caller]
    config = root / 'suites-covered.json'  # 缺覆盖的原始配置保留，不覆盖失败输入。
    slim.save(config, {'no_models': True, 'suites': [suite]})
    parent = slim.git(work, 'rev-parse', 'HEAD').decode().strip()
    migration.migrate(run, config)
    result = slim.read(run / 'hash-migration-comparison.json')
    assert result['before'][0]['exit'] != 0 and result['after'][0]['exit'] == 0
    assert set(slim.git(work, 'diff', '--name-only', parent, 'HEAD').decode().splitlines()) == {caller}
    expected = code.replace(b'\n', b'\r\n').replace(old.encode(), mapping[old].encode()).replace(old[:9].encode(), mapping[old].encode())
    assert (work / caller).read_bytes() == expected, 'migration changed non-hash bytes or line endings'
    for name in ('.project-map/tickets/record.md', 'evidence/record.txt', 'records/record.txt'):
        assert (work / name).read_text(encoding='utf-8') == old + '\n', 'read-only record changed'
    slim.save(run / 'plan.json', {'remove': {'evidence/run/raw.bin': {}}, 'keep': {}})
    with (work / caller).open('ab') as output:
        output.write(b'assert False\r\n')
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'add', caller], work)
    fixture.command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'known bad logic mutation'], work)
    try:
        slim.verify(run)
    except ValueError as error:
        assert '源码差异超出哈希字面量迁移' in str(error), str(error)
    else:
        raise AssertionError('04 accepted a test logic mutation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    for key in list(os.environ):
        if key.startswith('GIT_CONFIG_'):
            os.environ.pop(key)
    os.environ.update(GIT_AUTHOR_NAME='T101 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                      GIT_COMMITTER_NAME='T101 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
                      PYTHONDONTWRITEBYTECODE='1')
    root = Path(tempfile.mkdtemp(prefix='a2a-t101-followup-', dir='/tmp')).resolve()
    cases = []
    status = 'PASS'
    try:
        for name, test, known_bad in [
            ('archive-missing-and-rerun', lambda p: check_archive(p), None),
            ('legacy-07-rejected', lambda p: check_archive(p, True), 'missing source aborted the complete batch'),
            ('live-trial-and-formal-stop', check_trial, None),
            ('actual-filter-migration-and-logic-guard', check_migration, None),
            ('no-op-migration-mutant', lambda p: check_migration(p, True), '迁移后相关套件失败')]:
            try:
                test(root / name)
            except (AssertionError, ValueError) as error:
                if not known_bad:
                    raise
                assert known_bad in str(error), 'known-bad probe failed for an unrelated reason: ' + str(error)
                cases.append({'case': name, 'status': 'PASS', 'known_bad_rejected': True, 'reason': str(error)})
            else:
                assert not known_bad, 'known-bad candidate accepted'
                cases.append({'case': name, 'status': 'PASS'})
    except (AssertionError, ValueError, OSError) as error:
        import traceback
        (root / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        cases.append({'case': 'unexpected-failure', 'status': 'NO_GO', 'reason': str(error)})
        status = 'NO_GO'
    args.report.write_text(json.dumps({'status': status, 'artifact_root': str(root), 'cases': cases,
                                       'scope': '07/活跃 refs 试跑/实际 filter-repo 小夹具/机械迁移前后套件；未复制或改写真实仓库'},
                                      ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(status + ' ' + str(args.report))
    raise SystemExit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
