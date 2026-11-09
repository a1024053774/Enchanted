"""T-250：“改动”面板经真实入口的端到端测试。

真实入口：本源码树构建的工作台（app/build.mjs 到新 slot），由 tests/cdp_launch.cjs 以独立数据目录启动 Electron，经
DevTools 协议操作窗口；后台是同一源码树的门禁 CLI 以独立 state 启动的 daemon 与私有 hc core。夹具仓库由本测试新建；
期望值只从 git 读（status --porcelain=v2、diff --numstat、merge-base、log），由本文件自己解析，不导入产品实现。

失败方式（写断言之前列出）：
1. 分组错：冲突、已暂存、未暂存（含未跟踪）放错组，或一个文件同时有暂存和未暂存改动时只出现一次。
2. +/- 行数与 git diff --numstat / --cached --numstat / --no-index 不一致，或总计不是逐项之和。
3. 暂存、取消暂存、丢弃、提交没到 git，或改多了；丢弃不先确认，取消确认后仓库仍被改。
4. 没有已暂存文件时提交不先暂存全部改动。
5. 基线识别错（不是 main），或列出的文件与 git diff $(git merge-base HEAD main) --name-status 不一致。
6. 审阅备注没到终端，或文字与备注不一致；它的输入记录与在同一终端里打字不同。
7. 门禁 worktree 可以经主进程写。
8. 图片没有前后对比，Markdown 没有预览。
9. 测试碰到用户自己的 hc core。

--mutant 判红：在源码副本里改坏分组或行数，只构建这份副本，其余不变。
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import uuid
from types import SimpleNamespace

from hc_evidence import user_core_snapshot
from scripted_claude import Electron, source_tree, stop_fixture_core
from test_t249_git_graph_e2e import mouse_events

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'app/panels/changesModel.ts'
MUTANTS = {
    # 已暂存与未暂存互换。
    'groups': (MODEL, "if (xy[0] !== '.') staged.push({ path, code: xy[0]! });", "if (xy[1] !== '.') staged.push({ path, code: xy[1]! });"),
    # 增删行数互换。
    'counts': (MODEL, "counts.set(path, { add: add === '-' ? 0 : Number(add), del: del === '-' ? 0 : Number(del), binary: add === '-' });",
               "counts.set(path, { add: del === '-' ? 0 : Number(del), del: add === '-' ? 0 : Number(add), binary: add === '-' });"),
}
PNG_1 = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                      '1f15c4890000000d49444154789c6360f8cfc0000003010100c9fe92ef0000000049454e44ae426082')
PNG_2 = bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'
                      '1f15c4890000000d49444154789c63f8cfc0f000000401010074b3b0d40000000049454e44ae426082')
T0 = 1700000000


def wait_for(probe, message, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError(message)


def git(repo, *args, env=None, check=True):
    run = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, env=env)
    assert not check or run.returncode == 0, (args, run.stderr)
    return run.stdout


def commit(repo, message, when):
    env = dict(os.environ, GIT_AUTHOR_DATE=f'{when} +0000', GIT_COMMITTER_DATE=f'{when} +0000')
    git(repo, 'commit', '-q', '-m', message, env=env)


def build_repo(repo):
    """main 上两次提交；side 从第一次提交分出并改 conf.txt；feature 从 main 分出并提交两次，再合并 side 留下冲突。
    之后：a.txt 已暂存且另有未暂存改动，c.txt、keep.txt、img.png、doc.md 未暂存，两个未跟踪文件。"""
    repo.mkdir(parents=True)
    git(repo, 'init', '-q', '-b', 'main')
    git(repo, 'config', 'user.name', 'T250'); git(repo, 'config', 'user.email', 't250@example.invalid')
    (repo / 'a.txt').write_text(''.join(f'line {i}\n' for i in range(1, 31)))
    (repo / 'c.txt').write_text('one\ntwo\n')
    (repo / 'keep.txt').write_text('keep me\n')
    (repo / 'conf.txt').write_text('base\n')
    (repo / 'img.png').write_bytes(PNG_1)
    (repo / 'doc.md').write_text('# Title\n\nold text\n')
    git(repo, 'add', '.'); commit(repo, 'init', T0)
    git(repo, 'checkout', '-q', '-b', 'side')
    (repo / 'conf.txt').write_text('side\n'); git(repo, 'commit', '-q', '-am', 'side');
    git(repo, 'checkout', '-q', 'main')
    (repo / 'conf.txt').write_text('main\n'); git(repo, 'add', '.'); commit(repo, 'main change', T0 + 10)
    git(repo, 'checkout', '-q', '-b', 'feature')
    (repo / 'f1.txt').write_text('feature one\n'); git(repo, 'add', '.'); commit(repo, 'feature 1', T0 + 20)
    (repo / 'c.txt').write_text('one\ntwo\nthree\n'); git(repo, 'add', '.'); commit(repo, 'feature 2', T0 + 30)
    merged = subprocess.run(['git', '-C', str(repo), 'merge', '-q', 'side'], capture_output=True, text=True)
    assert merged.returncode != 0 and 'conf.txt' in git(repo, 'diff', '--name-only', '--diff-filter=U'), merged.stdout
    lines = (repo / 'a.txt').read_text().splitlines()
    lines[1] = 'line 2 staged'
    (repo / 'a.txt').write_text('\n'.join(lines) + '\n'); git(repo, 'add', 'a.txt')
    lines[19] = 'line 20 changed later'
    (repo / 'a.txt').write_text('\n'.join(lines) + '\n')
    (repo / 'c.txt').write_text('one\nTWO\nthree\nfour\n')
    (repo / 'keep.txt').write_text('changed, to be discarded\n')
    (repo / 'img.png').write_bytes(PNG_2)
    (repo / 'doc.md').write_text('# Title\n\nnew **text**\n\n- item\n')
    (repo / 'untracked one.txt').write_text('u1\nu2\nu3\n')
    (repo / 'sub').mkdir(); (repo / 'sub' / 'u2.txt').write_text('x\n')


def expected_groups(repo):
    """git status --porcelain=v2 -z 与三种 numstat，由测试自己解析。"""
    fields = git(repo, 'status', '--porcelain=v2', '-z', '--no-renames', '--untracked-files=all').split('\0')
    groups = []
    for line in fields:
        if not line:
            continue
        if line[0] == '?':
            groups.append(('unstaged', line[2:], '?'))
        elif line[0] == 'u':
            groups.append(('conflict', line.split(' ', 10)[10], 'U'))
        elif line[0] == '1':
            parts = line.split(' ', 8)
            if parts[1][0] != '.':
                groups.append(('staged', parts[8], parts[1][0]))
            if parts[1][1] != '.':
                groups.append(('unstaged', parts[8], parts[1][1]))

    def numstat(*args):
        out = {}
        for line in git(repo, 'diff', '--numstat', '--no-renames', *args).splitlines():
            add, delete, path = line.split('\t', 2)
            out[path] = (add, delete)  # 冲突文件打两行，取后一行（工作区对 ours）。
        return out
    staged, unstaged = numstat('--cached'), numstat()
    rows = []
    for group, path, code in groups:
        if code == '?':
            run = subprocess.run(['git', '-C', str(repo), 'diff', '--no-index', '--numstat', '--', '/dev/null', path], capture_output=True, text=True)
            add, delete = run.stdout.split('\t')[:2] if run.stdout else ('0', '0')
        else:
            add, delete = (staged if group == 'staged' else unstaged)[path]
        rows.append([group, path, code, add, delete])
    order = {'conflict': 0, 'staged': 1, 'unstaged': 2}
    return sorted(rows, key=lambda r: (order[r[0]], r[1]))


JS_ITEMS = '''(()=>{const c=document.querySelector('[data-changes]');if(!c)return null;
  return {repo:c.dataset.repo,scope:c.dataset.scope,base:c.dataset.base,mergeBase:c.dataset.mergeBase,readOnly:c.dataset.readOnly,
    total:[c.querySelector('[data-changes-total-add]')?.dataset.changesTotalAdd,c.querySelector('[data-changes-total-add]')?.dataset.changesTotalDel],
    items:[...c.querySelectorAll('[data-changes-group] [data-change-path]')].map(r=>[r.dataset.changeGroup,r.dataset.changePath,r.dataset.changeCode,r.dataset.add,r.dataset.del])}})()'''
JS_HELPERS = '''window.__t250={
  setValue(el,v){const proto=el instanceof HTMLTextAreaElement?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}))},
  key(el,key,extra){el.dispatchEvent(new KeyboardEvent('keydown',{key,bubbles:true,cancelable:true,...(extra||{})}))},
  row(group,path){return document.querySelector('[data-change-group="'+group+'"][data-change-path="'+CSS.escape(path)+'"]')},
  focusPane(launch){const p=document.querySelector('.pane[data-launch-id="'+launch+'"]');if(!p||p.offsetParent===null)return false;
    p.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));return p.dataset.paneKey||true}};true'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=sorted(MUTANTS))
    parser.add_argument('--shots', type=Path, help='截图目录（默认放在 --output 里）')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    shots = args.shots or args.output
    shots.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix='t250-'))
    state, home, repos = fixture / 'state', fixture / 'home', fixture / 'repos'
    for path in (state, home, repos):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T250% '\n", encoding='utf-8')
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'ENCHANTED_HC_CACHE_DIR') if k in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
    if 'ENCHANTED_HC_CACHE_DIR' not in env and not (ROOT.parent / 'hc-cache').is_dir():
        fallback = Path(os.path.expanduser('~/Documents/Code/hc-cache'))
        if fallback.is_dir():
            env['ENCHANTED_HC_CACHE_DIR'] = str(fallback)
    report = dict(status='INCOMPLETE', mutant=args.mutant, command=[sys.executable, *sys.argv], fixture=str(fixture), checks=[], commands=[],
                  versions=dict(node=subprocess.check_output(['node', '--version'], text=True).strip(), git=subprocess.check_output(['git', '--version'], text=True).strip()))
    running, electron, launches = False, None, {}

    def check(ok, what, detail=None):
        report['checks'].append(dict(ok=bool(ok), what=what, **({'detail': detail} if detail is not None and not ok else {})))
        assert ok, f'{what}：{detail}'

    def cli(*argv):
        command = ['node', str(ROOT / 'workbench/src/gates/cli.ts'), '--state', str(state), *argv]
        run = subprocess.run(command, env=env, capture_output=True, text=True, timeout=60, start_new_session=True)
        report['commands'].append(dict(argv=command, exit=run.returncode, stdout=run.stdout[-2000:], stderr=run.stderr[-2000:]))
        assert run.returncode == 0, f'{argv}: {run.stdout} {run.stderr}'
        return json.loads(run.stdout)

    def request(command, identity=None, **data):
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(20)
            connection.connect(str(state / 'control.sock'))
            connection.sendall((json.dumps(dict(id=str(uuid.uuid4()), identity=identity, input=dict(command=command, **data))) + '\n').encode())
            result = b''
            while b'\n' not in result:
                part = connection.recv(65536)
                assert part, '后台在回执前断开'
                result += part
        return json.loads(result.split(b'\n')[0])

    before_user = user_core_snapshot()
    try:
        alpha = repos / 'alpha'
        build_repo(alpha)
        managed = state / 'worktrees' / 't250' / 'wt'
        managed.parent.mkdir(parents=True)
        git(alpha, 'worktree', 'add', '-q', '--detach', str(managed), 'HEAD')
        real = lambda p: os.path.realpath(p)
        cli('daemon_start')
        running = True
        wait_for(lambda: request('pane_layout').get('recovering') is False, '恢复未结束')
        operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text(encoding='utf-8'))
        opened = request('project_open', operator, repo=str(alpha))
        assert opened['ok'], opened
        project = opened['project']
        launches['shell'] = cli('shell_start', '--project', project, '--cwd', str(alpha))['launch']
        window = request('window_open', operator, launch=launches['shell']['id'], project=project)
        assert window['ok'], window
        source = source_tree(fixture, patches=[MUTANTS[args.mutant]]) if args.mutant else ROOT
        out = fixture / 'ui-output'
        out.mkdir()
        electron = Electron(SimpleNamespace(source=source, env=env, state=state, dir=fixture, out=out), 't250-' + uuid.uuid4().hex[:8])
        ev = electron.evaluate

        def helper(expression):
            return ev(f'(()=>{{{JS_HELPERS};return ({expression})}})()')
        electron.until('窗口加载', f'''(()=>{{const r=document.querySelector('[data-project-id="{project}"]');if(!r||r.disabled)return false;r.click();return true}})()''', 60)
        electron.until('侧边面板开关打开', '''(()=>{const b=document.querySelector('[data-panel-toggle]');if(!b)return false;
          if(b.getAttribute('aria-pressed')==='true')return true;b.click();return false})()''', 20)
        electron.until('改动标签', '''(()=>{const b=document.querySelector('[data-panel-tab="changes"]');if(!b)return false;b.click();return true})()''', 20)
        # 聚焦项目终端：备注发往它，面板跟随它的 cwd（也是 alpha）。
        launch = launches['shell']['id']
        for _ in range(3):
            electron.until('终端的侧栏行', f'''(()=>{{const r=document.querySelector('[data-agent-launch="{launch}"]');if(!r||r.disabled)return false;r.click();return true}})()''', 30)
            try:
                electron.until('终端窗格', f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');return Boolean(p&&p.offsetParent!==null)}})()''', 15)
                break
            except AssertionError:
                continue
        check(helper(f'window.__t250.focusPane("{launch}")'), '聚焦项目终端窗格')
        electron.until('面板跟随终端', '''document.querySelector('[data-panel-dock]')?.dataset.followSource==='pane' ''', 30)

        def ui_matches(expected, label, seconds=20):
            last = {}
            def probe():
                value = ev(JS_ITEMS)
                last['value'] = value
                return value and value['scope'] == 'worktree' and value['items'] == expected and value
            try:
                return wait_for(probe, label, seconds)
            except AssertionError:
                return last.get('value')

        # 1. 分组与行数。
        expected = expected_groups(alpha)
        report['expected_initial'] = expected
        groups = {row[0] for row in expected}
        check(groups == {'conflict', 'staged', 'unstaged'} and any(r[2] == '?' for r in expected), '夹具有冲突、已暂存、未暂存、未跟踪文件', expected)
        shown = ui_matches(expected, '初始分组')
        report['ui_initial'] = shown
        check(shown and shown['items'] == expected, '分组、状态码与 +/- 行数与 git status --porcelain=v2、diff --numstat 一致', dict(ui=shown and shown['items'], git=expected))
        check(real(shown['repo']) == real(alpha), '面板读的是 alpha', shown['repo'])
        count = lambda v: 0 if v == '-' else int(v)
        total = [sum(count(r[3]) for r in expected), sum(count(r[4]) for r in expected)]
        check([int(v) for v in shown['total']] == total, '总计是逐项之和', dict(ui=shown['total'], git=total))
        electron.screenshot(shots / 'groups.png')

        # 2. 图片前后对比、Markdown 预览。
        helper('''window.__t250.row('unstaged','img.png').click()''')
        check(electron.until('图片对比', '''Boolean(document.querySelector('[data-changes-diff="img.png"] [data-image-before]')&&document.querySelector('[data-image-after]'))''', 20),
              '改动的图片显示改动前和改动后')
        helper('''window.__t250.row('unstaged','doc.md').click()''')
        electron.until('Markdown 预览按钮', '''(()=>{const b=document.querySelector('[data-changes-diff="doc.md"] [data-diff-preview]');if(!b)return false;b.click();return true})()''', 20)
        md = electron.until('Markdown 预览', '''document.querySelector('[data-markdown-preview]')?.innerText||null''', 20)
        check('Title' in md and 'text' in md and '**' not in md, 'Markdown 文件可以预览（标题与加粗渲染出来）', md)
        ev('''document.querySelector('[data-diff-preview]').click()''')

        # 3. 基线比较。
        ev('''document.querySelector('[data-changes-scope="base"]').click()''')
        base = electron.until('基线', '''(()=>{const c=document.querySelector('[data-changes]');return c&&c.dataset.scope==='base'&&c.dataset.mergeBase&&
          !document.querySelector('[data-changes] [data-change-group="unstaged"]')?{base:c.dataset.base,mergeBase:c.dataset.mergeBase,
          items:[...c.querySelectorAll('[data-change-group="range"]')].map(r=>[r.dataset.changePath,r.dataset.changeCode])}:null})()''', 30)
        merge_base = git(alpha, 'merge-base', 'HEAD', 'main').strip()
        name_status = sorted(line.split('\t')[::-1] for line in git(alpha, 'diff', merge_base, '--name-status', '--no-renames').splitlines())
        name_status = [[path, code[0]] for path, code in name_status]
        report['base'] = dict(ui=base, git=name_status)
        check(base['base'] == 'main' and base['mergeBase'] == merge_base, '基线识别为 main，合并基点与 git merge-base HEAD main 一致', base)
        check(sorted(base['items']) == name_status, '基线范围的文件与 git diff $(git merge-base HEAD main) --name-status 一致', report['base'])
        ev('''document.querySelector('[data-changes-history]').click()''')
        history = electron.until('本分支历史', '''(()=>{const r=[...document.querySelectorAll('[data-history-hash]')];return r.length?r.map(e=>e.dataset.historyHash):null})()''', 20)
        check(history == git(alpha, 'rev-list', f'{merge_base}..HEAD').split(), '历史只列本分支在基线之后的提交', history)
        ev('''document.querySelector('[data-changes-history]').click()''')
        electron.screenshot(shots / 'base.png')
        ev('''document.querySelector('[data-changes-scope="worktree"]').click()''')
        ui_matches(expected, '回到未提交')

        # 4. 暂存（按钮）、取消暂存（u 键）、丢弃（先取消，再确认）。
        helper('''window.__t250.row('unstaged','c.txt').querySelector('[data-changes-stage]').click()''')
        wait_for(lambda: 'c.txt' in git(alpha, 'diff', '--cached', '--name-only').split(), '暂存按钮没有暂存 c.txt')
        time.sleep(.5)
        after_stage = expected_groups(alpha)
        check(['staged', 'c.txt', 'M'] == after_stage[[r[1] for r in after_stage].index('c.txt')][:3] and not git(alpha, 'diff', '--name-only', '--', 'c.txt').strip(),
              '暂存 c.txt 后它整个进了暂存区', after_stage)
        check(ui_matches(after_stage, '暂存后刷新')['items'] == after_stage, '暂存后面板立即刷新，与 git 一致')
        helper('''window.__t250.row('staged','a.txt').click()''')
        electron.until('选中已暂存的 a.txt', '''document.querySelector('[data-change-group="staged"][data-change-path="a.txt"]')?.getAttribute('aria-selected')==='true' ''', 10)
        helper('''window.__t250.key(document.querySelector('[data-changes]'),'u')''')
        wait_for(lambda: 'a.txt' not in git(alpha, 'diff', '--cached', '--name-only').split(), 'u 键没有取消暂存 a.txt')
        after_unstage = expected_groups(alpha)
        check(not any(r[0] == 'staged' and r[1] == 'a.txt' for r in after_unstage) and [p for p in git(alpha, 'diff', '--cached', '--name-only').split() if p != 'conf.txt'] == ['c.txt'],
              '取消暂存 a.txt 后暂存区只剩 c.txt（冲突文件之外）', git(alpha, 'diff', '--cached', '--name-only'))
        ui_matches(after_unstage, '取消暂存后刷新')
        before_discard = git(alpha, 'status', '--porcelain=v2', '-z'), (alpha / 'keep.txt').read_bytes()
        helper('''window.__t250.row('unstaged','keep.txt').querySelector('[data-changes-discard]').click()''')
        check(electron.until('丢弃确认框', '''Boolean(document.querySelector('[data-changes-confirm]'))''', 10), '丢弃先出现确认框')
        ev('''document.querySelector('[data-confirm-cancel]').click()''')
        time.sleep(1)
        check((git(alpha, 'status', '--porcelain=v2', '-z'), (alpha / 'keep.txt').read_bytes()) == before_discard, '取消丢弃后仓库不变')
        helper('''window.__t250.row('unstaged','keep.txt').querySelector('[data-changes-discard]').click()''')
        electron.until('丢弃确认框', '''(()=>{const b=document.querySelector('[data-confirm-ok]');if(!b)return false;b.click();return true})()''', 10)
        wait_for(lambda: (alpha / 'keep.txt').read_text() == 'keep me\n', '确认后 keep.txt 没有回到 HEAD 的内容')
        status_after = git(alpha, 'status', '--porcelain=v2', '-z')
        check('keep.txt' not in status_after and status_after.count('\0') == before_discard[0].count('\0') - 1, '确认丢弃只恢复了 keep.txt')
        ui_matches(expected_groups(alpha), '丢弃后刷新')

        # 5. 审阅备注发到普通终端：终端里跑 cat > 文件，备注经粘贴到达。
        captured = fixture / 'notes.out'
        typed = request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data=f"cat > '{captured}'\r")
        assert typed['ok'], typed
        time.sleep(1.5)
        helper('''window.__t250.row('unstaged','a.txt').click()''')
        lines = electron.until('a.txt 的 diff', '''(()=>{const r=[...document.querySelectorAll('[data-changes-diff="a.txt"] [data-diff-line]')];
          return r.length?r.map(e=>({i:Number(e.dataset.diffLine),kind:e.dataset.kind,text:e.innerText})):null})()''', 20)
        added = [line for line in lines if line['kind'] == 'add']
        check(len(added) == 2 and 'line 2 staged' in added[0]['text'] and 'line 20 changed later' in added[1]['text'],
              '取消暂存后 a.txt 的未暂存 diff 有第 2 行和第 20 行两处改动', added)
        start = next(line['i'] for line in lines if line['kind'] == 'del' and 'line 20' in line['text'])
        rect = ev(f'''(()=>{{const a=document.querySelector('[data-diff-line="{start}"]').getBoundingClientRect(),b=document.querySelector('[data-diff-line="{added[1]['i']}"]').getBoundingClientRect();
          return [a.left+60,a.top+a.height/2,b.left+60,b.top+b.height/2]}})()''')
        mouse_events(electron, [dict(type='mouseMoved', x=rect[0], y=rect[1]), dict(type='mousePressed', x=rect[0], y=rect[1], button='left', clickCount=1, buttons=1),
                                dict(type='mouseMoved', x=rect[2], y=rect[3], button='left', buttons=1), dict(type='mouseReleased', x=rect[2], y=rect[3], button='left', clickCount=1)])
        note = '这一行为什么改？'
        electron.until('备注框', f'''(()=>{{{JS_HELPERS};const t=document.querySelector('[data-note-text]');if(!t)return false;window.__t250.setValue(t,{json.dumps(note)});return true}})()''', 10)
        helper('''window.__t250.key(document.querySelector('[data-note-text]'),'Enter')''')
        electron.until('备注计数', '''document.querySelector('[data-changes-notes]')?.dataset.changesNotes==='1' ''', 10)
        ev('''document.querySelector('[data-notes-send]').click()''')
        electron.until('发送后清空', '''!document.querySelector('[data-changes-notes]')''', 10)
        time.sleep(1)
        request('window_input', window['identity'], sequence=2, request_id=str(uuid.uuid4()), data='\r\x04')
        wait_for(lambda: captured.exists() and captured.read_text().strip(), '终端里的 cat 没写出备注')
        text = captured.read_text()
        report['notes_received'] = text
        expected_note = ['审阅备注（1 条）：', '', 'a.txt:20', '> line 20 changed later', note]
        check(text.strip().split('\n') == expected_note, '终端收到的文字与备注一致（路径、行号、引用的行、备注）', dict(got=text, want=expected_note))
        # 普通终端的打字不写 user_inputs（只有 agent 会话写）；备注走同一条输入路径，记录方式应与打字相同。
        def recorded(text):
            run = subprocess.run(['sqlite3', f'file:{state}/state.sqlite3?mode=ro', "select count(*) from user_inputs where instr(data, '" + text.replace("'", "''") + "') > 0"],
                                 capture_output=True, text=True)
            assert run.returncode == 0, run.stderr
            return int(run.stdout.strip() or 0)
        typed_records, note_records = recorded(f"cat > '{captured}'"), recorded(note)
        report['input_records'] = dict(typed=typed_records, note=note_records)
        check(typed_records == note_records, '备注的输入记录与在同一终端里打字相同（普通终端两者都不写 user_inputs）', report['input_records'])

        # 6. 提交：先把冲突按 ours 解决（git），界面提交已暂存的；再在没有已暂存文件时提交（先暂存全部）。
        git(alpha, 'checkout', '--ours', 'conf.txt'); git(alpha, 'add', 'conf.txt')
        ui_matches(expected_groups(alpha), '解决冲突后刷新')
        staged_before = git(alpha, 'diff', '--cached', '--name-only').split()
        message_1 = 'T250 merge side with staged files'
        helper(f'''(()=>{{const t=document.querySelector('[data-changes-message]');window.__t250.setValue(t,{json.dumps(message_1)});return true}})()''')
        helper('''window.__t250.key(document.querySelector('[data-changes-message]'),'Enter')''')
        wait_for(lambda: git(alpha, 'log', '-1', '--format=%s').strip() == message_1, 'Enter 没有提交')
        committed = git(alpha, 'show', '--format=', '--name-only', '-m', '--first-parent', 'HEAD').split()
        check(sorted(committed) == sorted(staged_before) and len(git(alpha, 'log', '-1', '--format=%P').split()) == 2,
              '提交的正是已暂存的文件，合并提交有两个父提交', dict(committed=committed, staged=staged_before))
        remaining = git(alpha, 'status', '--porcelain=v1', '--untracked-files=all')
        check(remaining.strip(), '未暂存的改动没被提交', remaining)
        ui_matches(expected_groups(alpha), '提交后刷新')
        message_2 = 'T250 commit everything'
        helper(f'''(()=>{{const t=document.querySelector('[data-changes-message]');window.__t250.setValue(t,{json.dumps(message_2)});return true}})()''')
        ev('''document.querySelector('[data-changes-commit]').click()''')
        wait_for(lambda: git(alpha, 'log', '-1', '--format=%s').strip() == message_2, '没有已暂存文件时提交按钮没有提交')
        check(git(alpha, 'status', '--porcelain=v1', '--untracked-files=all') == '', '没有已暂存文件时先暂存全部改动再提交，工作区干净')
        electron.until('面板显示没有改动', '''Boolean(document.querySelector('[data-changes-empty]'))''', 20)
        electron.screenshot(shots / 'clean.png')

        # 7. 门禁 worktree：主进程拒绝写。
        (managed / 'm.txt').write_text('m\n')
        direct = ev(f'''window.a2a.changesAction({json.dumps(real(managed))},{{type:'stage',entries:[{{path:'m.txt',group:'unstaged',untracked:true}}]}}).then(()=>'accepted',e=>String(e))''')
        check(direct != 'accepted' and '只读' in direct and '??' in git(managed, 'status', '--porcelain=v1'), '门禁 worktree 经主进程暂存被拒', direct)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(status='FAIL' if report['checks'] and not report['checks'][-1]['ok'] else report['status'],
                      error=str(error), traceback=traceback.format_exc())
    finally:
        try:
            if electron:
                electron.stop()
            if running:
                for launch in launches.values():
                    try:
                        cli('shell_close', '--launch', launch['id'])
                    except AssertionError as error:
                        report.setdefault('close_errors', []).append(str(error))
                cli('daemon_stop')
                wait_for(lambda: not (state / 'control.sock').exists(), '后台未退出')
            report['core_cleanup'] = stop_fixture_core(state, fixture, env)
            report['cleanup'] = 'PASS'
        except Exception as error:
            report['cleanup'] = str(error)
            if report['status'] == 'PASS':
                report['status'] = 'INCOMPLETE'
        report['user_core_unchanged'] = before_user == user_core_snapshot()
        if not report['user_core_unchanged']:
            report['status'] = 'NO_GO'
        if report.get('cleanup') == 'PASS':
            shutil.rmtree(fixture)
            report['fixture_removed'] = not fixture.exists()
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'mutant', 'error', 'cleanup', 'user_core_unchanged') if k in report}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
