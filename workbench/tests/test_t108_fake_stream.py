"""Check the actual fixture HTTP handler against the documented Messages SSE contract.

Failures: a final reply carries no text_delta, cannot be assembled as visible text,
misses end_turn/message_stop, or fails to issue AskUserQuestion before continuation.
This does not claim the real CLI emits Stop; the native/Electron run must prove that.
"""
import argparse
import ast
from http.server import BaseHTTPRequestHandler
import io
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--summary', type=Path, required=True)
args=p.parse_args()
assert not args.summary.exists()
report={'status':'INCOMPLETE','model_calls':0,'vendor_calls':0,'source':str(args.source)}
try:
    tree=ast.parse(args.source.read_text())
    handler=next(n for n in ast.walk(tree) if isinstance(n,ast.ClassDef) and n.name=='Handler')
    scope={'BaseHTTPRequestHandler':BaseHTTPRequestHandler,'json':json,'requests':[],'root_calls':[],
           'question':{'questions':[{'question':'独立问题','header':'独立','options':[{'label':'甲'},{'label':'乙'}],'multiSelect':False}]}}
    exec(compile(ast.Module(body=[handler],type_ignores=[]),str(args.source),'exec'),scope)
    def request(messages):
        body=json.dumps({'tools':[{'name':'AskUserQuestion'}],'messages':messages}).encode()
        obj=object.__new__(scope['Handler']);obj.path='/v1/messages'
        obj.rfile=io.BytesIO(body);obj.wfile=io.BytesIO();obj.headers={'Content-Length':str(len(body))}
        status=[];obj.send_response=status.append;obj.send_header=lambda *a:None;obj.end_headers=lambda:None
        obj.do_POST();assert status==[200]
        return [json.loads(line[6:]) for line in obj.wfile.getvalue().decode().splitlines() if line.startswith('data: ')]
    first=request([{'role':'user','content':'开始'}])
    assert any(e['type']=='content_block_start' and e['content_block']['type']=='tool_use' and
               e['content_block']['name']=='AskUserQuestion' for e in first)
    second=request([{'role':'user','content':[{'type':'tool_result','tool_use_id':'toolu_e2e_sentinel','content':'乙'}]}])
    deltas=[e['delta']['text'] for e in second if e['type']=='content_block_delta' and e['delta']['type']=='text_delta']
    assert ''.join(deltas)=='已收到答复。', 'Final response must transmit visible text through text_delta'
    assert second[-1]['type']=='message_stop'
    assert any(e['type']=='message_delta' and e['delta']['stop_reason']=='end_turn' for e in second)
    report.update(status='PASS',checks=['question_tool_stream','final_text_delta','end_turn_then_message_stop'])
except Exception as error:report['error']=str(error)
args.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report['status']=='PASS' else 1)
