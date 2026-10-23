"""Extend the protected T-133/T-107 scenario without changing its assertions.

Failure modes (contract: T-146-4): API removes the released controller but the
sidebar keeps its role or ended state; flow DOM retains it; Reflect loses the
ended historical role; an empty/unloaded page is mistaken for successful removal.
Real daemon, Electron and Claude CLI use the existing scripted Messages fixture.
--summary requires a fresh path; --revision runs old sources;
--mutant stale-terminal-ui keeps API correct but marks ordinary terminal UI ended.
"""
import argparse
import json
from pathlib import Path
import sys

import test_t133_t107_terminal_controller_e2e as oracle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--claude')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--revision')
    mode.add_argument('--mutant', choices=['stale-terminal-ui'])
    args = parser.parse_args()
    original_summary = args.summary.with_name(args.summary.stem + '-oracle.json')
    assert not args.summary.exists() and not original_summary.exists(), 'Fresh evidence paths required'
    extra = dict(checks=[], observed={})
    original_fixture, original_electron = oracle.Fixture, oracle.Electron

    class ObservedElectron(original_electron):
        def __init__(self, fixture, slot):
            super().__init__(fixture, slot)
            fixture.release_electron = self

    class ObservedFixture(original_fixture):
        def __init__(self, *arguments, **kwargs):
            if args.mutant:
                kwargs['patches'] = list(kwargs.get('patches', ())) + [
                    ('app/renderer.tsx', 'setOrdinaryTerminals(value.terminals);',
                     "setOrdinaryTerminals(value.terminals.map(row => ({...row, state: 'ended', state_label: '已结束'})));")]
            super().__init__(*arguments, **kwargs)

        def wait(self, label, predicate, timeout=90):
            result = super().wait(label, predicate, timeout)
            if label == '放弃身份的回合结束':
                self.check_release_visibility()
            return result

        def check_release_visibility(self):
            released = []
            for item in self.api.results['ideation']:
                try:
                    value = json.loads(item.get('text', ''))
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict) and value.get('ok') and value.get('role_request', {}).get('ended_reason') == 'released':
                    released.append(value['role_request'])
            assert len(released) == 1, released
            role = released[0]
            extra['observed']['released_role'] = role
            launch = role['launch']
            sidebar = self.request('sidebar_snapshot')
            extra['observed']['sidebar'] = sidebar
            assert not any(row['id'] == launch for row in sidebar['agents'])
            terminal = next(row for row in sidebar['terminals'] if row['id'] == launch)
            assert terminal['role'] == 'shell' and terminal['state'] == 'running', terminal
            extra['checks'].append('released_api_is_running_ordinary_terminal')
            electron = self.release_electron
            selector = json.dumps(f'.agent-row[data-agent-launch="{launch}"]')
            read_sidebar = (f"(()=>{{const rows=[...document.querySelectorAll({selector})];return rows.map(r=>"
                            "({state:r.dataset.agentState,role:r.querySelector('.agent-role').textContent,"
                            "ordinary:!!r.closest('.project-terminals'),visible:r.getClientRects().length>0}))})()")
            extra['observed']['sidebar_before_poll'] = electron.evaluate(read_sidebar)
            electron.screenshot(self.out / '07-release-before-poll.png')
            try:
                electron.until('交回后普通终端可见且运行中', f"JSON.stringify({read_sidebar}) === "
                               + json.dumps('[{"state":"running","role":"普通终端","ordinary":true,"visible":true}]'), 30)
            finally:
                extra['observed']['sidebar_dom'] = electron.evaluate(read_sidebar)
                electron.screenshot(self.out / '08-release-sidebar.png')
            extra['checks'].append('released_sidebar_dom_is_running_ordinary_terminal')
            electron.evaluate("document.querySelector('[data-project-id=\"demo\"]').click()")
            electron.until('流程页签可用', "!!document.querySelector('[data-flow-tab]')", 30)
            electron.evaluate("document.querySelector('[data-flow-tab]').click()")
            electron.until('流程已加载对照会话', "document.querySelectorAll('[data-flow-agent]').length > 0", 30)
            flow = self.request('flow_snapshot')
            extra['observed']['flow'] = flow
            flow_agents = flow['unassigned'] + [a for lane in flow['lanes'] for a in lane['agents'] + lane['monitors']]
            assert flow_agents and not any(row['id'] == launch for row in flow_agents)
            read_flow = "[...document.querySelectorAll('[data-flow-agent]')].map(n=>n.dataset.flowAgent).sort()"
            # Transport synchronization only; the independent assertion above requires removal.
            electron.until('流程 DOM 与后台同步', f'JSON.stringify({read_flow}) === '
                           + json.dumps(json.dumps(sorted(row['id'] for row in flow_agents), separators=(',', ':'))), 30)
            extra['observed']['flow_dom'] = electron.evaluate(read_flow)
            assert launch not in extra['observed']['flow_dom']
            extra['checks'].append('released_controller_absent_from_flow_api_and_dom')
            electron.screenshot(self.out / '09-release-flow.png')
            reflect = self.request('reflect_tree', project='demo')
            extra['observed']['reflect'] = reflect
            assert next(row for row in reflect['nodes'] if row['id'] == role['id'])['state'] == 'ended'
            electron.evaluate("document.querySelector('[data-reflect-tab]').click()")
            node = json.dumps(f'[data-reflect-node="{role["id"]}"]')
            electron.until('Reflect 保留已交回的历史角色',
                           f"(()=>{{const n=document.querySelector({node});return n?.dataset.reflectState==='ended' && "
                           "n.querySelector('.record-state').textContent==='已结束' && n.getClientRects().length>0})()", 30)
            extra['observed']['reflect_dom'] = electron.evaluate(
                f"(()=>{{const n=document.querySelector({node});return {{state:n.dataset.reflectState,text:n.innerText}}}})()")
            extra['checks'].append('released_role_history_visible_and_ended')
            electron.screenshot(self.out / '10-release-reflect.png')

    oracle.Fixture, oracle.Electron = ObservedFixture, ObservedElectron
    sys.argv = [sys.argv[0], '--summary', str(original_summary)]
    if args.claude:
        sys.argv += ['--claude', args.claude]
    if args.revision:
        sys.argv += ['--revision', args.revision]
    try:
        oracle.main()
        assert len(extra['checks']) == 4, 'Release visibility checkpoint was not reached'
    finally:
        report = json.loads(original_summary.read_text(encoding='utf-8')) if original_summary.exists() else dict(status='INCOMPLETE')
        report['release_visibility'] = extra
        report['visibility_mutant'] = args.mutant
        if len(extra['checks']) != 4:
            report['status'] = 'INCOMPLETE'
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open('x', encoding='utf-8') as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write('\n')


if __name__ == '__main__':
    main()
