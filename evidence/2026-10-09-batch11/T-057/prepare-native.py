import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

out = Path(__file__).resolve().parent
root = Path(sys.argv[1]).resolve()
assert str(root).startswith('/Volumes/WD-Elements/dev-cache/synara/instances/t057-') and not root.is_symlink()
old = out.parents[1]/'2026-10-09-batch8/T-055'
spec = importlib.util.spec_from_file_location('fixture_api', old/'fixture-api.py')
api = importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
fixture = api.Fixture(root)
binary = str(Path(shutil.which('codex')).resolve())
version = subprocess.check_output([binary, '--version'], text=True).strip()
assert version == 'codex-cli 0.162.0', version
home = Path(tempfile.mkdtemp(prefix='a2a-t057-codex-', dir='/tmp')).resolve()
home.chmod(0o700)
shutil.copyfile('/Users/luckye/.codex/auth.json', home/'auth.json'); (home/'auth.json').chmod(0o600)
config = 'check_for_update_on_startup = false\ncli_auth_credentials_store = "file"\nservice_tier = "fast"\n[projects.'+json.dumps(str(root))+']\ntrust_level = "trusted"\n'
(home/'config.toml').write_text(config, encoding='utf-8'); (home/'rules').mkdir()
rules = 'prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
(home/'rules/default.rules').write_text(rules, encoding='utf-8')
launcher = root/'codex-fixed'
launcher.write_text('#!/bin/sh\nexec '+binary+' -c \'service_tier="fast"\' -c check_for_update_on_startup=false "$@"\n', encoding='utf-8')
launcher.chmod(0o700)
enabled = fixture.control('settings', patch={'providers':{'codex':{'enabled':True,'homePath':str(home),'binaryPath':str(launcher)}}})
assert enabled['providers']['codex']['enabled'] is True
with (out/'native-isolation-01.json').open('x', encoding='utf-8') as file:
    json.dump({'root':str(root),'home':str(home),'config':config,'rules':rules,'argv_prefix':[binary,'-c','service_tier="fast"','-c','check_for_update_on_startup=false'],
               'cli_version':version,'hooks':[],'copied':['auth.json'],'limitation':'Fast is requested; it does not prove the supplier tier.'},file,ensure_ascii=False,indent=2)
state = fixture.gate('status', task='t057')
attempt = state['task']['current_attempt']
command = {'type':'thread.turn.start','commandId':str(uuid.uuid4()),'threadId':attempt['thread_id'],
           'message':{'messageId':str(uuid.uuid4()),'role':'user','text':'这是隔离的 T-057 传输验收。不要改文件，不要调用任何工具，不要 submit。对本条只回复 READY。此后收到的每条“问题 / 用户答复”消息，只原样复述整个消息，不采取任何行动。','attachments':[]},
           'modelSelection':{'provider':'codex','model':'gpt-6.1-sol','options':{'reasoningEffort':'xhigh','fastMode':True}},
           'runtimeMode':'approval-required','interactionMode':'default','dispatchOrigin':'agent','createdAt':'2026-10-09T14:00:00Z'}
receipt = fixture.control('command', command=command)
with (out/'native-initial-command-01.json').open('x', encoding='utf-8') as file:json.dump({'command':command,'receipt':receipt,'thread':attempt['thread_id']},file,ensure_ascii=False,indent=2)
print(json.dumps({'thread':attempt['thread_id'],'home':str(home),'cli':version,'receipt':receipt},ensure_ascii=False))
