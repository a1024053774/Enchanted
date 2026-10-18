#!/bin/bash
# T-094 独立审查重放。仅显式 Herdr 替身与 codex --version；不启动真实 pane，不发提示。
# 当前审查的沙箱内检查与结果见 independent-review-01.md；本脚本供主控独立重放。
set -u
set -o pipefail
review_out=$(mktemp -d /tmp/t094-review-outside-01.XXXXXX) || exit 1
printf '段名：建立隔离目录\n输出目录：%s\n' "$review_out"
mkdir "$review_out/version-home" || exit 1
export CODEX_HOME="$review_out/version-home"
export PYTHONDONTWRITEBYTECODE=1
cat > "$review_out/run_review.py" <<'REVIEW_PY'
#!/usr/bin/env python3
"""独立审查：冻结副本、真实命令入口和三个单处变异；不连接真实 Herdr。"""
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import time

OUT = Path(__file__).resolve().parent
SOURCE = Path('/Users/luckye/Documents/Code/a2a-wt-t094')
SHA = '3096bef9a2f0b3b0db739a51ad662dad3f0bdd83'
BASE = '61786370428c3ec5f894ea60acccf2695d54c2dc'
ENV = {k:v for k,v in os.environ.items() if not k.startswith(('A2A_', 'GIT_CONFIG_'))}
ENV['PYTHONDONTWRITEBYTECODE'] = '1'

def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], env=ENV, timeout=30)

def snapshot(name, revision=SHA):
    path = OUT/name
    path.mkdir()
    data = git('archive', revision, 'scripts', 'acceptance', '.project-map/roles/worker.md')
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(path)
    # 仅用于启动记录中的版本读取；独立本地 metadata，不登记共享 worktree，不提交。
    subprocess.run(['git', '-c', 'init.templateDir=', 'init', '-q', str(path)], env=ENV, check=True, timeout=15)
    common = Path(git('rev-parse', '--git-common-dir').decode().strip())
    if not common.is_absolute():
        common = (SOURCE/common).resolve()
    (path/'.git/objects/info/alternates').write_text(str(common/'objects')+'\n', encoding='utf-8')
    (path/'.git/HEAD').write_text(revision+'\n', encoding='utf-8')
    assert subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], env=ENV).decode().strip() == revision
    return path

def run(label, argv, expected, timeout=200):
    dest=OUT/label
    dest.mkdir()
    began=time.monotonic()
    with (dest/'stdout.txt').open('x',encoding='utf-8') as stdout, (dest/'stderr.txt').open('x',encoding='utf-8') as stderr:
        process=subprocess.Popen([str(a) for a in argv], cwd=OUT, env=ENV, stdout=stdout, stderr=stderr, start_new_session=True)
        expired=False
        try:
            rc=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            expired=True
            os.killpg(process.pid,signal.SIGKILL)
            rc=process.wait()
    row=dict(label=label,argv=[str(a) for a in argv],exit_code=rc,expected=expected,timeout=expired,seconds=time.monotonic()-began,output=str(dest))
    (dest/'run.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(row,ensure_ascii=False),flush=True)
    return rc==expected and not expired

phase=sys.argv[1]
if phase=='candidate':
    candidate=snapshot('candidate')
    ok=run('candidate-contract',[sys.executable,'-B',candidate/'scripts/test_launch_worker_failure.py','--report',OUT/'candidate-contract.json','-v'],0,110)
    if ok:
        ok=run('candidate-shell',[sys.executable,'-B',candidate/'acceptance/test_launcher_shell_ready_e2e.py','--artifacts',OUT/'candidate-shell-artifacts'],0,140)
    if ok:
        ok=run('candidate-trace',[sys.executable,'-B',candidate/'acceptance/test_herdr_traceability_e2e.py','--artifacts',OUT/'candidate-trace-artifacts'],0,140)
    (OUT/'candidate-status.json').write_text(json.dumps(dict(passed=ok,candidate=SHA))+'\n',encoding='utf-8')
    sys.exit(0 if ok else 1)
elif phase=='mutants':
    assert json.loads((OUT/'candidate-status.json').read_text())['passed'], '先确认候选通过'
    mutations=[
      ('skip-stable','if sampled - stable_since >= SHELL_STABLE_SECONDS:', 'if True:', 'shell','test_delayed_shell_then_commit'),
      ('drop-timeout-argv','last_shell_info, ensure_ascii=False)', 'None, ensure_ascii=False)', 'shell','test_child_foreground_times_out_with_argv'),
      ('half-as-success','failure = dict(row, phase="failed"', 'failure = dict(row, phase="started"', 'contract','test_process_started_without_registration_is_distinct')]
    all_ok=True
    for label,old,new,suite,case in mutations:
        mutant=snapshot('mutant-'+label)
        launcher=mutant/'scripts/launch-worker'
        text=launcher.read_text(encoding='utf-8')
        assert text.count(old)==1,(label,text.count(old))
        launcher.write_text(text.replace(old,new),encoding='utf-8')
        (mutant/'mutation.json').write_text(json.dumps(dict(old=old,new=new,case=case),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if suite=='shell':
            argv=[sys.executable,'-B',OUT/'candidate/acceptance/test_launcher_shell_ready_e2e.py','--launcher',launcher,'--artifacts',OUT/(label+'-artifacts'),'--case',case]
        else:
            argv=[sys.executable,'-B',OUT/'candidate/scripts/test_launch_worker_failure.py','--launcher',launcher,'--report',OUT/(label+'.json'),'LaunchFailure.'+case,'-v']
        all_ok=run('reject-'+label,argv,1,55) and all_ok
    sys.exit(0 if all_ok else 1)
else:
    raise ValueError(phase)
REVIEW_PY
printf '段名：建立隔离目录\n退出码：0\n输出目录：%s\n' "$review_out"
for review_stage in candidate mutants; do
  printf '\n段名：%s\n输出目录：%s\n' "$review_stage" "$review_out"
  python3 -B "$review_out/run_review.py" "$review_stage" 2>&1 | tee "$review_out/$review_stage.log"
  review_rc=${PIPESTATUS[0]}
  printf '段名：%s\n退出码：%s\n输出目录：%s\n' "$review_stage" "$review_rc" "$review_out"
  if [ "$review_rc" -ne 0 ]; then
    exit "$review_rc"
  fi
done
printf '\n段名：完成\n退出码：0\n输出目录：%s\n' "$review_out"
