"""Resolve the P1 endpoint from this API child's ready receipt, without I/O."""
def resolved_input(template, ready, api_pid):
    if template['api_url'] != 'http://127.0.0.1:0':
        raise ValueError('dynamic_endpoint_template_required')
    port = ready.get('port')
    if ready.get('host') != '127.0.0.1' or type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('invalid_api_ready_endpoint')
    if ready.get('pid') != api_pid or any(ready.get(key) != template[key] for key in ['launch', 'session']):
        raise ValueError('api_ready_identity_mismatch')
    endpoint = 'http://127.0.0.1:' + str(port)
    if ready.get('api_url') != endpoint:
        raise ValueError('api_ready_url_mismatch')
    return {**template, 'api_url': endpoint}
