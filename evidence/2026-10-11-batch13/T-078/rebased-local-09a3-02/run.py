import json,os,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
OUT=ROOT/'evidence/2026-10-11-batch13/T-078/rebased-local-09a3-02'
OUT.mkdir()
sys.path.insert(0,str(ROOT/'workbench/tests'))
from command_evidence import CommandLog
log=CommandLog(OUT)
env={k:v for k,v in os.environ.items() if not k.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
cases=[('entry',['node','workbench/tests/test_t078_empty_declaration_entry.ts',str(OUT/'entry')]),
       ('epochs',['node','workbench/tests/test_t078_claude_epochs.ts',str(OUT/'epochs'),'evidence/2026-10-11-batch13/T-078/hook-payloads-08e']),
       ('pane-runtime',['node','workbench/tests/test_t078_pane_runtime.ts',str(OUT/'pane-runtime')]),
       ('controller-window',['node','workbench/tests/test_t078_controller_window.ts',str(OUT/'controller-window')]),
       ('window-binding',['node','workbench/tests/test_t078_window_binding.mjs',str(OUT/'window-binding')]),
       ('inbox-domain',['node','workbench/tests/test_t078_inbox_domain.ts',str(OUT/'inbox-domain')]),
       ('controller-plan',['node','workbench/tests/test_t078_controller_plan.ts',str(OUT/'controller-plan')]),
       ('signals',['node','workbench/tests/test_t078_claude_signals.ts',str(OUT/'signals')]),
       ('receipts',['python3','-B','workbench/tests/test_t078_window_receipts.py','--output',str(OUT/'receipts.json')]),
       ('two-turn-profile',['node','workbench/tests/test_t078_two_turn_profile.ts',str(OUT/'two-turn-profile')]),
       ('fake-handler',['python3','-B','workbench/tests/test_t078_fake_two_requests.py',str(OUT/'fake-handler')])]
with tarfile.open(OUT/'sources.tar.gz','x:gz') as archive:
    for p in [*sorted((ROOT/'workbench/src').rglob('*.ts')),*[p for p in (ROOT/'workbench/app').rglob('*') if p.is_file()],*[ROOT/next(a for a in c[1] if a.startswith('workbench/tests/')) for c in cases]]:
        archive.add(p,arcname=str(p.relative_to(ROOT)))
r={'status':'INCOMPLETE','head':head,'argv':sys.argv,'scope':'沙箱内域及真实 daemon/window/hook 入口；PTY/vendor 身份为夹具；无 vendor/API/UI/model 启动','checks':[],'real_model_turns':0}
def save(): (OUT/'result.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
save()
for name,argv in cases:
    try:
        p=log.run(argv,cwd=ROOT,env=env,timeout=45)
        check={'name':name,'exit_code':p.returncode,'status':'PASS' if p.returncode==0 else 'INCOMPLETE'}
    except Exception as e:check={'name':name,'status':'INCOMPLETE','error':repr(e)}
    r['checks'].append(check);save();print(json.dumps(check,ensure_ascii=False),flush=True)
r['status']='PASS' if all(c['status']=='PASS' for c in r['checks']) else 'INCOMPLETE';save()
raise SystemExit(0 if r['status']=='PASS' else 1)
