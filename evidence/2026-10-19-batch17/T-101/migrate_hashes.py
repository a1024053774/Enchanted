#!/usr/bin/env python3
"""按 commit-map 机械迁移可执行测试/脚本中的哈希字面量，并保存同套件前后对照。"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

from slim_history import BASE, git, mounted, no_links, read, require, save

HASH = re.compile(rb'(?<![A-Za-z0-9_])[0-9a-f]{7,40}(?![A-Za-z0-9_])')
ROOTS = ('acceptance/', 'scripts/', 'workbench/tests/')
EXTENSIONS = ('.py', '.ts', '.js', '.mjs', '.cjs', '.sh')


def eligible(path):
    return path.startswith(ROOTS) and path.endswith(EXTENSIONS)


def read_mapping(path):
    lines = path.read_text(encoding='ascii').splitlines()
    require(lines and lines[0].split() == ['old', 'new'], 'commit-map 头无效')
    mapping = dict(line.split() for line in lines[1:])
    require(mapping and all(re.fullmatch('[0-9a-f]{40}', old) and re.fullmatch('[0-9a-f]{40}', new)
                            for old, new in mapping.items()), 'commit-map 内容无效')
    return mapping


def replace_literals(raw, mapping):
    changes = []
    prefixes = {}
    for old in mapping:
        prefixes.setdefault(old[:7].encode(), []).append(old)
    def replace(match):
        token = match[0].decode('ascii')
        matches = [old for old in prefixes.get(match[0][:7], []) if old.startswith(token)]
        if not matches:
            return match[0]
        require(len(matches) == 1, '旧哈希前缀不唯一；停止，不猜测：' + token)
        old = matches[0]
        new = mapping[old]
        require(int(new, 16), '被删除的旧提交无法机械迁移：' + token)
        if new.startswith(token):
            return match[0]
        changes.append({'offset': match.start(), 'old_literal': token, 'old_commit': old, 'new_commit': new})
        return new.encode('ascii')
    return HASH.sub(replace, raw), changes


def migration_plan(work, mapping):
    rows, outputs = [], {}
    for name in git(work, 'ls-files', '-z', *[root.rstrip('/') for root in ROOTS]).split(b'\0'):
        if not name:
            continue
        path = name.decode('utf-8')
        if not eligible(path):
            continue
        source = work / path
        require(source.is_file() and not source.is_symlink(), '调用方类型不支持：' + path)
        raw = source.read_bytes()
        raw.decode('utf-8')  # 只接受已核对的 UTF-8 源文件，原字节换行/BOM 保持。
        updated, edits = replace_literals(raw, mapping)
        if edits:
            rows.append({'path': path, 'source_blob': git(work, 'rev-parse', 'HEAD:' + path).decode().strip(), 'edits': edits})
            outputs[path] = updated
    return rows, outputs


def suites_manifest(path, changed):
    config = read(path)
    require(config.get('no_models') is True and isinstance(config.get('suites'), list) and config['suites'],
            '相关套件清单须明确 no_models=true，并列出 argv/covers/timeout_seconds')
    covered = set()
    for suite in config['suites']:
        require(isinstance(suite.get('argv'), list) and all(isinstance(arg, str) for arg in suite['argv'])
                and suite['argv'] and isinstance(suite.get('covers'), list), '套件格式无效')
        require(isinstance(suite.get('timeout_seconds'), (int, float)) and 0 < suite['timeout_seconds'] <= 3600,
                '套件须有 0～3600 秒的明确期限')
        covered.update(suite['covers'])
    require(changed <= covered, '缺少相关套件覆盖，停止；待补清单的调用方：' + ', '.join(sorted(changed - covered)))
    return config['suites']


def run_suites(work, suites, directory):
    directory.mkdir(parents=True, exist_ok=False)
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_CONFIG_')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    results = []
    for index, suite in enumerate(suites):
        output = directory / str(index)
        output.mkdir()
        command = [arg.replace('{worktree}', str(work)).replace('{output}', str(output)) for arg in suite['argv']]
        with (output / 'stdout.bin').open('xb') as stdout, (output / 'stderr.bin').open('xb') as stderr:
            try:
                result = subprocess.run(command, cwd=work, env=env, stdout=stdout, stderr=stderr,
                                        timeout=suite['timeout_seconds'], start_new_session=True)
                row = {'argv': command, 'exit': result.returncode, 'timeout': False}
            except subprocess.TimeoutExpired:
                # run 已终止该前台测试进程；未知子进程/副作用不自动重试或清理。
                row = {'argv': command, 'exit': None, 'timeout': True}
        row.update(covers=suite['covers'], stdout=str(output / 'stdout.bin'), stderr=str(output / 'stderr.bin'))
        save(output / 'result.json', row)
        results.append(row)
        require(not row['timeout'], '相关套件超时；停止，保留现场，不自动重试')
    return results


def migrate(run, suite_path, plan_only=False):
    require(read(run / 'backup.json').get('mode') != 'trial', '03b 只用于正式 run；本次试跑停在 03')
    work = run / 'prepared'
    require(not git(work, 'status', '--porcelain'), '先审查并提交 03 生成物；03b 必须从干净候选开始')
    mapping = read_mapping(run / 'candidate.git/filter-repo/commit-map')
    changes, outputs = migration_plan(work, mapping)
    parent = git(work, 'rev-parse', 'HEAD').decode().strip()
    plan = {'parent': parent, 'changes': changes, 'scope': list(ROOTS),
            'excluded': ['ticket、evidence、records 的引用均不改', '不改变断言、测试逻辑或其他字节']}
    plan_path = run / 'hash-migration-plan.json'
    if plan_path.exists():
        require(read(plan_path) == plan, '候选与先前迁移计划不同；保留旧计划，不覆盖')
    else:
        save(plan_path, plan)
    if plan_only:
        print('INCOMPLETE 迁移计划：' + str(plan_path))
        return
    require(suite_path is not None, '须提供 --suites：主控核对过的无模型相关套件清单，格式见 example')
    require(not (run / 'hash-migration-intent.json').exists(), '已有迁移意图；禁止自动重试，先核对现场')
    paths = {row['path'] for row in changes}
    suites = suites_manifest(suite_path, paths)
    save(run / 'hash-migration-intent.json', {'parent': parent, 'paths': sorted(paths), 'suites': suites,
                                             'authorization': '执行主控 #7：只机械替换哈希字面量，独立提交；不改断言/逻辑'})
    before = run_suites(work, suites, run / 'hash-migration-before')
    for path, updated in outputs.items():
        require((work / path).read_bytes() == git(work, 'show', parent + ':' + path), '前置套件改变了调用方，停止：' + path)
    require(not git(work, 'status', '--porcelain'), '前置套件污染候选；停止，不丢弃现场')
    for path, updated in outputs.items():
        (work / path).write_bytes(updated)
    after = run_suites(work, suites, run / 'hash-migration-after')
    passed = all(row['exit'] == 0 for row in after)
    save(run / 'hash-migration-comparison.json', {'status': 'PASS' if passed else 'NO_GO',
                                                 'before': before, 'after': after, 'changes': changes,
                                                 'note': '同一套 argv 模板/断言，输出写入各自新目录；原始输出只留外置盘'})
    require(passed, '迁移后相关套件失败；停止并上报，不修改断言/逻辑，不自动回退')
    for path, updated in outputs.items():
        require((work / path).read_bytes() == updated, '后置套件改变了调用方：' + path)
    changed = set(git(work, 'diff', '--name-only').decode().splitlines())
    require(changed == paths and not git(work, 'ls-files', '--others', '--exclude-standard'), '套件修改了计划外文件，停止')
    commit = parent
    if paths:
        git(work, 'add', '--', *sorted(paths))
        git(work, 'commit', '-m', 'Migrate executable commit literals using T-101 commit map')
        commit = git(work, 'rev-parse', 'HEAD').decode().strip()
        require(set(git(work, 'diff', '--name-only', parent, commit).decode().splitlines()) == paths,
                '迁移提交混入范围外文件')
    save(run / 'hash-migration.json', {'status': 'PASS', 'parent': parent, 'commit': commit,
                                     'changes': changes, 'suites': suites,
                                     'note': '单独提交只含可执行测试/脚本的已知 commit-map 哈希替换；ticket/evidence/records 未变'})
    print('PASS 哈希迁移与同套件前后对照：' + commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_id')
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--suites', type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.run_id), 'run id 不合法')
    mounted()
    no_links(BASE / args.run_id)
    migrate(BASE / args.run_id, args.suites, args.plan_only)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, UnicodeError) as error:
        print('NO_GO ' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        sys.exit(1)
