"""Archive only owned fixtures; exclude secrets and temporary provider homes."""
import json
from pathlib import Path
import subprocess
import tarfile

out=Path(__file__).resolve().parent
labels=['claude-probe34','claude-probe35','claude-probe36','claude-good37','claude-good38','claude-good39','claude-good40','claude-bad41','codex-good44','codex-bad45']
records=[]
archive=out/'retained-real-fixtures-49.tar.gz'
assert not archive.exists()
def filter_entry(member):
    parts=Path(member.name).parts
    if any(p in ('os-home','codex-empty','claude-empty','node_modules') for p in parts): return None
    if member.name.endswith('.token') or Path(member.name).name in ('auth.json','.credentials.json'): return None
    return member
with tarfile.open(archive,'w:gz') as tar:
    for label in labels:
        root=Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-'+label)
        assert root.parent==Path('/Volumes/WD-Elements/dev-cache/synara/instances') and root.exists()
        result=out/(label+'-real')
        record=dict(label=label,root=str(root),retained=True)
        if (result/'launch.json').exists():
            launch=json.loads((result/'launch.json').read_text(encoding='utf-8'))
            status=subprocess.run(['ps','-p',str(launch['pid']),'-o','stat='],text=True,capture_output=True)
            assert status.returncode!=0,'Owned process still exists'
            cleanup=json.loads((result/'auth-cleanup.json').read_text(encoding='utf-8'))
            assert not Path(cleanup['home']).exists(),'Temporary provider home still exists'
            record.update(pid=launch['pid'],server_gone=True,provider_home_removed=True)
        tar.add(root,arcname=root.name,filter=filter_entry)
        records.append(record)
with tarfile.open(archive,'r:gz') as tar:
    names=tar.getnames()
    assert not any(n.endswith('.token') or Path(n).name in ('auth.json','.credentials.json') for n in names)
with (out/'cleanup-real-49.json').open('x',encoding='utf-8') as f:
    json.dump(dict(status='PASS',archive=str(archive),excluded=['os-home','codex-empty','claude-empty','node_modules','*.token','auth.json','.credentials.json'],records=records,archive_entries=len(names),temporary_auth_removed=True,user_claude_credentials_copied=False),f,ensure_ascii=False,indent=2)
print('PASS owned processes stopped, temporary homes removed, retained fixtures archived without tokens/auth')
