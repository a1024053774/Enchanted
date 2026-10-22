"""libproc ABI/parser/tree failures using memory buffers only; no process query."""
import ctypes as C
import errno
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types

source=Path(__file__).resolve().parents[1]/'src/processSnapshot.py'
spec=importlib.util.spec_from_file_location('observer',source);mod=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else source.read_text();exec(compile(text,str(source),'exec'),vars(mod))
output=Path(sys.argv[1]);assert not output.exists();checks=[]
class Call:
 def __init__(self,fn):self.fn=fn
 def __call__(self,*args):return self.fn(*args)

def library(kind):
 calls={'info':0,'path':0,'children':0}
 def info(pid,flavor,arg,buffer,size):
  calls['info']+=1;assert flavor in (3,13)
  if flavor==13:
   # The short read after a denial: another user's process (privileged) or our own (denied_info).
   assert kind in ('denied_info','privileged','privileged_short','privileged_gone')
   if kind=='privileged_short':return size-1
   if kind=='privileged_gone':C.set_errno(errno.ESRCH);return 0
   value=mod.ShortInfo();value.status=2;value.pid=pid;value.ppid=21;value.pgid=22;value.uid=0 if kind=='privileged' else mod.os.geteuid()
   C.memmove(buffer,C.byref(value),size);return size
  if kind in ('denied_info','privileged','privileged_short','privileged_gone'):C.set_errno(errno.EPERM);return 0
  if kind=='gone':C.set_errno(errno.ESRCH);return 0
  if kind=='short_info':return size-1
  value=mod.BSDInfo();value.status=2;value.pid=pid;value.ppid=21;value.pgid=22;value.tpgid=0xffffffff if kind=='no_tty' else 22;value.start_sec=120;value.start_usec=7
  if kind=='zombie':value.status=5
  if kind=='exiting':value.flags=4
  if kind=='invalid_state':value.status=0
  if kind=='wrong_pid':value.pid=999
  if kind=='reused_pid' and calls['info']>=2:value.start_usec=8
  if kind=='reused_later' and calls['info']>=3:value.start_usec=8
  C.memmove(buffer,C.byref(value),size);return size
 def path(pid,buffer,size):
  calls['path']+=1
  if kind=='denied_path':C.set_errno(errno.EPERM);return 0
  value=b'/fixture/agent\0';C.memmove(buffer,value,len(value));return len(value)-1
 def children(flavor,pid,buffer,size):
  calls['children']+=1;assert flavor==6 and pid==22
  if kind=='denied_children':C.set_errno(errno.EPERM);return 0
  if kind=='full_children':return size
  if kind=='odd_children':return 3
  if kind=='duplicate_children':
   values=(C.c_int*2)(23,23);C.memmove(buffer,values,8);return 8
  return 0
 value=types.SimpleNamespace(proc_pidinfo=Call(info),proc_pidpath=Call(path),proc_listpids=Call(children))
 return value,calls
for kind in ('healthy','no_tty','gone','zombie','exiting','privileged','privileged_gone','invalid_state','denied_info','privileged_short','short_info','wrong_pid','reused_pid','reused_later','denied_path','denied_children','full_children','odd_children','duplicate_children'):
 lib,calls=library(kind);reader=mod.ProcReader(lib);error=None;row=None
 try:
  row=reader.read(22);children=reader.children(22)
  if kind=='reused_later':reader.read(22)
 except mod.QueryError as value:error=value
 if kind in ('healthy','no_tty','gone','zombie','exiting','privileged','privileged_gone'):
  assert error is None
  if kind in ('gone','zombie','exiting','privileged_gone'):assert row is None
  elif kind=='privileged':assert row=={'pid':22,'ppid':21,'pgid':22,'tpgid':-1,'command':'/fixture/agent','privileged':True,'uid':0},row
  else:assert row=={'pid':22,'ppid':21,'pgid':22,'tpgid':-1 if kind=='no_tty' else 22,'command':'/fixture/agent'}
 else:assert error is not None,'bad_native_observation_must_fail: '+kind
 checks.append({'case':kind,'rejected':error is not None,'error':getattr(error,'operation',None)})
rows={11:{'pid':11,'ppid':1,'pgid':11,'tpgid':12,'command':'/bin/zsh'},12:{'pid':12,'ppid':11,'pgid':12,'tpgid':12,'command':'/fixture/agent'},13:{'pid':13,'ppid':12,'pgid':12,'tpgid':12,'command':'/fixture/hook'}}
for kind in ('healthy_tree','gone_child','gone_root_final','wrong_parent','cycle','denied_tree'):
 class Reader:
  reads=0
  def read(self,pid):
   if pid==11:
    self.reads+=1
    if kind=='gone_root_final' and self.reads==2:return None
   if kind=='gone_child' and pid==13:return None
   value=dict(rows[pid])
   if kind=='wrong_parent' and pid==12:value['ppid']=999
   return value
  def children(self,pid):
   if kind=='denied_tree':raise mod.QueryError('proc_listpids_failed',1)
   if kind=='cycle' and pid==12:return [11]
   return {11:[12],12:[13],13:[]}[pid]
 try:result=mod.snapshot(11,Reader())
 except mod.QueryError:assert kind in ('wrong_parent','cycle','denied_tree')
 else:assert kind in ('healthy_tree','gone_child','gone_root_final') and [row['pid'] for row in result]==([] if kind=='gone_root_final' else [11,12] if kind=='gone_child' else [11,12,13])
 checks.append({'case':kind,'tree_contract':True})
# Compile against the installed public SDK, without running a process observer.
fields={'pid':'pbi_pid','ppid':'pbi_ppid','pgid':'pbi_pgid','tpgid':'e_tpgid','start_sec':'pbi_start_tvsec','start_usec':'pbi_start_tvusec'}
text='#include <stddef.h>\n#include <sys/proc.h>\n#include <sys/proc_info.h>\n_Static_assert(SZOMB==5 && PROC_FLAG_INEXIT==4,"exit flags");\n'
text+='_Static_assert(sizeof(struct proc_bsdinfo)=='+str(C.sizeof(mod.BSDInfo))+',"BSD size");\n'
for local,native in fields.items():text+='_Static_assert(offsetof(struct proc_bsdinfo,'+native+')=='+str(getattr(mod.BSDInfo,local).offset)+',"BSD offset");\n'
text+='_Static_assert(PROC_PIDT_SHORTBSDINFO==13 && sizeof(struct proc_bsdshortinfo)=='+str(C.sizeof(mod.ShortInfo))+',"short size");\n'
for local in ('pid','ppid','pgid','status','flags','uid'):text+='_Static_assert(offsetof(struct proc_bsdshortinfo,pbsi_'+local+')=='+str(getattr(mod.ShortInfo,local).offset)+',"short offset");\n'
result=subprocess.run(['/usr/bin/clang','-fsyntax-only','-x','c','-'],input=text,text=True,capture_output=True)
assert result.returncode==0,'SDK_BSDInfo_ABI_must_match: '+result.stderr
checks.append({'case':'public_SDK_ABI','sizeof':C.sizeof(mod.BSDInfo),'compile_exit':result.returncode,'observer_executions':0})
with output.open('x') as stream:json.dump({'status':'PASS','scope':'synthetic native API buffers/tree plus public SDK compile; no actual PID query/auth/network','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks)}))
