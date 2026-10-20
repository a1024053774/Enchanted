"""T-110 assertions through real Electron; expected behavior comes from the ticket."""
import time


def before_prompt(window, disabled, report):
    view = window.wait(lambda v: v['panes'] and not v['notices'], 'No idle notification')
    assert view['notices'] == []
    report['before_highlight'] = {kind: {row['id']: row['background'] for row in view[kind]} for kind in ['agents', 'projects']}
    window.call('watch-notices')
    if disabled:
        window.call('notification-setting', preference='notifications', enabled=False)
        window.wait(lambda v: v['notification_settings']['notifications'] is False, 'App notification setting disabled')
    report['checks'].append('t110_idle_silent_before_prompt')


def waiting(window, disabled, report):
    view = window.wait(lambda v: any(a['state'] == 'waiting_user_answer' for a in v['agents']), 'Sidebar waiting state')
    if disabled:
        # More than two production polling periods, while the genuine question waits.
        time.sleep(6.2)
        view = window.call('inspect')
        assert not view['notices'] and view['notice_additions'] == 0, view
        assert any(a['state'] == 'waiting_user_answer' for a in view['agents'])
        window.call('notification-setting', preference='notifications', enabled=True)
        window.wait(lambda v: v['notification_settings']['notifications'] is True, 'Setting re-enabled')
        time.sleep(3.2)
        assert window.call('inspect')['notices'] == [], 'Re-enabling must not repeat an observed question'
        report['checks'].append('t110_disabled_question_silent_and_no_replay')
        return
    view = window.wait(lambda v: len(v['notices']) == 1, 'One in-app waiting-user notification')
    notice = view['notices'][0]
    agent = next(a for a in view['agents'] if a['id'] == notice['launch'])
    project = next(p for p in view['projects'] if p['id'] == agent['project'])
    assert agent['state'] == project['state'] == 'waiting_user_answer'
    assert agent['background'] == project['background'] == 'rgba(230, 180, 80, 0.12)', view
    assert agent['background'] != report['before_highlight']['agents'][agent['id']], view
    assert project['background'] != report['before_highlight']['projects'][project['id']], view
    assert notice['id'] == view['questions'][0]['id'] and '等待用户回答' in notice['text']
    time.sleep(6.2)
    duplicate = window.call('inspect')
    assert len(duplicate['notices']) == 1 and duplicate['notice_additions'] == 1, duplicate
    window.call('background')
    window.wait(lambda v: v['badge'] == 1, 'Background Dock count one')
    window.call('notification-setting', preference='dockBadges', enabled=False)
    window.wait(lambda v: v['badge'] == 0 and v['notification_settings']['dockBadges'] is False, 'Dock preference clears count')
    window.call('notification-setting', preference='dockBadges', enabled=True)
    window.wait(lambda v: v['badge'] == 1, 'Dock preference restores pending count')
    window.call('foreground')
    window.wait(lambda v: v['badge'] == 0, 'Foreground clears Dock count')
    window.call('flow-page')
    window.wait(lambda v: v['terminal_hidden'], 'Flow page selected')
    window.call('click-notice')
    focused = window.wait(lambda v: not v['terminal_hidden'] and v['focused_launch'] == notice['launch'], 'Notification focuses the bound pane from flow')
    assert focused['focused_agent'] == notice['launch']
    report['checks'].extend(['t110_sidebar_project_and_agent_highlight_with_notice', 't110_question_identity_and_one_dom_addition',
                             't110_notification_click_focuses_bound_pane_from_flow', 't110_background_dock_count_and_setting'])


def after_answer(window, disabled, report):
    view = window.wait(lambda v: not v['notices'] and not v['questions'] and all(a['state'] != 'waiting_user_answer' for a in v['agents']),
                       'Answered question removes notification and waiting highlight')
    assert all(p['state'] != 'waiting_user_answer' for p in view['projects'])
    time.sleep(3.2)
    assert window.call('inspect')['notices'] == [], 'Idle does not notify'
    report['checks'].append('t110_answer_removes_notification_and_highlight_idle_silent')
