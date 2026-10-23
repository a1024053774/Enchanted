#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t139-t143 || exit 2
run_dir=$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-139-T-143/outside-02-XXXXXXXX") || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-t139-pycache
test_file=workbench/tests/test_t139_t143_views_perf_e2e.py
control=feea09ebc9156296bc2c95ec632169e876603ac3
failed=0

node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$run_dir/selection.json" > "$run_dir/selection.log" 2>&1 || failed=1
node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$run_dir/layout-store.json" > "$run_dir/layout-store.log" 2>&1 || failed=1
node workbench/tests/test_t139_terminal_catalog.mjs "$run_dir/terminal-catalog.json" > "$run_dir/terminal-catalog.log" 2>&1 || failed=1

# Identical fixture and measurement v2. Initial rAF establishes the timestamp;
# all 120 measured intervals are between frames, never from performance.now().
python3 "$test_file" --revision ebbae7bd0 --summary "$run_dir/baseline-v2.json" > "$run_dir/baseline-v2.log" 2>&1
python3 "$test_file" --revision "$control" --summary "$run_dir/t139-control.json" > "$run_dir/t139-control.log" 2>&1 || failed=1
python3 "$test_file" --revision "$control" --experiment screen-reader-off --summary "$run_dir/screen-reader-off.json" > "$run_dir/screen-reader-off.log" 2>&1 || failed=1
python3 "$test_file" --revision "$control" --experiment webgl --summary "$run_dir/webgl.json" > "$run_dir/webgl.log" 2>&1 || failed=1

# Current code, one variable: retain zero vs four inactive terminals.
# Both runs use screenReaderMode=false and the same sidebar/permission paths.
python3 "$test_file" --experiment destroy-on-switch --summary "$run_dir/without-retention.json" > "$run_dir/without-retention.log" 2>&1 || failed=1
python3 "$test_file" --summary "$run_dir/candidate.json" > "$run_dir/candidate.log" 2>&1 || failed=1

for mutant in task-includes-project-terminal duplicate-replay inactive-input; do
  python3 "$test_file" --mutant "$mutant" --summary "$run_dir/mutant-$mutant.json" > "$run_dir/mutant-$mutant.log" 2>&1
done

python3 workbench/tests/test_t107_live_sidebar_e2e.py --summary "$run_dir/t107.json" > "$run_dir/t107.log" 2>&1 || failed=1
python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary "$run_dir/t133-t107.json" > "$run_dir/t133-t107.log" 2>&1 || failed=1

# User's revised T-091 contract: preserve the existing failure, with the same
# protected oracle against both the original source and this candidate.
baseline_source=$(python3 - <<'PY'
import sys,tempfile
from pathlib import Path
sys.path.insert(0,'workbench/tests')
from scripted_claude import source_tree
print(source_tree(Path(tempfile.mkdtemp(prefix='t139-t091-outside-',dir='/private/tmp')),revision='ebbae7bd0'))
PY
)
if (( $? != 0 )); then exit 2; fi
print -r -- "$baseline_source" > "$run_dir/t091-baseline-source.txt"
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$run_dir/t091-baseline.json" --source "$baseline_source" > "$run_dir/t091-baseline.log" 2>&1
node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs "$run_dir/t091-candidate.json" > "$run_dir/t091-candidate.log" 2>&1

python3 - "$run_dir" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); results={}; problems=[]
for name in ('baseline-v2','t139-control','screen-reader-off','webgl','without-retention','candidate',
             'mutant-task-includes-project-terminal','mutant-duplicate-replay','mutant-inactive-input'):
    r=json.loads((p/(name+'.json')).read_text(encoding='utf-8'));m=r.get('metrics',{})
    results[name]={k:r.get(k) for k in ('status','error','failures','code_version','measurement_version')}
    results[name].update({k:m.get(k) for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median')})
    if r.get('measurement_version')!=2 or not m.get('scroll_fps_median') or not m.get('switch_ms_median'):
        problems.append(name+': missing valid metrics')
    required={'baseline-v2':'task_A_only_its_agents','mutant-task-includes-project-terminal':'task_A_only_its_agents',
              'mutant-duplicate-replay':'numbered_output_once_before_switch','mutant-inactive-input':'inactive_input_rejected'}.get(name)
    if required:
        if r['status']!='NO_GO' or required not in r['failures']: problems.append(name+': expected business red not obtained')
    elif r['status']!='PASS': problems.append(name+': not PASS')
a=json.loads((p/'t091-baseline.json').read_text());b=json.loads((p/'t091-candidate.json').read_text())
same=a['status']==b['status']=='INCOMPLETE' and a.get('error')==b.get('error') and a.get('checks')==b.get('checks')
results['t091']={'status':'PASS' if same else 'INCOMPLETE','disposition':'known preexisting failure unchanged' if same else 'failure changed; investigate',
                 'baseline_error':a.get('error'),'candidate_error':b.get('error')}
if not same: problems.append('T-091 changed failure')
for name in ('selection','layout-store','terminal-catalog','t107','t133-t107'):
    r=json.loads((p/(name+'.json')).read_text());results[name]={'status':r['status'],'error':r.get('error')}
    if r['status']!='PASS':problems.append(name+': not PASS')
summary={'status':'INCOMPLETE','run_checks':'PASS' if not problems else 'NO_GO','results':results,'problems':problems,
         'next':'Worker must choose WebGL/retention from measured comparisons, remove non-improvements, and update RESULTS.md before final acceptance.'}
(p/'COMPARISON.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
raise SystemExit(1 if problems else 0)
PY
if (( $? != 0 )); then failed=1; fi
print "结果目录：$run_dir"
print '请回传 COMPARISON.json 和结果目录；尚未决定 WebGL/窗格保留的最终保留项。'
exit "$failed"
