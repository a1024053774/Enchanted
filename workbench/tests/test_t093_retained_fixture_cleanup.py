"""Only synthetic owned directories are removed; OS guard is outside-only."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

p=Path(__file__).with_name('cleanup_t093_retained_fixture.py').resolve()
spec=importlib.util.spec_from_file_location('cleanup',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
output=Path(sys.argv[1]);assert not output.exists();checks=[]
for kind in ('initial','unconfirmed','closed','active','code'):
 root=Path(tempfile.mkdtemp(prefix='t093-chain-cleanup-unit-',dir='/private/tmp'))
 linked=Path(tempfile.mkdtemp(prefix='t093-linked-dependency-unit-',dir='/private/tmp'))
 try:
  for name in ('U','S','M','state','repo','synthetic-home','source-home/.claude'):(root/name).mkdir(parents=True)
  for name in ('home','claude','tmp','shell','requests','hooks','user-data'):(root/'roles/ideation'/name).mkdir(parents=True)
  for name in ('roles/ideation/role.md','source-home/private-sentinel','source-home/.claude/.credentials.json'):(root/name).write_text('synthetic only')
  if kind not in ('initial','code'):(root/'U/ready.json').write_text('{"pid":440401,"pgrp":440402}')
  if kind=='code':
   (root/'code/workbench/src').mkdir(parents=True);(root/'code/workbench/src/example.ts').write_text('synthetic source')
   (linked/'workbench/node_modules').mkdir(parents=True);(linked/'workbench/node_modules/keep').write_text('retained dependency')
   (root/'code/workbench/node_modules').symlink_to(linked/'workbench/node_modules',target_is_directory=True)
  if kind in ('closed','active'):
   receipt=root/'state/login-audits/12345678-1234-1234-1234-123456789012/metadata/removed.json'
   receipt.parent.mkdir(parents=True);receipt.write_text('{"isolated_home_removed":true,"cleanup_failures":[]}')
  def inactive(*args):raise ProcessLookupError()
  with patch.object(mod.os,'kill',side_effect=None if kind=='active' else inactive),patch.object(mod.os,'killpg',side_effect=inactive),patch.object(mod,'SOURCE',linked/'workbench/src/session.py' if kind=='code' else mod.SOURCE),patch.object(mod,'setup_quiescence',return_value={'complete':True,'matching_processes':[],'scope':'mocked unit evidence'}):
   if kind in ('unconfirmed','active'):
    expected='post_service_fixture_without_cleanup_receipt' if kind=='unconfirmed' else 'recorded_process_or_group_still_exists'
    try:mod.remove(root)
    except ValueError as error:assert str(error)==expected
    else:raise AssertionError('unsafe_fixture_must_not_be_deleted')
    assert (root/'source-home/.claude/.credentials.json').exists();checks.append({'case':kind,'refused_before_deletion':True})
   else:
    receipt=mod.remove(root);assert receipt['status']=='PASS' and receipt['root_removed'] and receipt['credential_file_present'];checks.append({'case':kind,'whole_root_removed':True})
    if kind=='code':assert (linked/'workbench/node_modules/keep').read_text()=='retained dependency','fixture_link_deletion_must_not_follow_dependency_target'
 finally:
  if root.exists():shutil.rmtree(root)
  shutil.rmtree(linked)
with output.open('x') as stream:json.dump({'status':'PASS','scope':'synthetic local fixtures; process probes mocked; no existing fixture removed or credential body read','checks':checks},stream,indent=2);stream.write('\n')
print(json.dumps({'status':'PASS','checks':len(checks)}))
