#!/usr/bin/env python3
"""T-249 reviewer counterfactuals; only mutate this disposable copy and restore bytes."""
import argparse, datetime, difflib, json, os, pathlib, shutil, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
NODE = '/opt/homebrew/Cellar/node/26.5.0/bin/node'
CASES = [
 dict(id='M1-untracked-disabled', path='workbench/app/panels/gitGraphModel.ts',
      before="if (commit.uncommitted && status === '?')", after="if (false && commit.uncommitted && status === '?')",
      expectation='未跟踪文本必须显示原始文件内容；禁用读取必须命中内容业务断言。',
      window_failure='未提交 未跟踪文本 diff 与原始文件及独立 Git 一致：untracked.txt'),
 dict(id='M2-path-containment-disabled', path='workbench/app/gitHost.ts',
      before="if (!resolved.startsWith(cwd + sep) || relative(cwd, resolved).split(sep).includes('.git') || !lstatSync(file).isFile())",
      after="if (false && (!resolved.startsWith(cwd + sep) || relative(cwd, resolved).split(sep).includes('.git') || !lstatSync(file).isFile()))",
      expectation='no-index 必须拒绝经符号链接逃到仓库外的文件；禁用边界必须被宿主测试拒绝。'),
 dict(id='M3-zero-drag', path='workbench/app/panels/GitGraphPanel.tsx',
      before='width - (moved.clientX - start)', after='width - 0 * (moved.clientX - start)',
      expectation='64 px 鼠标拖动必须改变表头与数据行列宽；零位移实现必须被拒绝。',
      window_failure='真实鼠标拖动改变可见日期列宽'),
 dict(id='M4-wrong-reset', path='workbench/app/panels/GitGraphPanel.tsx',
      before='[column]: columnDefaults[column] }))}', after='[column]: columnDefaults[column] + 32 }))}',
      expectation='双击必须恢复拖动前宽度；多留 32 px 必须被拒绝。',
      window_failure='真实鼠标双击恢复可见日期列宽'),
]
COMMANDS = [
 ['/usr/bin/python3', 'acceptance/T-249/check_git_graph.py'],
 [NODE, '--test', 'workbench/tests/test_t249_git_host.mjs'],
 ['/usr/bin/python3', 'workbench/tests/test_t249_outside_safety.py'],
]
def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
def prepare():
    originals = HERE / 'originals'; originals.mkdir()
    for name in sorted({c['path'] for c in CASES}):
        p = originals / name; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    for c in CASES:
        before = (ROOT / c['path']).read_text(encoding='utf-8')
        assert before.count(c['before']) == 1, c['id']
        after = before.replace(c['before'], c['after'])
        (HERE / (c['id'] + '.patch')).write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
          fromfile='a/'+c['path'], tofile='b/'+c['path'])), encoding='utf-8')
    save(HERE/'mutations.json', CASES)
def original(path): return (HERE/'originals'/path).read_bytes()
def pristine():
    return all((ROOT/c['path']).read_bytes() == original(c['path']) for c in CASES)
def apply(c):
    p=ROOT/c['path']; b=original(c['path']); assert p.read_bytes()==b, 'Unexpected source changes: '+c['path']
    p.write_bytes(b.replace(c['before'].encode(), c['after'].encode()))
def restore(c):
    p=ROOT/c['path']; b=original(c['path'])
    assert p.read_bytes()==b.replace(c['before'].encode(), c['after'].encode()), 'Concurrent edit; not overwriting'
    p.write_bytes(b)
def run(argv, out, env):
    p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True)
    (out/'stdout.txt').write_text(p.stdout,encoding='utf-8')
    (out/'stderr.txt').write_text(p.stderr,encoding='utf-8')
    data=dict(argv=argv,exit=p.returncode,cwd=str(ROOT))
    save(out/'command.json',data); return data

