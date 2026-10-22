"""T-136 真实运行：用户自己的 Claude Code（haiku，控成本）跑一次复盘，从界面“立即复盘”启动。

只跑复盘，不派 worker（真实 worker 要另配隔离登录，这次不需要）。后台、终端、界面都是真实的，HOME 是用户自己的，
Claude 用用户自己的登录。项目目录放在用户自己的 Claude 早已信任过的路径（--repo，须不存在），a2a 不代答信任、
不写用户配置；运行结束把这个目录移进夹具。期望：会话只写自己的 out/，项目里除了导入的报告没有别的改动；报告进 findings/，
建议（若有）出现在页面。
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture  # noqa: E402

SET_VALUE = ("var set=(el,v)=>{const proto=el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;"
             "Object.getOwnPropertyDescriptor(proto,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));};")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--model', default='claude-haiku-5-5')
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    assert not args.repo.exists(), '项目目录须不存在'
    trusted = json.loads((Path.home() / '.claude.json').read_text(encoding='utf-8')).get('projects', {}).get(str(args.repo), {})
    assert trusted.get('hasTrustDialogAccepted') is True, '须是用户已信任过的路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, model=args.model, checks=[])

    def plan(body):
        raise AssertionError('真实运行不该请求脚本化接口')

    fixture = Fixture('t136-real-', plan)
    # The user's own environment: their HOME and Claude login, no scripted endpoint. Claude finds its login in the
    # macOS keychain under the user's account name, so USER and LOGNAME come along (run 01 said "Not logged in").
    fixture.env.update(HOME=str(Path.home()), **{key: os.environ[key] for key in ('USER', 'LOGNAME') if key in os.environ})
    for key in ('ANTHROPIC_BASE_URL', 'ANTHROPIC_AUTH_TOKEN'):
        fixture.env.pop(key, None)
    args.repo.mkdir(parents=True)
    fixture.repo = args.repo
    report['fixture'], report['repo'] = str(fixture.dir), str(args.repo)
    electron = None

    def check(name, condition, detail=None):
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def listing():
        listed = fixture.request('retrospective_list', project='demo')
        assert listed.get('ok'), listed
        return listed

    try:
        (args.repo / 'findings').mkdir()
        fixture.start(args.claude, {'README.md': '# demo\n\n复盘真实运行的夹具项目。\n', 'findings/README.md': '发现\n'})
        electron = Electron(fixture, 't136-real-' + fixture.dir.name[10:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
        electron.until('复盘页签', "!!document.querySelector('[data-retrospective-tab]')", 20)
        electron.evaluate("document.querySelector('[data-retrospective-tab]').click()")
        electron.until('复盘页', "!!document.querySelector('[data-start-retrospective]')", 30)
        field = "[...document.querySelectorAll('.retrospective-page label')].find(l=>l.textContent.startsWith('{}')).querySelector('input')"
        electron.evaluate(SET_VALUE + f"set({field.format('模型')},{json.dumps(args.model)});set({field.format('思考强度')},'low');")
        electron.until('已填', f"{field.format('模型')}.value==={json.dumps(args.model)}", 10)
        electron.screenshot(fixture.out / '01-before-start.png')
        electron.evaluate("document.querySelector('[data-start-retrospective]').click()")
        run = fixture.wait('复盘开始', lambda: listing()['runs'], 30)[0]
        report['run'] = {k: run[k] for k in ('id', 'cli', 'model', 'effort', 'since', 'until', 'out', 'package')}
        started = [e for e in fixture.request('orchestration_events')['events'] if e['type'] == 'retrospective_started']
        report['argv_head'] = started[0]['data']['argv'][:10] if started else None
        check('launched_with_selected_model', run['model'] == args.model and started and
              started[0]['data']['argv'][started[0]['data']['argv'].index('--model') + 1] == args.model, report['argv_head'])
        electron.screenshot(fixture.out / '02-started.png')

        out = Path(run['out'])
        fixture.wait('会话写完', lambda: (out / 'suggestions.json').exists() and (out / 'report.md').exists(), 900)
        report['out_files'] = sorted(str(p.relative_to(out)) for p in out.rglob('*'))
        changed = [line for line in fixture.git('status', '--porcelain', '--untracked-files=all').splitlines()
                   if not re.fullmatch(r'\?\? findings/\d{4}-\d\d-\d\d-retrospective-[0-9a-f]{8}\.md', line)]
        check('session_wrote_only_out', changed == [], changed)
        assert fixture.request('retrospective_tick', fixture.operator)['ok']
        imported = fixture.wait('导入', lambda: next((e for e in next(r for r in listing()['runs'] if r['id'] == run['id'])['events']
                                                    if e['type'] in ('imported', 'import_failed')), None), 120)
        report['import'] = imported
        destination = Path(imported['data'].get('report', ''))
        check('report_in_findings', imported['type'] == 'imported' and destination.parent == args.repo / 'findings' and
              destination.read_text(encoding='utf-8') == (out / 'report.md').read_text(encoding='utf-8'), imported)
        shutil.copy2(destination, fixture.out / 'report.md')
        shutil.copy2(out / 'suggestions.json', fixture.out / 'suggestions.json')
        suggestions = listing()['suggestions']
        report['suggestions'] = [dict(title=s['title'], kind=s['kind']) for s in suggestions]
        electron.until('页面刷新', f"document.querySelector('tr[data-run-id=\"{run['id']}\"]')?.dataset.runState==='done'", 20)
        shown = electron.evaluate("document.querySelectorAll('.suggestion-card').length")
        check('suggestions_on_page', shown == len(suggestions), dict(shown=shown, listed=len(suggestions)))
        electron.screenshot(fixture.out / '03-imported.png')
        report['status'] = 'PASS'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
        raise
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            # The project directory goes into the fixture (kept as evidence), so the trusted path is free again.
            if args.repo.is_dir():
                shutil.move(str(args.repo), str(fixture.dir / 'repo'))
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
