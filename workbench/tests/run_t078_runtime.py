#!/usr/bin/env python3
"""Controller-run runtime checkpoint. No vendor CLI or Claude fixture runs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

from command_evidence import CommandLog

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=ROOT/'evidence/2026-10-11-batch13/T-078'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--label',default='outside-runtime-red-01')
    parser.add_argument('--phase',choices=['red','green'],default='red')
    parser.add_argument('--scope',choices=['runtime','input-failures','worker-inbox'],default='runtime')
    parser.add_argument('--rule-mutants',action='store_true')
    args=parser.parse_args()
    if args.rule_mutants and (args.scope!='worker-inbox' or args.phase!='green'):
        parser.error('Rule counterexamples require a green worker-inbox run first')
    if not args.label or args.label in ('.','..') or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for char in args.label):
        parser.error('A new single-directory label is required')
    out=BASE/args.label;out.mkdir(exist_ok=False)
    env={key:value for key,value in os.environ.items() if not key.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
    log=CommandLog(out)
    red_contracts={
        'runtime':['window_user_release_available'],
        'input-failures':['composition_holds_injection','request_id_reuse_is_not_written','binary_mouse_bytes_and_action'],
        'worker-inbox':['worker_client_queues_inbox_commands','worker_issue_records_real_sender','worker_assign_spoof_denied',
            'worker_list_uses_real_scope','worker_ack_is_owned_and_idempotent','worker_ready_is_role_denied',
            'worker_foreign_ack_is_denied','worker_stop_receipts_are_delivered_once','revoked_worker_inbox_is_rejected'],
    }
    expected_failures=red_contracts[args.scope] if args.phase=='red' else []
    record={'status':'INCOMPLETE','checkpoint_status':'INCOMPLETE','task':'T-078-1','ready_rev':1,
            'worker':'s13-t078','attempt':None,'session':None,'fence':None,'argv':sys.argv,
            'phase':args.phase,'scope':args.scope,'real_model_turns':0,'claude_started':False,'claude_fixture_started':False,
            'expected_contract_failure':expected_failures,
            'limitations':['逻辑入站 inbox 行由测试预置，不证明主控发送凭据。',
                           '原生接收器只生成最小 Codex 形状日志，不是供应商 CLI 验收。',
                           '真实两分钟与主控凭据路径、Claude 启动、多窗格及最终回归仍待完成。']}

    def save():
        (out/'checkpoint.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def run(argv,name,expected=0,timeout=60):
        command=log.run(argv,cwd=ROOT,env=env,timeout=timeout,
                        stdout_file=out/(name+'.stdout.txt'),stderr_file=out/(name+'.stderr.txt'))
        if command.returncode!=expected:
            raise RuntimeError({'unexpected_exit':command.evidence,'expected':expected})

    try:
        if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External volume is not mounted; no fallback')
        record['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='exec/t078':
            raise RuntimeError('Wrong worktree branch')
        record['diff']=subprocess.check_output(['git','diff','--','workbench'],cwd=ROOT,text=True)
        names=['run_t078_runtime.py','test_t078_input_entry.py','t078_runtime_scenario.py','t078_input_failures.py','t078_native_receiver.c',
               'test_t078_pane_runtime.ts','test_t078_inbox_domain.ts','test_t078_controller_plan.ts',
               't078_worker_inbox_client.mjs','t078_worker_inbox_scenario.py','t078_worker_mutants.py','archive_t078_evidence.py',
               'command_evidence.py','electron_client.py','electron_driver.mjs']
        files=[*sorted((ROOT/'workbench/src').rglob('*.ts')),*sorted((ROOT/'workbench/app').glob('*')),
               ROOT/'workbench/bin/inbox',ROOT/'workbench/package.json',ROOT/'workbench/package-lock.json',
               *[ROOT/'workbench/tests'/name for name in names],BASE/'outside-sandbox.sh']
        with tarfile.open(out/'sources.tar.gz','x:gz') as archive:
            for path in files:
                if path.is_file():archive.add(path,arcname=str(path.relative_to(ROOT)))
        frozen={path:path.read_bytes() for path in files if path.is_file()}
        save()
        # Preserve original large bytes externally before deleting local copies.
        if args.scope=='runtime':
            run([sys.executable,'-B',ROOT/'workbench/tests/archive_t078_evidence.py','--labels','outside-inbox-01','outside-inbox-02'],'archive-prior',timeout=120)
            run(['node',ROOT/'workbench/tests/test_t078_inbox_domain.ts',out/'domain'],'domain')
            run(['node',ROOT/'workbench/tests/test_t078_pane_runtime.ts',out/'pane-state'],'pane-state')
        flag={'runtime':'--runtime-probe','input-failures':'--input-failures','worker-inbox':'--worker-inbox'}[args.scope]
        run([sys.executable,'-B',ROOT/'workbench/tests/test_t078_input_entry.py','--source',ROOT,
             '--output',out/'runtime-entry',flag],
            'runtime-entry',expected=1 if args.phase=='red' else 0,timeout=240)
        observed=json.loads((out/'runtime-entry/results.json').read_text(encoding='utf-8'))
        failures=[item['name'] for item in observed['checks'] if item['status']!='PASS']
        expected_count={'runtime':12,'input-failures':11,'worker-inbox':14}[args.scope]
        if len(observed['checks'])!=expected_count or failures!=record['expected_contract_failure'] or not observed['setup_complete'] or not observed['cleanup_complete']:
            raise RuntimeError({'unexpected_contract_result':failures,'checks':len(observed['checks']),
                                'setup':observed['setup_complete'],'cleanup':observed['cleanup_complete']})
        if observed.get('setup_or_probe_error') or observed.get('cleanup_error'):
            raise RuntimeError('Probe or cleanup error is not product red evidence')
        record['runtime_checks']=[{'name':item['name'],'status':item['status']} for item in observed['checks']]
        record['red_evidence_confirmed' if args.phase=='red' else 'green_evidence_confirmed']=True
        if args.rule_mutants:
            from t078_worker_mutants import exercise
            build=Path(json.loads((out/'runtime-entry/build.json').read_text(encoding='utf-8'))['out'])
            record['worker_rule_counterexamples']=exercise(ROOT,out,build,run)
        changed=[str(path.relative_to(ROOT)) for path,data in frozen.items() if path.read_bytes()!=data]
        if changed:raise RuntimeError('Source changed during checkpoint: '+str(changed))
        run([sys.executable,'-B',ROOT/'workbench/tests/archive_t078_evidence.py','--labels',args.label],'archive-current',timeout=120)
        record['checkpoint_status']='PASS';save()
        print(json.dumps({'status':'INCOMPLETE','checkpoint_status':'PASS','phase':args.phase,'output':str(out)},ensure_ascii=False))
        return 0
    except Exception as error:
        record['error']=repr(error);save()
        print(json.dumps({'status':'INCOMPLETE','error':repr(error),'output':str(out)},ensure_ascii=False))
        return 1


if __name__=='__main__':raise SystemExit(main())
