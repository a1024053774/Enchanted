"""Shared registered-dispatch validation and deterministic SSE response.

The protocol API has two distinct request shapes for a tool dispatch: the
initial registered user turn, followed by Claude's user ``tool_result`` turn.
Both are bound to the same dispatch and tool-use id.  Ordinary (no-tool)
dispatches keep the original one-request contract.
"""
import json
import shlex

class ProtocolRefusal(ValueError): pass


def _content_blocks(message):
    content = message.get('content') if isinstance(message, dict) else None
    if isinstance(content, list):
        return [block for block in content if isinstance(block, dict)]
    return []


def _text_blocks(message):
    content = message.get('content') if isinstance(message, dict) else None
    if isinstance(content, str):
        return [content]
    return [block.get('text') for block in _content_blocks(message)
            if block.get('type') == 'text' and isinstance(block.get('text'), str)]


def _tool_result_block(messages, tool_use_id):
    matches = []
    for message in messages:
        if not isinstance(message, dict) or message.get('role') != 'user':
            continue
        for block in _content_blocks(message):
            if block.get('type') == 'tool_result':
                matches.append(block)
    if len(matches) > 1:
        raise ProtocolRefusal('tool_result_multiplicity')
    if matches and matches[0].get('tool_use_id') != tool_use_id:
        raise ProtocolRefusal('tool_use_id_mismatch')
    return matches[0] if matches else None


def _tool_result_payload(block, expected=None):
    if not isinstance(block, dict):
        raise ProtocolRefusal('tool_result_required')
    content = block.get('content')
    if isinstance(content, list):
        text = ''.join(part.get('text', '') for part in content
                       if isinstance(part, dict) and part.get('type') == 'text')
    elif isinstance(content, str):
        text = content
    else:
        raise ProtocolRefusal('tool_result_content_required')
    try:
        payload = json.loads(text)
    except (TypeError, ValueError) as error:
        raise ProtocolRefusal('tool_result_json_required') from error
    expected = expected or {}
    if expected.get('ok') is False:
        if payload.get('ok') is not False or payload.get('error') != expected.get('error'):
            raise ProtocolRefusal('tool_result_denial_mismatch')
        return payload
    if not isinstance(payload, dict) or payload.get('ok') is not True:
        raise ProtocolRefusal('tool_result_must_be_success')
    entry = payload.get('entry')
    if not isinstance(entry, dict) or entry.get('kind') != 'stop' or entry.get('from') != 'ideation':
        raise ProtocolRefusal('tool_result_stop_entry_required')
    return payload


def _canonical_tool(tool):
    """Return Anthropic's Bash schema, deriving command from frozen argv."""
    if not isinstance(tool, dict) or tool.get('name') != 'Bash':
        raise ProtocolRefusal('bash_tool_required')
    value = tool.get('input')
    if not isinstance(value, dict):
        raise ProtocolRefusal('bash_input_required')
    command = value.get('command')
    if not isinstance(command, str) or not command.strip():
        argv = value.get('argv')
        if not isinstance(argv, list) or not argv or not all(isinstance(item, str) for item in argv):
            raise ProtocolRefusal('bash_command_required')
        command = shlex.join(argv)
    return {**tool, 'input': {'command': command}}


def _tool_use_history(messages, expected):
    matches=[]
    for message in messages:
        if not isinstance(message, dict) or message.get('role') != 'assistant':
            continue
        for block in _content_blocks(message):
            if block.get('type') == 'tool_use' and block.get('id') == expected['id']:
                matches.append(block)
    if len(matches) != 1:
        raise ProtocolRefusal('tool_use_history_required')
    expected = _canonical_tool(expected)
    observed=matches[0]
    if observed.get('name') != expected.get('name') or observed.get('input') != expected.get('input'):
        raise ProtocolRefusal('tool_use_binding_mismatch')
    return observed


def _validate_registered_tool_result(dispatch, block):
    if block.get('tool_use_id') != dispatch['tool_use']['id']:
        raise ProtocolRefusal('tool_use_id_mismatch')
    expected = dispatch.get('tool_result') or {}
    payload = _tool_result_payload(block, expected)
    if expected.get('ok') is False:
        return payload
    expected_entry = expected.get('entry') if isinstance(expected, dict) else None
    if expected_entry:
        observed_entry = payload.get('entry') or {}
        for key in ('id', 'from', 'to', 'kind', 'refs'):
            if key in expected_entry and observed_entry.get(key) != expected_entry[key]:
                raise ProtocolRefusal('tool_result_binding_mismatch')
    return payload

def normalize_anthropic_request(request, registry, role=None):
    """Bind a real Claude /v1/messages body to exactly one registered dispatch."""
    if 'dispatch_id' in request:
        return request, False
    messages=request.get('messages')
    if not isinstance(messages,list) or not messages:
        raise ProtocolRefusal('messages_required')
    user_indexes=[i for i,item in enumerate(messages) if isinstance(item,dict) and item.get('role')=='user']
    if not user_indexes: raise ProtocolRefusal('messages_required')
    candidates_text=[]
    for index in user_indexes:
        candidates_text.extend(_text_blocks(messages[index]))
    candidates=[item for item in registry.get('dispatches',{}).values()
                if item.get('text') in candidates_text and (role is None or item.get('role')==role)]
    if len(candidates)!=1:
        raise ProtocolRefusal('registered_text_mismatch')
    dispatch=candidates[0]
    matched_text=dispatch['text']
    normalized_messages=list(messages)
    text_index=next(index for index in user_indexes if dispatch['text'] in _text_blocks(messages[index]))
    normalized_messages[text_index]={**messages[text_index],'content':matched_text}
    tool_result = _tool_result_block(messages, dispatch.get('tool_use', {}).get('id')) if dispatch.get('tool_use') else None
    normalized={
        'path':'/v1/messages', 'dispatch_id':dispatch['id'], 'dispatch_seq':dispatch['seq'],
        'role':dispatch['role'], 'request_id':dispatch.get('request_id'),
        'stop_id':dispatch.get('stop_id'), 'attempt':dispatch.get('attempt'),
        'session':dispatch.get('session'), 'fence':dispatch.get('fence'),
        'messages':normalized_messages, 'stream':request.get('stream'), 'model':request.get('model'),
        'tool_result': bool(tool_result), 'tool_result_block': tool_result,
    }
    if tool_result:
        normalized['tool_result_payload'] = _validate_registered_tool_result(dispatch, tool_result)
    return normalized, True

