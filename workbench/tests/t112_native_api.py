"""Observed 0.162.1 Responses wire contract, shared by T-112's native fixtures.

Sources: request-capture-02.json and code-mode-protocol-01.json. No model calls.
"""
import json
import re
import time
import uuid


def request_source(body):
    metadata = json.loads(body['client_metadata']['x-codex-turn-metadata'])
    assert metadata['request_kind'] == 'turn', 'Unexpected native request kind'
    return metadata['thread_source']


def request_tools(body):
    """0.162.1 declares tools in input.additional_tools (see captured wire body)."""
    tools = []
    for item in body['input']:
        if item.get('type') == 'additional_tools':
            assert isinstance(item['tools'], list), 'additional_tools.tools must be an array'
            tools.extend(item['tools'])
    assert tools, 'Native request has no additional_tools declarations'
    return tools


def shell_item(tools, command, cwd):
    """Read the outer tool and inner shell signature from the native declaration."""
    flattened = []
    for tool in tools:
        if tool['type'] == 'namespace':
            flattened.extend((child, tool['name']) for child in tool['tools'])
        else:
            flattened.append((tool, None))
    candidates = []
    for tool, namespace in flattened:
        if tool['type'] != 'custom':
            continue
        description = tool.get('description', '')
        for function, fields in re.findall(r'declare const tools:\s*\{\s*(\w+)\(args:\s*\{(.*?)\}\):\s*Promise', description, re.S):
            command_field = re.search(r'// Shell command to execute\.\s*(\w+)\??:\s*string;', fields)
            cwd_field = re.search(r'// Working directory for the command[^\n]*\n\s*(\w+)\??:\s*string;', fields)
            wait_field = re.search(r'// Wait before yielding output[^\n]*\n\s*(\w+)\??:\s*number;', fields)
            if command_field and cwd_field and wait_field:
                candidates.append((tool, namespace, function, command_field[1], cwd_field[1], wait_field[1]))
    assert len(candidates) == 1, 'Native declaration must identify one shell command function'
    tool, namespace, function, command_field, cwd_field, wait_field = candidates[0]
    assert 'text(value:' in tool['description'], 'Native code tool must declare the text output helper'
    args = {command_field: command, cwd_field: str(cwd), wait_field: 10000}
    code = 'text(await tools.' + function + '(' + json.dumps(args) + '));'
    item = dict(type='custom_tool_call', name=tool['name'], input=code,
                id='fc_' + uuid.uuid4().hex, call_id='call_t112_' + uuid.uuid4().hex)
    if namespace:
        item['namespace'] = namespace
    return item


def tool_events(item, model):
    response = dict(id='resp_' + uuid.uuid4().hex, object='response', status='completed', model=model,
                    output=[item], usage={'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15})
    assert item['type'] == 'custom_tool_call'
    field, stem = 'input', 'response.custom_tool_call_input'
    return [('response.created', {'response': dict(response, status='in_progress', output=[])}),
            ('response.output_item.added', {'output_index': 0, 'item': dict(item, **{field: ''}, status='in_progress')}),
            (stem + '.delta', {'output_index': 0, 'item_id': item['id'], 'delta': item[field]}),
            (stem + '.done', {'output_index': 0, 'item_id': item['id'], field: item[field]}),
            ('response.output_item.done', {'output_index': 0, 'item': dict(item, status='completed')}),
            ('response.completed', {'response': response})]


def assert_native_call(emitted, native_records):
    calls = [row for row in native_records if row.get('type') == emitted['type'] and row.get('call_id') == emitted['call_id']]
    assert len(calls) == 1, 'Expected one matching persisted native call'
    actual = calls[0]
    assert actual['name'] == emitted['name'], 'Native tool name changed'
    assert actual['input'] == emitted['input'], 'Native code input changed'


def message_events(text, model):
    item = {'id': 'msg_' + uuid.uuid4().hex, 'type': 'message', 'role': 'assistant', 'status': 'completed',
            'content': [{'type': 'output_text', 'text': text, 'annotations': []}]}
    response = {'id': 'resp_' + uuid.uuid4().hex, 'object': 'response', 'created_at': int(time.time()),
                'status': 'completed', 'model': model, 'output': [item],
                'usage': {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15}}
    return [('response.created', {'response': dict(response, status='in_progress', output=[])}),
            ('response.output_item.added', {'output_index': 0, 'item': dict(item, status='in_progress', content=[])}),
            ('response.content_part.added', {'item_id': item['id'], 'output_index': 0, 'content_index': 0,
                                           'part': {'type': 'output_text', 'text': '', 'annotations': []}}),
            ('response.output_text.delta', {'item_id': item['id'], 'output_index': 0, 'content_index': 0, 'delta': text}),
            ('response.output_item.done', {'output_index': 0, 'item': item}),
            ('response.completed', {'response': response})]
