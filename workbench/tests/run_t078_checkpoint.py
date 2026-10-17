#!/usr/bin/env python3
"""Run the approved first checkpoint outside the worker sandbox, once per label."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
EVIDENCE = ROOT / 'evidence/2026-10-11-batch13/T-078'
BASELINE = '14b57d22a84bcaebfa91c5051b9909b53a570fac'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', default='outside-green-01')
    parser.add_argument('--phase', choices=['red','green'], default='green')
    args = parser.parse_args()
    if not args.label or args.label in ('.','..') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.label):
        parser.error('label must be a single new evidence directory name')
    output = EVIDENCE / args.label
    output.mkdir(exist_ok=False)
    record = {'status':'INCOMPLETE','stage':'P1 and input contracts','phase':args.phase,'commands':[],
              'real_model_turns':0,'claude_started':False,'claude_fixture_started':False,
              'artifact':str(output),'argv':sys.argv}

    def save():
        (output / 'checkpoint.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    env = {key:value for key,value in os.environ.items()
           if not key.startswith(('A2A_', 'GIT_', 'CODEX_', 'CLAUDE_', 'ANTHROPIC_'))}
    env.pop('ELECTRON_RUN_AS_NODE',None)

    def run(argv, name, timeout):
        argv = [str(value) for value in argv]
        entry = {'argv':argv,'cwd':str(ROOT),'stdout':str(output/(name+'.stdout.txt')),
                 'stderr':str(output/(name+'.stderr.txt')),'timeout':timeout}
        record['commands'].append(entry); save()
        with Path(entry['stdout']).open('xb') as out, Path(entry['stderr']).open('xb') as err:
            child = subprocess.Popen(argv,cwd=ROOT,env=env,stdout=out,stderr=err,start_new_session=True)
            entry['pid']=child.pid; entry['started_at']=time.time(); save()
            try:
                entry['exit_code']=child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                entry['timed_out']=True; save()
                # Only this runner's own child process group; never other panes.
                if child.poll() is None:
                    if os.getpgid(child.pid) != child.pid:
                        raise RuntimeError('Own process group changed; inspect before cleanup')
                    entry['cleanup_signal']='SIGKILL to owned process group'
                    os.killpg(child.pid,signal.SIGKILL)
                entry['exit_code']=child.wait(timeout=10); save()
                raise RuntimeError(name+' exceeded its deadline; no automatic replay')
            finally:
                entry['ended_at']=time.time(); save()
        return entry

    try:
        if not os.path.ismount('/Volumes/WD-Elements'):
            raise RuntimeError('外置盘未挂载；不安装依赖、不回退')
        head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
        diff = subprocess.check_output(['git','diff','--','workbench/src','workbench/app','workbench/hooks'],cwd=ROOT,text=True)
        record.update(source_revision=head,branch=branch,product_diff=diff)
        if branch != 'exec/t078' or (args.phase == 'red' and (head != BASELINE or diff)):
            raise RuntimeError('First red checkpoint requires untouched product at the recorded exec/t078 baseline')
        files = [*sorted((ROOT/'workbench/src').rglob('*.ts')),
                 *sorted((ROOT/'workbench/app').glob('*')),
                 ROOT/'workbench/package.json',ROOT/'workbench/package-lock.json']
        for name in ['run_t078_checkpoint.py','test_t078_input_entry.py','t078_terminal_receiver.py','inspect_t078_p1.py',
                     'probe_t078_input_origin.mjs','t078_input_origin.html','electron_driver.mjs',
                     'electron_client.py','command_evidence.py']:
            files.append(ROOT/'workbench/tests'/name)
        with tarfile.open(output/'sources.tar.gz','x:gz') as archive:
            for path in files:
                if path.is_file():
                    archive.add(path,arcname=str(path.relative_to(ROOT)))
        record['source_paths']=[str(path.relative_to(ROOT)) for path in files if path.is_file()]
        relative = (ROOT/'workbench/node_modules/electron/path.txt').read_text(encoding='utf-8').strip()
        electron = (ROOT/'workbench/node_modules/electron/dist'/relative).resolve(strict=True)
        probe = run([electron,ROOT/'workbench/tests/probe_t078_input_origin.mjs',output/'p1'],'p1',90)
        if probe['exit_code'] != 0:
            raise RuntimeError('P1 未通过；保留现场，停止，不继续产品红态')
        p1 = json.loads((output/'p1/results.json').read_text(encoding='utf-8'))
        if p1['status'] != 'PASS':
            raise RuntimeError('P1 缺少通过结果')
        entry_name='entry-'+args.phase
        entry = run([sys.executable,'-B',ROOT/'workbench/tests/test_t078_input_entry.py',
                   '--source',ROOT,'--output',output/entry_name],entry_name,300)
        facts = json.loads((output/entry_name/'results.json').read_text(encoding='utf-8'))
        expected_names = {'window_input_reaches_pty','user_input_and_intervention','empty_callback_is_observation_only',
                          'anonymous_role_spoof_rejected_before_append'}
        expected_status='INCOMPLETE' if args.phase == 'red' else 'PASS'
        if (entry['exit_code'] != (1 if args.phase == 'red' else 0) or not facts.get('setup_complete') or not facts.get('cleanup_complete')
                or facts.get('setup_or_probe_error') or facts.get('cleanup_error')
                or {row['name'] for row in facts['checks']} != expected_names
                or any(row['status'] != expected_status or row['kind'] != 'contract' for row in facts['checks'])):
            raise RuntimeError('结果不符合本检查点的四项合同；保留现场交主控判定')
        record[args.phase+'_evidence_confirmed']=True
        record['checkpoint_status']='PASS'
        record['next']='本检查点仅覆盖输入与凭据的四项合同；其余行为、反例与回归仍待完成。'
        oversized = [str(path.relative_to(output)) for path in output.rglob('*') if path.is_file() and path.stat().st_size > 5*1024*1024]
        record['over_5mb']=oversized
        if oversized:
            raise RuntimeError('证据含大于 5 MB 文件；不得直接提交，先归档处理')
        save()
        print(json.dumps({'status':record['status'],'checkpoint_status':'PASS',args.phase+'_evidence_confirmed':True,'output':str(output)},ensure_ascii=False))
        return 0
    except Exception as error:
        record['error']=repr(error); save()
        print(json.dumps({'status':'INCOMPLETE','error':repr(error),'output':str(output)},ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
