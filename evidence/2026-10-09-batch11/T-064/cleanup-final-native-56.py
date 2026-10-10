"""Retain the last two fixtures after removing both source and native homes."""
import json
from pathlib import Path
import subprocess
import tarfile

out=Path(__file__).resolve().parent
records=[]
archive=out/'retained-final-native-56.tar.gz'; assert not archive.exists()
def filter_entry(member):
    if any(p in ('home','os-home','codex-empty','claude-empty','node_modules') for p in Path(member.name).parts): return None
    if member.name.endswith('.token') or Path(member.name).name in ('auth.json','.credentials.json'): return None
    return member
with tarfile.open(archive,'w:gz') as tar:
    for label,session in [('codex-good53',85437),('codex-bad54',23818)]:
        result=out/(label+'-real');launch=json.loads((result/'launch.json').read_text(encoding='utf-8'))
        auth=json.loads((result/'auth-cleanup.json').read_text(encoding='utf-8'))
        native=json.loads((result/'native-home-cleanup.json').read_text(encoding='utf-8'))
        assert not Path(auth['home']).exists() and not Path(native['home']).exists()
        assert subprocess.run(['ps','-p',str(launch['pid']),'-o','stat='],capture_output=True).returncode!=0
        root=Path(launch['root']);assert root.parent==Path('/Volumes/WD-Elements/dev-cache/synara/instances')
        tar.add(root,arcname=root.name,filter=filter_entry)
        records.append(dict(label=label,argv=['python3',str(out/'real-provider-33.py'),label,'codex','good' if label=='codex-good53' else 'checked-prompts'],tool_session=session,observed_driver_exit=0,source_home_deleted=True,native_home_deleted=True,owned_process_stopped=True,root=str(root),source_revision=launch['source_revision']))
with tarfile.open(archive) as tar:
    assert not any(p.name.endswith('.token') or Path(p.name).name in ('auth.json','.credentials.json') for p in tar.getmembers())
with (out/'cleanup-final-native-56.json').open('x',encoding='utf-8') as f:
    json.dump(dict(status='PASS',records=records,archive=str(archive),archive_bytes=archive.stat().st_size,codex_total_reserved=4,codex_limit=4),f,ensure_ascii=False,indent=2)
print('PASS final native homes removed, owned processes stopped, two final fixtures archived without auth/token/cache')
