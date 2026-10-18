"""Actual cleanup main writes error targets; all filesystem operations mocked."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import uuid
from unittest.mock import patch

source=Path(__file__).with_name('cleanup_t093_retained_fixture.py').resolve()
spec=importlib.util.spec_from_file_location('cleanup_cli',source);mod=importlib.util.module_from_spec(spec)
text=Path(sys.argv[2]).read_text() if len(sys.argv)>2 else source.read_text();exec(compile(text,str(source),'exec'),vars(mod))
output=Path(sys.argv[1]);assert not output.exists();checks=[]
scope=json.loads((mod.SOURCE.parents[2]/'evidence/2026-10-16-batch16/T-093/retained-cleanup-scope-05.json').read_text())
root=scope['roots'][0]
for operation,target,number in [('lstat',root+'/denied.json',13),('process_inventory_exec','/usr/bin/pgrep',1)]:
 result_path=Path('/private/tmp/t093-cli-error-unit-'+uuid.uuid4().hex+'.json')
 def fail(*args):
  if len(args)>2:args[2].update(operation=operation,path=target)
  raise PermissionError(number,'synthetic denial',target)
 try:
  with patch.object(sys,'argv',['cleanup','--protected','--root',root,'--output',str(result_path)]),patch.object(mod.runtime,'validate_bootstrap'),patch.object(mod,'remove',side_effect=fail),contextlib.redirect_stdout(io.StringIO()):
   code=mod.main()
  value=json.loads(result_path.read_text())
  try:
   assert code==2 and value['status']=='INCOMPLETE' and value['root_removed'] is False
   assert value.get('operation')==operation and value.get('path')==target and value.get('errno')==number,'actual_CLI_failure_receipt_must_include_operation_path_errno'
   checks.append({'operation':operation,'status':'PASS','errno':number,'retained_fixture_operations':0})
  except AssertionError as error:checks.append({'operation':operation,'status':'FAIL','business_failure':str(error)})
 finally:
  if result_path.exists():result_path.unlink()
status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL'
with output.open('x') as stream:json.dump({'status':status,'scope':'actual main and exclusive JSON writer, remove/bootstrap mocked; no retained root read/write or process/OS execution','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':status,'checks':len(checks)}));raise SystemExit(0 if status=='PASS' else 2)
