"""Synthetic directory disappearance and denied enumeration. No auth or real HOME."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
p=Path(__file__).resolve().parents[1]/'src/claudeLoginFiles.py'
spec=importlib.util.spec_from_file_location('private_files',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
for denied in (False,True):
 with tempfile.TemporaryDirectory(prefix='t093-stat-race-',dir='/private/tmp') as temporary:
  home=Path(temporary);(home/'.claude/vanishing').mkdir(parents=True)
  original=os.open
  def opened(name,*args,**kwargs):
   if name=='vanishing' and 'dir_fd' in kwargs:
    if denied:raise PermissionError('synthetic_enumeration_denied')
    (home/'.claude/vanishing').rmdir()
   return original(name,*args,**kwargs)
  value=None;failure=None
  with patch.object(module.os,'open',side_effect=opened):
   try:value=module.inventory(str(home))
   except OSError as error:failure=type(error).__name__
  good=failure=='PermissionError' if denied else failure is None and value.get('.claude/vanishing',{}).get('missing') is True
  checks.append({'permission_denied':denied,'observed_failure':failure,'pass':good})
report={'status':'PASS' if all(c['pass'] for c in checks) else 'INCOMPLETE','scope':'actual inventory helper on synthetic directories; no real HOME, auth, profile or network','checks':checks}
with output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report));raise SystemExit(0 if report['status']=='PASS' else 2)
