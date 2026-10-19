#!/usr/bin/env python3
"""主控独立运行的替换/单次发布入口；worker 不执行。"""
import argparse
import filecmp
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from slim_history import (ARCHIVES, BASE, HERE, REMOTE, SOURCE, VOLUME, mounted, no_links, object_count,
                          read, refs, require, same_count, save, scan, stable_snapshot, tree, git, disk_tree)


def clean_gate(run):
    require(read(run / 'backup.json').get('mode') != 'trial', '试跑 run 禁止替换或发布；正式运行必须重做完整备份')
    verified = read(run / 'verified.json')
    work = run / 'prepared'
    require(verified['status'] == 'PASS' and verified['head'] == git(work, 'rev-parse', 'HEAD').decode().strip()
            and verified['refs'] == refs(work) and not git(work, 'status', '--porcelain'),
            '核对后候选改变；不能替换或发布')
    scan_result = read(run / 'credential-scan.json')
    require(scan_result['status'] == 'PASS' and scan_result.get('unexempted_hit_count') == 0, '扫描未通过或缺少未豁免命中核对')
    same_count(read(run / 'backup.json')['objects'], object_count(run / 'repository'))
    return verified


def install(run):
    verified = clean_gate(run)
    require(os.environ.get('A2A_T101_QUIESCENT') == '1', '主控须先回收 worker、停止仓库写入，再设 A2A_T101_QUIESCENT=1')
    require(not (run / 'install-intent.json').exists(), '已有替换意图；禁止自动重试，核对现场')
    snapshot = read(run / 'snapshot.json')
    require(stable_snapshot(SOURCE) == snapshot, '备份后主仓库或并行 worktree 已变；用新 run 重做')
    same_count(read(run / 'backup.json')['objects'], object_count(SOURCE))
    staged = subprocess.run(['git', '-C', str(SOURCE), 'diff', '--cached', '--quiet'], capture_output=True)
    require(staged.returncode == 0, '主仓库有已暂存内容；停止，不重置人工暂存状态')
    # 并行交付必须先经原门禁集成；不能由替换脚本替代门禁或 cherry-pick 新提交。
    branches = {row['branch'] for row in snapshot['worktrees'].values() if row['branch'].startswith('refs/heads/exec/')}
    for branch in sorted(branches):
        result = subprocess.run(['git', '-C', str(SOURCE), 'merge-base', '--is-ancestor', branch, 'main'], capture_output=True)
        require(result.returncode == 0, branch + ' 尚未集成 main；停止，不丢弃并行提交')
    work = run / 'prepared'
    old = tree(run / 'repository', snapshot['head'])
    new = tree(work)
    changed = [p for p in sorted(old.keys() | new.keys()) if old.get(p) != new.get(p)]
    saved_main = run / 'repository'
    # 原始归档重新核对文件数和总字节数；主仓库旧文件必须仍与完整目录副本一致。
    manifests = read(run / 'archives.json')
    for entry in manifests.values():
        rows = read(Path(entry['index']))
        payload = Path(entry['archive']) / 'versions'
        expected = {row['file']: ['file', row['bytes']] for row in rows}
        require(disk_tree(payload) == expected and len(expected) == entry['files']
                and sum(row['bytes'] for row in rows) == entry['bytes'], '归档文件数/字节数改变；禁止替换')
    for path in changed:
        live = SOURCE / path
        saved = saved_main / path
        if path in old:
            require(live.exists() and saved.exists() and not live.is_symlink() and not saved.is_symlink()
                    and live.is_file() and saved.is_file() and filecmp.cmp(live, saved, shallow=False),
                    '候选要改的路径有人工修改/类型变化，保留现场：' + path)
        else:
            require(not live.exists() and not live.is_symlink(), '候选新增路径与未提交文件冲突：' + path)
        if path in new:
            require(new[path]['mode'] in ('100644', '100755'), '替换不支持变更链接/gitlink；停止')
    preserved = SOURCE.parent / ('.a2a-git-pre-slim-' + run.name)
    staging = SOURCE.parent / ('.a2a-git-t101-staging-' + run.name)
    no_links(preserved)
    no_links(staging)
    require(not preserved.exists() and not staging.exists(), '原 Git 保留目录或暂存目录已存在')
    candidate = run / 'candidate.git'
    candidate_bytes = sum(v[1] for v in disk_tree(candidate).values() if v[0] == 'file')
    require(shutil.disk_usage(SOURCE).free > candidate_bytes + 256 * 1024 * 1024, '内置盘不足以暂存瘦身后的 Git；不替换')
    # 不复制 candidate 的外置 worktree 登记和可能含原始正文的 filter-repo 中间产物。
    shutil.copytree(candidate, staging, symlinks=True, ignore=shutil.ignore_patterns('worktrees', 'filter-repo'))
    git(staging, 'config', 'core.bare', 'false')
    git(staging, 'config', 'core.logAllRefUpdates', 'true')
    git(staging, 'config', 'remote.origin.url', 'git@github.com:a1024053774/a2a.git')
    git(staging, 'config', 'remote.origin.fetch', '+refs/heads/*:refs/remotes/origin/*')
    require(refs(staging) == verified['refs'], '暂存 Git refs 不一致')
    # 保存所有非受控资料的完整副本在 backup 阶段已完成；本阶段只触及 changed。
    # linked worktree 停用并指回保留的旧 Git，文件和未提交内容原样保留。
    parked = []
    for name in snapshot['worktrees']:
        path = Path(name)
        if path == SOURCE:
            continue
        pointer = (path / '.git').read_text(encoding='utf-8').strip()
        require(pointer.startswith('gitdir: '), 'linked worktree 指针格式未知')
        metadata = Path(pointer[8:])
        require(metadata.parent == SOURCE / '.git/worktrees', 'linked worktree 归属不符')
        parked.append({'worktree': name, 'old_gitdir': str(metadata),
                       'preserved_gitdir': str(preserved / 'worktrees' / metadata.name)})
    require(stable_snapshot(SOURCE) == snapshot, '暂存期间源仓库变动；停止')
    save(run / 'install-intent.json', {'source': str(SOURCE), 'old_git': str(preserved), 'new_git': str(staging),
                                      'candidate': verified['head'], 'changed_paths': changed, 'parked_worktrees': parked,
                                      'warning': '若中途失败，保留现场并人工核对；不自动重试或 reset'})
    (SOURCE / '.git').rename(preserved)
    staging.rename(SOURCE / '.git')
    for row in parked:
        (Path(row['worktree']) / '.git').write_text('gitdir: ' + row['preserved_gitdir'] + '\n', encoding='utf-8')
    for path in changed:
        live = SOURCE / path
        if path not in new:
            live.unlink()  # 全量备份和逐文件比较完成后，只移出已核对的受控原始证据。
        else:
            live.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / path, live)
            live.chmod(0o755 if new[path]['mode'] == '100755' else 0o644)
    # 只重建新 main 的 index；不 checkout/reset 工作区，保留未受影响的 dirty/untracked 内容。
    git(SOURCE, 'read-tree', 'HEAD')
    require(git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == verified['head'], '替换后 HEAD 不一致')
    save(run / 'installed.json', {'status': 'PASS', 'head': verified['head'], 'preserved_git': str(preserved),
                                 'parked_worktrees': parked,
                                 'status_after_hex': git(SOURCE, 'status', '--porcelain=v1', '-z', '--untracked-files=all').hex(),
                                 'note': '旧 worktree 已停用，仍指向原历史；新仓库的 exec/t102 已按 ref-map 改写。需要继续工作时从新仓库另建 worktree。'})
    print('PASS 本地替换完成；旧 Git、旧 worktree、完整备份均保留；未 push')


