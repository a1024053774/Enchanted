import argparse, ast, json, pathlib, shutil, subprocess, tarfile, tempfile, traceback
p=argparse.ArgumentParser();p.add_argument('--script',type=pathlib.Path,required=True);p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--summary',type=pathlib.Path,required=True);a=p.parse_args()
assert not a.summary.exists()
source=a.source.resolve();text=a.script.read_text(encoding='utf-8').split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
module=ast.parse(text);bootstrap=next(n for n in module.body if isinstance(n,ast.Try))
preparation=[]
for statement in bootstrap.body:
 if any(isinstance(n,ast.List) and n.elts and isinstance(n.elts[0],ast.Constant) and n.elts[0].value=='npm' for n in ast.walk(statement)):break
 preparation.append(statement)
else:raise AssertionError('npm boundary not found')
root=pathlib.Path(tempfile.mkdtemp(prefix='t105-py39-check-',dir='/private/tmp'));candidate=root/'candidate';baseline=root/'baseline';candidate.mkdir();baseline.mkdir()
report=dict(status='INCOMPLETE',python=__import__('sys').version,script=str(a.script),command=__import__('sys').argv,scope='actual wrapper source copy / git archive / extraction before npm and Electron')
try:
 code=ast.fix_missing_locations(ast.Module(body=preparation,type_ignores=[]))
 exec(compile(code,str(a.script),'exec'),dict(source=source,root=root,candidate=candidate,baseline=baseline,subprocess=subprocess,shutil=shutil,tarfile=tarfile))
 expected=set(subprocess.check_output(['git','ls-tree','-r','--name-only','37c8a9e77','workbench'],cwd=source,text=True).splitlines())
 actual={str(p.relative_to(baseline)) for p in baseline.rglob('*') if p.is_file() or p.is_symlink()}
 assert actual==expected,dict(missing=sorted(expected-actual),extra=sorted(actual-expected))
 for name in ['workbench/app/main.ts','workbench/README.md','workbench/package-lock.json']:
  assert (baseline/name).read_bytes()==subprocess.check_output(['git','show','37c8a9e77:'+name],cwd=source)
 report.update(status='PASS',files=len(actual),checks=['fixed baseline file paths match git tree','three baseline files match git show byte for byte','actual wrapper preparation reaches npm boundary'])
except Exception as error:
 report.update(error=repr(error),traceback=traceback.format_exc())
finally:
 shutil.rmtree(root)
 a.summary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['status']=='PASS' else 1)
