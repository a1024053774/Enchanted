import json,os,shutil,subprocess,sys,tarfile,tempfile
from pathlib import Path
ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
out=ROOT/'evidence/2026-10-11-batch13/T-078/rebased-counterexample-09a3';out.mkdir()
fixture=Path(tempfile.mkdtemp(prefix='t078-rebased-mutant-',dir='/tmp')).resolve()
for part in ['src','app']:
    shutil.copytree(ROOT/'workbench'/part,fixture/'workbench'/part)
(fixture/'workbench/tests').mkdir()
shutil.copyfile(ROOT/'workbench/tests/test_t078_empty_declaration_entry.ts',fixture/'workbench/tests/test_t078_empty_declaration_entry.ts')
(fixture/'workbench/node_modules').symlink_to(ROOT/'workbench/node_modules',target_is_directory=True)
p=fixture/'workbench/src/panes.ts';s=p.read_text(encoding='utf-8')
old='const matches = () => pane.interrupted && pane.interruption === declaration.interruption && pane.inputGeneration === declaration.input_generation;'
assert s.count(old)==1;s=s.replace(old,'const matches = () => true;')
old='const control = binary || (!pasted && /[\\x00-\\x1f\\x7f]/.test(data));'
assert s.count(old)==1;s=s.replace(old,'const control = binary || (!pasted && (data === "\\r" || data === "\\n" || data === "\\x1b" || data === "\\x7f"));')
p.write_text(s,encoding='utf-8')
p=fixture/'workbench/src/gates/cli.ts';s=p.read_text(encoding='utf-8');old='await emit(hookOutput ?? (request.command === "signal" && result.ok ? {} : result), trace);'
assert s.count(old)==1;s=s.replace(old,'await emit(request.command === "signal" && result.ok ? {} : result, trace);');p.write_text(s,encoding='utf-8')
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
argv=['node','workbench/tests/test_t078_empty_declaration_entry.ts',str(out/'entry')]
r=subprocess.run(argv,cwd=fixture,env=env,capture_output=True,timeout=45)
(out/'stdout.bin').write_bytes(r.stdout);(out/'stderr.bin').write_bytes(r.stderr)
facts=json.loads((out/'entry/results.json').read_bytes());failed={c['name'] for c in facts['checks'] if c['status']!='PASS'}
required={'new_input_invalidates_declaration','composition_without_text_invalidates_declaration','controls_are_actions_not_messages','injected_mismatch_blocks_actual_hook_output'}
with tarfile.open(out/'mutant-sources.tar.gz','x:gz') as a:
    for name in ['workbench/src/panes.ts','workbench/src/gates/cli.ts','workbench/tests/test_t078_empty_declaration_entry.ts']:a.add(fixture/name,arcname=name)
result={'status':'PASS' if r.returncode==1 and required<=failed else 'INCOMPLETE','kind':'已知坏变体被独立断言拒绝','base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'argv':argv,'cwd':str(fixture),'exit_code':r.returncode,'required_failures':sorted(required),'observed_failures':sorted(failed),'mutations':['ignore interruption/generation freshness','restore old control-key classification','discard successful UPS blocking JSON'],
        'scope':'隔离复制源码及依赖链接；未构建、未修改产品；真实 socket/hook CLI，PTY/vendor 为夹具','real_model_turns':0}
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['status']=='PASS' else 1)
