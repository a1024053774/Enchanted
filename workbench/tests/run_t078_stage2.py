#!/usr/bin/env python3
"""Controller-run inbox checkpoint and original 8/9/18 regression suites."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

ROOT=Path('/Users/luckye/Documents/Code/a2a-wt-t078')
BASE=ROOT/'evidence/2026-10-11-batch13/T-078'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--label',default='outside-inbox-02')
    parser.add_argument('--final',action='store_true',help='Validate a committed candidate after rebase, with each suite run once')
    parser.add_argument('--identity-file',type=Path)
    args=parser.parse_args()
    if not args.label or args.label in ('.','..') or any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for char in args.label):
        parser.error('A new single-directory label is required')
    out=BASE/args.label;out.mkdir(exist_ok=False)
    record={'status':'INCOMPLETE','checkpoint':'inbox-domain-client-and-regression','argv':sys.argv,'commands':[],
            'real_model_turns':0,'claude_started':False,'claude_fixture_started':False}
    env={key:value for key,value in os.environ.items() if not key.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}

    def save():
        (out/'checkpoint.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def run(argv,name,timeout,expected=0):
        argv=[str(value) for value in argv]
        entry={'argv':argv,'cwd':str(ROOT),'timeout':timeout,'stdout':str(out/(name+'.stdout.txt')),'stderr':str(out/(name+'.stderr.txt'))}
        record['commands'].append(entry);save()
        with Path(entry['stdout']).open('xb') as stdout,Path(entry['stderr']).open('xb') as stderr:
            child=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=stdout,stderr=stderr,start_new_session=True)
            entry.update(pid=child.pid,started=time.time());save()
            try:
                entry['exit_code']=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                entry['timed_out']=True;save()
                if child.poll() is None:
                    if os.getpgid(child.pid)!=child.pid:raise RuntimeError('Own process group changed')
                    entry['cleanup_signal']='SIGKILL to owned child process group';os.killpg(child.pid,signal.SIGKILL)
                entry['exit_code']=child.wait(timeout=10)
                raise RuntimeError(name+' exceeded its deadline; inspect retained fixture, no retry')
            finally:
                entry['ended']=time.time();save()
        if entry['exit_code']!=expected:raise RuntimeError(name+' has an unexpected exit; stop for controller review')

    try:
        if not os.path.ismount('/Volumes/WD-Elements'):raise RuntimeError('External cache volume is not mounted')
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
        if branch!='exec/t078':raise RuntimeError('Wrong worker branch')
        record['head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if args.final:
            record['main']=subprocess.check_output(['git','rev-parse','main'],cwd=ROOT,text=True).strip()
            if subprocess.run(['git','merge-base','--is-ancestor','main','HEAD'],cwd=ROOT).returncode:
                raise RuntimeError('Rebase onto main before final verification')
            if subprocess.check_output(['git','status','--porcelain','--','workbench'],cwd=ROOT,text=True):
                raise RuntimeError('Commit the frozen workbench candidate before final verification')
        record['diff']=subprocess.check_output(['git','diff','--','workbench'],cwd=ROOT,text=True)
        assertion_diff=subprocess.check_output(['git','diff','--','acceptance/test_coop_e2e.py','acceptance/test_recovery_e2e.py','acceptance/test_run_e2e.py'],cwd=ROOT,text=True)
        if assertion_diff:raise RuntimeError('Business acceptance assertions changed')
        files=[*sorted((ROOT/'workbench/src').rglob('*.ts')),*sorted((ROOT/'workbench/app').glob('*')),
               ROOT/'workbench/bin/inbox',ROOT/'workbench/package.json',ROOT/'workbench/package-lock.json']
        for name in ['run_t078_stage2.py','test_t078_inbox_domain.ts','test_t078_inbox_entry.py','command_evidence.py',
                     'daemon_acceptance_adapter.py','daemon_acceptance_host.ts','run_daemon_acceptance.py',
                     'prepare_daemon_mutants.py','test_t078_pane_runtime.ts','test_t078_input_entry.py',
                     't078_runtime_scenario.py','t078_input_failures.py','t078_native_receiver.c',
                     'test_t078_controller_plan.ts','t078_worker_inbox_scenario.py','t078_worker_inbox_client.mjs','t078_worker_mutants.py',
                     'electron_driver.mjs','electron_client.py','archive_t078_evidence.py']:
            files.append(ROOT/'workbench/tests'/name)
        with tarfile.open(out/'sources.tar.gz','x:gz') as archive:
            for path in files:
                if path.is_file():archive.add(path,arcname=str(path.relative_to(ROOT)))
        identity={'task':'T-078-1','ready_rev':1,'worker':'s13-t078','attempt':None,'session':None,'fence':None,
                  'identity_note':'本卡未提供这些受管身份字段；不借用 T-075 的值。',
                  'real_codex_turns':0,'real_claude_turns':0}
        if args.identity_file:
            identity=json.loads(args.identity_file.read_text(encoding='utf-8'))
            if identity.get('task')!='T-078-1' or identity.get('worker')!='s13-t078':
                raise RuntimeError('Wrong evidence identity')
        identity_file=out/'evidence-identity.json'
        identity_file.write_text(json.dumps(identity,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        run(['node',ROOT/'workbench/tests/test_t078_inbox_domain.ts',out/'domain'],'domain',30)
        run([sys.executable,'-B',ROOT/'workbench/tests/test_t078_inbox_entry.py','--output',out/'inbox-entry'],'inbox-entry',150)
        if args.final:
            run(['node',ROOT/'workbench/tests/test_t078_pane_runtime.ts',out/'pane-state'],'pane-state',30)
            run(['node',ROOT/'workbench/tests/test_t078_controller_plan.ts',out/'controller-plan'],'controller-plan',30)
            frontend=None
            for name,flag in [('runtime-entry','--runtime-probe'),('input-entry','--input-failures'),('worker-inbox','--worker-inbox')]:
                run([sys.executable,'-B',ROOT/'workbench/tests/test_t078_input_entry.py','--source',ROOT,
                     '--output',out/name,flag,*(['--reuse-build',frontend] if frontend else [])],name,240)
                frontend=Path(json.loads((out/name/'build.json').read_text(encoding='utf-8'))['out'])
            from t078_worker_mutants import exercise
            record['worker_rule_counterexamples']=exercise(ROOT,out,frontend,run)
        suites=[('coop',8),('recovery',9),('run',18)]+([('cas',1)] if args.final else [])
        for suite,count in suites:
            target=out/suite
            run([sys.executable,'-B',ROOT/'workbench/tests/run_daemon_acceptance.py','--suite',suite,
                 '--label','t078-'+args.label+'-'+suite,'--output',target,'--identity-file',identity_file],suite,600)
            result=json.loads((target/'run.json').read_text(encoding='utf-8'))
            if result.get('status')!='PASS' or result.get('tests_run')!=count:
                raise RuntimeError(suite+' has an incomplete result or wrong test count')
        if args.final:
            from prepare_daemon_mutants import prepare
            from run_daemon_acceptance import business_mutant
            manifest_path=prepare(out/'mutants',task='T-078-1')
            manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
            record['counterexamples']={}
            for name,suite,method in [
                ('fence','coop','test_identity_gates_and_revocation_reject_old_verified_attempt'),
                ('cas','cas','test_external_write_between_read_and_cas_is_preserved'),
                ('lock','recovery','test_live_verify_excludes_verify_and_integrate')]:
                target=out/('mutant-'+name)
                run([sys.executable,'-B',ROOT/'workbench/tests/run_daemon_acceptance.py','--suite',suite,
                     '--test',method,'--mutant',name,'--mutant-manifest',manifest_path,
                     '--label','t078-'+args.label+'-'+name,'--output',target,'--identity-file',identity_file],
                    'mutant-'+name,180,expected=1)
                verdict=business_mutant(target,name,Path(manifest['mutants'][name]['core']))
                record['counterexamples'][name]=verdict;save()
                if not verdict['pass']:raise RuntimeError('Counterexample was not rejected by its business assertion: '+name)
            if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=record['head']:
                raise RuntimeError('Candidate changed during verification')
            run([sys.executable,'-B',ROOT/'workbench/tests/archive_t078_evidence.py','--labels',args.label],'archive-final',120)
        record['checkpoint_status']='PASS'
        record['regressions']={'coop':8,'recovery':9,'run':18}
        record['limitations']=['真实 Claude、主控凭据及三窗格仍未验证；独立审查另行记录；不是整票 PASS。'] if args.final else [
            '仍未验证主控 CLI、窗格唤醒、真实两分钟中断、最终变基候选；不是整票 PASS。']
        record['over_5mb']=[str(path.relative_to(out)) for path in out.rglob('*') if path.is_file() and path.stat().st_size>5*1024*1024]
        save()
        print(json.dumps({'status':'INCOMPLETE','checkpoint_status':'PASS','output':str(out),'over_5mb':record['over_5mb']},ensure_ascii=False))
        return 0
    except Exception as error:
        record['error']=repr(error);save()
        print(json.dumps({'status':'INCOMPLETE','error':repr(error),'output':str(out)},ensure_ascii=False))
        return 1


if __name__=='__main__':raise SystemExit(main())
