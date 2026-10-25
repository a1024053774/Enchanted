"""T-175: CJK text, a CJK table and powerline separators line up in the workbench terminal; the terminal font is a setting.

Real Electron/daemon/node-pty/zsh. The terminal prints a fixture file with `cat` (zero model calls); the checks read
pixels from a CDP screenshot, because the renderer draws on a canvas.
Failure modes (listed before implementation):
1. A CJK table's right border drifts between rows (L02: the right border of a Chinese table does not line up).
2. A line of CJK characters takes more or less than two cells per character (L02: gaps between Chinese characters).
3. A powerline separator (U+E0B0) shows as a missing-glyph box instead of a solid triangle (L02: p10k separators as boxes).
4. Changing the terminal font in settings does nothing until a restart, or the change is lost after a restart.
5. The expected widths come from the product: the fixture pads the table with its own width rule (wide = 2 cells for
   East Asian Wide/Fullwidth), independent of xterm.
--revision runs the same assertions on that tree.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import traceback
import unicodedata
import uuid

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_claude import Electron, Fixture, quote  # noqa: E402


def width(text):
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in text)


def pad(text, cells):
    return text + ' ' * (cells - width(text))


def table():
    rows = [('任务', '状态'), ('T-1', '机械检查通过，已到 verified，尚未集成'), ('T-2', '独立审查提出一条阻塞 issue，未闭合'),
            ('README', '加“用法”段（中文）')]
    left, right = max(width(a) for a, _ in rows) + 2, max(width(b) for _, b in rows) + 2
    lines = ['┌' + '─' * left + '┬' + '─' * right + '┐']
    for index, (a, b) in enumerate(rows):
        lines.append('│' + pad(' ' + a, left) + '│' + pad(' ' + b, right) + '│')
        if index == 0:
            lines.append('├' + '─' * left + '┼' + '─' * right + '┤')
    lines.append('└' + '─' * left + '┴' + '─' * right + '┘')
    return lines


CJK_LINE = '中文字符之间不该多出空隙'
FIXTURE = '\n'.join(['T175-BEGIN', *table(), CJK_LINE, '\x1b[34m\x1b[0m \x1b[34m\x1b[0m', 'T175-END']) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--revision')
    args = parser.parse_args()
    assert not args.summary.exists(), '保留已有证据，使用新路径'
    report = dict(status='INCOMPLETE', argv=sys.argv, revision=args.revision, checks=[], observed={},
                  runtime='real Electron/daemon/node-pty/zsh; cat of a fixture file, zero model calls')
    fixture = electron = None

    failed = []

    def check(name, condition, detail=None, soft=False):
        # Pixel checks are soft: all three are recorded before the run stops, so a red run shows each of them.
        report['observed'][name] = detail
        if not condition and soft:
            failed.append(name)
            return
        assert condition, f'{name}: {detail}'
        report['checks'].append(name)

    def no_model(body):
        raise AssertionError('no model in this test')

    try:
        fixture = Fixture('t175-', no_model, revision=args.revision)
        report['fixture'] = str(fixture.dir)
        fixture.start('/usr/bin/true', {'README.md': 'T-175 fixture\n'})
        (fixture.out / 'glyphs.txt').write_text(FIXTURE, encoding='utf-8')
        launch = fixture.terminal_launch
        opened = fixture.request('window_open', fixture.operator, launch=launch, project='demo')
        assert opened['ok'], opened
        term = dict(identity=opened['identity'], sequence=0)

        def type_in(data):
            term['sequence'] += 1
            sent = fixture.request('window_input', term['identity'], sequence=term['sequence'], request_id=str(uuid.uuid4()), data=data)
            assert sent['ok'], sent

        def cols():
            return fixture.request('workbench_snapshot', project='demo', launch=launch)['pane']['size']['cols']

        def open_window(label):
            nonlocal electron
            electron = Electron(fixture, label + fixture.dir.name[5:])
            row = f'.agent-row[data-agent-launch="{launch}"]'
            electron.until('项目终端出现', f'!!document.querySelector({json.dumps(row)})', 30)
            electron.evaluate(f'document.querySelector({json.dumps(row)}).click()')
            electron.until('终端窗格出现', '!!document.querySelector(".pane .xterm-screen")', 30)

        open_window('t175a-')
        type_in('clear; cat ' + quote(str(fixture.out / 'glyphs.txt')) + '\r')
        time.sleep(3)
        shot = fixture.out / 'glyphs.png'
        electron.screenshot(shot)
        box = electron.evaluate('(()=>{const r=document.querySelector(".pane .xterm-screen").getBoundingClientRect();'
                                'return {x:r.x,y:r.y,w:r.width,h:r.height,dpr:devicePixelRatio,canvas:!!document.querySelector(".pane .xterm-screen canvas")}})()')
        size = fixture.request('workbench_snapshot', project='demo', launch=launch)['pane']['size']
        report['observed']['screen'] = dict(box=box, size=size)
        image = Image.open(shot).convert('RGB')
        scale = box['dpr']
        cw, ch = box['w'] / size['cols'] * scale, box['h'] / size['rows'] * scale
        x0, y0 = box['x'] * scale, box['y'] * scale

        def band(row):
            return int(y0 + row * ch), int(y0 + (row + 1) * ch)

        def dark(p):
            return sum(p) / 3 < 110

        def rightmost_dark(row):
            top, bottom = band(row)
            for x in range(int(x0 + box['w'] * scale) - 1, int(x0), -1):
                if any(dark(image.getpixel((x, y))) for y in range(top, bottom)):
                    return x
            return None

        # Rows of the cat output: `clear` also clears its own command line, so T175-BEGIN is the first drawn row.
        lines = FIXTURE.splitlines()
        first = None
        for row in range(size['rows']):
            top, bottom = band(row)
            if rightmost_dark(row) is not None:
                first = row
                break
        rows = {}
        for offset, text in enumerate(lines):
            rows[text] = first + offset
        table_rows = [rows[line] for line in table()]
        right = [rightmost_dark(row) for row in table_rows]
        expected = x0 + width(table()[0]) * cw
        check('table_right_border_aligned', None not in right and max(right) - min(right) <= 2 * scale and
              expected - 1.5 * cw <= max(right) <= expected + 1, dict(right=right, expected=round(expected, 1), cell=round(cw, 2)), soft=True)
        cjk_end = rightmost_dark(rows[CJK_LINE])
        check('cjk_two_cells_each', cjk_end is not None and x0 + (width(CJK_LINE) - 2) * cw <= cjk_end <= x0 + width(CJK_LINE) * cw + 1,
              dict(end=cjk_end, start=round(x0, 1), cells=width(CJK_LINE), cell=round(cw, 2)), soft=True)
        # U+E0B0 is a solid right-pointing triangle: its cell's left edge is filled top to bottom, its right edge nearly empty.
        top, bottom = band(rows[lines[-2]])

        def blue_fraction(x):
            column = [image.getpixel((int(x), y)) for y in range(top, bottom)]
            return sum(1 for r, g, b in column if b > 120 and b > r + 50 and b > g + 30) / len(column)
        left_edge, right_edge = blue_fraction(x0 + cw * .12), blue_fraction(x0 + cw * .88)
        check('powerline_triangle_drawn', left_edge > .7 and right_edge < .35, dict(left=round(left_edge, 2), right=round(right_edge, 2)), soft=True)
        image.crop((int(x0), int(y0), int(x0 + box['w'] * scale), int(y0 + (first + len(lines) + 2) * ch))).save(fixture.out / 'glyphs-crop.png')
        report['observed']['shot'] = str(fixture.out / 'glyphs-crop.png')
        assert not failed, f'pixel checks failed: {failed}'

        before = cols()
        electron.evaluate('document.querySelector("[aria-label=\\"设置\\"]").click()')
        electron.until('终端字体设置', '!!document.querySelector("[data-terminal-font]")', 10)

        def set_font(value):
            electron.evaluate('(()=>{const i=document.querySelector("[data-terminal-font]");'
                              'Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(i,' + json.dumps(value) + ');'
                              'i.dispatchEvent(new Event("input",{bubbles:true}));i.form.requestSubmit();return true})()')
        set_font('Helvetica')
        wide = fixture.wait('换成比例字体后列数变化', lambda: (lambda c: c if c != before else None)(cols()), 15)
        check('font_change_applies_now', wide < before, dict(before=before, after=wide))
        custom = '"Courier New", "PingFang SC", monospace'
        set_font(custom)
        fixture.wait('换回等宽字体后列数恢复', lambda: cols() != wide, 15)
        electron.stop()
        electron = None
        open_window('t175b-')
        electron.evaluate('document.querySelector("[aria-label=\\"设置\\"]").click()')
        kept = electron.until('重启后的字体设置', 'document.querySelector("[data-terminal-font]")?.value ?? null', 10)
        check('font_kept_after_restart', kept == custom, kept)
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
    finally:
        for resource in (electron, fixture):
            if resource:
                try:
                    resource.stop()
                except Exception as error:
                    report.setdefault('cleanup_errors', []).append(str(error))
                    report['status'] = 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    print(json.dumps({k: report.get(k) for k in ('status', 'checks', 'error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
