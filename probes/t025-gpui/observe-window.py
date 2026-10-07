"""Read only the probe's on-screen window metadata; do not inspect other apps."""
import ctypes as c
import json
import sys

cf = c.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
cg = c.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
cf.CFStringCreateWithCString.argtypes = [c.c_void_p, c.c_char_p, c.c_uint32]
cf.CFStringCreateWithCString.restype = c.c_void_p
cf.CFArrayGetCount.argtypes = [c.c_void_p]
cf.CFArrayGetCount.restype = c.c_long
cf.CFArrayGetValueAtIndex.argtypes = [c.c_void_p, c.c_long]
cf.CFArrayGetValueAtIndex.restype = c.c_void_p
cf.CFDictionaryGetValue.argtypes = [c.c_void_p, c.c_void_p]
cf.CFDictionaryGetValue.restype = c.c_void_p
cf.CFNumberGetValue.argtypes = [c.c_void_p, c.c_int, c.c_void_p]
cf.CFStringGetCString.argtypes = [c.c_void_p, c.c_void_p, c.c_long, c.c_uint32]
cf.CFRelease.argtypes = [c.c_void_p]
cg.CGWindowListCopyWindowInfo.argtypes = [c.c_uint32, c.c_uint32]
cg.CGWindowListCopyWindowInfo.restype = c.c_void_p

def value(dictionary, key):
    key_ref = cf.CFStringCreateWithCString(None, key.encode('utf-8'), 0x08000100)
    result = cf.CFDictionaryGetValue(dictionary, key_ref)
    cf.CFRelease(key_ref)
    return result

def number(dictionary, key):
    ref = value(dictionary, key)
    out = c.c_double()
    if not ref or not cf.CFNumberGetValue(ref, 13, c.byref(out)):
        raise RuntimeError('window metadata missing number: ' + key)
    return out.value

def string(dictionary, key):
    ref = value(dictionary, key)
    if not ref:
        return None
    out = c.create_string_buffer(4096)
    if not cf.CFStringGetCString(ref, out, len(out), 0x08000100):
        raise RuntimeError('window metadata string cannot be decoded: ' + key)
    return out.value.decode('utf-8')

pid = int(sys.argv[1])
windows = cg.CGWindowListCopyWindowInfo(1 | 16, 0)  # on-screen, exclude desktop
if not windows:
    raise RuntimeError('window inventory unavailable')
result = []
for index in range(cf.CFArrayGetCount(windows)):
    window = cf.CFArrayGetValueAtIndex(windows, index)
    if number(window, 'kCGWindowOwnerPID') != pid:
        continue
    bounds = value(window, 'kCGWindowBounds')
    result.append({
        'pid': pid, 'window_number': int(number(window, 'kCGWindowNumber')),
        'owner': string(window, 'kCGWindowOwnerName'),
        'title': string(window, 'kCGWindowName'),
        'layer': number(window, 'kCGWindowLayer'),
        'bounds': {key: number(bounds, key) for key in ['X', 'Y', 'Width', 'Height']},
    })
cf.CFRelease(windows)
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if any(w['layer'] == 0 and w['bounds']['Width'] > 0 for w in result) else 1)
