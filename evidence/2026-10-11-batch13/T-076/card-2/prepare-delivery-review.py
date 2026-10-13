"""Controller-only setup for an approved interactive readonly audit, slot 7."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile

CARD=Path(__file__).resolve().parent
BUNDLE=CARD / 'delivery-review-01'
REVIEW_ROOT=Path('/private/tmp/a2a-t076-delivery-review-01')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--approval-file',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    approval=json.loads(args.approval_file.read_text())
    if not (approval.get('approved') is True and approval.get('policy')=='T076-2-delivery-review-01'
            and approval.get('slot')==7 and approval.get('root_turn_limit')==1 and approval.get('decision_ref')):
        raise RuntimeError('Explicit approval of audit slot 7 is required.')
    if REVIEW_ROOT.exists() or args.output.exists(): raise RuntimeError('Never reuse an audit root/output.')
    if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk is not mounted.')
    manifest=json.loads((BUNDLE / 'manifest.json').read_text()); repo=CARD.parents[3]
    for name in manifest['paths']:
        if (BUNDLE / 'candidate' / name).read_bytes()!=(repo / name).read_bytes():
            raise RuntimeError('Frozen candidate changed before review: '+name)
    args.output.mkdir(parents=True); REVIEW_ROOT.mkdir(mode=0o700)
    with tarfile.open(BUNDLE / 'candidate.tar.gz','r:gz') as archive:
        if any('..' in Path(m.name).parts or not m.name.startswith('candidate') or not (m.isfile() or m.isdir()) for m in archive.getmembers()):
            raise RuntimeError('Unexpected frozen candidate archive entry.')
        archive.extractall(REVIEW_ROOT)
    candidate=REVIEW_ROOT / 'candidate'; home=REVIEW_ROOT / 'codex-home'; home.mkdir(mode=0o700)
    shutil.copyfile(Path.home() / '.codex/auth.json',home / 'auth.json'); (home / 'auth.json').chmod(0o600)
    shutil.copyfile(BUNDLE / 'config.toml',home / 'config.toml')
    if sorted(p.name for p in home.iterdir())!=['auth.json','config.toml']: raise RuntimeError('Unexpected audit home content.')
    env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','CODEX_','GIT_'))}
    env.update(GIT_AUTHOR_NAME='Frozen audit',GIT_AUTHOR_EMAIL='audit@example.invalid',GIT_COMMITTER_NAME='Frozen audit',GIT_COMMITTER_EMAIL='audit@example.invalid',
               GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign',GIT_CONFIG_VALUE_1='false')
    commands=[]
    for argv in (['git','init','-b','review'],['git','add','.'],['git','commit','-m','Frozen T-076-2 audit candidate']):
        p=subprocess.run(argv,cwd=candidate,env=env,capture_output=True,text=True)
        commands.append(dict(argv=argv,cwd=str(candidate),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
        with (args.output / 'commands.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(commands[-1])+'\n')
        if p.returncode: raise RuntimeError('Owned candidate setup failed; retain audit root and report to controller.')
    argv=json.loads((BUNDLE / 'argv.json').read_text()); assert argv[-1]==(BUNDLE / 'PROMPT.txt').read_text()
    launch=args.output / 'launch.sh'
    launch.write_text('#!/bin/zsh\nset -euo pipefail\n[[ -t 0 && -t 1 ]] || { print -u2 "Interactive TTY required"; exit 2; }\n'
        +'print -r -- $$ > '+shlex.quote(str(args.output / 'cli.pid'))+'\n'
        +'exec env CODEX_HOME='+shlex.quote(str(home))+' '+shlex.join(argv)+'\n',encoding='utf-8'); launch.chmod(0o700)
    with (CARD / 'real-turn-budget.jsonl').open('a+',encoding='utf-8') as f:
        fcntl.flock(f,fcntl.LOCK_EX); f.seek(0); prior=[json.loads(l) for l in f if l.strip()]
        if sum(r['reserved'] for r in prior if r['kind']=='reservation')!=6:
            raise RuntimeError('Exactly the prior six reserved turns are required; no audit retry.')
        f.seek(0,2); f.write(json.dumps(dict(kind='reservation',slot=7,reserved=1,output=str(args.output),authorization=approval['decision_ref']))+'\n'); f.flush(); os.fsync(f.fileno())
    report=dict(status='PASS',phase='approved audit setup; model NOT_STARTED',root=str(REVIEW_ROOT),home=str(home),candidate=str(candidate),
                launch_script=str(launch),argv=argv,slot=7,reserved=1,commands=commands,approval=approval)
    (args.output / 'setup.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','phase','root','launch_script','slot')}))


if __name__=='__main__': main()