def https_env():
    env = dict(os.environ)
    # 只在该子进程中把 origin 的 SSH URL 改走 HTTPS，凭据由 gh helper 按需提供。
    # 不调用 gh auth token，不把 token 放 argv、文件或输出。
    configs = [('url.https://github.com/.insteadOf', 'git@github.com:'),
               ('credential.helper', ''), ('credential.helper', '!gh auth git-credential')]
    count = int(env.get('GIT_CONFIG_COUNT', '0'))
    for key, value in configs:
        env[f'GIT_CONFIG_KEY_{count}'] = key
        env[f'GIT_CONFIG_VALUE_{count}'] = value
        count += 1
    env['GIT_CONFIG_COUNT'] = str(count)
    env['GIT_TERMINAL_PROMPT'] = '0'
    return env


def remote_sha(env):
    api = subprocess.run(['gh', 'api', 'repos/a1024053774/a2a/git/ref/heads/main', '--jq', '.object.sha'],
                         capture_output=True, text=True, env=env)
    require(api.returncode == 0, 'gh api 核对失败；不输出可能含凭据的错误正文')
    sha = api.stdout.strip()
    require(len(sha) == 40 and all(c in '0123456789abcdef' for c in sha), '远端返回值不是完整提交号')
    remote = subprocess.run(['git', 'ls-remote', 'origin', 'refs/heads/main'], cwd=SOURCE,
                            capture_output=True, text=True, env=env)
    require(remote.returncode == 0, 'ls-remote 核对失败')
    require(remote.stdout.strip() == sha + '\trefs/heads/main', 'gh api 与 ls-remote 结果不同')
    return sha


