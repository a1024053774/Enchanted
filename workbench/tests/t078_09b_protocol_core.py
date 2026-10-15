"""Shared registered-dispatch validation and deterministic SSE response."""
class ProtocolRefusal(ValueError): pass
def validate_request(request, registry):
    dispatch=registry.get('dispatches',{}).get(request.get('dispatch_id'))
    if not dispatch: raise ProtocolRefusal('dispatch_not_registered')
    if request.get('dispatch_seq')!=dispatch['seq']: raise ProtocolRefusal('global_dispatch_seq_mismatch')
    if request.get('role')!=dispatch['role']: raise ProtocolRefusal('role_mismatch')
    if request.get('messages',[{}])[-1].get('content')!=dispatch['text']: raise ProtocolRefusal('registered_text_mismatch')
    if request.get('request_id')!=dispatch.get('request_id'): raise ProtocolRefusal('request_id_mismatch')
    for key in ['attempt','session','fence']:
        if request.get(key)!=dispatch.get(key): raise ProtocolRefusal('target_binding_mismatch')
    limit=registry.get('message_budget',6 if request.get('role')=='ideation' else 11)
    if len(request.get('messages',[]))>limit: raise ProtocolRefusal('message_budget_exhausted')
    return {'status':'PASS','sse':[{'type':'message_start','message':{'id':request['request_id'],'role':'assistant'}},{'type':'content_block_delta','delta':{'type':'text_delta','text':registry.get('ack_text','I1_ACK')}},{'type':'message_delta','usage':{'output_tokens':1}},{'type':'message_stop'}]}
