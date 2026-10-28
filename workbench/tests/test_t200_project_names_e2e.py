"""T-200：目录名含中文等非 ASCII 字符的项目，界面显示目录名，不显示由项目号生成规则得来的 `project`、`project-2`。
真实后台、socket、Electron 窗口（CDP 驱动），零模型调用。

预期来自需求（T-200 与第 1 轮试用发现 2）：
- 打开 `我的 项目` 与 `另一个项目`：侧栏、选中后的标题、角色申请横幅都显示目录名；项目号仍是 project、project-2（门禁记录不变）。
- 不同位置的两个目录同名（再打开一个 `我的 项目`）：界面上两者能区分。

失败方式（先列再写）：
1. 仍显示项目号（修前）。
2. 只改了侧栏，标题或申请横幅仍显示项目号。
3. 改了项目号或门禁记录（不做）。
4. 同名目录在界面上无法区分。
5. 普通 ASCII 名的项目显示变了（例如 demo 变成别的）。
--revision 在该版本的源码上跑同一场景（修前应在第 1 条失败）；--mutant 去掉同名区分。
"""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import traceback
import uuid

from scripted_claude import Electron, Fixture

MUTANTS = {
    'no-twin-suffix': [('app/renderer.tsx', "return twin ? `${name} · ${id}` : name;", 'return name;')],
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
                  runtime='real Electron/daemon/zsh; zero model calls', checks=[])
    fixture = electron = asker = None

    def check(name, condition, detail=None):
        report.setdefault('details', {})[name] = detail
        if condition:
            report['checks'].append(name)
        else:
            report.setdefault('failed', []).append(name)

    try:
        def no_model(body):
            raise AssertionError('T-200 不调用模型')
        fixture = Fixture('t200-', no_model, revision=args.revision, patches=MUTANTS.get(args.mutant, ()))
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/false', {'README.md': 'demo\n'})
        repos = [fixture.dir / '我的 项目', fixture.dir / '另一个项目', fixture.dir / 'elsewhere' / '我的 项目']
        ids = []
        for repo in repos:
            repo.mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True, env=fixture.env)
            (repo / 'README.md').write_text('t200\n', encoding='utf-8')
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True, env=fixture.env)
            subprocess.run(['git', '-C', str(repo), 'commit', '-q', '-m', 'init'], check=True, env=fixture.env)
            opened = fixture.request('project_open', fixture.operator, repo=str(repo))
            assert opened['ok'], opened
            ids.append(opened['project'])
        report['project_ids'] = ids
        check('project_ids_unchanged', ids == ['project', 'project-2', 'project-3'], ids)

        # A pending role request from a terminal of the first Chinese project, for the banner.
        launch = fixture.run_cli('shell_start', '--project', ids[0], '--cwd', str(repos[0]))['launch']['id']
        window = fixture.request('window_open', fixture.operator, launch=launch, project=ids[0])
        token_file = fixture.out / 'token-cn.txt'
        assert fixture.request('window_input', window['identity'], sequence=1, request_id=str(uuid.uuid4()),
                               data=f'print -r -- $A2A_TERMINAL_TOKEN > {token_file}\r')['ok']
        fixture.wait('终端令牌', lambda: token_file.exists() and token_file.read_text().strip(), 30)
        asker = socket.socket(socket.AF_UNIX)
        asker.connect(str(fixture.state / 'control.sock'))
        asker.sendall((json.dumps(dict(id=str(uuid.uuid4()), input=dict(command='role_request', role='ideation', wait_seconds=120),
                                       identity=dict(kind='terminal', launch=launch, token=token_file.read_text().strip()))) + '\n').encode())
        fixture.wait('申请待批', lambda: [r for r in fixture.request('sidebar_snapshot').get('role_requests', []) if r['launch'] == launch], 20)

        electron = Electron(fixture, 't200-' + uuid.uuid4().hex[:10])
        electron.until('项目列表', f'document.querySelectorAll("[data-project-id]").length >= 4')
        titles = electron.evaluate('Object.fromEntries([...document.querySelectorAll("[data-project-id]")].map(n=>[n.dataset.projectId,n.querySelector(".project-title").textContent]))')
        report['sidebar_titles'] = titles
        check('sidebar_shows_directory_names', titles.get('project', '').startswith('我的 项目') and titles.get('project-2') == '另一个项目', titles)
        check('ascii_project_unchanged', titles.get(fixture.project) == fixture.project, titles)
        check('twin_directories_distinguishable', titles.get('project') != titles.get('project-3') and
              titles.get('project-3', '').startswith('我的 项目'), titles)
        banner = electron.until('申请横幅', '(()=>{const n=document.querySelector(".role-requests");return n?n.textContent:null})()')
        report['banner'] = banner
        check('banner_shows_directory_name', '我的 项目' in banner, banner)
        electron.evaluate('document.querySelector(\'[data-project-id="project-2"]\').click()')
        heading = electron.until('标题', '(()=>{const h=document.querySelector("h1");return h&&h.textContent!=="正在读取项目"?h.textContent:null})()')
        report['heading'] = heading
        check('heading_shows_directory_name', heading == '另一个项目', heading)
        electron.screenshot(fixture.out / 'names.png')
        catalog = fixture.request('sidebar_snapshot')
        check('gate_records_keep_ids', sorted(p['project_id'] for p in catalog['projects']) == sorted([fixture.project, *ids]),
              [p['project_id'] for p in catalog['projects']])
        assert not report.get('failed'), '未通过：' + '、'.join(report['failed'])
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
        report['status'] = 'FAIL'
    finally:
        if asker:
            asker.close()
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
