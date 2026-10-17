import json,os,subprocess,sys,tempfile
from pathlib import Path
SOURCE=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
out=Path(sys.argv[1]);out.mkdir()
root=Path(tempfile.mkdtemp(prefix='t078-metadata-',dir='/tmp')).resolve()
repo=root/'工作目录 "quoted" \\ slash';repo.mkdir()
binary=root/'receiver'
commands=[]
def run(argv,**kwargs):
    p=subprocess.run([str(x) for x in argv],capture_output=True,timeout=20,**kwargs)
    n=len(commands)+1;(out/f'{n}.stdout.bin').write_bytes(p.stdout);(out/f'{n}.stderr.bin').write_bytes(p.stderr)
    commands.append({'argv':[str(x) for x in argv],'exit_code':p.returncode,'cwd':str(kwargs.get('cwd',SOURCE))});return p
c=run(['/usr/bin/clang','-Wall','-Wextra','-Werror','-std=c11',SOURCE/'workbench/tests/t078_native_receiver.c','-o',binary],cwd=SOURCE)
assert c.returncode==0,commands
checks=[]
for name,argv,expected_exit in [('native',[binary],2),('python',['python3','-B',SOURCE/'workbench/tests/t078_terminal_receiver.py'],1)]:
    home=root/(name+'-home');home.mkdir()
    env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))};env['CODEX_HOME']=str(home)
    p=run(argv,cwd=repo,env=env,input=b'')
    # Both fixtures write metadata before terminal setup. A pipe is deliberately
    # not a TTY, so their terminal-setup error is expected and is not a red claim.
    logs=list((home/'sessions').glob('*.jsonl'));assert len(logs)==1
    raw=logs[0].read_bytes();(out/(name+'-metadata.jsonl')).write_bytes(raw)
    value=json.loads(raw.splitlines()[0]);payload=value['payload']
    passed=p.returncode==expected_exit and value['type']=='session_meta' and payload['source']=='cli' and payload.get('cwd')==str(repo)
    checks.append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','expected_cwd':str(repo),'observed_cwd':payload.get('cwd'),'expected_exit_for_non_tty':expected_exit,'observed_exit':p.returncode})
r={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'INCOMPLETE','scope':'夹具实际写出的 metadata/cwd；无 PTY、GUI、vendor 或模型；TTY 设置错误不是缺陷红态','checks':checks,'commands':commands,'root':str(root),'real_model_turns':0}
(out/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='PASS' else 1)
