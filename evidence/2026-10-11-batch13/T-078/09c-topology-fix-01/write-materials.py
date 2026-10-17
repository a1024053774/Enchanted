"""Write unsigned probe material from an actual committed tool revision; no launch."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import subprocess

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
HERE=Path(__file__).resolve().parent;OUT=BASE/'09c-topology-probe-materials-01';RUN=BASE/'09c-topology-probe-run-01'


def text(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(value)


def save(path,value):text(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def command(argv):return shlex.join(list(map(str,argv)))+'\n'


def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);a=p.parse_args()
    actual=subprocess.check_output(['git','rev-parse',a.revision],cwd=SOURCE,text=True).strip();assert actual==a.revision
    subprocess.run(['git','merge-base','--is-ancestor',actual,'HEAD'],cwd=SOURCE,check=True)
    assert not subprocess.check_output(['git','diff',actual,'--','workbench','acceptance','scripts'],cwd=SOURCE)
    assert not RUN.exists() and not OUT.exists()
    tests=SOURCE/'workbench/tests';entry=tests/'t078_topology_probe.py';p1=RUN/'ideation-p1'
    for path in [entry,tests/'t078_process_tree.py',tests/'test_t078_09c_coordinator_chain.py',
                 tests/'test_t078_topology_probe_entry.py',BASE/'prepare-a14.py',BASE/'run-09b-stage-b.py']:
        assert path.is_file();ast.parse(path.read_text(encoding='utf-8'))
    OUT.mkdir()
    save(OUT/'SOURCE.json',{'status':'PASS','source_revision':actual,'business_source_unchanged_since':'7a6edbff87df85077b3a05d38f3cfd5654cde9c1',
        'scope':'test tools only; no process class has been allowed','real_probe_execution':'INCOMPLETE','new_parity_rehearsal':'INCOMPLETE'})
    save(OUT/'setup-approval.json',{'approved_by':None,'approval_ref':None,'source_revision':actual,
        'allow_role_cli_spawn':False,'max_role_sessions':1,'real_model_turns':0,'fake_API_processes':2,'daemon':1,
        'target':'new owned deterministic receiver only','scope':'main #365 isolated topology setup; role B1 is separately signed; no attempt-2 input or stop'})
    lines=['# 逐阶段由主控执行；签字字段保持空。不得整份无条件串行执行。',
           '# 1. 主控签本目录setup-approval；建新root/API/daemon/确定性目标，尚不启动角色CLI。',
           command(['python3','-B',entry,'--mode','setup','--approval',OUT/'setup-approval.json','--output',RUN]),
           '# 2. 审签新生成的ideation-p1/stage-b-approval.json；按B1-COMMANDS两行先dry-run再real。',
           '# 文件只列命令不自动签。B1/首启依现有标准工具；一次只运行一个批准动作。',
           '# 3. 真实B1后执行BIND-LAUNCH.txt；随后逐屏读取并各自签六键onboarding/*.json。',
           '# s7的key purpose为onboarding-notice；B1 screen_plan仍为security-notice+原文。',
           '# 首读不符用新-02只读；发生output_total_changed不重发已written的键。',
           '# 4. 主控核对s13完整空提示符/manual、0 POST后，拍idle的10秒连续ps。',
           command(['python3','-B',entry,'--mode','idle','--probe',RUN,'--output',RUN/'idle-01']),
           '# 5. 从turn-approval-template另存turn-approval.json，由主控签：1根/1POST、许可Enter=0。',
           '# 此调用只初始release+派发一个批准的模拟用户stop请求；API先保持该POST未返回，采样15秒。',
           '# 然后只发布这一条HTTP响应的阶段批准，让Claude到I_SEND_STOP许可屏，再采样15秒；不按许可Enter。',
           command(['python3','-B',entry,'--mode','turn','--probe',RUN,'--approval',RUN/'turn-approval.json','--output',RUN/'turn-01']),
           '# 6. 主控审完整许可原屏/PermissionRequest与三时点index、各summary和逐样本ps。',
           '# 捕获成功不等于进程合法；partial/vanished不得猜argv。取证后保留root，按原七进程单角色owner-bound流程另批回收。',
           '# 本材料不提供直接给Claude/未知子进程的信号命令、不删除root。']
    text(OUT/'PROBE-COMMANDS.txt','\n'.join(lines)+'\n')
    text(OUT/'REHEARSAL-COMMAND.txt','# 先审probe归属；未知子进程仍拒绝。此命令供应商角色为确定性PTY，不是真实Claude。\n'+command([
        'python3','-B',tests/'test_t078_09c_coordinator_chain.py','--signature-ref',
        'REHEARSAL ONLY main #365 full owner/topology/archive parity','--output',BASE/'09c-topology-parity-rehearsal-01']))
    rows=[]
    for suite,script,extra in [('pending','run-pending-checks.py',['--suite','local']),
                               ('startup-domain','run-startup-receipt-checks.py',['--suite','domain']),
                               ('startup-entry','run-startup-receipt-checks.py',['--suite','entry']),
                               ('worker','run-pending-checks.py',['--suite','runtime'])]:
        rows.append(command(['python3','-B',BASE/script,*extra,'--output',BASE/('09c-topology-regressions-'+suite+'-01')]))
    text(OUT/'REGRESSION-COMMANDS.txt','# 四段顺序执行，首败即停不重试；全新输出。\nset -e\n'+'\n'.join(rows))
    save(HERE/'material-generation.json',{'status':'PASS','source_revision':actual,'output':str(OUT),'scene_starts':0,
        'future_inputs':[str(RUN/'stage-a/readiness.json'),str(p1/'stage-b-approval.json'),str(p1/'launch-binding.json'),str(RUN/'turn-approval.json')],
        'output_existence_checked':True,'entry_paths_checked':True})
    print(json.dumps({'status':'PASS','source_revision':actual,'output':str(OUT),'scene_starts':0}))


if __name__=='__main__':main()
