client.call('capture',name='before-user-release')
result['draft_handling']=handling
result['waiting_for']='主控在本隔离窗口自行处理草稿、看到空框后点击“输入框已空，放行”。反例则保留恢复的草稿，声明为空；本驱动不代发清空键。'
print(json.dumps({'phase':'manual-draft-handling','launch':approval['input']['launch'],'window_id':window_id,'handling':handling,'instructions':result['waiting_for']},ensure_ascii=False),flush=True);save()
# The operator controls the visible isolated window. This harness
# never sends a clear key or automates a declaration in either case.
wait(lambda:any(e['type']=='user_queue_release' and e['launch']==binding['launch'] for e in events()),180)
release_event=next(e for e in events() if e['type']=='user_queue_release' and e['launch']==binding['launch'])
declarations=[r for r in user_inputs() if r.get('content',{}).get('action')=='queue-release']
assert len(declarations)==1 and declarations[0]['text']=='用户声明输入框已空'
assert declarations[0]['content']['declaration']==release_event['data']['declaration']
assert release_event['data']['declaration']['interruption']==held['interruption']
result['user_release']=release_event;result['declaration']=declarations[0];save()
client.call('capture',name='after-declaration')
