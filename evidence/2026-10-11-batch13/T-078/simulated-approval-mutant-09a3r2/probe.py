"""Execute the actual runner draft branch and Electron control-key branch, no GUI starts."""
import argparse,copy,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['always-empty','bypass-approval']);args=p.parse_args();args.output.mkdir()
source=Path(__file__).resolve().parents[2];sys.path.insert(0,str(source/'workbench/tests'))
runner=(source/'workbench/tests/run_t078_p1.py').read_text(encoding='utf-8')
start=runner.index("            client.call('capture',name='before-user-release')")
end=runner.index("            if handling=='retain-draft-for-block':",start)
import textwrap
segment=textwrap.dedent(runner[start:end]);compile(segment,'<actual runner draft branch>','exec')
(args.output/'runner-branch.py').write_text(segment,encoding='utf-8')
archived=json.loads((source/'evidence/2026-10-11-batch13/T-078/p1-materials-09a2/continue-esc/electron/before-user-release.json').read_bytes())
nonce=(source/'evidence/2026-10-11-batch13/T-078/p1-materials-09a2/nonce.txt').read_text()
(args.output/'nonce.txt').write_text(nonce,encoding='utf-8')
checks=[]
import p1_simulated_actions as action_module
if args.mutant=='always-empty':
    original=action_module.prompt_frame
    action_module.prompt_frame=lambda view:{**original(view),'empty':True}
elif args.mutant=='bypass-approval':
    action_module.validate_actions=lambda *args:None
def execute(handling,flaw=None):
    binding={'launch':'launch-sentinel','thread':'thread-sentinel','dispatch':'first-dispatch'}
    held={'interruption':9,'input_generation':1,'active':None,'state':'busy','interrupted':True}
    events=[];inputs=[];commands=[];result={'escape_delivery':{'action':{'source_ref':{'source_sequence':1}}}}
    view={**archived,**binding,'active_dispatch':'','state':'busy','input_enabled':True,'lifecycle':'running','offset':100,'interruption':9,'input_generation':1,'window_id':'window-sentinel'}
    if flaw=='missing-restored':view['terminal']=view['terminal'].replace(nonce,'OTHER')
    current=copy.deepcopy(view)
    class Client:
        def call(self,command,**values):
            commands.append({'command':command,**values})
            if command=='capture':return copy.deepcopy(current)
            if command=='inspect':return copy.deepcopy(current)
            if command=='terminal-key':
                assert values['key']=='Control+C';held['input_generation']+=1
                current['input_generation']=held['input_generation']
                action={'form':'message' if flaw=='message-control' else 'action','channel':'terminal-window','content':{'action':'terminal-key','data':'\x03'},'target':{'thread':binding['thread']},'source_ref':{'window_id':'window-sentinel','command_id':'clear-request','source_sequence':2}}
                inputs.append(action)
                for seq,kind,extra in [(10,'window_request_admitted',{'command':'window_input'}),(11,'terminal_input_write_intent',{'data':'\x03','encoding':'utf8','byte_length':1}),(12,'terminal_input_written',{'encoding':'utf8','byte_length':1})]:
                    if flaw=='no-written' and kind=='terminal_input_written':continue
                    events.append({'seq':seq,'launch':binding['launch'],'type':kind,'data':{'window_id':'window-sentinel','request_id':'clear-request','sequence':2,**extra}})
                if flaw!='not-empty':
                    lines=current['terminal'].splitlines();first=next(i for i,l in enumerate(lines) if l.startswith('❯'));last=next(i for i in range(first+1,len(lines)) if lines[i].strip().startswith('────'))
                    current['terminal']='\n'.join(lines[:first]+['❯ ']+lines[last:])
                current['offset']=100 if flaw=='old-output' else 150
                return {'attempted':True,'source':'test-simulated-user'}
            if command=='queue-release':
                declaration={'interruption':9,'input_generation':held['input_generation']}
                events.append({'seq':20,'launch':binding['launch'],'type':'user_queue_release','data':{'declaration':declaration}})
                inputs.append({'form':'action','channel':'terminal-window','text':'用户声明输入框已空','content':{'action':'queue-release','declaration':declaration},'source_ref':{'source_sequence':3,'window_id':'window-sentinel'}})
                return {'clicked':True,'source':'test-simulated-user'}
            raise AssertionError(command)
        def wait(self,predicate,**kwargs):
            if not predicate(current):raise TimeoutError('Observed view did not meet contract')
            return copy.deepcopy(current)
        def output_checkpoint(self,minimum,**kwargs):
            from contextlib import contextmanager
            @contextmanager
            def context():
                assert current['offset']>=minimum;yield {'highwater':current['offset'],'view':copy.deepcopy(current)}
            return context()
    def wait(predicate,*args):
        if not predicate():raise TimeoutError('Observed facts did not meet contract')
    def call(command,*args):
        if command=='pane_status':return copy.deepcopy(held)
        if command=='pane_output':return {'data_base64':__import__('base64').b64encode(b'X'*current['offset']).decode(),'total_bytes':current['offset'],'next_offset':current['offset']}
        raise AssertionError(command)
    consent={'source':'test-simulated-user','approved_by':'executor','approval_ref':'top-approval','basis':'main #150',
             'actions':[{'action':'Escape'},{'action':'clear-restored-draft','key':'Control+C'} if handling=='simulated-empty-declaration' else {'action':'retain-restored-draft'},
                        {'action':'declare-empty-release','truth':'empty' if handling=='simulated-empty-declaration' else 'intentionally-false'}]}
    for row in consent['actions']:row.update(approved_by='executor',approval_ref='step-'+row['action'],basis='explicit approval')
    namespace={'client':Client(),'handling':handling,'binding':binding,'held':copy.deepcopy(held),'thread':binding['thread'],'window_id':'window-sentinel','result':result,
               'wait':wait,'events':lambda:events,'user_inputs':lambda:inputs,'call':call,'after_seq':9,'approval':{'input':binding},'consent':consent,'nonce1':nonce,
               'root':args.output,'out':args.output/('case-'+str(len(checks))),'save':lambda:None,'json':json,'base64':__import__('base64')}
    namespace['out'].mkdir()
    try:exec(compile(segment,'<actual runner draft branch>','exec'),namespace)
    except Exception as error:return commands,result,repr(error)
    return commands,result,None
