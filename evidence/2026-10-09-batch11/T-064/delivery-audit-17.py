import ast
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import tarfile

out=Path(__file__).resolve().parent;repo=out.parents[2]
files=[]
for path in sorted(out.rglob('*')):
    if not path.is_file() or path.suffix not in ('.md','.py','.ts','.mts','.mjs','.json','.log'):continue
    text=path.read_bytes().decode('utf-8',errors='strict')
    if path.suffix=='.py':ast.parse(text,filename=str(path))
    if path.suffix=='.md':
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http:','https:','#')):continue
            assert (path.parent/target.split('#',1)[0]).is_file(),(path,target)
    assert not re.search(r'sagw_session_[0-9a-f-]{36}',text),path
    files.append(str(path.relative_to(repo)))
with tarfile.open(out/'retained-fixtures-16.tar.gz') as tar:
    members=[entry.name for entry in tar]
    assert not any(name.endswith(('.token','auth.json','.credentials.json')) for name in members)
commands=[['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'],
    ['git','diff','--check'],['git','status','--short']]
checks=[]
for argv in commands:
    run=subprocess.run(argv,cwd=repo,capture_output=True,text=True)
    checks.append(dict(argv=argv,cwd=str(repo),returncode=run.returncode,stdout=run.stdout,stderr=run.stderr))
    if argv[0]=='python3':assert run.returncode==0
fork=Path('/Users/luckye/Documents/Code/synara')
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()
assert revision=='0bf4bb2cab2216f567df2d4fb1729bee3cac6fe9'
record=dict(created_at=dt.datetime.now(dt.timezone.utc).isoformat(),fork_revision=revision,
    text_files_checked=files,archive_members=len(members),credentials_in_text_or_archive=False,
    checks=checks,status='INCOMPLETE',remaining='one independent review; user visual judgment')
with (out/'delivery-audit-17.json').open('x',encoding='utf-8') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print('PASS UTF-8, document links, Python syntax, no real gateway credentials in shared evidence, project map healthy; review pending')
