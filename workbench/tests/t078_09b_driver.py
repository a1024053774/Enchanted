"""Pure 09B two-role fake Messages/relay driver and oracle; no processes."""
from __future__ import annotations
from dataclasses import dataclass, field
import argparse, json, uuid
from pathlib import Path

def uid(): return str(uuid.uuid4())
class Refusal(ValueError): pass

@dataclass
class Target:
    task: str
    attempt: str = field(default_factory=uid)
    session: str = field(default_factory=uid)
    fence: int = 1
    thread: str = field(default_factory=uid)
    workspace: str = '/private/tmp/t078-09b-target'
    launch: str = field(default_factory=uid)
    shell_pid: int = 47001
    leader_pid: int = 47002
    native_session: str = field(default_factory=uid)
    baseline: bytes = b'TARGET_BASELINE\n'
    received: bytes = b'TARGET_BASELINE\n'
    reclaimed: bool = False
    archived: bool = False
    def interrupt(self):
        if self.received != self.baseline: raise Refusal('interrupt_already_written')
        self.received += b'\x1b'

@dataclass
class Dispatch:
    seq: int; id: str; role: str; text: str; launch: str

@dataclass
class Stop:
    id: str; request_id: str; from_role: str; to_role: str; refs: list[str]; ack_id: str|None=None

class Broker:
    def __init__(self): self.seq=0; self.dispatches=[]; self.stops=[]; self.effects=[]
    def dispatch(self,role,body,launch):
        self.seq+=1; d=Dispatch(self.seq,uid(),role,f'⟦门禁 #{self.seq}⟧\n{body}',launch);self.dispatches.append(d);return d
    def send_stop(self,actual_role,requested_from,target,request_id):
        if actual_role!='ideation': raise Refusal('invalid_stop_sender')
        s=Stop(uid(),request_id,actual_role,'executor',[f'thread:{target.thread}',f'attempt:{target.attempt}',f'input:{request_id}'])
        self.stops.append(s);d=self.dispatch('executor',f'stop {s.id} request {request_id}',target.launch)
        self.effects.append({'kind':'stop_sent','stop_id':s.id,'request_id':request_id,'dispatch_id':d.id,'dispatch_seq':d.seq,'requested_from':requested_from,'actual_from':actual_role});return s,d
    def execute_stop(self,role,stop,target,thread):
        if role!='executor': raise Refusal('controller_identity_required')
        if stop.ack_id: raise Refusal('stop_already_acknowledged')
        if thread!=target.thread or f'thread:{thread}' not in stop.refs: raise Refusal('stop_target_mismatch')
        target.interrupt();self.effects.append({'kind':'interrupt','stop_id':stop.id,'thread':thread,'actor':role,'delta':'1b'});return {'ok':True}
    def ack(self,role,stop,target):
        if role!=stop.to_role: raise Refusal('recipient_required')
        if stop.ack_id:return {'id':stop.ack_id,'replayed':True}
        stop.ack_id=uid();d=self.dispatch('ideation',f'ack {stop.id} request {stop.request_id}',target.launch)
        self.effects.append({'kind':'ack','ack_id':stop.ack_id,'stop_id':stop.id,'dispatch_id':d.id,'dispatch_seq':d.seq,'from':role,'reply_to':stop.id});return {'id':stop.ack_id,'replayed':False,'dispatch_id':d.id}

class Messages:
    def __init__(self,role,roots,messages,nonce): self.role=role;self.root_budget=roots;self.message_budget=messages;self.nonce=nonce;self.roots=0;self.messages=0;self.requests=[];self.tool_id=uid()
    def root(self,prompt,kind='confirm'):
        if self.roots>=self.root_budget:raise Refusal('root_budget_exhausted')
        self.roots+=1
        if kind=='tool':return self.tool(prompt)
        self.messages+=1;self.requests.append({'number':self.messages,'root':prompt,'kind':kind,'request_id':uid()});return None
    def tool(self,prompt):
        if self.messages+2>self.message_budget:raise Refusal('messages_budget_exhausted')
        self.messages+=2;rid=uid();self.requests.extend([{'number':self.messages-1,'root':prompt,'kind':'tool_use','tool_id':self.tool_id,'request_id':rid,'command':'/fixture/inbox-or-stop'},{'number':self.messages,'root':prompt,'kind':'tool_result','tool_id':self.tool_id,'request_id':rid,'queued':True}]);return rid
    def feedback(self,text,kind='feedback'):
        if self.roots>=self.root_budget or self.messages>=self.message_budget:raise Refusal('budget_exhausted')
        self.roots+=1;self.messages+=1;self.requests.append({'number':self.messages,'root':text,'kind':kind,'registered_text':text,'request_id':uid()})

