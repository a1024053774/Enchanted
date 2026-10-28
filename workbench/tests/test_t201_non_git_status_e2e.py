"""T-201：非 Git 目录作为项目时，侧栏状态说一句“不是 Git 仓库”，不露原始的 git 命令报错；Git 仓库真的读不了时仍如实显示原因。
真实后台、socket、Electron 窗口（CDP 驱动），零模型调用。

预期来自需求（T-201 与第 1 轮试用发现 3）：
- 普通目录：侧栏状态是“不是 Git 仓库”，不含 `Command failed`、`fatal:` 之类的原始报错；仍可以作为项目打开。
- 有 .git 但读不了的仓库（HEAD 被写坏；git 对它同样报 not a git repository）：仍显示“无法读取 Git”和原因，不被那句话盖掉。
- 打开后目录被删：显示“目录不存在”（不变）。

失败方式（先列再写）：
1. 普通目录仍显示原始命令报错（修前）。
2. 只看 git 的报错文字，把 HEAD 坏掉的真仓库也说成“不是 Git 仓库”。
3. 正常仓库的分支状态变了。
4. 普通目录打不开了（不做：禁止添加非 Git 目录）。
--revision 在该版本的源码上跑同一场景（修前应在第 1 条失败）；--mutant 去掉 .git 存在与否的判断。
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import uuid

from scripted_claude import Electron, Fixture

MUTANTS = {
    'message-only': [('src/sidebar.ts', "!existsSync(join(repo, '.git')) && ", '')],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--revision')
    target.add_argument('--mutant', choices=sorted(MUTANTS))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, mutant=args.mutant,
                  runtime='real Electron/daemon/git; zero model calls', checks=[])
    fixture = electron = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if condition:
            report['checks'].append(name)
        else:
            report.setdefault('failed', []).append(name)

    try:
        def no_model(body):
            raise AssertionError('T-201 不调用模型')
        fixture = Fixture('t201-', no_model, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/false', {'README.md': 'demo\n'})
        plain, broken, gone = fixture.dir / 'plain-dir', fixture.dir / 'broken-repo', fixture.dir / 'gone-repo'
        plain.mkdir()
        (plain / 'notes.txt').write_text('not a repository\n', encoding='utf-8')
        for repo in (broken, gone):
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=fixture.env)
            subprocess.run(['git', '-C', str(repo), 'commit', '-q', '--allow-empty', '-m', 'init'], check=True, env=fixture.env)
        ids = {}
        for repo in (plain, broken, gone):
            opened = fixture.request('project_open', fixture.operator, repo=str(repo))
            check(f'open_{repo.name}', opened.get('ok'), opened)
            ids[repo.name] = opened.get('project')
        (broken / '.git' / 'HEAD').write_text('garbage\n', encoding='utf-8')
        shutil.rmtree(gone)
        report['ids'] = ids

        electron = Electron(fixture, 't201-' + uuid.uuid4().hex[:10])
        electron.until('项目列表', 'document.querySelectorAll("[data-project-git]").length >= 4')
        status = electron.until('状态读到', '''(()=>{const s=Object.fromEntries([...document.querySelectorAll("[data-project-git]")].map(n=>[n.dataset.projectGit,n.textContent]));
          return Object.values(s).every(v=>v)?s:null})()''')
        report['sidebar_status'] = status
        plain_status = status.get(ids['plain-dir'], '')
        check('plain_says_not_git', '不是 Git 仓库' in plain_status, plain_status)
        check('plain_hides_raw_error', not any(word in plain_status for word in ('Command failed', 'fatal:', 'git -C')), plain_status)
        broken_status = status.get(ids['broken-repo'], '')
        check('broken_repo_shows_reason', broken_status.startswith('无法读取 Git') and 'not a git repository' in broken_status, broken_status)
        check('gone_repo_shows_missing', status.get(ids['gone-repo']) == '目录不存在', status.get(ids['gone-repo']))
        check('normal_repo_unchanged', status.get(fixture.project, '').startswith('main'), status.get(fixture.project))
        electron.screenshot(fixture.out / 'status.png')
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        for stop in (electron, fixture):
            if stop:
                try:
                    stop.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(report['status'], report.get('error', ''))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
