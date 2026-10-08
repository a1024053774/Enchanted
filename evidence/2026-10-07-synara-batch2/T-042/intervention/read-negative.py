from readbacks import *
rpc('native-unmanaged','orchestration.getThreadDetailSnapshot',{'threadId':f['reviewer']})
request('events-after-negative',{'command':'events','task':f['task']})
request('status-after-negative',{'command':'status','task':f['task']})
request('unmanaged-binding-after',path='/api/a2a?thread='+f['reviewer'])