def run(mutant=None):
    t=Target('09b-task');b=Broker();i=Messages('ideation',4,6,'I_'+uid());e=Messages('executor',6,11,'E_'+uid());pairs=[]
    def dispatch(role,body): return b.dispatch(role,body,t.launch)
    def feedback(session,d,kind='feedback'):
        session.feedback(d.text,kind);pairs.append({'dispatch_id':d.id,'dispatch_seq':d.seq,'registered':d.text,'observed':d.text})
    def root_dispatch(session,d,kind='tool'):
        session.root(d.text,kind);pairs.append({'dispatch_id':d.id,'dispatch_seq':d.seq,'registered':d.text,'observed':d.text})
    rid=i.root('⟦用户⟧\n'+i.nonce,'tool');rid=i.requests[-1]['request_id'];stop,sd=b.send_stop('ideation','executor',t,rid)
    send_result=dispatch('ideation','stop accepted '+stop.id);feedback(i,send_result,'send_feedback')
    root_dispatch(e,sd)
    try:b.execute_stop('executor',stop,t,uid());wrong='accepted'
    except Refusal as x:wrong=str(x)
    denial=dispatch('executor','wrong target '+wrong);root_dispatch(e,denial);b.execute_stop('executor',stop,t,t.thread)
    success=dispatch('executor','interrupt succeeded '+stop.id);root_dispatch(e,success);ack=b.ack('executor',stop,t);ad=next(d for d in b.dispatches if d.id==ack['dispatch_id'])
    ack_result=dispatch('executor','ack result '+ack['id']);root_dispatch(e,ack_result);dup=b.ack('executor',stop,t)
    dup_result=dispatch('executor','duplicate ack result '+dup['id']);root_dispatch(e,dup_result)
    try:b.execute_stop('executor',stop,t,t.thread);acked='accepted'
    except Refusal as x:acked=str(x)
    ack_wake=dispatch('ideation','ack wake '+stop.id);root_dispatch(i,ack_wake)
    try:b.ack('ideation',stop,t);foreign='accepted'
    except Refusal as x:foreign=str(x)
    foreign_result=dispatch('ideation','foreign ack '+foreign);root_dispatch(i,foreign_result,'confirm')
    final_result=dispatch('executor','final refusal '+acked);root_dispatch(e,final_result,'confirm')
    if mutant=='feedback-text':pairs[0]['observed']+=' stale'
    if mutant=='seq-reset':b.dispatches[1].seq=1
    if mutant=='identity':t.attempt=''
    if mutant=='duplicate-esc':t.received+=b'\x1b'
    return {'target':t,'broker':b,'roles':{'ideation':i,'executor':e},'pairs':pairs,'wrong':wrong,'foreign':foreign,'acked':acked,'duplicate':dup}

def oracle(s):
    t,b,r,p=s['target'],s['broker'],s['roles'],s['pairs']
    if not t.attempt or t.reclaimed or t.archived:raise AssertionError('target_identity_lifecycle')
    if t.received!=t.baseline+b'\x1b':raise AssertionError('target_must_receive_one_esc')
    if (s['wrong'],s['foreign'],s['acked'])!=('stop_target_mismatch','recipient_required','stop_already_acknowledged'):raise AssertionError('boundary_refusal')
    if [x['kind'] for x in b.effects].count('stop_sent')!=1 or [x['kind'] for x in b.effects].count('interrupt')!=1 or [x['kind'] for x in b.effects].count('ack')!=1:raise AssertionError('effect_counts')
    if (r['ideation'].roots,r['ideation'].messages,r['executor'].roots,r['executor'].messages)!=(4,6,6,11):raise AssertionError('role_budget')
    if [d.seq for d in b.dispatches]!=list(range(1,len(b.dispatches)+1)):raise AssertionError('global_dispatch_seq')
    for d in b.dispatches:
        if not d.id or d.text!=f'⟦门禁 #{d.seq}⟧\n'+d.text.split('\n',1)[1]:raise AssertionError('dispatch_text')
    if any(x['registered']!=x['observed'] for x in p):raise AssertionError('registered_feedback_text')
    if any(not v for v in [t.attempt,t.session,t.thread,t.launch]):raise AssertionError('placeholder_identity')
    return {'status':'PASS','dispatch_count':len(b.dispatches),'effects':b.effects,'role_budgets':{'ideation':[r['ideation'].roots,r['ideation'].messages],'executor':[r['executor'].roots,r['executor'].messages]},'target_received_hex':t.received.hex()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mutant',choices=['feedback-text','seq-reset','identity','duplicate-esc']);a=p.parse_args();a.output.mkdir();s=run(a.mutant);rec={'status':'INCOMPLETE','mutant':a.mutant,'scope':'Pure fake Messages/relay driver and independent oracle; no socket, CLI, daemon, target or model','real_process_starts':0}
    try:rec.update(status='PASS',oracle=oracle(s),checks='PASS')
    except AssertionError as x:rec.update(checks='FAIL',error=str(x))
    out={'status':rec['status'],'mutant':a.mutant,'oracle':rec.get('oracle'),'error':rec.get('error'),'checks':rec['checks'],'scope':rec['scope'],'real_process_starts':0,'dispatches':[d.__dict__ for d in s['broker'].dispatches],'pairs':s['pairs'],'effects':s['broker'].effects,'target':{'attempt':s['target'].attempt,'received_hex':s['target'].received.hex()}}
    (a.output/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':rec['status'],'mutant':a.mutant,'error':rec.get('error')}));raise SystemExit(0 if rec['status']=='PASS' else 1)
if __name__=='__main__':main()
