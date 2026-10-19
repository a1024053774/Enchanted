#!/usr/bin/env python3
"""T-101 的离线准备入口；生产副作用只由 RUN-OUTSIDE 脚本调用。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import random
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

SOURCE = Path('/Users/luckye/Documents/Code/a2a')
VOLUME = Path('/Volumes/WD-Elements')
BASE = VOLUME / 'a2a-backup-pre-slim'
ARCHIVES = VOLUME / 'a2a-evidence/2026-10-19-batch17/T-101'
HERE = Path(__file__).resolve().parent
REL = Path('evidence/2026-10-19-batch17/T-101')
LIMIT = 5 * 1024 * 1024
REMOTE = 'a96a040d3d87e43e7fc882da9e574bed2dbcd2d4'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mounted(path=VOLUME):
    path = Path(path)
    require(path.is_dir() and not path.is_symlink() and path.resolve() == path
            and os.path.ismount(path), '外置盘未真实挂载；不创建目录、不回退内置盘')


def no_links(path):
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), '拒绝路径祖先中的符号链接')


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def git(repo, *args):
    # 不显示 Git 的错误正文：配置或会话内容可能含凭据。
    process = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    require(process.returncode == 0, 'Git 命令失败（未记录正文）：' + args[0])
    return process.stdout


def refs(repo):
    return git(repo, 'for-each-ref', '--format=%(refname) %(objectname)').decode().splitlines()


def worktrees(repo):
    return [Path(row[9:]) for row in git(repo, 'worktree', 'list', '--porcelain').decode().splitlines()
            if row.startswith('worktree ')]


def tree(repo, rev='HEAD'):
    result = {}
    for entry in git(repo, 'ls-tree', '-r', '-z', rev).split(b'\0'):
        if not entry:
            continue
        header, rawpath = entry.split(b'\t', 1)
        mode, kind, oid = header.decode().split()
        path = rawpath.decode('utf-8')
        require('\n' not in path and '\r' not in path and not path.startswith('/')
                and '..' not in PurePosixPath(path).parts, '不支持的 Git 路径；停止')
        result[path] = {'mode': mode, 'kind': kind, 'oid': oid}
    return result


def object_count(repo):
    return len(git(repo, 'cat-file', '--batch-all-objects', '--batch-check=%(objectname)').splitlines())


def reachable_count(repo):
    return len(git(repo, 'rev-list', '--objects', '--all', '--no-object-names').splitlines())


def same_count(source_count, copied_count):
    require(source_count == copied_count, '备份对象数不一致；禁止继续或替换')


def disk_tree(root):
    """核对目录复制的文件数/字节数与链接目标；不跟随链接、不计算校验值。"""
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            rel = str(path.relative_to(root))
            if path.is_symlink():
                result[rel] = ['link', os.readlink(path)]
            elif path.is_file():
                result[rel] = ['file', path.stat().st_size]
    return result


def stable_snapshot(repo):
    return {'refs': refs(repo), 'head': git(repo, 'rev-parse', 'HEAD').decode().strip(),
            'worktrees': {str(p): {'head': git(p, 'rev-parse', 'HEAD').decode().strip(),
                                  'branch': git(p, 'symbolic-ref', 'HEAD').decode().strip(),
                                  'status': git(p, 'status', '--porcelain=v1', '-z', '--untracked-files=all').hex()}
                          for p in worktrees(repo)}}


def backup(run):
    require(git(SOURCE, 'symbolic-ref', 'HEAD').strip() == b'refs/heads/main', '主仓库须停在 main；不备份错误分支作为替换基线')
    require(not run.exists(), 'run 已存在；改用新 run id，保留失败现场')
    run.mkdir(parents=True)
    before = stable_snapshot(SOURCE)
    save(run / 'snapshot.json', before)
    count = object_count(SOURCE)
    physical = git(SOURCE, 'count-objects', '-v').decode()
    git(SOURCE, 'bundle', 'create', str(run / 'all.bundle'), '--all')
    git(SOURCE, 'bundle', 'verify', str(run / 'all.bundle'))
    copies = {}
    for index, source in enumerate(worktrees(SOURCE)):
        target = run / ('repository' if source == SOURCE else f'worktree-{index}')
        inventory = disk_tree(source)
        shutil.copytree(source, target, symlinks=True)
        require(inventory == disk_tree(source) == disk_tree(target), '仓库目录复制核对不一致；保留现场')
        copies[str(source)] = str(target)
    copied = object_count(run / 'repository')
    same_count(count, copied)
    git(run, 'clone', '--mirror', '--no-local', str(run / 'all.bundle'), str(run / 'bundle-check.git'))
    same_count(reachable_count(SOURCE), reachable_count(run / 'bundle-check.git'))
    require(before == stable_snapshot(SOURCE), '复制期间 refs/工作区变动；停止，使用新 run 重做备份')
    save(run / 'backup.json', {'status': 'PASS', 'snapshot': before, 'copies': copies,
                              'objects': count, 'copy_objects': copied,
                              'bundle_reachable_objects': reachable_count(run / 'bundle-check.git'),
                              'git_count_objects': physical,
                              'git_bytes': sum(v[1] for v in disk_tree(SOURCE / '.git').values() if v[0] == 'file'),
                              'evidence_files': sum(p.startswith('evidence/') for p in tree(SOURCE))})
    print('PASS 备份与对象数核对；原件未修改，副本不得清理')


def trial_backup(run):
    """活跃开发期只固定已提交 refs；不是供替换使用的完整原仓库备份。"""
    require(git(SOURCE, 'symbolic-ref', 'HEAD').strip() == b'refs/heads/main', '主仓库须停在 main')
    require(not run.exists(), 'run 已存在；改用新 run id')
    run.mkdir(parents=True)
    before = stable_snapshot(SOURCE)
    git(SOURCE, 'bundle', 'create', str(run / 'all.bundle'), '--all')
    git(SOURCE, 'bundle', 'verify', str(run / 'all.bundle'))
    heads = [line.split() for line in git(run, 'bundle', 'list-heads', str(run / 'all.bundle')).decode().splitlines()]
    git(run, 'clone', '--mirror', '--no-local', str(run / 'all.bundle'), str(run / 'repository'))
    frozen = run / 'repository'
    # bundle 中具名 refs 是本次真正固定的边界；不把复制期间的 live refs 当作快照。
    expected_refs = sorted(ref + ' ' + oid for oid, ref in heads if ref.startswith('refs/'))
    require(refs(frozen) == expected_refs, 'bundle 与试跑副本 refs 不符')
    git(frozen, 'symbolic-ref', 'HEAD', 'refs/heads/main')
    snapshot = {'refs': refs(frozen), 'head': git(frozen, 'rev-parse', 'HEAD').decode().strip(),
                'worktrees': before['worktrees'], 'worktrees_scope': '仅观察，未复制或冻结这些工作区'}
    after = stable_snapshot(SOURCE)
    save(run / 'snapshot.json', snapshot)
    save(run / 'trial-observations.json', {'status': 'INCOMPLETE', 'before': before, 'after': after,
                                         'live_changed': before != after,
                                         'note': '允许 live refs、dirty 日志和活跃 worktree 前进；只处理 bundle 固定的提交'})
    save(run / 'backup.json', {'status': 'INCOMPLETE', 'mode': 'trial', 'snapshot': snapshot,
                              'objects': object_count(frozen), 'copies': {},
                              'note': '仅已提交 refs 的 bundle 与独立 mirror；不复制 dirty 文件/完整目录，不满足正式备份验收。禁止 04/05/06。'})
    print('INCOMPLETE 试跑提交快照已固定；未触碰 dirty 原件，不能用于正式替换')


def history_versions(repo):
    """raw diff 包含每个历史路径的每个 blob 版本；不只取 rev-list 的首个路径名。"""
    process = subprocess.Popen(['git', '-C', str(repo), 'log', '--all', '--root', '-m', '--format=',
                                '--raw', '--no-abbrev', '--no-renames', '-z'], stdout=subprocess.PIPE)
    versions = defaultdict(set)
    pending = b''
    header = None
    while True:
        chunk = process.stdout.read(1024 * 1024)
        if not chunk:
            break
        pending += chunk
        fields = pending.split(b'\0')
        pending = fields.pop()
        for field in fields:
            if header is None:
                if field.strip():
                    require(field.lstrip().startswith(b':'), '无法解析历史 raw diff')
                    header = field.lstrip()[1:].split()
            else:
                path = field.decode('utf-8')
                require('\n' not in path and '\r' not in path and '..' not in PurePosixPath(path).parts,
                        '历史路径无法安全归档')
                if header[1] != b'000000' and header[1] != b'160000':
                    versions[path].add(header[3].decode())
                header = None
    require(process.wait() == 0 and header is None and not pending.strip(), '历史枚举不完整')
    return {p: sorted(v) for p, v in versions.items()}


def sizes(repo, oids):
    process = subprocess.run(['git', '-C', str(repo), 'cat-file', '--batch-check=%(objectname) %(objectsize)'],
                             input=('\n'.join(sorted(oids)) + '\n').encode(), capture_output=True)
    require(process.returncode == 0, '无法读取对象大小')
    return {oid: int(size) for oid, size in (line.split() for line in process.stdout.decode().splitlines())}


def category(path, markers):
    parts = PurePosixPath(path).parts
    if not path.startswith('evidence/'):
        return None
    for i, part in enumerate(parts[1:-1], 1):
        prefix = '/'.join(parts[:i + 1])
        if (part in ('run', 'fixtures') or part.startswith(('run-', 'run_', 'fixtures-', 'fixtures_'))
                or part.endswith('-artifacts') or prefix in markers):
            return prefix
    name = parts[-1].lower()
    if (name.endswith(('.tar.gz', '.bin', '.sqlite', '.sqlite3', '.sqlite-wal', '.sqlite3-wal',
                       '.sqlite-shm', '.sqlite3-shm', '.sqlite-journal', '.sqlite3-journal', '.db', '.db-wal', '.db-shm'))
            or ('monitor' in name and name.endswith(('.log', '.jsonl', '.ndjson', '.txt', '.out')))):
        return path
    return None


def summary(path):
    name = PurePosixPath(path).name.lower()
    return (name == 'run.json' or name.endswith(('.md', '.archive.json', '.py', '.sh', '.bash', '.zsh'))
            or name.startswith(('review', 'controller-decision'))
            or (name.endswith(('.ts', '.js', '.mjs', '.cjs')) and name.startswith(
                ('run', 'check', 'test', 'prepare', 'verify', 'outside', 'replay', 'probe', 'record', 'readback'))))


def plan(run):
    backup_info = read(run / 'backup.json')
    require(backup_info['status'] == 'PASS' or backup_info.get('mode') == 'trial', '备份未通过')
    repo = run / 'repository'
    versions = history_versions(repo)
    object_sizes = sizes(repo, {oid for row in versions.values() for oid in row})
    markers = {str(PurePosixPath(p).parent) for p in versions if p.endswith('/run.json')}
    # 不把票根本身当整批 run。下层实际运行目录仍按标记分类。
    markers = {p for p in markers if len(PurePosixPath(p).parts) > 3}
    explicit = {line.strip() for line in (HERE / 'keep-paths.txt').read_text(encoding='utf-8').splitlines()
                if line.strip() and not line.startswith('#')}
    require(explicit <= versions.keys(), '指定小输入在历史中缺失；停止')
    current = tree(repo)
    source_text = b'\n'.join(git(repo, 'cat-file', 'blob', row['oid']) for p, row in current.items()
                             if not p.startswith('evidence/') and row['kind'] == 'blob'
                             and p.endswith(('.py', '.ts', '.mjs', '.js', '.sh')))
    removed, kept, review = {}, {}, []
    for path, blobs in versions.items():
        size = max(object_sizes[oid] for oid in blobs)
        group = category(path, markers)
        if not group and not (path.startswith('evidence/') and size > LIMIT):
            continue
        group = group or path
        referenced = path.encode() in source_text
        preserve = size <= LIMIT and (summary(path) or path in explicit or referenced)
        if preserve:
            kept[path] = 'explicit' if path in explicit else 'literal-reference' if referenced else 'summary/script'
        else:
            removed[path] = {'group': group, 'versions': blobs,
                             'bytes': sum(object_sizes[oid] for oid in blobs)}
            if size <= LIMIT and PurePosixPath(path).suffix in ('.json', '.txt', '.yaml', '.toml'):
                review.append(path)
    # constructed BASE / name 引用无法靠静态字面量证明；主控必须审查 plan 后再运行 rewrite。
    require(removed, '未找到可归档路径；拒绝空改写')
    save(run / 'plan.json', {'remove': removed, 'keep': kept, 'possible_inputs_to_review': review,
                             'sizes': object_sizes, 'source_refs': backup_info['snapshot']['refs']})
    (run / 'remove.txt').write_text(''.join('literal:' + p + '\n' for p in sorted(removed)), encoding='utf-8')
    save(run / 'plan-summary.json', {'status': 'INCOMPLETE', 'removed_paths': len(removed),
                                    'kept_paths': len(kept), 'possible_inputs': len(review),
                                    'note': '先审查 plan.json；构造路径输入须人工核对。未执行改写。'})
    print('INCOMPLETE 清单已生成；主控审查 remove/keep/possible_inputs 后才运行 rewrite')


def archive(run, data):
    repo = run / 'repository'
    root = ARCHIVES / run.name
    require(not root.exists(), '归档目录已存在；不覆盖')
    root.mkdir(parents=True)
    groups = defaultdict(list)
    for path, row in data['remove'].items():
        groups[row['group']].append((path, row))
    manifests = {}
    existing = tree(repo)
    for group, rows in groups.items():
        target = root / group
        payload = target / 'versions'
        expected = {}
        index = []
        reader = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for path, row in rows:
            for oid in row['versions']:
                relative = str(Path(oid) / path)
                output = payload / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                reader.stdin.write((oid + '\n').encode()); reader.stdin.flush()
                header = reader.stdout.readline().decode().split()
                require(header == [oid, 'blob', str(data['sizes'][oid])], '历史对象归档头不一致')
                with output.open('xb') as handle:
                    remaining = data['sizes'][oid]
                    while remaining:
                        chunk = reader.stdout.read(min(remaining, 1024 * 1024))
                        require(chunk, '历史对象归档意外结束')
                        handle.write(chunk)
                        remaining -= len(chunk)
                require(reader.stdout.read(1) == b'\n', '历史对象归档边界不一致')
                expected[relative] = ['file', data['sizes'][oid]]
                index.append({'original': path, 'object': oid, 'bytes': data['sizes'][oid], 'file': relative})
        reader.stdin.close()
        require(reader.wait() == 0, '历史对象归档进程失败')
        require(disk_tree(payload) == expected, '归档文件数/字节数不一致；禁止改写')
        save(target / 'index.json', index)
        manifest_path = group + '.T-101-' + run.name + '.archive.json'
        require(manifest_path not in existing, '已有同名清单；不能覆盖：' + manifest_path)
        manifests[manifest_path] = {'original': group, 'archive': str(target),
                                    'bytes': sum(row['bytes'] for _, row in rows),
                                    'files': len(expected), 'replay': ['python3', str(REL / 'replay_archive.py'), str(target / 'index.json'), 'NEW_OUTPUT_DIRECTORY'],
                                    'index': str(target / 'index.json'), 'scope': '各历史路径/blob 版本；摘要和小输入另留仓库'}
    save(run / 'archives.json', manifests)
    return manifests


def rewrite_links(work, removed, manifests):
    group_map = {row['original']: name for name, row in manifests.items()}
    mapping = {path: group_map[row['group']] for path, row in removed.items()}
    edits = []
    patterns = [re.compile(r'(!?\[[^\]\r\n]*\]\()([^\r\n)]+)(\))'),
                re.compile(r'^(\[[^\]\r\n]+\]:[ \t]*)([^\r\n]+)()', re.MULTILINE)]
    for path in sorted(work.rglob('*.md')):
        if path.is_symlink() or '.git' in path.parts:
            continue
        relative = path.relative_to(work).as_posix()
        text = path.read_bytes().decode('utf-8')
        def replace(match):
            payload = match[2]
            if payload.startswith('<'):
                raw, closing, tail = payload[1:].partition('>')
                require(closing, '无法解析 Markdown 角括号链接：' + relative)
                angle = True
            else:
                raw, space, title = payload.partition(' ')
                tail = space + title
                angle = False
            if ':' in raw or raw.startswith('#'):
                return match[0]
            target = posixpath.normpath(posixpath.join(posixpath.dirname(relative), unquote(raw.split('#')[0])))
            manifest = mapping.get(target)
            if manifest is None:
                manifest = group_map.get(target)
            if manifest is None:
                return match[0]
            updated = posixpath.relpath(manifest, posixpath.dirname(relative) or '.')
            edits.append({'document': relative, 'original': raw, 'manifest': updated})
            # 图像改为普通清单链接；清单不是图片。
            return match[1].lstrip('!') + ('<' + updated + '>' if angle else updated) + tail + match[3]
        updated = text
        for pattern in patterns:
            updated = pattern.sub(replace, updated)
        if updated != text:
            path.write_bytes(updated.encode('utf-8'))
    return edits


def rewrite(run):
    data = read(run / 'plan.json')
    same_count(read(run / 'backup.json')['objects'], object_count(run / 'repository'))
    require(refs(run / 'repository') == data['source_refs'], '备份 refs 与清单不一致')
    manifests = archive(run, data)
    candidate = run / 'candidate.git'
    git(run, 'clone', '--mirror', '--no-local', str(run / 'repository'), str(candidate))
    tool = BASE / 'tools/bin/git-filter-repo'
    require(tool.is_file(), '先运行 RUN-OUTSIDE-00-tools.sh')
    command = [str(tool), '--invert-paths', '--paths-from-file', str(run / 'remove.txt'),
               '--prune-empty', 'never', '--prune-degenerate', 'never',
               '--preserve-commit-hashes', '--replace-refs', 'delete-no-add']
    result = subprocess.run(command, cwd=candidate, capture_output=True)
    save(run / 'filter.json', {'argv': command, 'exit': result.returncode,
                              'output_omitted': '不记录 fast-export 或可能含凭据的正文'})
    require(result.returncode == 0, 'filter-repo 失败；保留现场，不用 --force 重试')
    scan(candidate, run / 'retained-initial-credential-scan.json')
    work = run / 'prepared'
    git(candidate, 'worktree', 'add', str(work), 'main')
    for path, content in manifests.items():
        save(work / path, content)
    records = work / 'records'
    records.mkdir(exist_ok=True)
    for name in ('commit-map', 'ref-map'):
        target = records / f'T-101-{run.name}-{name}.txt'
        require(not target.exists(), '映射文件已存在')
        shutil.copyfile(candidate / 'filter-repo' / name, target)
    edits = rewrite_links(work, data['remove'], manifests)
    save(work / REL / f'{run.name}-link-edits.json', edits)
    save(work / REL / f'{run.name}-summary.json', {
        'status': 'INCOMPLETE', 'backup': str(run), 'archive_root': str(ARCHIVES / run.name),
        'removed_paths': len(data['remove']), 'retained_paths': len(data['keep']),
        'linked_worktrees': read(run / 'snapshot.json')['worktrees'],
        'next': '审查生成的差异，处理旧哈希直接执行引用，提交后运行 verify；未替换，未 push'})
    print('INCOMPLETE 候选已准备：' + str(work) + '；先审查并提交生成文件，再运行 verify')


TOKEN_RULES = [
    ('vendor-key', rb'(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})'),
    ('private-key', rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'),
    ('jwt', rb'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}'),
    ('credential-assignment', rb'''(?i)["']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|client[_-]?secret|password|token)["']?\s*[:=]\s*["'][A-Za-z0-9_+/=.-]{12,}["']'''),
    ('authorization-bearer', rb'(?i)Bearer\s+[A-Za-z0-9_+/=.-]{20,}'),
    ('credential-in-url', rb'https?://[^\s/:@]{2,}:[^\s/@]{4,}@'),
]


def scan_bytes(data):
    return [{'type': kind, 'offset': match.start()} for kind, rule in TOKEN_RULES
            for match in re.finditer(rule, data)]


def scan(repo, report):
    versions = history_versions(repo)
    names = defaultdict(list)
    hits = []
    for path, blobs in versions.items():
        lower = path.lower()
        name = PurePosixPath(lower).name
        if name in ('auth.json', 'token', '.token', 'token.json', 'tokens.json', 'token.txt',
                    'credentials.json', '.credentials.json', 'id_rsa', 'id_ed25519') or any(p in ('.claude', '.codex') for p in PurePosixPath(lower).parts):
            hits.append({'path': path, 'type': 'auth-file-or-cli-home-copy'})
        for oid in blobs:
            names[oid].append(path)
    objects = git(repo, 'rev-list', '--objects', '--all', '--no-object-names').decode().splitlines()
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    count = 0
    for oid in objects:
        process.stdin.write((oid + '\n').encode()); process.stdin.flush()
        header = process.stdout.readline().decode().split()
        require(len(header) == 3, '凭据扫描对象读取失败')
        size = int(header[2])
        data = process.stdout.read(size)
        require(len(data) == size and process.stdout.read(1) == b'\n', '凭据扫描对象读取不完整')
        if header[1] in ('blob', 'commit', 'tag'):
            count += 1
            for hit in scan_bytes(data):
                hits.append(dict(hit, object=oid, paths=names.get(oid, ['git-' + header[1]])))
    process.stdin.close()
    require(process.wait() == 0, '凭据扫描进程失败')
    save(report, {'status': 'PASS' if not hits else 'NO_GO', 'scope': '所有 refs 可达 blob、commit、tag；所有历史路径',
                  'objects_scanned': count, 'hits': hits, 'hit_count': len(hits),
                  'limitations': '固定模式扫描，不能证明不存在加密、未知格式或任意编码的秘密；不自动豁免假 token。'})
    require(not hits, '凭据扫描命中；只报告位置/类型，停止并上报，不替换或 push')


def old_hash_commands(work, mapping):
    from migrate_hashes import eligible, replace_literals
    hits = []
    for name in git(work, 'ls-files', '-z').split(b'\0'):
        if not name:
            continue
        path = name.decode('utf-8')
        if eligible(path):
            raw = (work / path).read_bytes()
            _, edits = replace_literals(raw, mapping)
            for edit in edits:
                hits.append({'path': path, 'line': raw[:edit['offset']].count(b'\n') + 1,
                             'old': edit['old_literal'], 'new': edit['new_commit']})
    return hits


def verify(run):
    require(read(run / 'backup.json').get('mode') != 'trial', '试跑 run 不能进入 04；正式全员静止后用新 run 重做完整备份')
    from migrate_hashes import eligible, read_mapping, replace_literals
    work = run / 'prepared'
    require(not git(work, 'status', '--porcelain'), '候选尚有未提交文件；先审查并提交')
    migration = read(run / 'hash-migration.json')
    require(migration['status'] == 'PASS', '03b 哈希迁移与同套件对照未通过')
    mapping = read_mapping(run / 'candidate.git/filter-repo/commit-map')
    data = read(run / 'plan.json')
    versions = history_versions(work)
    require(not (data['remove'].keys() & versions.keys()), '归档路径仍存在保留历史中')
    old = tree(run / 'repository')
    new = tree(work)
    for path in data['keep']:
        if path in old:
            require(path in new, '保留输入/摘要缺失：' + path)
            if not path.endswith('.md'):
                require(old[path] == new[path], '保留输入内容改变：' + path)
    # 除主控 #7 授权的机械哈希迁移，所有代码/验收输入仍必须保持原 blob。
    for path, row in old.items():
        if not path.startswith(('evidence/', 'records/')) and not path.endswith('.md'):
            if eligible(path) and new.get(path) != row:
                require(path in new and new[path]['mode'] == row['mode'], '迁移不能改变调用方类型/模式：' + path)
                expected, edits = replace_literals(git(run / 'repository', 'cat-file', 'blob', row['oid']), mapping)
                require(edits and git(work, 'cat-file', 'blob', new[path]['oid']) == expected,
                        '源码差异超出哈希字面量迁移：' + path)
            else:
                require(new.get(path) == row, '源码/输入被意外改写：' + path)
    require(len(mapping) >= 5 and all(int(v, 16) for v in mapping.values()), '映射缺失或提交被删除')
    random_sample = random.SystemRandom().sample(sorted(mapping), 5)
    for oid in random_sample:
        require(git(work, 'cat-file', '-t', mapping[oid]).strip() == b'commit', '映射目标不是提交')
    save(run / 'mapping-sample.json', [{'old': old, 'new': mapping[old]} for old in random_sample])
    new_refs = dict(line.split() for line in refs(work))
    parallel = []
    for line in read(run / 'snapshot.json')['refs']:
        ref, old_oid = line.split()
        if ref.startswith('refs/heads/exec/'):
            require(old_oid in mapping and new_refs.get(ref) == mapping[old_oid], '并行分支未按映射表保留：' + ref)
            parallel.append({'ref': ref, 'old': old_oid, 'new': mapping[old_oid]})
    save(run / 'parallel-ref-map.json', parallel)
    scan(work, run / 'credential-scan.json')
    hash_calls = old_hash_commands(work, mapping)
    save(run / 'old-hash-commands.json', hash_calls)
    require(not hash_calls, '测试/脚本仍直接执行旧哈希；映射表不能替代调用方迁移，请主控处理')
    project_map = '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py'
    result = subprocess.run([sys.executable, project_map, 'status', '--root', str(work)], capture_output=True, text=True)
    save(run / 'project-map-status.json', {'argv': [sys.executable, project_map, 'status', '--root', str(work)],
                                        'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    require(result.returncode == 0, '完整候选的 project_map status 未通过')
    # 无模型的现有回归；每条都通过才生成机器绑定的 verify 收据。
    checks = [['python3', '-B', 'acceptance/test_dispatch_session_e2e.py'],
              ['python3', '-B', 'acceptance/test_inbox_e2e.py']]
    # 首轮真实测试的 git init 被调用者的会话钩子误接管。只隔离夹具子进程的
    # 进程级 Git 配置，不改用户/项目配置或现有测试；证据见 existing-checks-01。
    suite_env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_CONFIG_')}
    for index, command in enumerate(checks):
        command += ['--artifacts', str(run / f'check-{index}-artifacts')]
        result = subprocess.run(command, cwd=work, capture_output=True, env=suite_env)
        save(run / f'check-{index}.json', {'argv': command, 'exit': result.returncode,
                                         'environment': '夹具子进程移除继承的 GIT_CONFIG_*；不写全局配置',
                                         'output_omitted': '原始输出可能含会话正文，主控如需诊断须在外置盘受限现场核对'})
        require(result.returncode == 0, '相关现有回归失败；停止替换')
    same_count(read(run / 'backup.json')['objects'], object_count(run / 'repository'))
    save(run / 'verified.json', {'status': 'PASS', 'head': git(work, 'rev-parse', 'HEAD').decode().strip(),
                               'refs': refs(work), 'git_bytes': sum(v[1] for v in disk_tree(run / 'candidate.git').values() if v[0] == 'file'),
                               'evidence_files': sum(p.startswith('evidence/') for p in new),
                               'limitations': '未运行模型、完整工作台业务回归、Electron 或实际替换。'})
    print('PASS 离线候选核对；替换和发布仍未执行')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['backup', 'plan', 'rewrite', 'verify'])
    parser.add_argument('run_id')
    parser.add_argument('--trial', action='store_true', help='仅 backup：固定已提交 refs，允许 live 开发，不生成正式备份')
    args = parser.parse_args()
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.run_id), 'run id 不合法')
    mounted(VOLUME)
    no_links(BASE / args.run_id)
    no_links(ARCHIVES / args.run_id)
    require(not args.trial or args.phase == 'backup', '--trial 只用于 01 backup')
    (trial_backup if args.trial else globals()[args.phase])(BASE / args.run_id)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError) as error:
        # 不输出异常原文中潜在的文件内容；本脚本的 ValueError 都是固定诊断。
        print('NO_GO ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
