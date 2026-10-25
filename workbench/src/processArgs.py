"""Read one process's argv through sysctl KERN_PROCARGS2 (T-184). Only the caller's own processes answer.
Prints {"schema":1,"pid":N,"argv":[...]} for the daemon to test one fact (are Enchanted's launch arguments there); the
daemon keeps none of it."""
import sys
sys.dont_write_bytecode = True
import ctypes as C
import json

CTL_KERN, KERN_PROCARGS2 = 1, 49


def argv_of(pid):
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
    return [part.decode('utf-8', 'replace') for part in rest.split(b'\0')[:argc]]


def main():
    pid = int(sys.argv[1])
    print(json.dumps({'schema': 1, 'pid': pid, 'argv': argv_of(pid)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
