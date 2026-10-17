"""Normal quit for one verified Electron process. No force quit or group signal.

Controller execution only: /bin/ps plus NSRunningApplication.terminate() for
the exact PID. No application start, hook, key, model, or permission request.
"""
import ctypes
from pathlib import Path
import subprocess
import time

from capture_window import process_identity


def read_process(pid):
    try:
        return process_identity(pid)
    except subprocess.CalledProcessError as error:
        if error.returncode == 1 and not error.stdout.strip() and not error.stderr.strip():
            return None
        raise


def confirm_owner(owner):
    current = read_process(owner['pid'])
    if current is not None and current != {key: owner[key] for key in ['pid', 'started', 'command']}:
        raise RuntimeError('electron_pid_start_or_command_changed')
    return current


def request_normal_quit(owner):
    if confirm_owner(owner) is None:
        return {'pid': owner['pid'], 'method': 'already_absent', 'requested': False}
    if owner['driver'] not in owner['command'] or owner['executable'] not in owner['command']:
        raise RuntimeError('electron_owner_command_does_not_match_launch')
    # The SDK declares terminate as a normal quit request for this one instance.
    # It is asynchronous; a successful request is never treated as exit evidence.
    ctypes.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit')
    objc = ctypes.CDLL('/usr/lib/libobjc.A.dylib')
    objc.objc_getClass.argtypes = [ctypes.c_char_p]
    objc.objc_getClass.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p
    address = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    send_id = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(address)
    send_pid = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32)(address)
    send_bool = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(address)
    send_int = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p)(address)
    send_text = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p)(address)
    send_void = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(address)
    selector = lambda name: objc.sel_registerName(name.encode('ascii'))
    pool = send_id(objc.objc_getClass(b'NSAutoreleasePool'), selector('new'))
    try:
        application = send_pid(objc.objc_getClass(b'NSRunningApplication'),
                               selector('runningApplicationWithProcessIdentifier:'), owner['pid'])
        if not application or send_int(application, selector('processIdentifier')) != owner['pid']:
            raise RuntimeError('electron_running_application_not_found')
        url = send_id(application, selector('executableURL'))
        path = send_id(url, selector('path')) if url else None
        encoded = send_text(path, selector('UTF8String')) if path else None
        if not encoded or Path(encoded.decode('utf-8')).resolve(strict=True) != Path(owner['executable']).resolve(strict=True):
            raise RuntimeError('electron_application_executable_changed')
        if confirm_owner(owner) is None:
            return {'pid': owner['pid'], 'method': 'already_absent', 'requested': False}
        if not send_bool(application, selector('terminate')):
            raise RuntimeError('electron_normal_quit_request_refused')
        return {'pid': owner['pid'], 'method': 'NSRunningApplication.terminate', 'requested': True}
    finally:
        if pool:
            send_void(pool, selector('drain'))


def normal_quit(owner, *, observe, child=None, timeout=15):
    observe({'normal_quit': request_normal_quit(owner)})
    deadline = time.monotonic() + timeout
    while True:
        if child is not None:
            child.poll()  # Reap only our own Popen child before checking its absence.
        if confirm_owner(owner) is None:
            value = {'pid': owner['pid'], 'exit_confirmed': True}
            observe(value)
            return value
        if time.monotonic() >= deadline:
            raise TimeoutError('electron_normal_quit_exit_unconfirmed; stop without force quit')
        time.sleep(0.1)
