"""Prepare T-108's proposed real-Claude fixture. No auth reads or model input.

This helper does not start the daemon, the CLI's interactive session, or Electron.
Run only after the controller approves the separate real-turn plan.
"""
import argparse
import json
import os
import re
from pathlib import Path
import socket
import subprocess
import uuid

p=argparse.ArgumentParser()
p.add_argument('--root',required=True,type=Path)
p.add_argument('--claude',required=True,type=Path)
p.add_argument('--revision',required=True)
args=p.parse_args()
source=Path(__file__).resolve().parents[2]
assert len(args.revision)==40 and all(c in '0123456789abcdef' for c in args.revision)
executable=args.claude.resolve(strict=True)
assert executable.is_file() and os.access(executable,os.X_OK)
# No inherited provider or Git settings, and no access to login credentials.
env={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','A2A_','CLAUDE_','ANTHROPIC_','CODEX_')) and k!='NODE_OPTIONS'}
root=args.root.resolve()
assert root.parent==Path('/private/tmp') and root.name.startswith('t108-real-') and not root.exists()
root.mkdir(mode=0o700)
for name in ['repo','state','manager-home']:(root/name).mkdir(mode=0o700)
env.update(HOME=str(root/'manager-home'),LC_ALL='C',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
           GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
           GIT_AUTHOR_NAME='T108 fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',
           GIT_COMMITTER_NAME='T108 fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid')
probe=subprocess.run([str(executable),'--version'],env=env,capture_output=True,text=True,check=True,timeout=10)
version=re.fullmatch(r'([0-9]+\.[0-9]+\.[0-9]+) \(Claude Code\)',probe.stdout.strip())
assert version is not None, 'Installed CLI version could not be read'
version=version.group(1)
assert subprocess.run(['git','rev-parse','HEAD'],cwd=source,env=env,capture_output=True,text=True,check=True).stdout.strip()==args.revision
role=root/'roles/ideation'
for name in ['home','claude','tmp','shell','requests','hooks','user-data']:(role/name).mkdir(parents=True,mode=0o700)
(role/'role.md').write_text('隔离验收主控。收到唯一用户输入后，仅调用一次 AskUserQuestion。问题为“选择部署区域？”，header 为“区域”；两个选项依次为“东区”（说明“第一个区域”）、“西区”（说明“第二个区域”），multiSelect=false。必须等待原生回答；收到回答后只输出“已收到答复。”并结束。不调用其他工具，不读写文件，不追加提问。\n',encoding='utf-8')
repo=root/'repo'
subprocess.run(['git','init','-b','main',str(repo)],env=env,check=True,capture_output=True)
(repo/'fixture').write_text('isolated T108 real-turn fixture\n',encoding='utf-8')
subprocess.run(['git','-C',str(repo),'add','.'],env=env,check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'commit','-m','fixture'],env=env,check=True,capture_output=True)
card={'id':'T108-real','source':None,'goal':'核验原生提问并作答','non_goals':['交付与集成'],
      'paths':{'allow':['.'],'deny':[]},'oracle_paths':['fixture'],'completion_conditions':[{'argv':['/usr/bin/false']}],
      'red_commands':[],'task_type':'后端逻辑','repair_target':None,'complexity':'L',
      'executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'high'},'base_commit':None,'writer':None}
manifest={'schema':1,'root':str(root),'state':str(root/'state'),'task':'T108-real','preset':'ideation',
          'launch':str(uuid.uuid4()),'session':str(uuid.uuid4()),'thread':str(uuid.uuid4()),
          'executable':str(executable),'version':version,'role_file':str(role/'role.md'),
          'code_revision':args.revision,'source_snapshot':str(source),'authentication':'normal-login',
          'credential_source':'macos-keychain','upstream_url':'https://api.anthropic.com','turn_limit':1}
for name,value in [('card.json',card),('manifest.json',manifest)]:
 (root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# A collision at actual launch is a failure, not permission to reuse another listener.
with socket.socket() as listener:
 listener.bind(('127.0.0.1',0));port=listener.getsockname()[1]
address=socket.getaddrinfo('api.anthropic.com',443,family=socket.AF_INET,type=socket.SOCK_STREAM)[0][4][0]
(root/'network.json').write_text(json.dumps({'forward_port':port,'upstream_address':address})+'\n')
print(json.dumps({'status':'PREPARED','root':str(root),'launch':manifest['launch'],'model_calls':0,'vendor_calls':0},ensure_ascii=False))
