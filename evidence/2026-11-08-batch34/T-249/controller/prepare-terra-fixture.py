"""独立验收夹具：只在指定的新目录建本地 Git 仓库；不启动应用或 agent。"""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


root = Path(sys.argv[1]).resolve()
assert root.parent == Path('/private/tmp') and root.name.startswith('t249-terra-')
root.mkdir()
repos = root / 'repos'
repos.mkdir()
env = dict(os.environ, GIT_AUTHOR_NAME='Terra fixture', GIT_COMMITTER_NAME='Terra fixture',
           GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_EMAIL='fixture@example.invalid')
clock = 1700000100


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], env=env, text=True)


def init(path):
    path.mkdir(parents=True)
    git(path, 'init', '-q', '-b', 'main')


def commit(path, title):
    global clock
    clock += 10
    env.update(GIT_AUTHOR_DATE=f'{clock} +0000', GIT_COMMITTER_DATE=f'{clock} +0000')
    git(path, 'add', '-A')
    git(path, 'commit', '-q', '-m', title)
    return git(path, 'rev-parse', 'HEAD').strip()


alpha = repos / 'alpha'
init(alpha)
(alpha / 'first.txt').write_text('root first\n')
(alpha / 'file*.txt').write_text('literal star root\n')
(alpha / 'file-other.txt').write_text('decoy root\n')
a1 = commit(alpha, '根提交：独立验收')
git(alpha, 'checkout', '-q', '-b', 'feature')
(alpha / 'feature.txt').write_text('feature content\n')
feature = commit(alpha, '功能分支提交')
git(alpha, 'tag', 'terra-tag', feature)
git(alpha, 'checkout', '-q', 'main')
(alpha / 'first.txt').write_text('main second\n')
(alpha / 'file*.txt').write_text('literal star second\n')
(alpha / 'file-other.txt').write_text('decoy second\n')
a2 = commit(alpha, '主分支第二次提交')
clock += 10
env.update(GIT_AUTHOR_DATE=f'{clock} +0000', GIT_COMMITTER_DATE=f'{clock} +0000')
git(alpha, 'merge', '-q', '--no-ff', '-m', '合并功能分支', 'feature')
(alpha / 'first.txt').write_text('main second\nworking change\n')
(alpha / 'untracked.txt').write_text('untracked content\n')

beta = repos / 'beta'
init(beta)
(beta / 'beta.txt').write_text('beta independent\n')
commit(beta, '另一个仓库')
multi = repos / 'many'
for path in (multi / 'group' / 'one', multi / 'group' / 'two', multi / 'three'):
    init(path)
    (path / 'readme.txt').write_text(path.name + '\n')
    commit(path, '多仓库 ' + path.name)

unborn = repos / 'unborn'
init(unborn)
(unborn / 'staged.txt').write_text('staged before first commit\n')
(unborn / 'file[1].txt').write_text('bracket staged\n')
git(unborn, 'add', 'staged.txt', 'file[1].txt')
(unborn / 'file[1].txt').write_text('bracket staged\nbracket working\n')
(unborn / 'untracked.txt').write_text('new file before first commit\n')

managed = root / 'state/worktrees/terra/readonly'
managed.parent.mkdir(parents=True)
git(alpha, 'worktree', 'add', '-q', '--detach', str(managed), 'HEAD')
oracle = {}
for name, path in (('alpha', alpha), ('beta', beta), ('unborn', unborn), ('managed', managed)):
    entry = {'repo': str(path), 'status_v2': git(path, 'status', '--porcelain=v2', '--branch'),
             'refs': git(path, 'for-each-ref', '--format=%(objectname) %(refname)')}
    if name != 'unborn':
        entry['rev_list'] = git(path, 'rev-list', '--date-order', '--parents', '--all')
    oracle[name] = entry
oracle['detail_choices'] = {'root': a1, 'normal': a2, 'feature': feature}
oracle['manygit'] = sorted(str(p.parent) for p in multi.rglob('.git'))
oracle['source'] = '所有期望由本脚本创建的 Git 历史及原始 Git 命令产生，不调用产品实现。'
oracle['time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(root / 'oracle-before.json').write_text(json.dumps(oracle, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'root': str(root), 'oracle': str(root / 'oracle-before.json'), 'repositories': list(oracle)[:4]}, ensure_ascii=False))
