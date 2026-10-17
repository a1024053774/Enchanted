client.call('capture',name='before-user-release')
from p1_simulated_actions import prompt_frame,bound_held
from p1_window_receipts import confirmed_control
result['draft_handling']=handling
result['automation']={'source':'test-simulated-user','approved_by':'executor','approval_ref':consent['approval_ref'],'actions':consent['actions']}
nonce1=(root/'nonce.txt').read_text(encoding='utf-8')
view=client.wait(lambda v:bound_held(v,binding) and nonce1 in prompt_frame(v)['text'])
restored=client.call('capture',name='restored-draft')
assert bound_held(restored,binding) and restored['window_id']==window_id and nonce1 in prompt_frame(restored)['text']
result['restored_draft']=restored
draft_status=call('pane_status','--thread',thread)
assert draft_status['interruption']==held['interruption'] and draft_status['input_generation']==held['input_generation'] and draft_status['active'] is None
if handling=='simulated-empty-declaration':
    before_output=call('pane_output','--launch',binding['launch'],'--offset','0')
    before_clear=max((e['seq'] for e in events()),default=after_seq)
    result['clear_attempt']=client.call('terminal-key',key='Control+C',**binding,window_id=window_id,interruption=held['interruption'],approval_ref=consent['actions'][1]['approval_ref'])
    def clear_receipt():return confirmed_control(events(),user_inputs(),launch=binding['launch'],thread=thread,window=window_id,after_seq=before_clear,data='\x03')
    wait(lambda:clear_receipt() is not None)
    result['clear_delivery']=clear_receipt();save()
    after_clear=call('pane_status','--thread',thread)
    assert after_clear['active'] is None and after_clear['interruption']==held['interruption'] and after_clear['input_generation']==held['input_generation']+1
    empty=client.wait(lambda v:bound_held(v,binding) and v.get('interruption')==held['interruption'] and
                      v.get('input_generation')==after_clear['input_generation'] and v['offset']>before_output['total_bytes'] and prompt_frame(v)['empty'])
    with client.output_checkpoint(empty['offset']) as checkpoint:
        captured=client.call('capture',name='cleared-draft')
        assert bound_held(captured,binding) and captured['window_id']==window_id and captured['interruption']==held['interruption']
        assert captured['input_generation']==after_clear['input_generation'] and captured['offset']==checkpoint['highwater'] and prompt_frame(captured)['empty']
        raw=call('pane_output','--launch',binding['launch'],'--offset','0')
        data=base64.b64decode(raw['data_base64']);assert len(data)>=checkpoint['highwater']
        with (out/'cleared-draft-pty.bin').open('xb') as stream:stream.write(data[:checkpoint['highwater']])
        result['empty_editor_observation']={'frame':prompt_frame(captured),'snapshot':captured,'pty_highwater':checkpoint['highwater'],'pty_file':'cleared-draft-pty.bin'}
else:
    assert handling=='retain-draft-for-block'
    after_clear=draft_status
fresh=call('pane_status','--thread',thread)
assert fresh['interruption']==held['interruption'] and fresh['input_generation']==after_clear['input_generation'] and fresh['active'] is None
result['declaration_click']=client.call('queue-release',source='test-simulated-user',approval_ref=consent['actions'][2]['approval_ref'],launch=binding['launch'],interruption=held['interruption'],input_generation=fresh['input_generation'])
assert result['declaration_click']['clicked'] is True and result['declaration_click']['source']=='test-simulated-user';save()
wait(lambda:any(e['type']=='user_queue_release' and e['launch']==binding['launch'] for e in events()))
release_event=next(e for e in events() if e['type']=='user_queue_release' and e['launch']==binding['launch'])
declarations=[r for r in user_inputs() if r.get('content',{}).get('action')=='queue-release']
assert len(declarations)==1 and declarations[0]['text']=='用户声明输入框已空'
assert declarations[0]['content']['declaration']==release_event['data']['declaration']
assert release_event['data']['declaration']['interruption']==held['interruption']
assert release_event['data']['declaration']['input_generation']==fresh['input_generation']
result['user_release']=release_event;result['declaration']=declarations[0];save()
client.call('capture',name='after-declaration')