def publish(run):
    verified = clean_gate(run)
    installed = read(run / 'installed.json')
    require(installed['status'] == 'PASS' and installed['head'] == verified['head'], '本地替换未通过')
    require(git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == verified['head']
            and git(SOURCE, 'symbolic-ref', 'HEAD').strip() == b'refs/heads/main', '发布候选或当前分支改变')
    require(git(SOURCE, 'remote', 'get-url', 'origin').strip() == b'git@github.com:a1024053774/a2a.git', 'origin 不符')
    require(not (run / 'push-intent.json').exists(), '已有 push 意图；禁止重试，先人工核对远端')
    # 再扫实际替换后的仓库，而不是借用旧候选的扫描结论。
    scan(SOURCE, run / 'installed-credential-scan.json')
    env = https_env()
    before = remote_sha(env)
    require(before == REMOTE, '远端 main 已变化；停止并上报，不能变更 lease')
    command = ['git', 'push', '--force-with-lease=main:' + REMOTE, 'origin', 'main']
    save(run / 'push-intent.json', {'argv': command, 'before': before, 'candidate': verified['head'],
                                   'origin': 'git@github.com:a1024053774/a2a.git', 'transport': 'HTTPS via gh credential helper'})
    result = subprocess.run(command, cwd=SOURCE, env=env, capture_output=True)
    save(run / 'push-exit.json', {'exit': result.returncode, 'output_omitted': '不记录凭据相关输出'})
    require(result.returncode == 0, 'push 非零；保留意图，不自动重试')
    after = remote_sha(env)
    save(run / 'published.json', {'status': 'PASS' if after == verified['head'] else 'NO_GO',
                                 'origin': 'git@github.com:a1024053774/a2a.git', 'before': before,
                                 'after': after, 'candidate': verified['head'], 'pushed_refs': ['refs/heads/main']})
    require(after == verified['head'], 'push 后 gh api/ls-remote 与候选不一致')
    print('PASS 已核对发布：' + after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['install', 'publish'])
    parser.add_argument('run_id')
    args = parser.parse_args()
    import re
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.run_id), 'run id 不合法')
    mounted(VOLUME)
    no_links(BASE / args.run_id)
    globals()[args.phase](BASE / args.run_id)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError) as error:
        print('NO_GO ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
