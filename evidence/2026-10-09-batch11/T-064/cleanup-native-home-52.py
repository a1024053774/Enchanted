"""Remove owned native overlays and retain the first archive privately.

The native overlay links auth to the /tmp home. Auth bytes are not inspected.
Replay applies only to these recorded owned fixtures after their processes stop.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

out=Path(__file__).resolve().parent
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances')
records=[]
for label in ('codex-good44','codex-bad45'):
    result=out/(label+'-real')
    launch=json.loads((result/'launch.json').read_text(encoding='utf-8'))
    cleanup=json.loads((result/'auth-cleanup.json').read_text(encoding='utf-8'))
    root=Path(launch['root'])
    assert root==base/('s11-t064-'+label)
    assert subprocess.run(['ps','-p',str(launch['pid']),'-o','stat='],capture_output=True).returncode!=0
    overlay=root/'home/codex-home-overlay'
    assert overlay.exists() and not overlay.is_symlink() and overlay.resolve()==overlay
    auth=overlay/'auth.json'
    assert auth.is_symlink() and auth.resolve()==Path(cleanup['home'])/'auth.json'
    assert not auth.exists() and not Path(cleanup['home']).exists()
    record=dict(label=label,overlay=str(overlay),native_config=(overlay/'config.toml').read_text(encoding='utf-8'),auth_was_link_to_deleted_tmp_home=True,auth_bytes_read=False)
    shutil.rmtree(overlay)
    assert not overlay.exists()
    record['native_home_removed']=True; records.append(record)
private=base/'s11-t064-artifacts52'; private.mkdir(mode=0o700)
original=out/'retained-real-fixtures-49.tar.gz'
retained=private/original.name
assert original.exists() and not retained.exists()
subprocess.run(['git','restore','--staged','--',str(original)],check=True)
shutil.move(str(original),str(retained))
archive=out/'retained-real-fixtures-52.tar.gz'; assert not archive.exists()
previous=json.loads((out/'cleanup-real-49.json').read_text(encoding='utf-8'))
def filter_entry(member):
    if any(part in ('home','os-home','codex-empty','claude-empty','node_modules') for part in Path(member.name).parts): return None
    if member.name.endswith('.token') or Path(member.name).name in ('auth.json','.credentials.json'): return None
    return member
with tarfile.open(archive,'w:gz') as tar:
    for item in previous['records']:
        root=Path(item['root']); assert root.parent==base and root.exists()
        tar.add(root,arcname=root.name,filter=filter_entry)
with tarfile.open(archive,'r:gz') as tar:
    names=tar.getnames()
    assert not any(n.endswith('.token') or Path(n).name in ('auth.json','.credentials.json') for n in names)
with (out/'cleanup-native-home-52.json').open('x',encoding='utf-8') as f:
    json.dump(dict(status='PASS',records=records,first_archive_retained=str(retained),first_archive_bytes=retained.stat().st_size,delivered_archive=str(archive),delivered_archive_bytes=archive.stat().st_size,excluded_native_home_and_plugin_download_cache=True,previous_receipt='cleanup-real-49.json',original_fixture_data_retained=True),f,ensure_ascii=False,indent=2)
print('PASS owned native overlays removed; first archive retained privately; smaller delivery archive contains runtime evidence')
