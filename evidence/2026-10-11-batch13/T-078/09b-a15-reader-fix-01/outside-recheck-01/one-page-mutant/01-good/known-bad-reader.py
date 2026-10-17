"""Read one complete, stable PTY byte range through the existing gate output API."""
import base64
import binascii


def _page(value, launch, offset, total):
    if value.get('launch') != launch:
        raise ValueError('output_launch_mismatch')
    for name in ['start_offset', 'next_offset', 'total_bytes']:
        if type(value.get(name)) is not int or value[name] < 0:
            raise ValueError('invalid_output_offset')
    if value['start_offset'] != offset:
        raise ValueError('output_offset_gap')
    if total is not None and value['total_bytes'] != total:
        raise ValueError('output_total_changed')
    try:
        raw = base64.b64decode(value['data_base64'], validate=True)
    except (KeyError, TypeError, ValueError, binascii.Error) as error:
        raise ValueError('invalid_output_base64') from error
    if value['next_offset'] - offset != len(raw):
        raise ValueError('output_byte_count_mismatch')
    if value['next_offset'] > value['total_bytes']:
        raise ValueError('output_beyond_total')
    if not raw and offset < value['total_bytes']:
        raise ValueError('output_zero_progress')
    return raw


def validate_capture(raw, capture):
    if capture.get('complete') is not True or capture.get('start_offset') != 0:
        raise ValueError('incomplete_output_capture')
    total = capture.get('total_bytes')
    if type(total) is not int or total < 0 or capture.get('next_offset') != total or len(raw) != total:
        raise ValueError('incomplete_output_capture')
    offset = 0
    pages = capture.get('pages', [])
    if not pages:
        raise ValueError('missing_output_pages')
    for index, page in enumerate(pages):
        if (any(type(page.get(name)) is not int for name in ['start_offset', 'next_offset', 'total_bytes'])
                or page.get('start_offset') != offset or page.get('total_bytes') != total
                or type(page.get('bytes')) is not int or page['bytes'] < 0
                or page.get('next_offset') != offset + page['bytes']
                or page['next_offset'] > total or (page['bytes'] == 0 and (offset < total or index != len(pages) - 1))):
            raise ValueError('incomplete_output_capture')
        offset = page['next_offset']
    if offset != total or pages[-1]['bytes'] != 0:
        raise ValueError('missing_output_eof_confirmation')


def read_complete_output(fetch_page, launch):
    total = None
    offset = 0
    chunks, pages = [], []
    while True:
        value = fetch_page(offset)
        raw = _page(value, launch, offset, total)
        if total is None:
            total = value['total_bytes']
        pages.append({'start_offset': offset, 'next_offset': value['next_offset'],
                      'total_bytes': total, 'bytes': len(raw)})
        chunks.append(raw)
        if offset == total:
            break
        offset = value['next_offset']
    raw = b''.join(chunks)
    capture = {'complete': True, 'start_offset': 0, 'next_offset': total, 'total_bytes': total, 'pages': pages}
    validate_capture(raw, capture)
    return {'raw': raw, 'capture': capture, 'output': {'launch': launch, 'start_offset': 0,
            'next_offset': total, 'total_bytes': total, 'data_base64': base64.b64encode(raw).decode('ascii')}}


def verify_permission_output(dispatch_result, fetch_page, launch, expected_raw):
    capture = dispatch_result.get('permission_screen_capture')
    if not isinstance(capture, dict):
        raise ValueError('permission_complete_capture_required')
    validate_capture(expected_raw, capture)
    observed = read_complete_output(fetch_page, launch)
    if observed['raw'] != expected_raw:
        raise ValueError('permission_screen_changed')
    return observed['capture']

def read_complete_output(fetch_page, launch):
    value=fetch_page(0); raw=base64.b64decode(value['data_base64'])
    return {'raw':raw,'output':value,'capture':{'complete':True,'start_offset':0,'next_offset':value['next_offset'],'total_bytes':value['total_bytes'],'pages':[]}}
