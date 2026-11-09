"""T-261：顶部任务条最新在前、较早的收进下拉框。真实 Electron、后台与门禁；零模型调用。

期望来自本测试自己的创建顺序（任务 id 故意与创建顺序不同），不读产品排序代码。
失败方式：按 id 而不是创建顺序排；较早任务没有收起或丢失；从下拉框选旧任务不切换；
选中的旧任务在任务条上认不出；刷新后顺序变了。
--mutant by-id：任务条改回按 id 排序。
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripted_claude import Electron, Fixture, ROOT

# Created in this order; ids are not in creation order.
TASKS = ['T-07', 'T-12', 'T-01', 'T-30', 'T-05', 'T-22', 'T-09', 'T-15', 'T-03', 'T-27', 'T-11', 'T-02']
RECENT = 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--mutant', choices=['by-id'])
    args = parser.parse_args()
    assert not args.summary.exists(), '保留旧证据，请使用新路径'
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='INCOMPLETE', argv=sys.argv, checks=[], mutant=args.mutant,
                  code_version=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    fixture = electron = None

    def check(name, condition, detail=None):
        report['checks'].append(dict(name=name, passed=bool(condition), detail=detail))
        assert condition, name + ': ' + str(detail)

    try:
        patches = [('app/renderer.tsx', '(b.created ?? 0) - (a.created ?? 0) || a.task_id.localeCompare(b.task_id)', 'a.task_id.localeCompare(b.task_id)')] if args.mutant else []
        fixture = Fixture('t261-', lambda _: (_ for _ in ()).throw(AssertionError('禁止模型请求')), patches=patches)
        report['fixture'] = str(fixture.dir)
        fake = fixture.dir / 'controlled-claude'
        built = subprocess.run(['cc', str(ROOT / 'workbench/tests/t093_fake_claude.c'), '-o', str(fake)], capture_output=True, text=True)
        assert built.returncode == 0, built.stderr
        fixture.start(str(fake), {'README.md': 'T-261\n', 'check.py': 'raise SystemExit(0)\n'})
        for task in TASKS:
            fixture.card(task, task.lower() + '.txt', 'check.py')
        newest = [fixture.project + '+' + task for task in reversed(TASKS)]
        electron = Electron(fixture, fixture.dir.name)
        ev = electron.evaluate
        electron.until('项目出现', '''(()=>{const r=document.querySelector('[data-project-id="demo"]');if(!r)return false;r.click();return true})()''')
        strip = '''(()=>{const n=document.querySelector('.task-strip');if(!n)return null;return {
          chips:[...n.querySelectorAll('[data-task-option]')].map(b=>({id:b.dataset.taskOption,current:b.getAttribute('aria-current')==='page'})),
          older:[...n.querySelectorAll('[data-task-older-option]')].map(o=>o.value)}})()'''
        seen = electron.until('任务条', f'(()=>{{const s={strip};return s&&s.chips.length+s.older.length==={len(TASKS)}?s:null}})()', 30)
        report['initial'] = seen
        check('newest_first_visible', [c['id'] for c in seen['chips']] == newest[:RECENT], dict(ui=seen['chips'], want=newest[:RECENT]))
        check('older_folded_in_order', seen['older'] == newest[RECENT:], dict(ui=seen['older'], want=newest[RECENT:]))
        oldest = newest[-1]
        ev(f'''(()=>{{const s=document.querySelector('[data-task-older]');const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;
          set.call(s,{json.dumps(oldest)});s.dispatchEvent(new Event('change',{{bubbles:true}}));return true}})()''')
        picked = electron.until('选中最旧的任务', f'''(()=>{{const s={strip};return s&&s.chips.some(c=>c.id==={json.dumps(oldest)}&&c.current)?s:null}})()''', 30)
        check('old_task_selected_and_shown', [c['id'] for c in picked['chips']] == newest[:RECENT] + [oldest] and picked['older'] == newest[RECENT:], picked)
        electron.screenshot(args.summary.parent / (args.summary.stem + '-strip.png'))
        ev('location.reload()')
        electron.until('刷新后项目', '''(()=>{const r=document.querySelector('[data-project-id="demo"]');if(!r)return false;r.click();return true})()''')
        again = electron.until('刷新后任务条', f'(()=>{{const s={strip};return s&&s.chips.length+s.older.length>={len(TASKS)}?s:null}})()', 30)
        check('order_after_reload', [c['id'] for c in again['chips']][:RECENT] == newest[:RECENT] and again['older'] == newest[RECENT:], again)
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
        if report['checks'] and not report['checks'][-1]['passed']:
            report['status'] = 'FAIL'
    finally:
        if electron:
            electron.stop()
        if fixture:
            fixture.stop()
            report['core_cleanup'] = getattr(fixture, 'core_cleanup', None)
        args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report.get(k) for k in ('status', 'mutant', 'error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
