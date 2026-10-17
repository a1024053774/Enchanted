#!/usr/bin/env python3
"""Capture one owned Electron window; the controller runs this outside the sandbox.

CLI: /bin/ps (read), /usr/sbin/screencapture -x -o -l WINDOW FILE.
Hooks: none. Keys: none. CLI/model starts: none. Provider/model budget: 0.
Uses existing screen-recording permission; never requests or changes permission.
"""
import argparse
import ctypes
import json
from pathlib import Path
import plistlib
import struct
import subprocess


def process_identity(pid):
    value = subprocess.run(['/bin/ps', '-ww', '-p', str(pid), '-o', 'pid=,lstart=,command='],
                           env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'LANG': 'C'},
                           capture_output=True, text=True, timeout=5, check=True)
    pieces = value.stdout.strip().split(maxsplit=6)
    if value.stderr.strip() or len(pieces) != 7 or int(pieces[0]) != pid:
        raise RuntimeError('owner_process_readback_failed')
    return {'pid': pid, 'started': ' '.join(pieces[1:6]), 'command': pieces[6]}


def owned_window(pid):
    cg = ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    cg.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
    if not cg.CGPreflightScreenCaptureAccess():
        raise PermissionError('screen_recording_permission_missing; stop and report to controller')
    cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    cg.CGWindowListCopyWindowInfo.restype = ctypes.c_void_p
    cf.CFPropertyListCreateData.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long,
                                          ctypes.c_ulong, ctypes.c_void_p]
    cf.CFPropertyListCreateData.restype = ctypes.c_void_p
    cf.CFDataGetLength.argtypes = [ctypes.c_void_p]
    cf.CFDataGetLength.restype = ctypes.c_long
    cf.CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
    cf.CFDataGetBytePtr.restype = ctypes.c_void_p
    cf.CFRelease.argtypes = [ctypes.c_void_p]
    array = cg.CGWindowListCopyWindowInfo(17, 0)  # On-screen, excluding desktop elements.
    if not array:
        raise RuntimeError('window_inventory_unavailable')
    data = None
    try:
        data = cf.CFPropertyListCreateData(None, array, 100, 0, None)
        if not data:
            raise RuntimeError('window_inventory_decode_failed')
        rows = plistlib.loads(ctypes.string_at(cf.CFDataGetBytePtr(data), cf.CFDataGetLength(data)))
    finally:
        if data:
            cf.CFRelease(data)
        cf.CFRelease(array)
    # Never persist another application's title, PID or window metadata.
    matching = [row for row in rows if row.get('kCGWindowOwnerPID') == pid and
                row.get('kCGWindowLayer') == 0 and row.get('kCGWindowIsOnscreen') and
                row.get('kCGWindowBounds', {}).get('Width', 0) > 0 and
                row.get('kCGWindowBounds', {}).get('Height', 0) > 0]
    if len(matching) != 1:
        raise RuntimeError('owned_window_is_not_unique')
    row = matching[0]
    return {'pid': pid, 'window_number': row['kCGWindowNumber'], 'bounds': row['kCGWindowBounds']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--owner', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    owner = json.loads(args.owner.read_text(encoding='utf-8'))
    expected = {key: owner[key] for key in ['pid', 'started', 'command']}
    if not Path(owner['driver']).is_file() or owner['driver'] not in expected['command'] or \
            owner['executable'] not in expected['command'] or process_identity(owner['pid']) != expected:
        raise RuntimeError('owner_process_identity_changed')
    if args.output.exists() or not args.output.parent.is_dir():
        raise RuntimeError('capture_requires_new_file_in_existing_directory')
    before = owned_window(owner['pid'])
    argv = ['/usr/sbin/screencapture', '-x', '-o', '-l', str(before['window_number']), str(args.output)]
    subprocess.run(argv, check=True, capture_output=True, timeout=15)
    after = owned_window(owner['pid'])
    if before != after or process_identity(owner['pid']) != expected:
        raise RuntimeError('capture_owner_changed')
    raw = args.output.read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n' or len(raw) < 24:
        raise RuntimeError('capture_is_not_png')
    dimensions = struct.unpack('>II', raw[16:24])
    if min(dimensions) <= 0:
        raise RuntimeError('capture_has_no_pixels')
    print(json.dumps({'status': 'PASS', 'owner': before, 'argv': argv, 'pixels': dimensions,
                      'bytes': len(raw), 'original_single_frame': str(args.output)}))


if __name__ == '__main__':
    main()
