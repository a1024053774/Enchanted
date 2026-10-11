#!/usr/bin/env python3
"""Launch only controller-authorized rev-4 native CLI probes."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import uuid

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def launch(label,cli):
    if not Path('/Volumes/WD-Elements').is_mount():
        raise SystemExit('External volume absent; no cache fallback')
    out=BASE/label;out.mkdir()
    temp=Path(tempfile.mkdtemp(prefix='a2a-t074-rev4-',dir='/tmp'))
    fixture=temp/'fixture';fixture.mkdir();fixture=fixture.resolve()
    shell=temp/'shell';shell.mkdir()
    subprocess.run(['git','init','-q',str(fixture)],check=True)
    subprocess.run(['git','-C',str(fixture),'-c','user.name=T074 Fixture','-c','user.email=fixture@example.invalid','commit','--allow-empty','-qm','T074 rev4 fixture'],check=True)
    node_pty=ROOT.parent/'synara/apps/server/node_modules/node-pty'
    env={key:os.environ[key] for key in ['PATH','LANG','LC_ALL','LC_CTYPE','TMPDIR'] if key in os.environ}
    env.update(SHELL='/bin/zsh',TERM='xterm-256color',COLORTERM='truecolor',LANG='en_US.UTF-8',ZDOTDIR=str(shell),PYTHONDONTWRITEBYTECODE='1')
    command=shlex.join(['python3',str(BASE/'turn-hook-record.py'),str(out/'turn-hooks.jsonl')])
    hook=[{'hooks':[{'type':'command','command':command,'timeout':3}]}]
    events=['UserPromptSubmit','Stop','PermissionRequest']
    home=None;session=None;transcript=None
    if cli=='codex':
        executable=Path(shutil.which('codex')).resolve()
        version=subprocess.check_output([str(executable),'--version'],text=True).strip()
        if version!='codex-cli 0.162.1':raise SystemExit('Pinned Codex differs')
        home=temp/'codex-home';home.mkdir(mode=0o700)
        shutil.copyfile(Path.home()/'.codex/auth.json',home/'auth.json');(home/'auth.json').chmod(0o600)
        (home/'config.toml').write_text(f'[projects.{json.dumps(str(fixture))}]\ntrust_level="trusted"\n',encoding='utf-8')
        (home/'rules').mkdir()
        (home/'rules/default.rules').write_text('prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n',encoding='utf-8')
        env.update(HOME=str(shell),CODEX_HOME=str(home))
        argv=[str(executable),'--no-daemon','--no-alt-screen','-C',str(fixture),'-m','gpt-6-astra','-c','model_reasoning_effort="xhigh"','-c','service_tier="fast"','-c','check_for_update_on_startup=false','-s','workspace-write','-a','on-request','-c','tui.notifications=false','-c','notify='+json.dumps(['python3',str(BASE/'notify.py'),str(out/'notify.jsonl')])]
        # The exact recorders are scoped to this authorized probe invocation.
        toml='[{hooks=[{type="command",command='+json.dumps(command)+',timeout=3}]}]'
        for event in events:argv+=['-c','hooks.'+event+'='+toml]
        argv+=['--dangerously-bypass-hook-trust']
    else:
        executable=Path(shutil.which('claude')).resolve()
        version=subprocess.check_output([str(executable),'--version'],text=True).strip()
        if version!='2.1.296 (Claude Code)':raise SystemExit('Pinned Claude differs')
        session=str(uuid.uuid4())
        encoded=''.join(c if c.isascii() and c.isalnum() else '-' for c in str(fixture))
        transcript=Path.home()/'.claude/projects'/encoded/(session+'.jsonl')
        env.update(HOME=str(Path.home()),DISABLE_AUTOUPDATER='1')
        settings={'hooks':{event:hook for event in events},'permissions':{'ask':['Bash(python3 *)'],'allow':['Bash(/bin/sleep *)']}}
        save(out/'claude-settings.json',settings)
        argv=[str(executable),'--session-id',session,'--model','claude-haiku-5-5','--permission-mode','manual','--settings',str(out/'claude-settings.json'),'--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--tools','Bash,Read,Write','--disable-slash-commands']
    # Bootstrap is submitted through the backend, so every Stop has a local submission.
    manifest=dict(created_at=dt.datetime.now(dt.timezone.utc).isoformat(),task_card='T-074-1',ready_rev=4,
                  starting_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  cli=cli,version=version,launch_mode='on-request' if cli=='codex' else 'manual',cli_argv=argv,
                  node_pty_path=str(node_pty),node_version=subprocess.check_output(['node','--version'],text=True).strip(),node_pty_version=json.loads((node_pty/'package.json').read_text())['version'],
                  temp_root=str(temp),fixture=str(fixture),output=str(out),codex_home=str(home) if home else None,
                  native_session=session,native_transcript=str(transcript) if transcript else None,
                  socket=str(temp/'control.sock'),env=env,hook_definition={event:hook for event in events},
                  hook_authorization='controller-decision-04.md, retaining decision 03 hooks; PermissionRequest is diagnostic only',
                  authentication='isolated auth.json' if cli=='codex' else 'normal CLI login; no credentials inspected/copied')
    save(out/'launch.json',manifest)
    shutil.copyfile(BASE/'rev4-host.cjs',out/'rev4-host.cjs')
    log=open(out/'host.log','ab')
    process=subprocess.Popen(['node',str(out/'rev4-host.cjs'),str(out/'launch.json')],cwd=fixture,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
    save(out/'host-process.json',dict(pid=process.pid,start_new_session=True))
    print(json.dumps(dict(label=label,pid=process.pid,cli=cli,native_transcript=str(transcript) if transcript else None),ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('label');parser.add_argument('--cli',choices=['codex','claude'],required=True)
    args=parser.parse_args();launch(args.label,args.cli)
