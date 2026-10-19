#!/usr/bin/env python3
"""隔离 Git/文件系统反例。不写外置盘，不启动模型，不替换真实仓库。"""
import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def env():
    result = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_CONFIG_', 'A2A_'))}
    result.update(GIT_AUTHOR_NAME='T101 fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                  GIT_COMMITTER_NAME='T101 fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid',
                  PYTHONDONTWRITEBYTECODE='1')
    return result


def command(argv, cwd=None):
    result = subprocess.run(argv, cwd=cwd, env=env(), capture_output=True)
    assert result.returncode == 0, 'fixture command failed: ' + argv[0]
    return result.stdout


def repo(path, with_secret=False):
    path.mkdir()
    command(['git', 'init', '-b', 'main'], path)
    (path / 'README.md').write_text('独立中文输入 café\n', encoding='utf-8')
    if with_secret:
        folder = path / 'evidence/batch/task/run-01'
        folder.mkdir(parents=True)
        # 只在 /tmp 夹具中组合公开合成 sentinel，不在仓库文本中放完整 token。
        sentinel = 'sk-' + 'X7' * 20
        (folder / 'session.jsonl').write_text(sentinel + '\n', encoding='utf-8')
        (folder / 'auth.json').write_text('{}\n', encoding='utf-8')
        (folder / 'same.txt').write_text('same blob\n', encoding='utf-8')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], path)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture first version'], path)
    if with_secret:
        (folder / 'session.jsonl').unlink()
        (folder / 'auth.json').unlink()
        (folder / 'same.txt').rename(folder / 'renamed.txt')
        command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '-A'], path)
        command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture removes sensitive history from tip only'], path)
    for branch in ('exec/t101', 'exec/t102'):
        command(['git', 'branch', branch], path)


def missing_mount(module, root):
    root.mkdir()
    module.VOLUME = root / 'ordinary-unmounted-directory'
    module.VOLUME.mkdir()
    module.BASE = module.VOLUME / 'backup'
    module.ARCHIVES = module.VOLUME / 'archives'
    module.SOURCE = root / 'source'
    repo(module.SOURCE)
    before = module.disk_tree(root)
    saved = sys.argv
    sys.argv = ['slim_history.py', 'backup', 'probe']
    try:
        try:
            module.main()
        except ValueError as error:
            assert '未真实挂载' in str(error), 'unexpected failure reason'
        else:
            raise AssertionError('unmounted directory accepted')
    finally:
        sys.argv = saved
    assert module.disk_tree(root) == before, 'unmounted invocation changed files'


def count_mismatch(module, installer, root):
    root.mkdir()
    source = root / 'source'
    repo(source)
    run = root / 'run'
    run.mkdir()
    shutil.copytree(source, run / 'repository')
    shutil.copytree(source, run / 'prepared')
    command(['git', 'clone', '--mirror', '--no-local', str(source), str(run / 'candidate.git')])
    head = command(['git', 'rev-parse', 'HEAD'], source).decode().strip()
    module.save(run / 'verified.json', {'status': 'PASS', 'head': head, 'refs': module.refs(run / 'prepared')})
    module.save(run / 'credential-scan.json', {'hit_count': 0})
    module.save(run / 'backup.json', {'objects': module.object_count(source) + 1})
    module.save(run / 'snapshot.json', module.stable_snapshot(source))
    module.save(run / 'archives.json', {})
    installer.SOURCE = source
    installer.same_count = module.same_count
    previous = os.environ.get('A2A_T101_QUIESCENT')
    os.environ['A2A_T101_QUIESCENT'] = '1'
    try:
        try:
            installer.install(run)
        except ValueError as error:
            assert '备份对象数不一致' in str(error), 'unexpected failure reason'
        else:
            raise AssertionError('count mismatch reached installation')
    finally:
        if previous is None:
            os.environ.pop('A2A_T101_QUIESCENT', None)
        else:
            os.environ['A2A_T101_QUIESCENT'] = previous
    assert not (run / 'install-intent.json').exists(), 'installation started despite mismatch'
    assert (source / '.git').is_dir(), 'source Git was replaced'
    assert not (root / '.a2a-git-pre-slim-run').exists(), 'source Git was moved'


