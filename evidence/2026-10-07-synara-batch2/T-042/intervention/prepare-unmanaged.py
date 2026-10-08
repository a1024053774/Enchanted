from readbacks import *
rpc('unmanaged-create','orchestration.dispatchCommand',{'type':'thread.create','commandId':f['reviewer']+'-create','threadId':f['reviewer'],'projectId':f['project'],'title':'普通会话反例 T042-非-29','modelSelection':{'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'xhigh','fastMode':True}},'runtimeMode':'full-access','interactionMode':'default','envMode':'local','branch':None,'worktreePath':None,'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z')})
request('unmanaged-binding-before',path='/api/a2a?thread='+f['reviewer'])
request('membership-before-negative',path='/api/a2a/membership')
