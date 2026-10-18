"""T-096 runner resource cleanup. Imported without starting processes.

Output None means a nonblocking pipe has no bytes available. It is not EOF.
Only a verified Electron exit permits daemon shutdown; stream diagnostics and
nonzero exit do not replace that exit evidence or suppress safe later cleanup.
"""

import ctypes
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import struct
import uuid



def dead_endpoint_rejection(exit_code, reply, *, epoch, credential_exists):
    # This exact structured refusal is observed on the frozen baseline before
    # credential creation/spawn. Timeouts and other startup errors stay unknown.
    return (epoch==2 and exit_code==1 and reply.get('ok') is False and
        reply.get('error')=='daemon_call_failed' and
        reply.get('details')=='Error: socket exists; query its owner, do not replace it' and not credential_exists)


def probe_process(pid, *, run=None):
    if not isinstance(pid,int) or isinstance(pid,bool) or pid<=0:
        raise RuntimeError('positive process PID required')
    argv=['/bin/ps','-ww','-p',str(pid),'-o','pid=,lstart=,command=']
    if run is None:
        response=subprocess.run(argv,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','LANG':'C'},capture_output=True,text=True,timeout=5)
    else:
        response=run(argv,allow_failure=True)
    if not isinstance(response.stdout,str) or not isinstance(response.stderr,str):
        raise RuntimeError('process probe output not captured')
    if response.returncode==1 and not response.stdout.strip() and not response.stderr.strip():
        return None
    if response.returncode!=0:
        raise subprocess.CalledProcessError(response.returncode,argv,output=response.stdout,stderr=response.stderr)
    pieces=response.stdout.strip().split(maxsplit=6)
    if response.stderr.strip() or len(pieces)!=7 or int(pieces[0])!=pid:
        raise RuntimeError('process identity readback invalid')
    return dict(pid=pid,started=' '.join(pieces[1:6]),command=pieces[6])


def parse_native_argv(data):
    argc=struct.unpack_from('i',data)[0]
    if argc<1 or argc>256: raise RuntimeError('native argc invalid')
    cursor=data.index(b'\0',4)+1
    while cursor<len(data) and data[cursor]==0: cursor+=1
    args=[]
    for unused in range(argc):
        end=data.index(b'\0',cursor); args.append(data[cursor:end].decode('utf-8')); cursor=end+1
    return args


def native_argv(pid):
    libc=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    mib=(ctypes.c_int*3)(1,49,pid)
    size=ctypes.c_size_t()
    if libc.sysctl(mib,3,None,ctypes.byref(size),None,0): raise RuntimeError('native argv size unavailable')
    raw=ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib,3,raw,ctypes.byref(size),None,0): raise RuntimeError('native argv unavailable')
    return parse_native_argv(raw.raw[:size.value])


def operator_request(state, command, credential, **fields):
    # Credential bytes stay inside this function and the private socket request.
    # No caller receives them; errors contain only a code, never the envelope.
    fd=os.open(credential,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:
            raise RuntimeError('operator credential is not private')
        with os.fdopen(fd,'r',encoding='utf-8',closefd=False) as source:
            identity=json.load(source)
    finally:
        os.close(fd)
    if identity.get('kind')!='operator' or identity.get('state')!=str(Path(state).resolve()) or not identity.get('epoch') or not identity.get('token'):
        raise RuntimeError('operator credential does not bind this fixture')
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(30); client.connect(str(Path(state)/'control.sock'))
        request=dict(id=str(uuid.uuid4()),input=dict(command=command,**fields),identity=identity)
        client.sendall((json.dumps(request)+'\n').encode('utf-8'))
        response=b''
        while b'\n' not in response:
            chunk=client.recv(65536)
            if not chunk: raise RuntimeError('daemon disconnected; request outcome unknown')
            response+=chunk
            if len(response)>4*1024*1024: raise RuntimeError('daemon response budget exceeded')
        result=json.loads(response.split(b'\n',1)[0])
    if result.get('ok') is not True:
        raise RuntimeError('daemon refused '+command+': '+str(result.get('error')))
    return result


def close_observer(observer, *, expected_crash, read_process, normal_quit):
    outcome = dict(exited=False, diagnostics=[], stdout_eof=False)
    observer.process.poll()
    owner = observer.owner
    if owner is None:
        raise RuntimeError('electron owner unrecorded; preserve fixture for controller')
    identity = {key: owner[key] for key in ['pid', 'started', 'command']}
    current = read_process(owner['pid'])
    if current is not None and current != identity:
        raise RuntimeError('electron PID/start/command changed; preserve fixture for controller')
    if current is not None:
        if not observer.ready_confirmed:
            raise RuntimeError('electron startup unconfirmed; preserve fixture for controller')
        outcome['quit_events'] = []
        normal_quit(owner, observe=outcome['quit_events'].append, child=observer.process)
    observer.process.poll()
    if read_process(owner['pid']) is not None or observer.process.returncode is None:
        raise RuntimeError('electron exit unconfirmed; preserve fixture for controller')
    observer.exit_confirmed = outcome['exited'] = True
    if observer.process.returncode != 0 and not expected_crash:
        outcome['diagnostics'].append('unexpected Electron exit: ' + str(observer.process.returncode))
    try:
        # The pipe is deliberately nonblocking. Read only currently available
        # bytes; neither None nor BlockingIOError permits writing a fake buffer.
        while True:
            try:
                chunk = observer.process.stdout.read(65536)
            except BlockingIOError:
                break
            if chunk is None:
                break
            if chunk == b'':
                outcome['stdout_eof'] = True
                break
            observer.stdout.write(chunk)
            if observer.stdout.tell() > observer.max_stdout_bytes:
                raise RuntimeError('observer stdout budget exceeded; available bytes retained')
        observer.stdout.flush()
    except BaseException as error:
        outcome['diagnostics'].append('observer output drain: ' + str(error))
    # One failed close cannot skip closing the other resources or daemon_stop.
    for resource in [observer.selector, observer.log, observer.stderr, observer.stdout,
                     observer.process.stdin, observer.process.stdout]:
        try:
            resource.close()
        except BaseException as error:
            outcome['diagnostics'].append('observer stream close: ' + str(error))
    return outcome


def finish_cleanup(*, close_electron, stop_daemon, confirm_writers, archive):
    outcome = dict(cleanup_complete=False, writers_absent=False, diagnostics=[], handoff=None)
    try:
        electron = close_electron()
        outcome['electron'] = electron
        outcome['diagnostics'].extend(electron['diagnostics'])
        if not electron['exited']:
            raise RuntimeError('Electron exit unconfirmed')
    except BaseException as error:
        outcome['handoff'] = 'Electron ownership/exit unknown: ' + str(error)
        return outcome
    try:
        outcome['daemon_stop'] = stop_daemon()
    except BaseException as error:
        outcome['diagnostics'].append('daemon_stop: ' + str(error))
    try:
        # A stop receipt is not proof of exit; a lost receipt is not proof the
        # daemon survived. Independently verify every registered writer.
        confirm_writers()
        outcome['writers_absent'] = True
    except BaseException as error:
        outcome['handoff'] = 'Writer exit unconfirmed: ' + str(error)
        return outcome
    try:
        archive()
        outcome['cleanup_complete'] = True
    except BaseException as error:
        outcome['handoff'] = 'Stopped fixture archive incomplete: ' + str(error)
    return outcome
