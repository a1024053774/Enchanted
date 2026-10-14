"""Correlate window action, PTY intent/write and submission retirement from stored facts."""
def confirmed_escape(events, inputs, *, launch, thread, dispatch, window, after_seq):
    actions = [v for v in inputs if v.get('form') == 'action' and v.get('channel') == 'terminal-window'
               and v.get('content') == {'action': 'terminal-key', 'data': '\x1b'}
               and v.get('target', {}).get('thread') == thread
               and v.get('source_ref', {}).get('window_id') == window]
    for action in actions:
        source = action['source_ref']
        matching = [e for e in events if e['seq'] > after_seq and e['launch'] == launch
                    and e['data'].get('window_id') == window
                    and e['data'].get('request_id') == source['command_id']
                    and e['data'].get('sequence') == source['source_sequence']]
        intent = [e for e in matching if e['type'] == 'terminal_input_write_intent' and e['data'].get('data') == '\x1b' and e['data'].get('encoding') == 'utf8' and e['data'].get('byte_length') == 1]
        written = [e for e in matching if e['type'] == 'terminal_input_written' and e['data'].get('encoding') == 'utf8' and e['data'].get('byte_length') == 1]
        admitted = [e for e in matching if e['type'] == 'window_request_admitted' and e['data'].get('command') == 'window_input']
        retired = [e for e in events if e['seq'] > after_seq and e['launch'] == launch and e['type'] == 'claude_submission_retired'
                   and e['data'].get('dispatch') == dispatch and e['data'].get('reason') == 'user-esc']
        if len(admitted) == len(intent) == len(written) == len(retired) == 1 and admitted[0]['seq'] < intent[0]['seq'] < written[0]['seq'] < retired[0]['seq']:
            return {'action': action, 'admitted': admitted[0], 'intent': intent[0], 'written': written[0], 'retired': retired[0]}
    return None
