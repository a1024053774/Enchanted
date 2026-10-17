"""Fixed fake-API request and SSE contract for one real controller tool call."""
import json


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(p['text'] for p in content if isinstance(p, dict) and p.get('type') == 'text')
    raise ValueError('Tool result content must be text or content blocks.')


def user_text_parts(messages):
    parts = []
    for message in messages:
        if message.get('role') != 'user':
            continue
        content = message.get('content', [])
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            parts.extend(p['text'] for p in content if isinstance(p, dict) and p.get('type') == 'text')
        else:
            raise ValueError('User content must be text or content blocks.')
    return parts


def validate_request(body, number, scenario, registered_feedback=None):
    if scenario.get('name') not in ('slice1-inbox-red', 'slice1-inbox-green'):
        raise ValueError('A declared controller inbox slice is required.')
    green = scenario['name'] == 'slice1-inbox-green'
    limit = 3 if green else 2
    if body.get('model') != 'claude-haiku-5-5' or body.get('stream') is not True:
        raise ValueError('Declared model and streaming mode are required.')
    if not 1 <= number <= limit:
        raise ValueError('The declared Messages budget is exhausted.')
    messages = body.get('messages', [])
    if number == 1:
        texts = user_text_parts(messages)
        if not texts or texts[-1] != '⟦主控 #1⟧\n' + scenario['nonce']:
            raise ValueError('The exact registered root prompt is required.')
        tool = next((t for t in body.get('tools', []) if t.get('name') == 'Bash'), None)
        if not tool or tool.get('input_schema', {}).get('properties', {}).get('command', {}).get('type') != 'string':
            raise ValueError('The real CLI must advertise a Bash command tool.')
        return {'root_prompt': texts[-1]}
    if number == 3 and green:
        tools = [p for m in messages if m.get('role') == 'assistant' for p in m.get('content', [])
                 if isinstance(p, dict) and p.get('type') == 'tool_use']
        if len(tools) != 1 or tools[0] != {'type': 'tool_use', 'id': scenario['tool_use_id'], 'name': 'Bash', 'input': {'command': scenario['bash_command']}}:
            raise ValueError('The feedback history must retain exactly the frozen tool call.')
        user = next((m for m in reversed(messages) if m.get('role') == 'user'), None)
        content = user.get('content') if user else None
        if not isinstance(content, str) and not (isinstance(content, list) and
                all(isinstance(p, dict) and p.get('type') == 'text' and isinstance(p.get('text'), str) for p in content)):
            raise ValueError('The feedback message must contain text only.')
        text = text_content(content)
        if not isinstance(registered_feedback, str) or not registered_feedback.startswith('⟦门禁 #2⟧\n'):
            raise ValueError('The registered feedback reference is required.')
        if text != registered_feedback:
            raise ValueError('The second root must be the registered gate feedback.')
        first_json = text.find('\n[')
        if first_json < 0:
            raise ValueError('Feedback must carry the real relay receipt array.')
        receipts = json.loads(text[first_json + 1:])
        if len(receipts) != 1 or receipts[0].get('replayed') is not False or receipts[0].get('result', {}).get('ok') is not True:
            raise ValueError('Exactly one new successful execution receipt is required.')
        result = receipts[0]['result']
        ids = [entry['entry']['id'] for entry in result.get('entries', [])]
        expected = [entry['id'] for entry in scenario['inbox_fixture'] if entry['to'] == 'ideation']
        if ids != expected or not ids:
            raise ValueError('Actual role scope must return the independent ideation sentinel only.')
        tool_results = [p for m in messages if m.get('role') == 'user' for p in m.get('content', [])
                        if isinstance(p, dict) and p.get('type') == 'tool_result' and p.get('tool_use_id') == scenario['tool_use_id']]
        if len(tool_results) != 1:
            raise ValueError('The original tool result must remain correlated.')
        queued = json.loads(text_content(tool_results[0]['content']).strip())
        if not queued.get('request_id') or receipts[0].get('request_id') != queued['request_id']:
            raise ValueError('Execution feedback must match the actual queued request.')
        return {'feedback_prompt': text, 'receipts': receipts}
    results = [(i, p) for i, m in enumerate(messages) if m.get('role') == 'user'
               for p in m.get('content', []) if isinstance(p, dict) and p.get('type') == 'tool_result']
    tools = [(i, p) for i, m in enumerate(messages) if m.get('role') == 'assistant'
             for p in m.get('content', []) if isinstance(p, dict) and p.get('type') == 'tool_use']
    if len(results) != 1 or len(tools) != 1:
        raise ValueError('Exactly one tool call and one result are required.')
    tool_index, tool = tools[0]
    result_index, result = results[0]
    if tool_index >= result_index:
        raise ValueError('The tool result must follow its tool call.')
    # 2.1.296 appends system metadata after the actual user tool_result.
    # Preserve the body; only text system metadata may follow that result.
    for message in messages[result_index + 1:]:
        content = message.get('content')
        if message.get('role') != 'system' or not (isinstance(content, str) or
                isinstance(content, list) and all(isinstance(p, dict) and p.get('type') == 'text'
                                                 and isinstance(p.get('text'), str) for p in content)):
            raise ValueError('Only text system metadata may follow the tool result.')
    if (tool.get('id') != scenario['tool_use_id'] or tool.get('name') != 'Bash'
            or tool.get('input') != {'command': scenario['bash_command']}
            or result.get('tool_use_id') != scenario['tool_use_id']):
        raise ValueError('The tool call and result must match the frozen command and ID.')
    text = text_content(result.get('content'))
    if not text.strip():
        raise ValueError('An empty tool result is not execution evidence.')
    if green:
        queued = json.loads(text.strip())
        if result.get('is_error', False) or queued.get('ok') is not True or queued.get('queued') is not True or queued.get('delivered') is not False or not queued.get('request_id'):
            raise ValueError('The real tool must report queue admission without claiming delivery.')
    return {'tool_result': result, 'text': text}


def response_events(number, scenario, message_id):
    yield 'message_start', {'type': 'message_start', 'message': {
        'id': message_id, 'type': 'message', 'role': 'assistant', 'model': 'claude-haiku-5-5',
        'content': [], 'stop_reason': None, 'stop_sequence': None,
        'usage': {'input_tokens': 128, 'output_tokens': 1}}}
    if number == 1:
        block = {'type': 'tool_use', 'id': scenario['tool_use_id'], 'name': 'Bash', 'input': {}}
        delta = {'type': 'input_json_delta', 'partial_json': json.dumps({'command': scenario['bash_command']})}
        reason = 'tool_use'
    else:
        block = {'type': 'text', 'text': ''}
        delta = {'type': 'text_delta', 'text': (scenario['final_ack'] if number == 3 else scenario['ack']) + ' ' + scenario['nonce']}
        reason = 'end_turn'
    yield 'content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': block}
    yield 'content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': delta}
    yield 'content_block_stop', {'type': 'content_block_stop', 'index': 0}
    yield 'message_delta', {'type': 'message_delta', 'delta': {'stop_reason': reason, 'stop_sequence': None},
                            'usage': {'output_tokens': 32}}
    yield 'message_stop', {'type': 'message_stop'}