def anthropic_sse(result, model, request_id):
    """Return valid streaming events for the real Claude client path."""
    if result.get('tool_use'):
        tool=_canonical_tool(result['tool_use']); payload=json.dumps(tool['input'],ensure_ascii=False,separators=(',',':'))
        return [
            {'type':'message_start','message':{'id':request_id,'type':'message','role':'assistant','model':model or 'claude-haiku-5-5','content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':0,'output_tokens':0}}},
            {'type':'content_block_start','index':0,'content_block':{'type':'tool_use','id':tool['id'],'name':tool['name'],'input':{}}},
            {'type':'content_block_delta','index':0,'delta':{'type':'input_json_delta','partial_json':payload}},
            {'type':'content_block_stop','index':0},
            {'type':'message_delta','delta':{'stop_reason':'tool_use','stop_sequence':None},'usage':{'output_tokens':1}},
            {'type':'message_stop'},
        ]
    text=result['sse'][1]['delta']['text']
    return [
        {'type':'message_start','message':{'id':request_id,'type':'message','role':'assistant','model':model or 'claude-haiku-5-5','content':[],'stop_reason':None,'stop_sequence':None,'usage':{'input_tokens':0,'output_tokens':0}}},
        {'type':'content_block_start','index':0,'content_block':{'type':'text','text':''}},
        {'type':'content_block_delta','index':0,'delta':{'type':'text_delta','text':text}},
        {'type':'content_block_stop','index':0},
        {'type':'message_delta','delta':{'stop_reason':'end_turn','stop_sequence':None},'usage':{'output_tokens':1}},
        {'type':'message_stop'},
    ]

def validate_request(request, registry):
    dispatch=registry.get('dispatches',{}).get(request.get('dispatch_id'))
    if not dispatch: raise ProtocolRefusal('dispatch_not_registered')
    if request.get('dispatch_seq')!=dispatch['seq']: raise ProtocolRefusal('global_dispatch_seq_mismatch')
    if request.get('role')!=dispatch['role']: raise ProtocolRefusal('role_mismatch')
    messages=request.get('messages')
    if not isinstance(messages,list) or not messages: raise ProtocolRefusal('messages_required')
    user_messages=[item for item in messages if isinstance(item,dict) and item.get('role')=='user']
    if not user_messages: raise ProtocolRefusal('registered_text_mismatch')
    registered_texts=[]
    for message in user_messages:
        registered_texts.extend(_text_blocks(message))
    if dispatch['text'] not in registered_texts: raise ProtocolRefusal('registered_text_mismatch')
    if dispatch.get('request_id') not in (None,'') and request.get('request_id')!=dispatch.get('request_id'): raise ProtocolRefusal('request_id_mismatch')
    if dispatch.get('stop_id') not in (None,'') and request.get('stop_id')!=dispatch.get('stop_id'): raise ProtocolRefusal('stop_id_mismatch')
    for key in ['attempt','session','fence']:
        if request.get(key)!=dispatch.get(key): raise ProtocolRefusal('target_binding_mismatch')
    limit=registry.get('message_budget',6 if request.get('role')=='ideation' else 11)
    if len(request.get('messages',[]))>limit: raise ProtocolRefusal('message_budget_exhausted')
    if dispatch.get('tool_use'):
        if request.get('tool_result'):
            _tool_use_history(messages, dispatch['tool_use'])
            payload=request.get('tool_result_payload') or _validate_registered_tool_result(dispatch, request.get('tool_result_block'))
            return {'status':'PASS','settlement':True,'tool_result':payload,
                    'sse': _settlement_sse(registry.get('ack_text','STOP_SENT'))}
        return {'status':'PASS','tool_use':_canonical_tool(dispatch['tool_use']),
                'sse':[{'type':'message_start','message':{'id':request['request_id'],'role':'assistant'}},
                       {'type':'content_block_delta','delta':{'type':'text_delta','text':'tool_use'}},
                       {'type':'message_stop'}]}
    return {'status':'PASS','sse':[{'type':'message_start','message':{'id':request['request_id'],'role':'assistant'}},{'type':'content_block_delta','delta':{'type':'text_delta','text':registry.get('ack_text','I1_ACK')}},{'type':'message_delta','usage':{'output_tokens':1}},{'type':'message_stop'}], **({'tool_use':dispatch['tool_use']} if dispatch.get('tool_use') else {})}


def _settlement_sse(text):
    return [{'type':'message_start','message':{'id':'settlement','role':'assistant'}},
            {'type':'content_block_delta','delta':{'type':'text_delta','text':text}},
            {'type':'message_stop'}]
