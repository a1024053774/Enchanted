"""T-249：Git 图面板经真实入口的端到端测试。

真实入口：本源码树构建的工作台（app/build.mjs 到新 slot），由 tests/cdp_launch.cjs 以独立数据目录启动 Electron，
经 DevTools 协议（tests/cdp.mjs）操作窗口；后台是同一源码树的门禁 CLI 以独立 state 启动的 daemon 与私有 hc core。
夹具仓库全部由本测试新建；期望值只从 git 读（rev-list、for-each-ref、status），不导入、不调用产品实现。

失败方式（写断言之前列出）：
1. 提交顺序、父子关系、引用标签与 git 不一致（排序改错、父提交顺序颠倒、标签挂错提交）。
2. 没有未提交行，或它没有用虚线连到 HEAD。
3. 写操作没到 git，或改多了；名字以 - 开头被当成选项执行，或绕过界面直接调主进程时没被拒。
4. 聚焦窗格换到另一个仓库的终端时面板不换；读的是启动目录而不是 shell 现在的 cwd；固定后仍跟随。
5. 非仓库目录不显示多仓库列表，或数量与夹具不符。
6. 跟随门禁 worktree 时写操作可用，或 Git 元数据被改。
7. 测试碰到用户自己的 hc core。
8. renderer 没有挂载侧边面板；必须在窗口和面板开关可用后命中“侧边面板存在”，启动失败不算红态。
9. 点提交没有可见详情，或详情元数据、文件列表与 Git 不符；no-details 必须命中对应业务断言。
10. 点文件没有可见 diff，或单文件 diff 混入其他文件；根提交、普通提交、未提交和无 HEAD 都从窗口操作。
11. 未跟踪文本被占位说明替代；特殊文件名混入邻居内容，空文件/二进制伪装文本，切换文件保留旧内容。
12. 列分隔条未接线或双击不复原；用 CDP Input 的真实鼠标输入核对可见列几何，不调用 React handler。

--mutant 用于判红：在源码副本里改坏模型或断开 renderer 的面板挂载，只构建这份副本的界面，其余不变。
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

ROOT = Path(__file__).resolve().parents[2]
MODEL = 'app/panels/gitGraphModel.ts'
MUTANTS = {
    'no-panel': ('app/renderer.tsx', '{dockOpen && <PanelDock', '{false && <PanelDock'),
    'no-details': ('app/panels/GitGraphPanel.tsx', '{selectedCommit && <CommitDetails', '{false && selectedCommit && <CommitDetails'),
    'no-diff': ('app/panels/GitGraphPanel.tsx', 'onClick={() => void openDiff(file.path, file.status)}', 'onClick={() => {}}'),
    'no-resize': ('app/panels/GitGraphPanel.tsx', 'const start = event.clientX, width = columns[column];', 'return; const start = event.clientX, width = columns[column];'),
    'no-reset': ('app/panels/GitGraphPanel.tsx', 'onDoubleClick={() => setColumns(value => ({ ...value, [column]: columnDefaults[column] }))}', 'onDoubleClick={() => {}}'),
    'stale-diff': ('app/panels/GitGraphPanel.tsx', 'setDiff(current => current === loading ? { path, rows,', 'setDiff(current => true ? { path, rows,'),
    'no-untracked': (MODEL, "if (commit.uncommitted && status === '?')", "if (false && commit.uncommitted && status === '?')"),
    # 父提交顺序颠倒：merge 的两个父提交互换。
    'parents': (MODEL, "parents: parents ? parents.split(' ') : [],", "parents: parents ? parents.split(' ').reverse() : [],"),
    # 排序改错：从旧到新。
    'order': (MODEL, "  return commits;", "  return commits.reverse();"),
}
BASELINE_C = '18c108fcaed1c4ecf51831f2272578a3b09427be'
UNTRACKED_PATHS = ['untracked.txt', 'new/file*.txt', 'new/file[1].txt', 'new/:(glob)*.txt', 'new/-leading.txt', 'new/empty.txt', 'new/binary.bin']
T0 = 1700000000


def wait_for(probe, message, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = probe()
        if value:
            return value
        time.sleep(.1)
    raise AssertionError(message)


def check_panel_present(electron, check, seconds=20):
    # 先确认开关已打开。随后只将正常 DOM 查询返回的“没有面板”记为断言失败；
    # CDP 断连、窗口退出等异常直接交给 main，保留 INCOMPLETE，不冒充 no-panel 红态。
    electron.until('侧边面板开关打开', '''(()=>{const b=document.querySelector('[data-panel-toggle]');if(!b)return false;
      if(b.getAttribute('aria-pressed')==='true')return true;b.click();return false})()''', 20)
    end = time.monotonic() + seconds
    present = False
    while time.monotonic() < end:
        present = electron.evaluate("Boolean(document.querySelector('[data-panel-dock]'))")
        if present:
            break
        time.sleep(.1)
    check(present, '侧边面板存在')


def check_dom(electron, check, expression, what, seconds=20):
    """正常 DOM 查询一直没有业务结果才判红；CDP/窗口异常原样传播。"""
    end = time.monotonic() + seconds
    value = None
    while time.monotonic() < end:
        value = electron.evaluate(expression)
        if value:
            break
        time.sleep(.1)
    check(bool(value), what)
    return value


def git(repo, *args, env=None):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, text=True, capture_output=True, env=env).stdout


def commit_env(when):
    return dict(os.environ, GIT_AUTHOR_DATE=f'{when} +0000', GIT_COMMITTER_DATE=f'{when} +0000', GIT_AUTHOR_NAME='T',
                GIT_AUTHOR_EMAIL='t@example.invalid', GIT_COMMITTER_NAME='T', GIT_COMMITTER_EMAIL='t@example.invalid')


def commit(repo, name, when, message):
    Path(repo, name).write_text(message + '\n')
    git(repo, 'add', name)
    git(repo, 'commit', '-q', '-m', message, env=commit_env(when))
    return git(repo, 'rev-parse', 'HEAD').strip()


def build_main_repo(repo):
    """两条分支、一次 merge、一个轻量标签和一个附注标签、一个未提交改动（外加一个未跟踪文件）。"""
    repo.mkdir(parents=True)
    git(repo, 'init', '-q', '-b', 'main')
    c1 = commit(repo, 'a.txt', T0 + 1, 'c1')
    c2 = commit(repo, 'b.txt', T0 + 2, 'c2')
    git(repo, 'checkout', '-q', '-b', 'feature', c1)
    f1 = commit(repo, 'f.txt', T0 + 3, 'f1')
    git(repo, 'tag', 'v1', f1)
    git(repo, 'checkout', '-q', 'main')
    c3 = commit(repo, 'c.txt', T0 + 4, 'c3')
    git(repo, 'checkout', '-q', 'feature')
    commit(repo, 'g.txt', T0 + 5, 'f2')
    git(repo, 'checkout', '-q', 'main')
    git(repo, 'merge', '-q', '--no-ff', '--no-edit', 'feature', env=commit_env(T0 + 6))
    git(repo, 'tag', '-a', 'v2', '-m', 'v2', c3, env=commit_env(T0 + 6))
    git(repo, 'checkout', '-q', '-b', 'side', c2)
    commit(repo, 's.txt', T0 + 7, 's1')
    git(repo, 'checkout', '-q', 'main')
    Path(repo, 'a.txt').write_text('changed\n')
    Path(repo, 'new.txt').write_text('new\n')
    return dict(c1=c1, c2=c2, c3=c3, f1=f1)


def small_repo(repo, message):
    repo.mkdir(parents=True)
    git(repo, 'init', '-q', '-b', 'main')
    return commit(repo, 'r.txt', T0 + 10, message)


def build_detail_repos(history, unborn):
    """3 种字面路径 × 3 种 diff；无 HEAD 时另含 staged/mixed/intent-to-add/untracked。"""
    names = ['file*.txt', 'file-other.txt', 'file[1].txt', 'file1.txt', ':(glob)*.txt', 'other.txt']
    nonce = uuid.uuid4().hex[:12]
    for repo in (history, unborn):
        repo.mkdir(parents=True)
        git(repo, 'init', '-q', '-b', 'main')
    hashes = {}
    for index, phase in enumerate(('root', 'normal', 'uncommitted')):
        for number, name in enumerate(names):
            (history / name).write_text(f'DETAIL-{nonce}-{number}-{phase}\n', encoding='utf-8')
        if phase != 'uncommitted':
            git(history, 'add', '--all')
            env = dict(commit_env(T0 + 20 + index), GIT_AUTHOR_NAME='Details Author ' + nonce,
                       GIT_COMMITTER_NAME='Details Committer ' + nonce)
            git(history, 'commit', '-qm', f'details-{phase}-{nonce}\n\nDETAIL-BODY-{phase}-{nonce}', env=env)
            hashes[phase] = git(history, 'rev-parse', 'HEAD').strip()
    for number, name in enumerate(names):
        (unborn / name).write_text(f'UNBORN-{nonce}-{number}-index\n', encoding='utf-8')
    staged = [name for name in names if name != ':(glob)*.txt']
    git(unborn, '--literal-pathspecs', 'add', '--', *staged)
    (unborn / 'file[1].txt').write_text(f'UNBORN-{nonce}-mixed-working\nsecond-line\n', encoding='utf-8')
    git(unborn, '--literal-pathspecs', 'add', '-N', '--', ':(glob)*.txt')
    for repo in (history, unborn):
        (repo / 'new').mkdir()
        for name in UNTRACKED_PATHS:
            (repo / name).write_text(f'UNTRACKED-{repo.name}-{name}-{nonce}\n第二行\n', encoding='utf-8')
        (repo / 'new/empty.txt').write_bytes(b'')
        (repo / 'new/binary.bin').write_bytes(b'\x00\x01\xff\n')
        (repo / 'new/file1.txt').write_text('OTHER-FILE-SENTINEL\n', encoding='utf-8')
    return hashes


def check_commit_details(electron, check, repo, revision, case, selected_paths):
    """只点可见的行和文件按钮；期望由真实 Git 读取，不调产品模型或 IPC。"""
    row_id = revision if revision is not None else '*'
    row = f'''[...document.querySelectorAll('[data-git-rows] [data-commit-hash]')].find(r=>r.dataset.commitHash==={json.dumps(row_id)})'''
    electron.until('点击 ' + case + ' 提交行', f'''(()=>{{const r={row};if(!r||r.offsetParent===null)return false;
      r.scrollIntoView({{block:'nearest'}});r.click();return true}})()''')
    detail_selector = '[data-git-details]'
    check_dom(electron, check, f'''(()=>{{const d=document.querySelector('{detail_selector}');
      return Boolean(d&&d.offsetParent!==null&&d.dataset.gitDetails==={json.dumps(row_id)})}})()''', '点击提交后详情可见')
    observed = check_dom(electron, check, '''(()=>{const d=document.querySelector('[data-git-details]');
      if(!d||d.offsetParent===null)return null;const files=[...d.querySelectorAll('[data-git-file]')];
      if(!files.length&&!d.querySelector('.panel-error'))return null;
      return {title:d.querySelector('.git-details-title')?.textContent,hash:d.querySelector('[data-detail-hash]')?.textContent,
        parents:[...d.querySelectorAll('[data-detail-parents] button')].map(b=>b.textContent),
        meta:Object.fromEntries([...d.querySelectorAll('.git-meta>div')].map(r=>[r.querySelector('dt').textContent,r.querySelector('dd').textContent])),
        body:d.querySelector('.git-body')?.textContent,error:d.querySelector('.panel-error')?.textContent,
        files:files.map(b=>({path:b.querySelector('.file-path').textContent,add:b.querySelector('.add')?.textContent,del:b.querySelector('.del')?.textContent}))}})()''',
        case + ' 详情文件列表已加载')
    check(not observed.get('error'), case + ' 详情读取无错误', observed)
    empty_tree = git(repo, 'hash-object', '-t', 'tree', '/dev/null').strip()
    if revision is not None:
        fields = git(repo, 'show', '-s', '--format=%H%x00%P%x00%s%x00%an%x00%ae%x00%cn%x00%B', revision).rstrip('\n').split('\0')
        oid, parents, subject, author, email, committer, body = fields
        check(observed['hash'] == oid and observed['title'] == subject, case + ' 详情哈希和标题与 Git 一致', observed)
        check(observed['parents'] == [p[:10] for p in parents.split()], case + ' 可见父提交与 Git 一致', observed['parents'])
        check(author in observed['meta'].get('作者', '') and email in observed['meta'].get('作者', '')
              and committer in observed['meta'].get('提交者', ''), case + ' 作者和提交者与 Git 一致', observed['meta'])
        check(observed['body'] == body, case + ' 提交正文与 Git 一致', observed['body'])
        comparison = [parents.split()[0] if parents else empty_tree, oid]
        untracked = []
    else:
        head = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', '-q', 'HEAD'], text=True, capture_output=True)
        assert head.returncode in (0, 1), head.stderr
        comparison = [head.stdout.strip() if head.returncode == 0 else empty_tree]
        untracked = git(repo, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')[:-1]
    tracked = git(repo, 'diff', '--no-renames', '--name-only', '-z', *comparison).split('\0')[:-1]
    expected_paths = sorted(tracked + untracked)
    check(sorted(f['path'] for f in observed['files']) == expected_paths, case + ' 可见文件列表与 Git 一致',
          dict(ui=observed['files'], git=expected_paths))
    for file in observed['files']:
        if file['path'] in untracked:
            continue
        stats = git(repo, '--literal-pathspecs', 'diff', '--no-renames', '--numstat', '-z', *comparison, '--', file['path']).split('\t')[:2]
        check([file['add'], file['del']] == ['+' + stats[0], '-' + stats[1]], case + ' 文件行数与 Git 一致：' + file['path'], file)
    diffs = []
    for path in selected_paths:
        check(path in expected_paths, case + ' 夹具包含待点击的文件：' + path)
        electron.until('点击文件 ' + path, f'''(()=>{{const b=[...document.querySelectorAll('[data-git-file]')].find(b=>b.querySelector('.file-path')?.textContent==={json.dumps(path)});
          if(!b||b.offsetParent===null)return false;b.scrollIntoView({{block:'nearest'}});b.click();return true}})()''')
        shown = check_dom(electron, check, f'''(()=>{{const d=document.querySelector('[data-git-diff]');
          if(!d||d.offsetParent===null||d.dataset.gitDiff!=={json.dumps(path)}||d.querySelector('.panel-empty')?.textContent==='正在读取 diff…')return null;
          return {{path:d.querySelector('.git-diff-head code')?.textContent,
            lines:[...d.querySelectorAll('.diff-lines>div')].map(r=>r.lastElementChild.textContent),note:d.querySelector('.panel-empty')?.textContent}}}})()''',
          '点击文件后单文件 diff 可见')
        check(shown['path'] == path, case + ' diff 显示选中的文件名', shown)
        if path in untracked:
            command = ['git', '-C', str(repo), 'diff', '--no-index', '--no-color', '--no-ext-diff', '--no-textconv', '--', '/dev/null', './' + path]
            oracle = subprocess.run(command, text=True, capture_output=True)
            assert oracle.returncode in (0, 1) and not oracle.stderr, (command, oracle.stderr)
            raw = (repo / path).read_bytes()
            lines = oracle.stdout.splitlines()
            first_hunk = next((i for i, line in enumerate(lines) if line.startswith('@@')), None)
            expected_lines = [] if first_hunk is None else lines[first_hunk:]
            if raw and b'\x00' not in raw:
                check(shown['lines'] == expected_lines and '+' + raw.decode('utf-8').splitlines()[0] in shown['lines'],
                      case + ' 未跟踪文本 diff 与原始文件及独立 Git 一致：' + path,
                      dict(ui=shown, git=expected_lines, file=raw.decode('utf-8'), command=command))
            elif not raw:
                check(not shown['lines'] and '空文件' in (shown.get('note') or ''), case + ' 空文件不伪装文本 diff', shown)
            else:
                check(not shown['lines'] and shown.get('note') == oracle.stdout and 'Binary files ' in oracle.stdout,
                      case + ' 二进制显示 Git 说明而非文本 hunk', shown)
        else:
            patch = git(repo, '--literal-pathspecs', 'diff', '--no-color', '--no-ext-diff', '--no-textconv', '--no-renames', *comparison, '--', path)
            lines = patch.splitlines()
            first_hunk = next(i for i, line in enumerate(lines) if line.startswith('@@'))
            expected_lines = lines[first_hunk:]
            check(shown['lines'] == expected_lines, case + ' 单文件 diff 内容与独立 Git 一致：' + path,
                  dict(ui=shown['lines'], git=expected_lines))
        diffs.append(shown)
        electron.evaluate("document.querySelector('.git-diff-head button').click()")
        electron.until('返回文件列表', "Boolean(document.querySelector('[data-git-file]'))")
    electron.evaluate("document.querySelector('[data-git-details] [aria-label=\"关闭详情\"]').click()")
    electron.until('关闭详情', "!document.querySelector('[data-git-details]')")
    return dict(case=case, revision=revision, expected_paths=expected_paths, observed=observed, diffs=diffs)


def check_deferred_selection(electron, check, repo):
    """只挂起真实文件读取后的返回；通过可见控件改变选择，再释放原结果。"""
    records = []
    for next_selection in ('close', 'other-file'):
        electron.evaluate("document.querySelector('[data-commit-hash=\"*\"]').click()")
        electron.until('未跟踪文件可点击', '''(()=>{const b=[...document.querySelectorAll('[data-git-file]')].find(b=>b.dataset.gitFile==='untracked.txt');
          if(!b||b.offsetParent===null)return false;b.click();return true})()''')
        electron.until('真实 diff 结果已到达挂起点', "typeof window.__t249ReleaseDiff==='function'")
        check(electron.evaluate("document.querySelector('[data-git-diff]')?.dataset.gitDiff") == 'untracked.txt', '挂起时显示当前文件的加载状态')
        electron.evaluate("document.querySelector('.git-diff-head button').click()")
        if next_selection == 'other-file':
            electron.until('点击另一个文件', '''(()=>{const b=[...document.querySelectorAll('[data-git-file]')].find(b=>b.dataset.gitFile==='new/-leading.txt');
              if(!b||b.offsetParent===null)return false;b.click();return true})()''')
            electron.until('另一个文件真实内容已显示', "Boolean(document.querySelector('.diff-lines'))")
        electron.evaluate("window.__t249ReleaseDiff(); delete window.__t249ReleaseDiff; true")
        # Barrier: the released async continuation and React render finish before inspection.
        electron.evaluate("new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve(true))))")
        shown = electron.evaluate('''(()=>{const d=document.querySelector('[data-git-diff]');return d?
          {path:d.dataset.gitDiff,lines:[...d.querySelectorAll('.diff-lines>div')].map(r=>r.lastElementChild.textContent)}:null})()''')
        if next_selection == 'close':
            check(shown is None, '关闭 diff 后迟到内容不能重开', shown)
        else:
            expected = (repo / 'new/-leading.txt').read_text(encoding='utf-8').splitlines()
            check(shown and shown['path'] == 'new/-leading.txt' and all('+' + line in shown['lines'] for line in expected),
                  '切换文件后迟到内容不能覆盖新选择', shown)
        records.append(dict(next_selection=next_selection, observed=shown))
        electron.evaluate("document.querySelector('[data-git-details] [aria-label=\"关闭详情\"]').click()")
    return records


def refs_of(repo):
    """{提交: {(kind, 短名)}}，附注标签按它指向的提交。"""
    out = {}
    for line in git(repo, 'for-each-ref', '--format=%(objectname) %(*objectname) %(refname)', 'refs/heads', 'refs/tags').splitlines():
        oid, peeled, name = line.split(' ', 2)
        kind, short = ('branch', name[len('refs/heads/'):]) if name.startswith('refs/heads/') else ('tag', name[len('refs/tags/'):])
        out.setdefault(peeled or oid, set()).add((kind, short))
    return out


def ref_lines(repo):
    return git(repo, 'for-each-ref', '--format=%(objectname) %(refname)').splitlines()


def metadata_files(git_dir):
    """门禁 worktree 的 Git 元数据：.git 下每个文件的路径与内容。"""
    return {str(path.relative_to(git_dir)): path.read_bytes()
            for path in Path(git_dir).rglob('*') if path.is_file()}


def mouse_events(electron, events):
    """CDP 的浏览器输入通道；不是 DOM dispatchEvent 或 React handler。"""
    script = r'''
const [port, events] = process.argv.slice(1);
const page = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(p => p.type === 'page');
if (!page) throw new Error('no page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let id = 0;
for (const params of JSON.parse(events)) {
  await new Promise((resolve, reject) => {
    const request = ++id, timer = setTimeout(() => reject(new Error('mouse input timeout')), 5000);
    ws.onmessage = event => { const message = JSON.parse(event.data); if (message.id !== request) return;
      clearTimeout(timer); message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(); };
    ws.send(JSON.stringify({id:request, method:'Input.dispatchMouseEvent', params}));
  });
  await new Promise(resolve => setTimeout(resolve, 60));
}
ws.close();
'''
    run = subprocess.run(['node', '--input-type=module', '-e', script, str(electron.port), json.dumps(events)],
                         capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stderr


def check_column_width(electron, check):
    geometry = '''(()=>{const s=document.querySelector('.git-head .column-resizer'),c=s?.parentElement;
      const row=document.querySelector('.git-rows .git-date');if(!s||!c||!row||s.offsetParent===null)return null;
      const b=s.getBoundingClientRect(),x=b.x+b.width/2,y=b.y+b.height/2;
      return {x,y,header:c.getBoundingClientRect().width,row:row.getBoundingClientRect().width,
        hit:document.elementFromPoint(x,y)?.closest('.column-resizer')===s}})()'''
    before = check_dom(electron, check, geometry, '可见列分隔条有可测几何')
    check(before['hit'], '鼠标坐标命中可见列分隔条', before)
    x, y = before['x'], before['y']
    events = [dict(type='mouseMoved', x=x, y=y), dict(type='mousePressed', x=x, y=y, button='left', buttons=1, clickCount=1)]
    events += [dict(type='mouseMoved', x=x-delta, y=y, button='left', buttons=1) for delta in (16, 32, 48, 64)]
    events += [dict(type='mouseReleased', x=x-64, y=y, button='left', buttons=0, clickCount=1)]
    mouse_events(electron, events)
    dragged = electron.evaluate(geometry)
    check(dragged and abs(dragged['header'] - before['header'] - 64) < 2
          and abs(dragged['row'] - before['row'] - 64) < 2,
          '真实鼠标拖动改变可见日期列宽', dict(before=before, dragged=dragged, input=events))
    x, y = dragged['x'], dragged['y']
    double = [dict(type=kind, x=x, y=y, button='left', buttons=1 if kind == 'mousePressed' else 0, clickCount=count)
              for count in (1, 2) for kind in ('mousePressed', 'mouseReleased')]
    mouse_events(electron, double)
    restored = electron.evaluate(geometry)
    check(restored and abs(restored['header'] - before['header']) < 1 and abs(restored['row'] - before['row']) < 1,
          '真实鼠标双击恢复可见日期列宽', dict(before=before, dragged=dragged, restored=restored, input=double))
    return dict(before=before, dragged=dragged, restored=restored, input=events+double)


JS_ROWS = '''(()=>{const g=document.querySelector('[data-git-graph]');if(!g)return null;
  return {repo:g.dataset.repo,readOnly:g.dataset.readOnly,rows:[...g.querySelectorAll('[data-git-rows] [data-commit-hash]')].map(r=>({
    hash:r.dataset.commitHash,uncommitted:r.dataset.uncommitted==='true',parents:r.dataset.parents?r.dataset.parents.split(' '):[],
    lane:Number(r.dataset.lane),segments:JSON.parse(r.dataset.segments),subject:r.querySelector('.git-subject')?.textContent??'',
    refs:[...r.querySelectorAll('[data-ref-kind]')].map(p=>[p.dataset.refKind,p.dataset.refName])}))}})()'''
JS_DOCK = '''(()=>{const d=document.querySelector('[data-panel-dock]');if(!d)return null;
  return {dir:d.dataset.followedDir,source:d.dataset.followSource,managed:d.dataset.managed,
    repo:document.querySelector('[data-git-graph]')?.dataset.repo??null,manygit:document.querySelector('[data-manygit]')?.dataset.manygit??null,
    repos:[...document.querySelectorAll('[data-manygit-repo]')].map(r=>r.dataset.manygitRepo),
    readOnlyNote:Boolean(document.querySelector('[data-git-readonly]'))}})()'''
# React 读的是原生 value setter 和冒泡的 input 事件。
JS_HELPERS = '''window.__t249={
  setValue(el,v){Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}))},
  menu(el){const b=el.getBoundingClientRect();el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,button:2,clientX:b.left+8,clientY:b.top+8}))},
  focusPane(launch){const p=document.querySelector('.pane[data-launch-id="'+launch+'"]');if(!p||p.offsetParent===null)return false;
    p.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}));return p.dataset.paneKey||true}};true'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mutant', choices=sorted(MUTANTS))
    parser.add_argument('--baseline-c', action='store_true', help='仅 app 恢复旧 C，后台保持当前已集成代码；新检查必须业务判红')
    parser.add_argument('--deferred-diff', action='store_true', help='测试调度：挂起真实读取的返回，在选择改变后释放，证明迟到结果不覆盖')
    parser.add_argument('--shots', type=Path, help='截图目录（默认放在 --output 里；证据目录只留文本时指向本机临时目录）')
    args = parser.parse_args()
    assert not (args.baseline_c and (args.mutant or args.deferred_diff))
    assert args.mutant != 'stale-diff' or args.deferred_diff
    args.output.mkdir(parents=True, exist_ok=False)
    shots = args.shots or args.output
    shots.mkdir(parents=True, exist_ok=True)
    fixture = Path(tempfile.mkdtemp(prefix='t249-'))
    state, home, repos = fixture / 'state', fixture / 'home', fixture / 'repos'
    for path in (state, home, repos):
        path.mkdir()
    (home / '.zshrc').write_text("PS1='T249% '\n", encoding='utf-8')
    env = {k: os.environ[k] for k in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'ENCHANTED_HC_CACHE_DIR') if k in os.environ}
    env.update(HOME=str(home), SHELL='/bin/zsh', TERM='xterm-256color', A2A_OPERATOR_CREDENTIAL=str(fixture / 'operator.json'))
    if 'ENCHANTED_HC_CACHE_DIR' not in env and not (ROOT.parent / 'hc-cache').is_dir():
        fallback = Path(os.path.expanduser('~/Documents/Code/hc-cache'))
        if fallback.is_dir():
            env['ENCHANTED_HC_CACHE_DIR'] = str(fallback)
    report = dict(status='INCOMPLETE', mutant=args.mutant, baseline_c=BASELINE_C if args.baseline_c else None, deferred_diff=args.deferred_diff, versions=dict(node=subprocess.check_output(['node', '--version'], text=True).strip(), git=subprocess.check_output(['git', '--version'], text=True).strip()), command=[sys.executable, *sys.argv], fixture=str(fixture), checks=[], commands=[])
    running = False
    electron = None
    launches = {}

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
        # 夹具：项目主目录 alpha（主夹具）、另一个仓库 beta、非仓库目录 multi（下面 3 个仓库，两组）、
        # 门禁 worktree 目录（<state>/worktrees/ 下的真实 linked worktree），以及一个普通的非仓库起始目录 start。
        alpha, beta, multi, start = repos / 'alpha', repos / 'beta', repos / 'multi', repos / 'start'
        hashes = build_main_repo(alpha)
        small_repo(beta, 'beta-1')
        details, unborn = repos / 'details', repos / 'unborn'
        detail_hashes = build_detail_repos(details, unborn)
        expected_multi = [multi / 'g1' / 'r1', multi / 'g1' / 'r2', multi / 'r3']
        for path in expected_multi:
            small_repo(path, 'multi')
        (multi / 'plain').mkdir()
        start.mkdir()
        managed = state / 'worktrees' / 't249' / 'wt'
        managed.parent.mkdir(parents=True)
        git(alpha, 'worktree', 'add', '-q', '--detach', str(managed), 'HEAD')
        real = lambda p: os.path.realpath(p)
        report['fixture_repos'] = dict(alpha=real(alpha), beta=real(beta), multi=real(multi), managed=real(managed), details=real(details), unborn=real(unborn),
                                       multi_repos=sorted(real(p) for p in expected_multi))

        cli('daemon_start')
        running = True
        wait_for(lambda: request('pane_layout').get('recovering') is False, '恢复未结束')
        operator = json.loads(Path(env['A2A_OPERATOR_CREDENTIAL']).read_text(encoding='utf-8'))
        opened = request('project_open', operator, repo=str(alpha))
        assert opened['ok'], opened
        project = opened['project']
        for name, cwd in (('roam', start), ('multi', multi), ('managed', managed), ('details', details), ('unborn', unborn)):
            launches[name] = cli('shell_start', '--project', project, '--cwd', str(cwd))['launch']
        # roam 从非仓库目录 start 启动，再在 shell 里 cd 到 beta：面板要读 shell 现在的 cwd，不是启动目录。
        window = request('window_open', operator, launch=launches['roam']['id'], project=project)
        assert window['ok'], window
        typed = request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()), data=f"cd '{beta}'\r")
        assert typed['ok'], typed
        shell_pid = request('pane_status', thread=launches['roam']['thread'])['shell_pid']

        def shell_cwd():
            found = subprocess.run(['/usr/sbin/lsof', '-a', '-p', str(shell_pid), '-d', 'cwd', '-Fn'], capture_output=True, text=True).stdout
            return next((line[1:] for line in found.splitlines() if line.startswith('n/')), None)
        wait_for(lambda: shell_cwd() == real(beta), 'roam 终端的 shell 没有 cd 到 beta')

        patches = [MUTANTS[args.mutant]] if args.mutant else []
        if args.deferred_diff:
            patches.append(('app/panels/GitGraphPanel.tsx', '      const rows = diffRows(text);',
                "      if (path === 'untracked.txt') await new Promise<void>(resolve => { (window as any).__t249ReleaseDiff = () => { resolve(); }; });\n      const rows = diffRows(text);"))
        source = source_tree(fixture, patches=patches) if patches else ROOT
        if args.baseline_c:
            source = source_tree(fixture, copy=True)
            for name in subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASELINE_C, 'workbench/app'], cwd=ROOT, text=True).splitlines():
                target = source / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(subprocess.check_output(['git', 'show', BASELINE_C + ':' + name], cwd=ROOT))
        out = fixture / 'ui-output'
        out.mkdir()
        electron = Electron(SimpleNamespace(source=source, env=env, state=state, dir=fixture, out=out), 't249-' + uuid.uuid4().hex[:8])
        ev = electron.evaluate

        def type_name(value):
            return (f'''(()=>{{{JS_HELPERS};const i=document.querySelector('[data-git-dialog="createBranch"] [data-git-input="name"]');'''
                    f'''if(!i)return false;window.__t249.setValue(i,{json.dumps(value)});return true}})()''')

        def helper(expression):
            return ev(f'(()=>{{{JS_HELPERS};return ({expression})}})()')
        electron.until('窗口加载', f'''(()=>{{{JS_HELPERS};const r=document.querySelector('[data-project-id="{project}"]');if(!r||r.disabled)return false;r.click();return true}})()''', 60)
        check_panel_present(electron, check)

        # 1. 项目主目录：没有聚焦窗格时跟随项目主目录 alpha。
        dock = electron.until('面板跟随项目主目录', f'''(()=>{{const d={JS_DOCK};return d&&d.source==='project'&&d.repo?d:null}})()''', 30)
        check(real(dock['repo']) == real(alpha), '没有聚焦窗格时面板跟随项目主目录', dock)
        graph = electron.until('提交表', f'''(()=>{{const g={JS_ROWS};return g&&g.rows.length>1?g:null}})()''', 30)
        electron.screenshot(shots / 'graph.png')
        report['column_geometry'] = check_column_width(electron, check)
        commits = [row for row in graph['rows'] if not row['uncommitted']]
        expected = [line.split() for line in git(alpha, 'rev-list', '--date-order', '--parents', '--all').splitlines() if line]
        report['observed_rows'] = [dict(hash=r['hash'], parents=r['parents'], lane=r['lane'], refs=r['refs']) for r in graph['rows']]
        check([r['hash'] for r in commits] == [e[0] for e in expected], '提交顺序与 git rev-list --date-order --all 一致',
              dict(ui=[r['hash'][:8] for r in commits], git=[e[0][:8] for e in expected]))
        check([r['parents'] for r in commits] == [e[1:] for e in expected], '每行父提交与 git rev-list --parents 一致')
        refs = refs_of(alpha)
        check(all(set(map(tuple, r['refs'])) == refs.get(r['hash'], set()) for r in commits), '每行的分支与标签与 git for-each-ref 一致',
              [(r['hash'][:8], r['refs'], sorted(refs.get(r['hash'], set()))) for r in commits])
        head = git(alpha, 'rev-parse', 'HEAD').strip()
        status = [e for e in git(alpha, 'status', '--porcelain=v1', '-z', '--untracked-files=all').split('\0') if e]
        top = graph['rows'][0]
        check(top['uncommitted'] and top['parents'] == [head], '最上面一行是未提交的改动，父提交是 HEAD', top)
        check(f'（{len(status)} 个文件）' in top['subject'], '未提交行的文件数与 git status 一致', dict(subject=top['subject'], status=len(status)))
        head_row = next(r for r in graph['rows'] if r['hash'] == head)
        check(any(s[5] for s in top['segments']) and any(s[5] and s[3] == 0.5 and s[2] == head_row['lane'] for s in head_row['segments']),
              '未提交行用虚线连到 HEAD 的圆点', dict(top=top['segments'], head=head_row['segments']))

        # 在写操作之前走完整详情路径；断开详情或文件点击分别命中自己的业务断言。
        report['detail_scenarios'] = [check_commit_details(electron, check, alpha, hashes['c3'], '主仓库普通提交', ['c.txt'])]
        electron.screenshot(shots / 'details-closed.png')

        # 2. 写操作：新建分支再删除；名字以 - 开头被拒（界面校验与主进程边界各一次），仓库不变。
        before = ref_lines(alpha)
        row = f'''document.querySelector('[data-git-rows] [data-commit-hash="{hashes['c3']}"]')'''
        helper(f'window.__t249.menu({row})')
        electron.until('右键菜单', '''(()=>{const b=document.querySelector('[data-git-menu] [data-git-action="createBranch"]');if(!b)return false;b.click();return true})()''')
        electron.until('新建分支对话框', type_name('made-by-ui'))
        electron.until('确认', '''(()=>{const i=document.querySelector('[data-git-input="name"]');if(i?.value!=='made-by-ui')return false;document.querySelector('[data-git-confirm]').click();return true})()''')
        electron.until('对话框关闭', '''!document.querySelector('[data-git-dialog]')''')
        after = ref_lines(alpha)
        check(sorted(after) == sorted(before + [f"{hashes['c3']} refs/heads/made-by-ui"]), '界面新建分支后只多出 refs/heads/made-by-ui，指向 c3',
              dict(before=before, after=after))
        label = '''document.querySelector('[data-ref-kind="branch"][data-ref-name="made-by-ui"]')'''
        electron.until('新分支标签出现在图上', f'Boolean({label})', 20)
        helper(f'window.__t249.menu({label})')
        electron.until('删除分支菜单', '''(()=>{const b=document.querySelector('[data-git-menu] [data-git-action="deleteBranch"]');if(!b)return false;b.click();return true})()''')
        danger = electron.until('删除确认框', '''(()=>{const c=document.querySelector('[data-git-dialog="deleteBranch"] [data-git-confirm]');return c?c.className:null})()''')
        check('danger' in danger, '删除分支的确认按钮标为破坏性操作', danger)
        ev('''document.querySelector('[data-git-confirm]').click()''')
        electron.until('对话框关闭', '''!document.querySelector('[data-git-dialog]')''')
        check(sorted(ref_lines(alpha)) == sorted(before), '界面删除分支后引用回到原样')
        helper(f'window.__t249.menu({row})')
        electron.until('右键菜单', '''(()=>{const b=document.querySelector('[data-git-menu] [data-git-action="createBranch"]');if(!b)return false;b.click();return true})()''')
        electron.until('输入 -bad', type_name('-bad'))
        electron.until('确认', '''(()=>{const i=document.querySelector('[data-git-input="name"]');if(i?.value!=='-bad')return false;document.querySelector('[data-git-confirm]').click();return true})()''')
        refusal = electron.until('拒绝提示', '''document.querySelector('[data-git-dialog-error]')?.textContent||null''')
        ev('''document.querySelector('[data-git-cancel]').click()''')
        direct = ev(f'''window.a2a.gitAction({json.dumps(real(alpha))},{{type:'createBranch',hash:{json.dumps(hashes['c3'])}}},{{name:'-f'}}).then(()=>'accepted',e=>String(e))''')
        check(direct != 'accepted', '绕过界面直接请求主进程新建名为 -f 的分支被拒', direct)
        check(sorted(ref_lines(alpha)) == sorted(before), '名字以 - 开头被拒，引用不变', dict(refusal=refusal, direct=direct))
        check(git(alpha, 'status', '--porcelain=v1', '--untracked-files=all').count('\n') == len(status), '写操作没有动未提交的改动')

        # 3. 跟随：聚焦 roam 终端（shell 已 cd 到 beta）→ 面板换成 beta。
        def show(name):
            launch = launches[name]['id']
            visible = f'''(()=>{{const p=document.querySelector('.pane[data-launch-id="{launch}"]');return Boolean(p&&p.offsetParent!==null)}})()'''
            for _ in range(3):
                electron.until(f'{name} 的侧栏行', f'''(()=>{{const r=document.querySelector('[data-agent-launch="{launch}"]');if(!r||r.disabled)return false;r.click();return true}})()''', 30)
                try:
                    electron.until(f'{name} 终端窗格', visible, 15)
                    break
                except AssertionError:
                    continue
            check(helper(f'window.__t249.focusPane("{launch}")'), f'聚焦 {name} 终端窗格')
            return launch
        show('roam')
        dock = electron.until('面板跟随 roam 终端', f'''(()=>{{const d={JS_DOCK};return d&&d.source==='pane'&&d.repo?d:null}})()''', 30)
        check(real(dock['repo']) == real(beta) and real(dock['dir']) == real(beta), '聚焦的终端 cd 到另一个仓库后，面板换成那个仓库（读的是 shell 的 cwd）', dock)
        ev('''document.querySelector('[data-panel-pin]').click()''')
        electron.until('固定', f'''{JS_DOCK}?.source==='pinned' ''')
        show('multi')
        time.sleep(5)
        dock = ev(JS_DOCK)
        check(dock['source'] == 'pinned' and real(dock['repo'] or '') == real(beta), '固定后聚焦别的终端，面板不再跟随', dock)
        electron.screenshot(shots / 'pinned.png')
        ev('''document.querySelector('[data-panel-unpin]').click()''')
        dock = electron.until('取消固定后跟随 multi', f'''(()=>{{const d={JS_DOCK};return d&&d.source==='pane'&&d.manygit&&d.repos.length?d:null}})()''', 40)
        check(real(dock['manygit']) == real(multi), '非仓库目录显示多仓库列表', dock)
        check(sorted(real(p) for p in dock['repos']) == report['fixture_repos']['multi_repos'], '多仓库列表的仓库与夹具一致（3 个）', dock['repos'])
        electron.screenshot(shots / 'manygit.png')

        # 4. 受管 worktree 只读。
        common_git = Path(git(managed, 'rev-parse', '--path-format=absolute', '--git-common-dir').strip())
        metadata_before, refs_before = metadata_files(common_git), ref_lines(managed)
        show('managed')
        dock = electron.until('面板跟随门禁 worktree', f'''(()=>{{const d={JS_DOCK};return d&&d.source==='pane'&&d.repo&&d.managed==='true'?d:null}})()''', 30)
        check(real(dock['repo']) == real(managed) and dock['readOnlyNote'], '跟随门禁 worktree 时面板只读并说明原因', dock)
        electron.until('受管图的提交表', f'''(()=>{{const g={JS_ROWS};return g&&g.readOnly==='true'&&g.rows.some(r=>!r.uncommitted)}})()''', 30)
        first = git(managed, 'rev-parse', 'HEAD').strip()
        helper(f'''window.__t249.menu(document.querySelector('[data-git-rows] [data-commit-hash="{first}"]'))''')
        disabled = electron.until('受管菜单', '''(()=>{const items=[...document.querySelectorAll('[data-git-menu] [data-git-action]')];if(!items.length)return null;
          return items.map(b=>[b.dataset.gitAction,b.getAttribute('aria-disabled')])})()''')
        writes = [entry for entry in disabled if entry[0] != 'copy']
        check(writes and all(state_ == 'true' for _, state_ in writes), '受管 worktree 的写操作菜单项全部不可用', disabled)
        ev('''document.querySelector('[data-git-menu] [data-git-action="createBranch"]').click()''')
        time.sleep(1)
        check(not ev('''Boolean(document.querySelector('[data-git-dialog]'))'''), '点不可用的写操作不弹确认框')
        ev('''document.querySelector('.git-menu-backdrop')?.click()''')
        direct = ev(f'''window.a2a.gitAction({json.dumps(real(managed))},{{type:'createBranch',hash:{json.dumps(first)}}},{{name:'t249-managed'}}).then(()=>'accepted',e=>String(e))''')
        check(direct != 'accepted' and '只读' in direct, '直接请求主进程改门禁 worktree 被拒', direct)
        direct_read = ev(f'''window.a2a.gitRead({json.dumps(real(managed))},['symbolic-ref','HEAD','refs/heads/feature']).then(()=>'accepted',e=>String(e))''')
        check(direct_read != 'accepted', '只读入口拒绝改写 HEAD 的 symbolic-ref 参数', direct_read)
        electron.screenshot(shots / 'managed.png')
        time.sleep(2)
        check(metadata_files(common_git) == metadata_before and ref_lines(managed) == refs_before, '门禁 worktree 的 Git 元数据不变')

        if args.deferred_diff:
            show('details')
            electron.until('面板跟随详情夹具', f'''(()=>{{const g={JS_ROWS};return g&&g.repo==={json.dumps(real(details))}&&g.rows.length>0}})()''', 30)
            report['deferred_selection'] = check_deferred_selection(electron, check, details)

        # 5. 系统覆盖详情接线：3 类 diff × 3 种字面路径，另测没有 HEAD 的混合状态。
        special_paths = ['file*.txt', 'file[1].txt', ':(glob)*.txt']
        for name, repo, cases in (() if args.deferred_diff else (
            ('details', details, [('根提交', detail_hashes['root']), ('普通提交', detail_hashes['normal']), ('未提交', None)]),
            ('unborn', unborn, [('首次提交前', None)]),
        )):
            show(name)
            electron.until('面板跟随 ' + name, f'''(()=>{{const g={JS_ROWS};return g&&g.repo==={json.dumps(real(repo))}&&g.rows.length>0}})()''', 30)
            git_dirs = {Path(git(repo, 'rev-parse', '--path-format=absolute', option).strip()) for option in ('--git-dir', '--git-common-dir')}
            before_read = {str(path): metadata_files(path) for path in git_dirs}
            for case, revision in cases:
                paths = special_paths + (UNTRACKED_PATHS if revision is None else [])
                report['detail_scenarios'].append(check_commit_details(electron, check, repo, revision, case, paths))
            after_dirs = {Path(git(repo, 'rev-parse', '--path-format=absolute', option).strip()) for option in ('--git-dir', '--git-common-dir')}
            check(after_dirs == git_dirs and {str(path): metadata_files(path) for path in after_dirs} == before_read,
                  name + ' 详情读取前后真实 git-dir/common-dir 路径和字节不变')
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
        after_user = user_core_snapshot()
        report['user_core_unchanged'] = before_user == after_user
        if not report['user_core_unchanged']:
            report['status'] = 'NO_GO'
        if report.get('cleanup') == 'PASS':
            sizes = [p.stat().st_size for p in fixture.rglob('*') if not p.is_symlink() and p.is_file()]
            report['fixture_summary'] = dict(directory=str(fixture), time=time.time(), files=len(sizes), bytes=sum(sizes), result=report['status'])
            # 先落文本状态，再删除夹具；不复制后台凭据和 hc registry。
            (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            shutil.rmtree(fixture)
            report['fixture_removed'] = not fixture.exists()
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status', 'mutant', 'error', 'cleanup', 'user_core_unchanged') if k in report}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
