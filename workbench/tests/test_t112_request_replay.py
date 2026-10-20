"""Replay the captured 0.162.1 HTTP body through the actual fixture handler.

Failures: assumes top-level tools, ignores advertised names/parameters, missing
or ambiguous declarations, or emits a call before preserving the request.
Only the server boundary is supplied. No CLI, socket, model or shell is started.
"""
import argparse
from copy import deepcopy
import io,json,tempfile
from pathlib import Path
import diagnose_t112_reviewer as fixture

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evidence/2026-10-20-batch18/T-112/request-capture-02.json'
class HandlerProbed(Exception):pass

def replay(body):
    report={}
    original=fixture.ThreadingHTTPServer
    with tempfile.TemporaryDirectory(prefix='t112-http-replay-',dir='/private/tmp') as raw:
        root=Path(raw)
        def boundary(address,Handler):
            request=json.dumps(body).encode()
            obj=object.__new__(Handler);obj.path='/v1/responses'
            obj.rfile=io.BytesIO(request);obj.wfile=io.BytesIO();obj.headers={'Content-Length':str(len(request))}
            statuses=[]
            def response(code):
                journal=root/'case/api-requests.jsonl'
                assert journal.exists() and json.loads(journal.read_text(encoding='utf-8').splitlines()[0])['raw_body']==request.decode()
                statuses.append(code)
            obj.send_response=response;obj.send_header=lambda *a:None;obj.end_headers=lambda:None
            obj.send_error=lambda code,*a:statuses.append(code)
            obj.do_POST()
            report['http_status']=statuses
            report['events']=[json.loads(line[6:]) for line in obj.wfile.getvalue().decode().splitlines() if line.startswith('data: ')]
            raise HandlerProbed()
        fixture.ThreadingHTTPServer=boundary
        try:
            fixture.run_reviewer_case(ROOT,root/'source',root/'case','replay-revision',{},report)
        except HandlerProbed:pass
        finally:fixture.ThreadingHTTPServer=original
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--summary',required=True,type=Path);args=p.parse_args();assert not args.summary.exists()
    body=json.loads(CAPTURE.read_text(encoding='utf-8'))['requests'][0]['body']
    report={'status':'INCOMPLETE','scope':'actual captured request through real fake API handler; no native sandbox','source_capture':str(CAPTURE),'checks':[]}
    try:
        observed=replay(body);report['captured_request_replay']=observed
        assert observed['http_status']==[200], 'Captured native request must get a tool response, observed HTTP '+str(observed['http_status'])
        item=observed['events'][-1]['response']['output'][0]
        declared=next(t for entry in body['input'] if entry.get('type')=='additional_tools' for ns in entry['tools'] for t in ns.get('tools',[]) if t.get('type')=='custom')
        assert item['type']=='custom_tool_call' and item['name']==declared['name'] and item['namespace']=='functions'
        assert 'exec_command' in item['input'] and 'candidate-probe.txt' in item['input'] and 'protected.txt' in item['input']
        report['checks'].append('captured_additional_tools_request_gets_native_tool_call')
        title_body=json.loads((ROOT/'evidence/2026-10-20-batch18/T-112/code-mode-protocol-01.json').read_text(encoding='utf-8'))['requests'][1]['body']
        title=replay(title_body);report['title_request_replay']=title
        assert title['http_status']==[200] and 'emitted_tool_call' not in title['cases'][0]
        title_text=''.join(item['delta'] for item in title['events'] if item['type']=='response.output_text.delta')
        title_value=json.loads(title_text)
        assert set(title_value)=={'title'} and 1<=len(title_value['title'])<=36
        report['checks'].append('captured_thread_title_receives_json_text_without_consuming_root_tool')
        changed=deepcopy(body)
        for entry in changed['input']:
            if entry.get('type')=='additional_tools':
                for ns in entry['tools']:
                    for t in ns.get('tools',[]):
                        if t.get('type')=='custom':
                            t['name']='outer_shell_sentinel'
                            t['description']=t['description'].replace('exec_command','run_shell_sentinel').replace('cmd: string','line_sentinel: string').replace('workdir?: string','directory_sentinel?: string').replace('yield_time_ms?: number','wait_sentinel?: number')
        mutated=replay(changed);report['renamed_declaration_replay']=mutated
        assert mutated['http_status']==[200]
        renamed=mutated['events'][-1]['response']['output'][0]
        assert renamed['name']=='outer_shell_sentinel'
        code=renamed['input']
        assert code.startswith('text(await tools.run_shell_sentinel(')
        supplied=json.loads(code[len('text(await tools.run_shell_sentinel('):-3])
        assert set(supplied)=={'line_sentinel','directory_sentinel','wait_sentinel'}
        report['checks'].append('outer_tool_inner_function_and_parameters_come_from_request')
        absent=deepcopy(body);absent['input']=[item for item in absent['input'] if item.get('type')!='additional_tools']
        refused=replay(absent);report['missing_declaration_replay']=refused
        assert refused['http_status']==[500] and not refused['events']
        report['checks'].append('missing_declarations_refused_without_inventing_tool')
        report['status']='PASS'
    except Exception as error:report['error']=str(error)
    args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'error':report.get('error')}));raise SystemExit(0 if report['status']=='PASS' else 1)
