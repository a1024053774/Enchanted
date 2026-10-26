"""Read one process's argv through sysctl KERN_PROCARGS2 (T-184). Only the caller's own processes answer.
Prints {"schema":1,"pid":N,"argv":[...],"shim":...} for the daemon to test one fact (are Enchanted's launch arguments
there); the daemon keeps none of it. Of the environment the process started with, only A2A_SHIM is read (T-187)."""
import sys
sys.dont_write_bytecode = True
import ctypes as C
import json

CTL_KERN, KERN_PROCARGS2 = 1, 49


def launch_of(pid):
    libc = C.CDLL('/usr/lib/libc.dylib', use_errno=True)
    mib = (C.c_int * 3)(CTL_KERN, KERN_PROCARGS2, pid)
    size = C.c_size_t(0)
    if libc.sysctl(mib, 3, None, C.byref(size), None, 0) != 0:
        raise OSError(C.get_errno(), 'sysctl size')
    buffer = C.create_string_buffer(size.value)
    if libc.sysctl(mib, 3, buffer, C.byref(size), None, 0) != 0:
        raise OSError(C.get_errno(), 'sysctl read')
    raw = buffer.raw[:size.value]
    argc = int.from_bytes(raw[:4], sys.byteorder)
    rest = raw[4:]
    rest = rest[rest.index(b'\0'):].lstrip(b'\0')  # skip the executable path and its padding
    parts = rest.split(b'\0')
    shim = next((part[len(b'A2A_SHIM='):].decode('utf-8', 'replace') for part in parts[argc:] if part.startswith(b'A2A_SHIM=')), None)
    return [part.decode('utf-8', 'replace') for part in parts[:argc]], shim


def main():
    pid = int(sys.argv[1])
    argv, shim = launch_of(pid)
    print(json.dumps({'schema': 1, 'pid': pid, 'argv': argv, 'shim': shim}, ensure_ascii=False))


if __name__ == '__main__':
    main()