def preserve_dirty_and_parallel(module, installer, root):
    root.mkdir()
    source = root / 'source'
    repo(source)
    (source / 'records').mkdir()
    (source / 'records/launches.jsonl').write_text('committed launch\n', encoding='utf-8')
    raw = source / 'evidence/batch/task/run/raw.bin'
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b'fixture raw bytes')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture tracked inputs'], source)
    parallel = root / 't102'
    command(['git', 'worktree', 'add', str(parallel), 'exec/t102'], source)
    (parallel / 'package.txt').write_text('T102 parallel delivery\n', encoding='utf-8')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], parallel)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'T102 fixture delivery'], parallel)
    # 包含主分支自己的记录提交，所以保留一个真实 merge 拓扑。
    command(['git', '-c', 'core.hooksPath=/dev/null', 'merge', '--no-edit', 'exec/t102'], source)
    prepared = root / 'run/prepared'
    prepared.mkdir(parents=True)
    for path in module.tree(source):
        target = prepared / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / path, target)
    # 用独立 Git 根模拟已改写的候选，仅测试安装，不把它算作 filter-repo 证据。
    command(['git', 'init', '-b', 'main'], prepared)
    (prepared / 'README.md').write_text('candidate public README\n', encoding='utf-8')
    (prepared / 'evidence/batch/task/run/raw.bin').unlink()
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], prepared)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'independent replacement fixture'], prepared)
    for branch in ('exec/t101', 'exec/t102'):
        command(['git', 'branch', branch], prepared)
    user_bytes = b'committed launch\nuser appended launch\n'
    (source / 'records/launches.jsonl').write_bytes(user_bytes)
    inbox = source / '.project-map/inbox/pending.md'
    inbox.parent.mkdir(parents=True)
    inbox.write_text('uncommitted user inbox\n', encoding='utf-8')
    run = root / 'run'
    shutil.copytree(source, run / 'repository', symlinks=True)
    command(['git', 'clone', '--mirror', '--no-local', str(prepared), str(run / 'candidate.git')])
    head = command(['git', 'rev-parse', 'HEAD'], prepared).decode().strip()
    module.save(run / 'verified.json', {'status': 'PASS', 'head': head, 'refs': module.refs(prepared)})
    module.save(run / 'credential-scan.json', {'hit_count': 0})
    module.save(run / 'backup.json', {'objects': module.object_count(source)})
    module.save(run / 'snapshot.json', module.stable_snapshot(source))
    module.save(run / 'archives.json', {})
    installer.SOURCE = source
    previous = os.environ.get('A2A_T101_QUIESCENT')
    os.environ['A2A_T101_QUIESCENT'] = '1'
    try:
        installer.install(run)
    finally:
        if previous is None:
            os.environ.pop('A2A_T101_QUIESCENT', None)
        else:
            os.environ['A2A_T101_QUIESCENT'] = previous
    assert (source / 'records/launches.jsonl').read_bytes() == user_bytes
    assert inbox.read_text(encoding='utf-8') == 'uncommitted user inbox\n'
    assert (source / 'README.md').read_text(encoding='utf-8') == 'candidate public README\n'
    assert command(['git', 'show', 'exec/t102:package.txt'], source) == b'T102 parallel delivery\n'
    assert command(['git', 'show', 'HEAD:package.txt'], parallel) == b'T102 parallel delivery\n'
    assert not raw.exists()
    assert (run / 'repository/evidence/batch/task/run/raw.bin').read_bytes() == b'fixture raw bytes'


def historical_secret(module, root):
    root.mkdir()
    source = root / 'source'
    repo(source, with_secret=True)
    versions = module.history_versions(source)
    assert 'evidence/batch/task/run-01/same.txt' in versions
    assert 'evidence/batch/task/run-01/renamed.txt' in versions, 'same blob at second path omitted'
    report = root / 'scan.json'
    try:
        module.scan(source, report)
    except ValueError as error:
        assert '凭据扫描命中' in str(error)
    else:
        raise AssertionError('historical credentials accepted')
    result = json.loads(report.read_text(encoding='utf-8'))
    assert {'vendor-key', 'auth-file-or-cli-home-copy'} <= {row['type'] for row in result['hits']}, 'historical vendor key or auth-copy detection missing'
    assert ('sk-' + 'X7' * 20) not in report.read_text(encoding='utf-8'), 'secret leaked into evidence'
    # 当前 tree 无此文件，但扫描必须仍覆盖前一个提交。
    assert not (source / 'evidence/batch/task/run-01/session.jsonl').exists()


def merge_only_blob(module, root):
    root.mkdir()
    source = root / 'source'
    repo(source)
    command(['git', 'checkout', '-b', 'side'], source)
    (source / 'README.md').write_text('side\n', encoding='utf-8')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-am', 'side'], source)
    command(['git', 'checkout', 'main'], source)
    (source / 'README.md').write_text('main\n', encoding='utf-8')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-am', 'main'], source)
    conflict = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'merge', 'side'], cwd=source,
                              env=env(), capture_output=True)
    assert conflict.returncode == 1, 'fixture must produce a real merge conflict'
    (source / 'README.md').write_text('merge resolution unique to merge commit\n', encoding='utf-8')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', 'README.md'], source)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'resolve merge'], source)
    oid = command(['git', 'rev-parse', 'HEAD:README.md'], source).decode().strip()
    assert oid in module.history_versions(source)['README.md'], 'merge-only blob version omitted'