for name,handling,flaw in [('clean-clears-and-declares','simulated-empty-declaration',None),('block-retains-and-declares','retain-draft-for-block',None),
                          ('reject-residual-draft','simulated-empty-declaration','not-empty'),('reject-missing-restored','simulated-empty-declaration','missing-restored'),
                          ('reject-control-as-message','simulated-empty-declaration','message-control'),('reject-missing-written','simulated-empty-declaration','no-written'),
                          ('reject-old-output','simulated-empty-declaration','old-output')]:
    commands,result,error=execute(handling,flaw);clears=[c for c in commands if c['command']=='terminal-key'];declares=[c for c in commands if c['command']=='queue-release']
    passed=(not error and len(declares)==1 and len(clears)==(1 if handling=='simulated-empty-declaration' else 0) and result.get('automation',{}).get('source')=='test-simulated-user') if flaw is None else bool(error and not declares)
    checks.append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','commands':commands,'error':error})
approval={'input':{'launch':'approval-unseen-launch','session':'approval-unseen-session','task':'t078-p1-approval-sentinel'}}
consent={'launch':'approval-unseen-launch','session':'approval-unseen-session','scenario':'approval-sentinel','source':'test-simulated-user',
         'approved_by':'executor','approval_ref':'main150','basis':'explicit approval','actions':[
             {'action':'Escape','approved_by':'executor','approval_ref':'esc-ref','basis':'Esc approved'},
             {'action':'clear-restored-draft','key':'Control+C','approved_by':'executor','approval_ref':'clear-ref','basis':'single Ctrl+C approved'},
             {'action':'declare-empty-release','truth':'empty','approved_by':'executor','approval_ref':'declare-ref','basis':'declare after observation approved'}]}
for name in ['valid-unseen-approval','missing-step-approval','wrong-source','stale-session','unapproved-key','false-clean-declaration','missing-global-reference']:
    value=copy.deepcopy(consent)
    if name=='missing-step-approval':value['actions'][1]['approved_by']=None
    if name=='wrong-source':value['source']='real-user'
    if name=='stale-session':value['session']='stale'
    if name=='unapproved-key':value['actions'][1]['key']='Control+U'
    if name=='false-clean-declaration':value['actions'][2]['truth']='intentionally-false'
    if name=='missing-global-reference':value['approval_ref']=None
    error=None
    try:action_module.validate_actions(approval,value,'simulated-empty-declaration')
    except Exception as failure:error=repr(failure)
    passed=error is None if name=='valid-unseen-approval' else error is not None
    checks.append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','input':value,'error':error})
r={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','checks':checks,'argv':sys.argv,'scope':'Actual runner branch and approval helper, synthetic client/window facts; no CLI/API/UI/model starts','real_model_turns':0,'mutant':args.mutant}
(args.output/'probe.py').write_bytes(Path(__file__).read_bytes());(args.output/'helper.py').write_bytes((source/'workbench/tests/p1_simulated_actions.py').read_bytes())
(args.output/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':r['status'],'checks':len(checks),'failed':[c['name'] for c in checks if c['status']!='PASS']},ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
