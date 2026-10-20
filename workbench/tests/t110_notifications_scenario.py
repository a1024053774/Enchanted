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


def waiting(window, disabled, report, receipt_comparison_refresh=False):
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
    original_project = agent['project']
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


    window.call('refresh-list')
    time.sleep(3.2)
    refreshed = window.call('inspect')
    assert len(refreshed['notices']) == 1 and refreshed['notices'][0]['id'] == notice['id'] and refreshed['notice_additions'] == 1, 'List refresh must not add another reminder'
    window.call('reload-window')
    window.wait(lambda v: len(v['notices']) == 1 and v['notices'][0]['id'] == notice['id'], 'Reload preserves the same pending question entry')
    window.call('watch-notices')
    time.sleep(6.2)
    stable = window.call('inspect')
    assert len(stable['notices']) == 1 and stable['notice_additions'] == 0, 'Polling after reload must not append reminders'
    report['checks'].append('t110_refresh_reload_keeps_one_question')

    # Rename only this fixture's socket; the real daemon and CLI keep running.
    window.call('background')
    window.wait(lambda v: v['badge'] == 1, 'Disconnect starts with a verified waiting badge')
    original_pane = next(pane['key'] for pane in view['panes'] if pane['launch'] == notice['launch'])
    socket_identity = window.call('disconnect-sidebar')
    try:
        disconnected = window.wait(lambda v: not v['notices'] and v['agents'] and all(a['state'] == 'unknown' for a in v['agents']),
                                   'Disconnected sidebar becomes unknown')
        report['disconnect_observation'] = {key: disconnected[key] for key in ['badge', 'notices', 'agents', 'sidebar_error']}
        assert disconnected['badge'] == 0, 'Disconnected unknown state must clear Dock badge'
        assert disconnected['sidebar_error'], 'The failed read must remain visible to the caller'
        # Use the existing preload/main resize entry while the endpoint is
        # absent; do not rely on ResizeObserver timing to exercise this fault.
        resize = window.call('offline-resize', pane=original_pane)
        report['disconnected_resize'] = resize
        assert resize['rejected'] and 'ENOENT' in resize['error'], 'Offline resize must preserve its original transport failure'
        window.call('foreground')
        window.call('background')
        assert window.call('inspect')['badge'] == 0, 'Focus changes must not restore an untrusted badge'
        window.call('refresh-list')
        window.wait(lambda v: v['sidebar_error'] and not v['notices'] and v['badge'] == 0, 'Refresh during disconnection stays unknown')
        window.call('reload-window')
        window.wait(lambda v: v['sidebar_error'] and not v['notices'] and v['badge'] == 0, 'Reload during disconnection stays unknown')
    finally:
        restored = window.call('reconnect-sidebar')
        report['reconnect_observation'] = restored
        window.call('foreground')
    assert restored['socket'] == socket_identity, 'Restore the original live daemon endpoint'
    backend_agent = next(agent for agent in restored['sidebar']['agents'] if agent['id'] == notice['launch'])
    assert backend_agent['state'] == 'waiting_user_answer' and backend_agent['question_id'] == notice['id'], 'Backend must confirm the same native question after reconnect'
    assert restored['selection']['task']['project_id'] == original_project, 'Keep the original local project binding'
    assert original_pane in restored['selection']['paneKeys'], 'Keep the original pane binding'
    if receipt_comparison_refresh:
        # Both comparison versions take this same visible action. The primary
        # suite still requires selection recovery without this extra refresh.
        window.call('refresh-list')
        report['receipt_comparison_refresh'] = True
    window.wait(lambda v: v['selected_project'] == original_project and any(a['id'] == notice['launch'] for a in v['agents']),
                'Reload keeps the selected project after reconnect')
    if receipt_comparison_refresh:
        # A successful refresh can mount e1's pane for the first time, so both
        # comparison versions use the same visible reload to resume pane reads.
        window.call('reload-window')
    else:
        window.call('reconnect-pane', pane=original_pane)
    recovered = window.wait(lambda v: any(a['state'] == 'waiting_user_answer' for a in v['agents']) and
                            any(q['id'] == notice['id'] for q in v['questions']), 'Same native question returns after reconnect')
    assert recovered['notices'] == [], 'Reconnect must not repeat the same question'
    window.call('refresh-list')
    time.sleep(3.2)
    assert window.call('inspect')['notices'] == [], 'Refresh after reconnect must not repeat the same question'
    window.call('reload-window')
    window.wait(lambda v: any(a['state'] == 'waiting_user_answer' for a in v['agents']) and
                any(q['id'] == notice['id'] for q in v['questions']), 'Reload after reconnect preserves the same native question')
    window.call('watch-notices')
    time.sleep(6.2)
    stable = window.call('inspect')
    assert stable['notices'] == [] and stable['notice_additions'] == 0, 'Reload after reconnect must not emit another reminder'
    window.call('background')
    window.wait(lambda v: v['badge'] == 1, 'Fresh verified read restores only the waiting count')
    assert window.call('inspect')['notices'] == []
    window.call('foreground')
    window.wait(lambda v: v['badge'] == 0, 'Foreground after reconnect clears badge')
    report['checks'].append('t110_real_disconnect_clears_badge_refresh_reload_reconnect_deduplicates')


def after_answer(window, disabled, report):
    view = window.wait(lambda v: not v['notices'] and not v['questions'] and all(a['state'] != 'waiting_user_answer' for a in v['agents']),
                       'Answered question removes notification and waiting highlight')
    assert all(p['state'] != 'waiting_user_answer' for p in view['projects'])
    time.sleep(3.2)
    assert window.call('inspect')['notices'] == [], 'Idle does not notify'
    report['checks'].append('t110_answer_removes_notification_and_highlight_idle_silent')
