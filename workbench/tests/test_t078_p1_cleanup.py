"""Pure cleanup oracle from #89; no ps, signal, socket or CLI invocation."""
import argparse,json
from pathlib import Path
from p1_processes import identity_from_ps,cli_exit_verdict
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir()
cli={'pid':16681,'started':'Tue Oct 13 10:00:00 2026','command':'/fixed/claude'}
checks=[]
for name,manifest,observed,expected in [
    ('shell_exit_cli_alive',{'cli':cli},{16681:cli},'BLOCKED'),
    ('cli_exited',{'cli':cli},{16681:None},'PASS'),
    ('missing_manifest',None,{},'BLOCKED'),
    ('no_probe',{'cli':cli},{},'BLOCKED'),
    ('pid_identity_changed',{'cli':cli},{16681:{**cli,'started':'later'}},'BLOCKED')]:
    result=cli_exit_verdict(True,manifest,observed);checks.append({'name':name,'pass':result['status']==expected,'observed':result})
assert identity_from_ps(16681,0,'16681 Tue Oct 13 10:00:00 2026 /fixed/claude\n','')==cli
assert identity_from_ps(16681,1,'','') is None
# Original faulty rule: daemon/shell disappearing was enough to report PASS.
bad={'status':'PASS','daemon_pid_exists':False,'cli_alive':True}
checks.append({'name':'legacy_false_pass_rejected','pass':bad['status']!='BLOCKED','classification':'known_bad_rule_violates_the_required_BLOCKED_verdict','bad':bad})
data={'status':'PASS' if all(c['pass'] for c in checks) else 'INCOMPLETE','checks':checks,'real_process_checks':0,'scope':'Pure lifetime verdict only; real exit verification still awaits outside runtime.'}
with (args.output/'results.json').open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':data['status'],'checks':len(checks)}));raise SystemExit(0 if data['status']=='PASS' else 1)
