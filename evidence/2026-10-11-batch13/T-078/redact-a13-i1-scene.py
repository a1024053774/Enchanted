"""Create a credential-free A-13 I1 scene summary; never copy raw Claude/API logs."""
import argparse, json, tarfile
from pathlib import Path

SENSITIVE = ('authorization', 'anthropic_auth_token', 'api_key', 'token', 'secret', 'system')


def tool_blocks(request):
    body = request.get('body_raw')
    try: data = json.loads(body) if isinstance(body, str) else {}
    except Exception: return [], []
    uses=[]; results=[]
    for message in data.get('messages', []):
        for block in message.get('content', []) if isinstance(message, dict) and isinstance(message.get('content'), list) else []:
            if not isinstance(block, dict): continue
            if block.get('type') == 'tool_use': uses.append({'id': block.get('id'), 'name': block.get('name'), 'input': block.get('input')})
            if block.get('type') == 'tool_result':
                value=block.get('content');
                try: value=json.loads(value) if isinstance(value, str) else value
                except Exception: pass
                results.append({'tool_use_id': block.get('tool_use_id'), 'content': value, 'is_error': block.get('is_error', False)})
    return uses, results


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve();out=a.output.resolve();assert root.is_dir() and not out.exists();out.mkdir(parents=False)
    requests=[];errors=[]
    request_file=root/'roles/ideation/requests.ndjson'
    if request_file.exists():
        for line in request_file.read_text(encoding='utf-8').splitlines():
            if not line: continue
            row=json.loads(line); uses,results=tool_blocks(row)
            requests.append({'message_kind':row.get('message_kind'),'dispatch_id':row.get('dispatch_id'),'sequence':len(requests)+1,
                             'tool_use':uses,'tool_result':results,'error_code':row.get('error')})
            if row.get('error'): errors.append(row['error'])
    responses=[]; response_file=root/'roles/ideation/responses.ndjson'
    if response_file.exists():
        for line in response_file.read_text(encoding='utf-8').splitlines():
            if line:
                row=json.loads(line);responses.append({'dispatch_id':row.get('dispatch_id'),'request_id':row.get('request_id'),'events':row.get('events')})
    registry=json.loads((root/'roles/ideation/protocol-registry.json').read_text()) if (root/'roles/ideation/protocol-registry.json').exists() else {}
    safe_registry={'dispatches':[]}
    for value in registry.get('dispatches',{}).values():
        safe_registry['dispatches'].append({'id':value.get('id'),'seq':value.get('seq'),'role':value.get('role'),'tool_use':value.get('tool_use')})
    summary={'status':'PASS','request_count':len(requests),'response_count':len(responses),'requests':requests,'responses':responses,
             'errors':errors,'protocol_registry':safe_registry,'raw_logs_copied':False,'credentials_copied':False,
             'scope':'Counts, tool_use/tool_result bodies, registry IDs and error codes only; no raw system/tools/auth/debug files'}
    raw=json.dumps(summary,ensure_ascii=False)
    assert not any(word in raw.lower() for word in SENSITIVE if word in ('authorization','anthropic_auth_token','api_key','secret'))
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    with tarfile.open(out/'redacted-fixture.tar.gz','w:gz') as archive: archive.add(out/'summary.json',arcname='summary.json')
    print(json.dumps({'status':'PASS','request_count':len(requests),'response_count':len(responses),'archive':str(out/'redacted-fixture.tar.gz')}))


if __name__=='__main__': main()
