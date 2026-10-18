"""Read one macOS PTY process tree through libproc. No ps, shell or argv reads."""
import sys
sys.dont_write_bytecode = True
import ctypes as C
import errno
import json

# Public SDK: sys/proc_info.h struct proc_bsdinfo, PROC_PIDTBSDINFO=3.
# proc_listpids returns bytes; PROC_PPID_ONLY=6 limits each query to one parent.
class BSDInfo(C.Structure):
    _fields_ = [(name,C.c_uint32) for name in (
        'flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]+[
        ('comm',C.c_char*16),('name',C.c_char*32),('nfiles',C.c_uint32),
        ('pgid',C.c_uint32),('jobc',C.c_uint32),('tty',C.c_uint32),('tpgid',C.c_uint32),
        ('nice',C.c_int32),('start_sec',C.c_uint64),('start_usec',C.c_uint64)]

MAX_PROCESSES=4096

class QueryError(RuntimeError):
    def __init__(self,operation,number=None):
        super().__init__(operation)
        self.operation=operation;self.errno=number

class ProcReader:
    def __init__(self,library):
        self.library=library
        self.identities={}
        library.proc_listpids.argtypes=[C.c_uint32,C.c_uint32,C.c_void_p,C.c_int]
        library.proc_listpids.restype=C.c_int
        library.proc_pidinfo.argtypes=[C.c_int,C.c_int,C.c_uint64,C.c_void_p,C.c_int]
        library.proc_pidinfo.restype=C.c_int
        library.proc_pidpath.argtypes=[C.c_int,C.c_void_p,C.c_uint32]
        library.proc_pidpath.restype=C.c_int

    def bsd(self,pid):
        info=BSDInfo();C.set_errno(0)
        size=self.library.proc_pidinfo(pid,3,0,C.byref(info),C.sizeof(info))
        number=C.get_errno()
        if size==0 and number==errno.ESRCH:return None
        if size!=C.sizeof(info):raise QueryError('proc_pidinfo_failed_or_short',number)
        if info.pid!=pid:raise QueryError('proc_pidinfo_identity_mismatch')
        if info.status==5 or info.flags&4:return None  # SZOMB / PROC_FLAG_INEXIT.
        if info.status not in (1,2,3,4):raise QueryError('proc_pidinfo_invalid_state')
        return info

    def read(self,pid):
        before=self.bsd(pid)
        if before is None:return None
        path=C.create_string_buffer(4096);C.set_errno(0)
        size=self.library.proc_pidpath(pid,path,C.sizeof(path));number=C.get_errno()
        if size==0 and number==errno.ESRCH:return None
        if size<=0 or size>=C.sizeof(path):raise QueryError('proc_pidpath_failed_or_truncated',number)
        after=self.bsd(pid)
        if after is None:return None
        identity=lambda value:(value.pid,value.ppid,value.pgid,value.tpgid,value.start_sec,value.start_usec)
        if identity(before)!=identity(after):raise QueryError('process_identity_changed_during_query')
        current=identity(after)
        if pid in self.identities and self.identities[pid]!=current:raise QueryError('process_identity_changed_during_query')
        self.identities[pid]=current
        command=path.value.decode('utf-8',errors='strict')
        if not command.startswith('/'):raise QueryError('absolute_executable_path_required')
        return {'pid':pid,'ppid':after.ppid,'pgid':after.pgid,'tpgid':C.c_int32(after.tpgid).value,'command':command}

    def children(self,pid):
        buffer=(C.c_int*(MAX_PROCESSES+1))();C.set_errno(0)
        size=self.library.proc_listpids(6,pid,buffer,C.sizeof(buffer));number=C.get_errno()
        if size<0 or size==0 and number:raise QueryError('proc_listpids_failed',number)
        if size%C.sizeof(C.c_int) or size>=C.sizeof(buffer):raise QueryError('proc_listpids_invalid_or_truncated')
        values=list(buffer[:size//C.sizeof(C.c_int)])
        if len(values)!=len(set(values)) or any(value<=0 for value in values):raise QueryError('proc_listpids_invalid_identity')
        return values


def snapshot(root_pid,reader):
    root=reader.read(root_pid)
    if root is None:return []
    rows=[root];seen={root_pid};index=0
    while index<len(rows):
        parent=rows[index]['pid'];index+=1
        for pid in reader.children(parent):
            if pid in seen:raise QueryError('process_tree_duplicate_or_cycle')
            seen.add(pid)
            row=reader.read(pid)
            if row is None:continue  # Observed exit/zombie; permission denial raises.
            if row['ppid']!=parent:raise QueryError('process_parent_changed_during_query')
            rows.append(row)
            if len(rows)>MAX_PROCESSES:raise QueryError('process_tree_limit_exceeded')
    current=[]
    for row in rows:
        fresh=reader.read(row['pid'])
        if fresh is None:
            if row['pid']==root_pid:return []
            continue
        if fresh!=row:raise QueryError('process_identity_changed_during_query')
        current.append(fresh)
    return current


def main():
    if not(sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):raise QueryError('python_isolated_no_site_no_bytecode_required')
    if sys.platform!='darwin':raise QueryError('macOS_process_query_required')
    if len(sys.argv)!=2 or not sys.argv[1].isdigit() or not 1<int(sys.argv[1])<2**31:raise QueryError('valid_root_pid_required')
    pid=int(sys.argv[1]);reader=ProcReader(C.CDLL('/usr/lib/libproc.dylib',use_errno=True))
    print(json.dumps({'schema':1,'root_pid':pid,'method':'macOS libproc','rows':snapshot(pid,reader)}))

if __name__=='__main__':
    try:main()
    except Exception as error:
        sys.stderr.write(json.dumps({'error':'process_query_failed','operation':getattr(error,'operation',type(error).__name__),'errno':getattr(error,'errno',None)})+'\n')
        raise SystemExit(2)