def local():
    out=HERE/'local-01'; out.mkdir(); temp=out/'tmp'; temp.mkdir()
    env=dict(os.environ,PATH=str(pathlib.Path(NODE).parent)+':'+os.environ['PATH'],TMPDIR=str(temp),PYTHONDONTWRITEBYTECODE='1')
    rows=[]
    for c in [None,*CASES]:
        name=c['id'] if c else 'candidate'; folder=out/name; folder.mkdir()
        if c: apply(c)
        try:
            for i,cmd in enumerate(COMMANDS):
                dest=folder/str(i+1); dest.mkdir()
                result=run(cmd,dest,env); result.update(case=name); rows.append(result)
                print(name,i+1,'exit',result['exit'],flush=True)
        finally:
            if c: restore(c)
    save(out/'summary.json',dict(executor='reviewer',results=rows,restored=pristine(),temporary_remaining=[str(p) for p in temp.iterdir()]))
    temp.rmdir()

def external():
    out=HERE/'external-01'; out.mkdir()
    env=dict(os.environ,PATH=str(pathlib.Path(NODE).parent)+':'+os.environ['PATH'],PYTHONDONTWRITEBYTECODE='1')
    for key in ['ELECTRON_RUN_AS_NODE','ELECTRON_OVERRIDE_DIST_PATH','npm_config_cache','electron_config_cache']: env.pop(key,None)
    own=pathlib.Path(tempfile.mkdtemp(prefix='t249-r142-',dir='/private/tmp'))
    env.update(TMPDIR=str(own),TMP=str(own),TEMP=str(own),ENCHANTED_HC_CACHE_DIR='/Users/luckye/Documents/Code/hc-cache')
    modules=ROOT/'workbench/node_modules'; copied=False; clean=False; rows=[]
    def processes():
        return sorted(' '.join(s.split()) for s in subprocess.check_output(['/bin/ps','-axo','pid=,lstart=,command='],text=True).splitlines() if '/Applications/Enchanted.app/' in s)
    before=processes(); save(out/'before.json',before)
    try:
        assert pristine()
        if not modules.exists():
            copied=True
            subprocess.run(['/usr/bin/ditto','/Users/luckye/Documents/Code/a2a/workbench/node_modules',str(modules)],check=True)
        for c in [None,CASES[0],CASES[2],CASES[3]]:
            name=c['id'] if c else 'candidate'; folder=out/name; folder.mkdir()
            if c: apply(c)
            try:
                argv=['/usr/bin/python3','workbench/tests/test_t249_git_graph_e2e.py','--output',str(folder/'window'),'--shots',str(folder/'shots')]
                result=run(argv,folder,env)
                report_path=folder/'window/run.json'
                r=json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
                clean=r.get('cleanup')=='PASS' and r.get('fixture_removed') is True
                failures=[x['what'] for x in r.get('checks',[]) if x.get('ok') is False]
                business=(result['exit']==0 and r.get('status')=='PASS') if c is None else (result['exit']!=0 and r.get('status')=='FAIL' and c['window_failure'] in failures)
                ok=business and clean and r.get('user_core_unchanged') is True
                rows.append(dict(case=name,**result,status=r.get('status','INCOMPLETE'),failures=failures,expected=c.get('window_failure') if c else 'PASS',ok=ok,cleanup=clean))
                save(folder/'assessment.json',rows[-1]); print(json.dumps(rows[-1],ensure_ascii=False),flush=True)
            finally:
                if c: restore(c)
            if not ok: break
    finally:
        after=processes(); save(out/'after.json',after)
        save(out/'summary.json',dict(executor='controller outside native sandbox',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
          candidate='63304e0fcb3510d9cf4b1cbea5c3064fbb8286dd',verification_merge='92163e7d850df1d093a607144c6dfd7d256f53e1',
          results=rows,source_restored=pristine(),formal_app_unchanged=before==after,owned_tmp=str(own),cleanup_confirmed=clean,
          status='PASS' if len(rows)==4 and all(r['ok'] for r in rows) and before==after and pristine() else 'INCOMPLETE'))
        if clean:
            # Only our just-created cache and dependency copy; never a shared checkout.
            if copied: shutil.rmtree(modules)
            sizes=[p.stat().st_size for p in own.rglob('*') if p.is_file() and not p.is_symlink()]
            save(out/'cleanup.json',dict(path=str(own),files=len(sizes),bytes=sum(sizes),dependencies_removed=copied))
            shutil.rmtree(own)
        print('Evidence:',out,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['prepare','local','external']); a=p.parse_args()
    {'prepare':prepare,'local':local,'external':external}[a.mode]()
