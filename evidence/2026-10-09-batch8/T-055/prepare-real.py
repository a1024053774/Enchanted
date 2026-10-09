import importlib.util, json, os, shutil, subprocess, tempfile, sys
from pathlib import Path
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fixture_api',out/'fixture-api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
if len(sys.argv) > 2:
    out=Path(sys.argv[2]);out.mkdir()
fixture=api.Fixture(sys.argv[1]);root=fixture.root
repo=root/'repo';repo.mkdir()
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),*args],text=True,
        env={**os.environ,'GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1'}).strip()
git('init');git('config','user.name','T055 isolated fixture');git('config','user.email','fixture@example.invalid');git('config','commit.gpgsign','false')
(repo/'fixture.txt').write_text('T055 independent fixture\n')
git('add','fixture.txt');git('-c','core.hooksPath=/dev/null','commit','-m','Fixture baseline')
(root/'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1],"fixture.txt").read_text()=="T055 independent fixture\\n"\n')
instructions='这是隔离的 T-055 验收。不要改文件，不要调用 shell，不要 submit。只调用一次 a2a_raise，上报标题“oracle 漏了空页”，正文“分页夹具没有覆盖最后一页为空的情况。”，blocking=true，refs=[]。调用成功后只回复“等候用户答复”。下一条问题答复到达后，只逐字回复用户答复的正文，不调用工具。'
(root/'instructions.txt').write_text(instructions)
paths=[Path('/Users/luckye/.codex/config.toml'),Path('/Users/luckye/.codex/rules')]
paths.extend(paths[1].rglob('*'))
metadata={str(p):dict(size=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,mode=p.stat().st_mode) for p in paths}
assert os.environ.get('HERDR_ENV')=='1'
herdr=subprocess.run(['herdr','status'],capture_output=True,text=True)
binary=str(Path(shutil.which('codex')).resolve()); version=subprocess.check_output([binary,'--version'],text=True).strip()
assert version=='codex-cli 0.162.0',version
with (out/'user-before-real.json').open('x') as file:
    json.dump(dict(metadata=metadata,herdr_status=dict(exit=herdr.returncode,stdout=herdr.stdout,stderr=herdr.stderr),codex_binary=binary,codex_version=version),file,indent=2)
home=Path(tempfile.mkdtemp(prefix='a2a-t055-codex-',dir='/tmp')).resolve();home.chmod(0o700)
shutil.copyfile('/Users/luckye/.codex/auth.json',home/'auth.json');(home/'auth.json').chmod(0o600)
# Root is a new, verified fixture directory and owns every generated worktree.
config='check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n[projects.'+json.dumps(str(root))+']\ntrust_level = "trusted"\n'
(home/'config.toml').write_text(config);(home/'rules').mkdir()
rules='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
(home/'rules/default.rules').write_text(rules)
launcher=root/'codex-fixed'
launcher.write_text('#!/bin/sh\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n');launcher.chmod(0o700)
with (out/'codex-isolation.json').open('x') as file:
    json.dump(dict(home=str(home),config=config,rules=rules,launcher=launcher.read_text(),version=version,hooks=[],copied=['auth.json']),file,indent=2)
enabled=fixture.control('settings',patch={'providers':{'codex':{'enabled':True,'homePath':str(home),'binaryPath':str(launcher)}}})
# Settings include credential-state fields: keep only the non-secret patch in evidence.
assert enabled['providers']['codex']['enabled'] is True
created=fixture.gate('create',task='t055',project='t055-project',title='T055 问题答复',repo=str(repo),base=git('rev-parse','HEAD'),oracle=str(root/'oracle.py'),instructions=str(root/'instructions.txt'))
with (out/'real-create.json').open('x') as file:json.dump(created,file,ensure_ascii=False,indent=2)
assert created['ok'],created
runtime_mode=sys.argv[3] if len(sys.argv)>3 else 'approval-required'
dispatched=fixture.gate('dispatch',task='t055',runtimeMode=runtime_mode)
with (out/'real-dispatch.json').open('x') as file:json.dump(dispatched,file,ensure_ascii=False,indent=2)
print(json.dumps(dispatched,ensure_ascii=False))
assert dispatched['ok'],dispatched
