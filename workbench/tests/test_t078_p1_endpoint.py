"""Pure binding tests; arbitrary ports are inputs, no socket is opened."""
import argparse,json,sys
from pathlib import Path
from p1_endpoint import resolved_input

parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir()
template={'api_url':'http://127.0.0.1:0','launch':'independent-launch','session':'independent-session','root':'unchanged-root','task':'unchanged-task'}
def receipt(port):return {'host':'127.0.0.1','port':port,'api_url':'http://127.0.0.1:'+str(port),'pid':1234,'launch':template['launch'],'session':template['session']}
checks=[]
for port in [12345,54321]:
    observed=resolved_input(template,receipt(port),1234)
    checks.append({'name':'allocated_port_'+str(port),'pass':observed=={**template,'api_url':'http://127.0.0.1:'+str(port)},'observed':observed})
for name,change in [('zero_port',{'port':0}),('wrong_pid',{'pid':9876}),('wrong_session',{'session':'other'}),('wrong_launch',{'launch':'other'}),('wrong_host',{'host':'example.invalid'}),('wrong_url',{'api_url':'http://example.invalid:12345'})]:
    value={**receipt(12345),**change}
    try:resolved_input(template,value,1234);refused=False
    except ValueError:refused=True
    checks.append({'name':name,'pass':refused})
# Known-bad prior behavior: ignore the bound endpoint and keep the template URL.
bad=dict(template)
checks.append({'name':'ignored_ready_receipt_counterexample','pass':bad!={**template,'api_url':'http://127.0.0.1:12345'},'bad_output':bad,'classification':'pure_binding_counterexample'})
result={'status':'PASS' if all(c['pass'] for c in checks) else 'INCOMPLETE','checks':checks,'argv':sys.argv,'socket_starts':0,'real_cli_starts':0}
with (args.output/'results.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':result['status'],'checks':len(checks)}));raise SystemExit(0 if result['status']=='PASS' else 1)
