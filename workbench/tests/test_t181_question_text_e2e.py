"""T-181（L09）：Claude Code 的 AskUserQuestion 在 Enchanted 终端里问题正文显示为空白。
真实后台、真实 Electron 与 xterm（WebGL 渲染），真实安装的 Claude Code 在项目终端的 zsh 里由用户命令启动；模型是本地脚本化接口。
问题用 lcu 实测里那一句原文（约 170 字、含路径与括号）和一句短问题对照，两个终端同时显示。

要回答的是：正文空白发生在哪一层。
1. Claude Code 根本没把正文写进终端（PTY 原始输出里没有）→ CLI 自身的排版，不归工作台。
2. PTY 里有，xterm 的缓冲区里没有 → 工作台的终端写入或解析问题。
3. 缓冲区里有，截图上看不到 → 渲染（颜色、字形、WebGL）问题。
每个终端记录 PTY 原始输出、xterm 缓冲区全文与截图。

修后的检查（期望来自 T-181 ticket：L09“能修则修”；L08 主控说明要让做主控的 CLI 直接知道 a2a request 与 a2a help）：
4. question_visible_<名>：截图里问题正文那一行有足够的深色像素（修前是白字白底，几乎为 0）。
5. orientation_in_model_context：Claude Code 发给模型的第一个请求里带着 Enchanted 的开局说明（SessionStart 钩子），
   含 `a2a help` 与 `a2a request`；修前没有。
--revision 在该版本源码上跑同一场景（修前应复现 4、5）。
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, prompt_text  # noqa: E402

LONG = ('是否批准我成为本项目（/private/tmp/a2a-lcu-demo）的执行主控（a2a request executor）？批准后我将：1）生成 restock.md 补货清单'
        '（当前 stock.csv 中低于 min 的有 苹果 3/5、牛奶 1/4）；2）另起一个任务在 README.md 加一段用法说明；两件事分别派给两个 worker 并行完成。')
SHORT = '先做哪一个？'
OPTIONS = [dict(label='批准（Recommended）', description='同意我作为执行主控，派两个 worker 并行完成 restock.md 和 README 用法说明'),
           dict(label='不批准', description='不执行，保持项目现状')]
# Test-only instrumentation: reach each pane's xterm to read its buffer.
EXPOSE = [('app/renderer.tsx', 'term.open(mount.current!);', 'term.open(mount.current!); (mount.current as any).__testTerminal = term;')]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude', default=shutil.which('claude') or str(Path.home() / '.local/bin/claude'))
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留既有证据，改用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, real_model_turns=0, observed={}, checks=[], failed=[])
    contexts = []

    def check(name, condition, detail=None):
        (report['checks'] if condition else report['failed']).append(dict(name=name, detail=detail))

    def plan(body):
        text = prompt_text(body)
        whole = json.dumps(body, ensure_ascii=False)
        contexts.append('a2a help' in whole and 'a2a request executor' in whole and 'Enchanted 工作台的项目终端' in whole)
        question = LONG if 'L09_LONG' in text else SHORT
        return 'asker', [('AskUserQuestion', dict(questions=[dict(question=question, header='批准申请', multiSelect=False, options=OPTIONS)]))], '好的。'

    fixture = Fixture('t181q-', plan, revision=args.revision, patches=EXPOSE)
    report['fixture'] = str(fixture.dir)
    electron = None

    def strip(raw):
        return re.sub(r'\s+', '', re.sub(r'\x1b\[[0-9;?<>=]*[A-Za-z~]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b[()][A-Z0-9]|\x1b[=>78]', '', raw))

    def raw(launch):
        return (fixture.state / 'traces' / launch / 'pty.raw').read_text(encoding='utf-8', errors='replace')

    def buffer(launch):
        return electron.evaluate(f"""(()=>{{const t=document.querySelector('.pane[data-launch-id="{launch}"] .terminal-mount')?.__testTerminal;
          return t?Array.from({{length:t.buffer.active.length}},(_,i)=>t.buffer.active.getLine(i).translateToString(true)).join('\\n'):null}})()""")

    def type_in(term, data):
        term['sequence'] += 1
        sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
        assert sent['ok'], sent

    try:
        fixture.start(args.claude, {'README.md': 'demo\n'})
        claude_json = json.loads((fixture.home / '.claude.json').read_text(encoding='utf-8'))
        claude_json['projects'] = {str(fixture.repo): {'hasTrustDialogAccepted': True}}
        (fixture.home / '.claude.json').write_text(json.dumps(claude_json), encoding='utf-8')
        electron = Electron(fixture, 't181q-' + fixture.dir.name[6:])
        electron.until('项目出现', "!!document.querySelector('[data-project-id=\"demo\"]')")
        for name, marker, question in (('long', 'L09_LONG', LONG), ('short', 'L09_SHORT', SHORT)):
            launch = fixture.run_cli('shell_start', '--project', 'demo', '--cwd', str(fixture.repo))['launch']['id']
            window = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
            assert window['ok'], window
            term = dict(identity=window['identity'], sequence=0)
            electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
            electron.until('终端出现', f"!!document.querySelector('[data-terminal-launch=\"{launch}\"], [data-agent-launch=\"{launch}\"]')", 30)
            electron.evaluate(f"document.querySelector('[data-terminal-launch=\"{launch}\"], [data-agent-launch=\"{launch}\"]').click()")
            electron.until('窗格出现', f"!!document.querySelector('.pane[data-launch-id=\"{launch}\"] .terminal-mount')?.__testTerminal", 30)
            type_in(term, 'claude --model claude-haiku-5-5\r')
            fixture.wait('Claude 启动', lambda: 'ClaudeCodev' in strip(raw(launch)) and '❯' in strip(raw(launch)).split('ClaudeCodev', 1)[1], 60)
            type_in(term, marker)
            time.sleep(1)
            type_in(term, '\r')
            fixture.wait('问题出现', lambda: 'Entertoselect' in strip(raw(launch)), 60)
            time.sleep(2)
            text = buffer(launch) or ''
            columns = electron.evaluate(f"document.querySelector('.pane[data-launch-id=\"{launch}\"] .terminal-mount').__testTerminal.cols")
            needle = strip(question)[:24]
            pty = strip(raw(launch))
            report['observed'][name] = dict(launch=launch, cols=columns, question_in_pty=needle in pty, question_in_buffer=needle in strip(text),
                                            header_in_buffer='批准申请' in text,
                                            buffer_tail=text.rstrip().splitlines()[-30:])
            (fixture.out / f'{name}-pty.raw').write_text(raw(launch), encoding='utf-8')
            (fixture.out / f'{name}-buffer.txt').write_text(text, encoding='utf-8')
            electron.screenshot(fixture.out / f'{name}.png')
            # The question's row on screen: its viewport row times the cell height, inside the xterm screen element.
            where = electron.evaluate(f"""(()=>{{const m=document.querySelector('.pane[data-launch-id="{launch}"] .terminal-mount'),t=m.__testTerminal,b=t.buffer.active;
              let row=-1;for(let i=0;i<t.rows;i++){{const l=b.getLine(b.viewportY+i);if(l&&l.translateToString(true).includes({json.dumps(question[:6])})){{row=i;break}}}}
              const r=m.querySelector('.xterm-screen').getBoundingClientRect();return {{row,rows:t.rows,left:r.left,top:r.top,width:r.width,height:r.height,inner:window.innerWidth}}}})()""")
            image = Image.open(fixture.out / f'{name}.png').convert('L')
            scale = image.width / where['inner']
            cell = where['height'] / where['rows']
            box = tuple(round(v * scale) for v in (where['left'], where['top'] + where['row'] * cell, where['left'] + where['width'], where['top'] + (where['row'] + 1) * cell))
            dark = sum(1 for value in image.crop(box).getdata() if value < 160) if where['row'] >= 0 else 0
            report['observed'][name].update(question_row=where['row'], dark_pixels=dark)
            check(f'question_visible_{name}', dark >= 200, dict(row=where['row'], dark_pixels=dark))
        check('orientation_in_model_context', bool(contexts) and all(contexts), contexts)
        report['status'] = 'PASS' if not report['failed'] else 'INCOMPLETE'
    except BaseException as error:
        report['error'] = f'{type(error).__name__}: {error}'
        if electron:
            try:
                electron.screenshot(fixture.out / 'failure.png')
            except BaseException:
                pass
    finally:
        try:
            if electron:
                electron.stop()
        finally:
            fixture.stop()
            report['out'] = str(fixture.out)
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], error=report.get('error'), failed=[f['name'] for f in report['failed']],
                          observed={k: {x: v.get(x) for x in ('question_in_pty', 'question_in_buffer', 'dark_pixels')} for k, v in report['observed'].items()}),
                     ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
