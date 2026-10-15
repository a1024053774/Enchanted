"""Shared registered-dispatch validation and deterministic SSE response."""
class ProtocolRefusal(ValueError): pass

def normalize_anthropic_request(request, registry, role=None):
    """Bind a real Claude /v1/messages body to exactly one registered dispatch."""
    if 'dispatch_id' in request:
        return request, False
    messages=request.get('messages')
    if not isinstance(messages,list) or not messages:
        raise ProtocolRefusal('messages_required')
    user_indexes=[i for i,item in enumerate(messages) if isinstance(item,dict) and item.get('role')=='user']
    if not user_indexes: raise ProtocolRefusal('messages_required')
    user_index=user_indexes[-1]; content=messages[user_index].get('content')
    candidates_text=[content] if isinstance(content,str) else [item.get('text') for item in content if isinstance(item,dict) and item.get('type')=='text'] if isinstance(content,list) else []
    if not candidates_text:
        raise ProtocolRefusal('registered_text_mismatch')
    candidates=[item for item in registry.get('dispatches',{}).values()
                if item.get('text') in candidates_text and (role is None or item.get('role')==role)]
    if len(candidates)!=1:
        raise ProtocolRefusal('registered_text_mismatch')
    dispatch=candidates[0]
    matched_text=next(item['text'] for item in candidates if item['text'] in candidates_text)
    normalized_messages=list(messages);normalized_messages[user_index]={**messages[user_index],'content':matched_text}
    normalized={
        'path':'/v1/messages', 'dispatch_id':dispatch['id'], 'dispatch_seq':dispatch['seq'],
        'role':dispatch['role'], 'request_id':dispatch.get('request_id'),
        'stop_id':dispatch.get('stop_id'), 'attempt':dispatch.get('attempt'),
        'session':dispatch.get('session'), 'fence':dispatch.get('fence'),
        'messages':normalized_messages, 'stream':request.get('stream'), 'model':request.get('model'),
    }
    return normalized, True

def anthropic_sse(result, model, request_id):
    """Return valid streaming events for the real Claude client path."""
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
    if not user_messages or user_messages[-1].get('content')!=dispatch['text']: raise ProtocolRefusal('registered_text_mismatch')
    if dispatch.get('request_id') not in (None,'') and request.get('request_id')!=dispatch.get('request_id'): raise ProtocolRefusal('request_id_mismatch')
    if dispatch.get('stop_id') not in (None,'') and request.get('stop_id')!=dispatch.get('stop_id'): raise ProtocolRefusal('stop_id_mismatch')
    for key in ['attempt','session','fence']:
        if request.get(key)!=dispatch.get(key): raise ProtocolRefusal('target_binding_mismatch')
    limit=registry.get('message_budget',6 if request.get('role')=='ideation' else 11)
    if len(request.get('messages',[]))>limit: raise ProtocolRefusal('message_budget_exhausted')
    return {'status':'PASS','sse':[{'type':'message_start','message':{'id':request['request_id'],'role':'assistant'}},{'type':'content_block_delta','delta':{'type':'text_delta','text':registry.get('ack_text','I1_ACK')}},{'type':'message_delta','usage':{'output_tokens':1}},{'type':'message_stop'}]}
