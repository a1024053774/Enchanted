"""Fixed fake-API request and SSE contract for one real controller tool call."""
import json


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(p['text'] for p in content if isinstance(p, dict) and p.get('type') == 'text')
    raise ValueError('Tool result content must be text or content blocks.')


def validate_request(body, number, scenario):
    if body.get('model') != 'claude-haiku-5-5' or body.get('stream') is not True:
        raise ValueError('Declared model and streaming mode are required.')
    if number not in (1, 2):
        raise ValueError('The two-Messages budget is exhausted.')
    messages = body.get('messages', [])
    if number == 1:
        texts = [p.get('text') for m in messages if m.get('role') == 'user'
                 for p in m.get('content', []) if isinstance(p, dict) and p.get('type') == 'text']
        if not texts or texts[-1] != '⟦主控 #1⟧\n' + scenario['nonce']:
            raise ValueError('The exact registered root prompt is required.')
        tool = next((t for t in body.get('tools', []) if t.get('name') == 'Bash'), None)
        if not tool or tool.get('input_schema', {}).get('properties', {}).get('command', {}).get('type') != 'string':
            raise ValueError('The real CLI must advertise a Bash command tool.')
        return {'root_prompt': texts[-1]}
    if not messages or messages[-1].get('role') != 'user':
        raise ValueError('The next user message must carry the tool result.')
    results = [p for p in messages[-1].get('content', [])
               if isinstance(p, dict) and p.get('type') == 'tool_result']
    tools = [p for m in messages if m.get('role') == 'assistant' for p in m.get('content', [])
             if isinstance(p, dict) and p.get('type') == 'tool_use']
    if len(results) != 1 or len(tools) != 1:
        raise ValueError('Exactly one tool call and one result are required.')
    tool, result = tools[0], results[0]
    if (tool.get('id') != scenario['tool_use_id'] or tool.get('name') != 'Bash'
            or tool.get('input') != {'command': scenario['bash_command']}
            or result.get('tool_use_id') != scenario['tool_use_id']):
        raise ValueError('The tool call and result must match the frozen command and ID.')
    text = text_content(result.get('content'))
    if not text.strip():
        raise ValueError('An empty tool result is not execution evidence.')
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
        delta = {'type': 'text_delta', 'text': scenario['ack'] + ' ' + scenario['nonce']}
        reason = 'end_turn'
    yield 'content_block_start', {'type': 'content_block_start', 'index': 0, 'content_block': block}
    yield 'content_block_delta', {'type': 'content_block_delta', 'index': 0, 'delta': delta}
    yield 'content_block_stop', {'type': 'content_block_stop', 'index': 0}
    yield 'message_delta', {'type': 'message_delta', 'delta': {'stop_reason': reason, 'stop_sequence': None},
                            'usage': {'output_tokens': 32}}
    yield 'message_stop', {'type': 'message_stop'}