def archive_and_links(module, root):
    root.mkdir()
    run = root / 'run'
    run.mkdir()
    source = run / 'repository'
    repo(source)
    raw = 'evidence/batch/task/run/raw.bin'
    group = 'evidence/batch/task/run'
    path = source / raw
    path.parent.mkdir(parents=True)
    versions = {}
    for text in (b'\0old', b'\0new-longer'):
        path.write_bytes(text)
        command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
        command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'fixture blob version'], source)
        oid = command(['git', 'rev-parse', 'HEAD:' + raw], source).decode().strip()
        versions[oid] = text
    old_manifest = source / (group + '.archive.json')
    old_manifest.write_bytes(b'{"previous":true}\n')
    command(['git', '-c', 'core.hooksPath=/dev/null', 'add', '.'], source)
    command(['git', '-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'existing manifest'], source)
    module.ARCHIVES = root / 'simulated-external-archive'
    data = {'remove': {raw: {'group': group, 'versions': list(versions),
                             'bytes': len(b'\0old') + len(b'\0new-longer')}},
            'sizes': {oid: len(content) for oid, content in versions.items()}}
    manifests = module.archive(run, data)
    assert len(manifests) == 1
    manifest_path, row = next(iter(manifests.items()))
    assert row['original'] == group and row['files'] == 2 and row['bytes'] == 15
    index = module.read(Path(row['index']))
    assert len(index) == 2 and {v['object'] for v in index} == versions.keys()
    for entry in index:
        assert (Path(row['archive']) / 'versions' / entry['file']).read_bytes() == versions[entry['object']], 'archived content changed'
    for name, entry in manifests.items():
        module.save(source / name, entry)
    (source / 'README.md').write_bytes(('[原始](%s "标题")\r\n![图像](<%s>)\r\n[历史]: %s\r\n' % (raw, raw, raw)).encode('utf-8'))
    edits = module.rewrite_links(source, data['remove'], manifests)
    result = (source / 'README.md').read_bytes()
    assert len(edits) == 3 and raw.encode() not in result, 'removed link target remains in Markdown'
    assert result.count(b'\r\n') == 3 and '标题'.encode() in result and '原始'.encode() in result
    assert b'![' not in result, 'manifest incorrectly rendered as image'
    assert old_manifest.read_bytes() == b'{"previous":true}\n', 'prior manifest overwritten'
    assert (source / manifest_path).is_file()


def run_probe(folder, name, test, mutation=None):
    target = folder / name
    target.mkdir()
    code = (HERE / 'slim_history.py').read_text(encoding='utf-8')
    if mutation:
        before, after = mutation
        assert before in code
        code = code.replace(before, after, 1)
    (target / 'slim_history.py').write_text(code, encoding='utf-8')
    shutil.copyfile(HERE / 'install_publish.py', target / 'install_publish.py')
    module = load(target / 'slim_history.py', name + '_slim')
    sys.modules['slim_history'] = module
    installer = load(target / 'install_publish.py', name + '_install')
    try:
        with (target / 'probe.stdout').open('x', encoding='utf-8') as output, contextlib.redirect_stdout(output):
            if test in (count_mismatch, preserve_dirty_and_parallel):
                test(module, installer, target / 'fixture')
            else:
                test(module, target / 'fixture')
    except (AssertionError, ValueError) as error:
        if mutation:
            return {'case': name, 'status': 'PASS', 'known_bad_rejected': True,
                    'observable': str(error)}
        raise
    assert not mutation, 'known-bad implementation passed acceptance probe'
    return {'case': name, 'status': 'PASS', 'known_bad_rejected': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists(), 'preserve previous report'
    root = Path(tempfile.mkdtemp(prefix='a2a-t101-check-', dir='/tmp')).resolve()
    rows = []
    cases = [
        ('missing-mount', missing_mount, None),
        ('missing-mount-mutant', missing_mount, ('and os.path.ismount(path)', 'and True')),
        ('object-count-mismatch', count_mismatch, None),
        ('object-count-mutant', count_mismatch, ('require(source_count == copied_count,', 'require(True,')),
        ('historical-secret', historical_secret, None),
        ('empty-scanner-mutant', historical_secret,
         ('def scan_bytes(data):\n', 'def scan_bytes(data):\n    return []\n')),
        ('merge-only-blob', merge_only_blob, None),
        ('merge-diff-mutant', merge_only_blob, ("'--root', '-m', '--format='", "'--root', '--format='")),
        ('preserve-dirty-and-parallel', preserve_dirty_and_parallel, None),
        ('archive-versions-and-links', archive_and_links, None),
        ('same-size-corrupt-archive-mutant', archive_and_links,
         ('handle.write(chunk)', 'handle.write(b"Z" * len(chunk))')),
    ]
    try:
        for name, test, mutation in cases:
            rows.append(run_probe(root, name, test, mutation))
        clean = root / 'clean-source'
        repo(clean)
        module = load(HERE / 'slim_history.py', 'clean_scan')
        module.scan(clean, root / 'clean-scan.json')
        rows.append({'case': 'clean-scan', 'status': 'PASS'})
        status = 'PASS'
    except (AssertionError, ValueError, OSError) as error:
        rows.append({'case': 'unexpected-failure', 'status': 'NO_GO', 'diagnostic': str(error)})
        status = 'NO_GO'
    args.report.write_text(json.dumps({'status': status, 'artifact_root': str(root), 'cases': rows,
                                       'limitations': '仅隔离保护与扫描反例；未安装 filter-repo，未验证真实全历史改写、外置盘复制、替换、push。'},
                                      ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(status + ' ' + str(args.report))
    raise SystemExit(0 if status == 'PASS' else 1)


if __name__ == '__main__':
    main()
