"""Replay #155's original command/owner and the actual localized failed ps row."""
import argparse,ast,importlib.util,json,sys
from pathlib import Path
from p1_processes import identity_from_ps
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
base=Path(__file__).resolve().parents[2]/'evidence/2026-10-11-batch13/T-078';script=base/'cleanup-block-recovery-09a3r2.py'
spec=importlib.util.spec_from_file_location('cleanup_guard_only',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
tree=ast.parse(script.read_text(encoding='utf-8'));main=next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name=='main');probe=next(v for v in main.body if isinstance(v,ast.FunctionDef) and v.name=='probe')
original='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python -B /Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_fake_messages.py /private/tmp/t078-2-p1-09a3r2-block-093154n0'
owner=['/usr/bin/python3','-B','/Users/luckye/Documents/Code/a2a-wt-t078/workbench/tests/t078_fake_messages.py','/private/tmp/t078-2-p1-09a3r2-block-093154n0']
raw=(base/'p1-materials-09a3r2-block/cleanup-recovery-153/command-output/00001.stdout.bin').read_text(encoding='utf-8')
calls=[]
class Log:
    def run(self,argv,**kwargs):
        from types import SimpleNamespace
        locale=(kwargs.get('env') or {}).get('LC_ALL');calls.append({'argv':argv,'LC_ALL':locale})
        # Only the probe's canonical locale request selects the canonical test
        # row. This simulates ps, not a real outside process observation.
        text='48954 Wed Oct 14 14:14:35 2026 '+original+'\n' if locale=='C' else raw
        return SimpleNamespace(returncode=0,stdout=text,stderr='')
namespace={'log':Log(),'SOURCE':module.SOURCE,'identity_from_ps':identity_from_ps}
exec(compile(ast.Module(body=[probe],type_ignores=[]),'<actual cleanup probe>','exec'),namespace)
checks=[{'name':'original_command_matches_owner_arguments','pass':module.owns_api(original) and owner==module.EXPECTED_ARGV}]
value=namespace['probe'](48954,True)
checks.append({'name':'probe_requests_canonical_locale_and_preserves_command','pass':calls[-1]['LC_ALL']=='C' and value['command']==original and module.owns_api(value['command']),'observed':value,'call':calls[-1]})
error=None
try:identity_from_ps(48954,0,raw,'')
except ValueError as failure:error=repr(failure)
checks.append({'name':'localized_noncanonical_row_is_rejected','pass':error is not None,'error':error})
checks.append({'name':'foreign_root_still_rejected','pass':not module.owns_api(original.replace(str(module.ROOT),'/private/tmp/foreign'))})
checks.append({'name':'extra_arguments_still_rejected','pass':not module.owns_api(original+' extra')})
r={'status':'PASS' if all(v['pass'] for v in checks) else 'INCOMPLETE','checks':checks,'original_command':original,'original_owner_argv':owner,'original_failed_ps':raw,'argv':sys.argv,'scope':'Actual probe closure + saved raw row + canonical-locale ps simulator; no main/ps/signal/archive/delete starts'}
(args.output/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');(args.output/'cleanup-script.py').write_bytes(script.read_bytes());(args.output/'p1_processes.py').write_bytes(Path(__file__).with_name('p1_processes.py').read_bytes())
print(json.dumps({'status':r['status'],'failed':[v['name'] for v in checks if not v['pass']]}));raise SystemExit(0 if r['status']=='PASS' else 1)
