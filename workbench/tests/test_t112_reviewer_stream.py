"""Protocol preflight from a captured CLI declaration; no native sandbox proof.
Failures: lost input deltas, changed call payload, or wrong local title stream.
"""
import argparse,json
from pathlib import Path
from t112_native_api import request_tools,shell_item,tool_events,message_events,assert_native_call
CAPTURE=Path(__file__).resolve().parents[2]/'evidence/2026-10-20-batch18/T-112/request-capture-02.json'

def check(events=tool_events):
    command='/usr/bin/printf "T112 sentinel with spaces"'
    cwd=Path('/private/tmp/t112 independent workspace')
    body=json.loads(CAPTURE.read_text(encoding='utf-8'))['requests'][0]['body']
    item=shell_item(request_tools(body),command,cwd)
    stream=events(item,'gpt-6.1-sol')
    assert stream[0][0]=='response.created' and stream[-1][0]=='response.completed'
    payload=''.join(value['delta'] for event,value in stream if event=='response.custom_tool_call_input.delta')
    assert payload,'Native stream consumer needs a tool input delta'
    completed=stream[-1][1]['response']['output'][0]
    assert_native_call(item,[completed])
    assert payload.startswith('text(await tools.exec_command(') and payload.endswith('));')
    args=json.loads(payload[len('text(await tools.exec_command('):-3])
    assert args['cmd']==command and args['workdir']==str(cwd)
    assert completed['input']==payload
    changed=dict(completed,input='text("ignored command");')
    try:assert_native_call(item,[changed])
    except AssertionError:pass
    else:raise AssertionError('Matching call_id with changed command must fail')
    title=message_events(json.dumps({'title':'T112 local probe'}),'gpt-6.1-sol')
    text=''.join(value['delta'] for event,value in title if event=='response.output_text.delta')
    assert json.loads(text)=={'title':'T112 local probe'}
    assert title[-1][1]['response']['status']=='completed'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--summary',required=True,type=Path);args=p.parse_args();assert not args.summary.exists()
    report={'status':'INCOMPLETE','scope':'captured declaration and SSE preflight; no native sandbox','source_capture':str(CAPTURE)}
    try:
        check()
        def missing_delta(item,model):return [(event,value) for event,value in tool_events(item,model) if not event.endswith('.delta')]
        try:check(missing_delta)
        except AssertionError as error:
            assert str(error)=='Native stream consumer needs a tool input delta'
            report['known_bad_rejected']=str(error)
        else:raise AssertionError('Missing-delta mutant must fail')
        report.update(status='PASS',checks=['captured_tool_declaration','input_delta_and_completion','native_call_payload_mutant_rejected','title_json_text_delta','missing_delta_mutant_rejected'])
    except Exception as error:report['error']=str(error)
    args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['status']=='PASS' else 1)
