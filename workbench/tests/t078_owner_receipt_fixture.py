"""Explicit metadata/lifecycle unit fixture, never a real process owner."""
import json
from pathlib import Path
import shlex


def write_owner_receipts(owner,parent):
    root=Path(owner['root']);parent=Path(parent);parent.mkdir(parents=True)
    target=owner['target_binding'];processes=owner['processes']
    labels=['daemon','target_shell','target_leader','ideation_shell','ideation_cli',
            'executor_shell','executor_cli','ideation_api','executor_api']
    for index,label in enumerate(labels):
        if label not in processes:processes[label]={'pid':2000000000+index,'started':'unit-fixture-lstart','command':'/fixture/'+label}
    owner.update(scene='09C',source_revision='1'*40,source=str(Path(__file__).resolve().parents[2]),
                 stage_a=str(parent/'stage-a'),identity_receipt=str(parent/'identity.json'))
    claim={**target,'runtime_identity':{'launch':target['launch']}}
    owner['claim_binding']=claim;owner['roles']={}
    def save(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False)+'\n')
    apis=[]
    for role in ['ideation','executor']:
        api=processes[role+'_api'];ready={'pid':api['pid'],'role':role,'stage':'A','protocol':'rev2-raw-c-profile-v1','model_turns':0}
        ready_path=root/'roles'/role/'api-ready.json'
        if ready_path.exists():
            original=json.loads(ready_path.read_bytes())
            assert all(original.get(key)==value for key,value in ready.items()),'unit API ready must match its original producer'
            ready=original
        else:save(ready_path,ready)
        apis.append({'pid':api['pid'],'role':role,'ready':ready,'argv':shlex.split(api['command'])})
        session=role+'-unit-session';launch=role+'-unit-launch';cli=processes[role+'_cli']
        cli['command']=shlex.join(['/fixture/python','--session-id',session,'--debug-file',str(root/'roles'/role/'claude-debug.log')])
        manifest=parent/(role+'-manifest.json')
        save(manifest,{'launch':launch,'session':session,'shell_pid':processes[role+'_shell']['pid'],
            'cli':{'pid':cli['pid'],'started':cli['started'],'command':'/fixture/python'},'scope':'explicit metadata unit fixture, no real process'})
        owner['roles'][role]={'launch':launch,'session':session,'manifest':str(manifest)}
    ready={'root':str(root),'target_binding':claim,'daemon':{'pid':processes['daemon']['pid']},
        'target_process':{'shell_pid':processes['target_shell']['pid'],'leader':processes['target_leader']['pid']},'api_processes':apis}
    save(parent/'stage-a/readiness.json',ready);save(parent/'identity.json',{'root':str(root),'processes':processes})
    owner['process_graph']={key:{'ppid':0,'pgid':v['pid'],'tpgid':v['pid']} for key,v in processes.items()}
    return owner
