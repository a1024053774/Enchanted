import json,os,shutil,subprocess,tempfile
from pathlib import Path
from owned_api import connection
out=Path(__file__).resolve().parent
f=json.loads((out/'fixture.json').read_text());a=json.loads((out/'dispatch.json').read_text())['body']['attempt']
home=Path(tempfile.mkdtemp(prefix='a2a-t042-codex-',dir='/tmp')).resolve();home.chmod(0o700)
shutil.copyfile('/Users/luckye/.codex/auth.json',home/'auth.json');(home/'auth.json').chmod(0o600)
config='check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n'+''.join('[projects.'+json.dumps(p)+']\ntrust_level = "trusted"\n' for p in [f['repo'],a['workspace']])
(home/'config.toml').write_text(config);(home/'rules').mkdir();rules='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n';(home/'rules/default.rules').write_text(rules)
binary=str(Path(shutil.which('codex')).resolve());version=subprocess.check_output([binary,'--version'],text=True).strip();assert version=='codex-cli 0.161.0',version
base=Path('/Volumes/WD-Elements/dev-cache/synara/instances/t042-intervention-01');launcher=base/'codex-fixed'
launcher.write_text('#!/bin/sh\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n');launcher.chmod(0o700)
(out/'codex-isolation.json').write_text(json.dumps({'home':str(home),'config':config,'rules':rules,'copied':['auth.json'],'hooks':[],'binary':binary,'version':version,'launcher':launcher.read_text()},indent=2))
s=(out/'native-rpc.mjs').read_text().replace('tag: "orchestration.dispatchCommand"','tag: process.env.A2A_RPC_TAG || "orchestration.dispatchCommand"');(out/'native-rpc.mjs').write_text(s)
patch={'providers':{'codex':{'enabled':True,'homePath':str(home),'binaryPath':str(launcher)}}}
(out/'enable-input.json').write_text(json.dumps(patch))
endpoint,token,pid=connection();env=json.loads((out/'isolation.json').read_text())['env'];env.update(A2A_GATE_BEARER=token,A2A_RPC_TAG='server.updateSettings')
r=subprocess.run(['./a2a/scripts/bun','run','node',str(out/'native-rpc.mjs'),'enable',endpoint,str(out/'enable-input.json')],cwd='/Users/luckye/Documents/Code/synara',env=env,capture_output=True,text=True)
(out/'enable-command.json').write_text(json.dumps({'argv':r.args,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2));assert r.returncode==0,r.stderr
