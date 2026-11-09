import argparse, difflib, json, os, subprocess
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--mutant', required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; d=root/'.t265-review-checks'; source=root/'workbench/src/panes.ts'
original=(d/'panes.original.ts').read_bytes(); assert source.read_bytes()==original
text=original.decode('utf-8')
write='    writeFileSync(materials, `${pane.record.role_text}\\n\\n${prompt}`, { encoding: "utf8", flag: "wx", mode: 0o600 });'
entry=next(line for line in text.splitlines() if 'await this.dispatch(pane, `审查材料已保存到本次会话的文件' in line)
mutations={
'inline': (entry, '    await this.dispatch(pane, `${pane.record.role_text}\\n\\n${prompt}`);'),
'cut': ('`${pane.record.role_text}\\n\\n${prompt}`, { encoding:', '`${pane.record.role_text}\\n\\n${prompt}`.slice(0,1024), { encoding:'),
'overwrite': ('{ encoding: "utf8", flag: "wx", mode: 0o600 }', '{ encoding: "utf8", flag: "w", mode: 0o600 }'),
'dispatch-first': (write+'\n'+entry, entry+'\n'+write),
'omit-agy': ('if (pane.record.cli === "agy") {', 'if (false) {')}
before,after=mutations[args.mutant]; assert text.count(before)==1
changed=text.replace(before,after)
with (d/(args.mutant+'.patch')).open('x',encoding='utf-8') as f:
    f.write(''.join(difflib.unified_diff(text.splitlines(True),changed.splitlines(True),fromfile='candidate/workbench/src/panes.ts',tofile='mutant/workbench/src/panes.ts')))
cmd=['/opt/homebrew/Cellar/node/26.5.0/bin/node','--test','workbench/tests/test_t265_review_materials.mjs']
env=os.environ.copy(); env['A2A_REQUEST_DIR']=str(d/'fixtures'); env.pop('T265_MUTANT',None)
try:
    source.write_text(changed,encoding='utf-8')
    r=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True)
    result=dict(mutant=args.mutant,command=cmd,exit=r.returncode,stdout=r.stdout,stderr=r.stderr)
    with (d/(args.mutant+'.json')).open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
finally:
    source.write_bytes(original)
    assert source.read_bytes()==original
