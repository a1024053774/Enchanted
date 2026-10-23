#!/bin/zsh
set -u
cd /Users/luckye/Documents/Code/a2a-wt-t139-t143 || exit 2
run_dir=$(mktemp -d "$PWD/evidence/2026-10-23-batch23/T-139-T-143/outside-05-XXXXXXXX") || exit 2
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-t139-pycache
test_file=workbench/tests/test_t139_t143_views_perf_e2e.py
failed=0

# Validate the actual meter expression before starting the expensive real run.
python3 workbench/tests/test_t143_output_meter.py --summary "$run_dir/output-meter-boundaries.json" > "$run_dir/output-meter-boundaries.log" 2>&1 || exit 1

# Prove one complete real Electron run produces valid metrics before the batch.
python3 "$test_file" --summary "$run_dir/candidate.json" > "$run_dir/candidate.log" 2>&1
python3 - "$run_dir/candidate.json" <<'PY_PREFLIGHT'
import json,math,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'));m=r.get('metrics',{})
valid=(r.get('status')=='PASS' and r.get('harness_version')==5 and r.get('measurement_version')==3 and
       all(isinstance(m.get(k),(int,float)) and math.isfinite(m[k]) and m[k]>0
           for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median','output_to_visible_ms')) and m.get('output_to_visible',{}).get('rendered') is True and m.get('output_to_visible',{}).get('visible') is True and
       len(m.get('scroll',[]))==3 and all(len(s.get('frames',[]))==120 and all(v>0 for v in s['frames']) for s in m['scroll']) and
       len(m.get('switch_ms',[]))==8)
out={'status':'PASS' if valid else 'INCOMPLETE','single_run_metrics':{k:m.get(k) for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median','output_to_visible_ms')},'error':r.get('error')}
Path(sys.argv[1]).with_name('PREFLIGHT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
raise SystemExit(0 if valid else 1)
PY_PREFLIGHT
if (( $? != 0 )); then
  print "单项自测未产出完整有效指标，停止批量运行。结果目录：$run_dir"
  exit 1
fi

node workbench/tests/test_t143_retained_focus.mjs "$run_dir/retained-focus.json" > "$run_dir/retained-focus.log" 2>&1 || failed=1
node --experimental-vm-modules workbench/tests/test_t139_selection.mjs "$run_dir/selection.json" > "$run_dir/selection.log" 2>&1 || failed=1
node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs "$run_dir/layout-store.json" > "$run_dir/layout-store.log" 2>&1 || failed=1
node workbench/tests/test_t139_terminal_catalog.mjs "$run_dir/terminal-catalog.json" > "$run_dir/terminal-catalog.log" 2>&1 || failed=1

# Same fixture and measurement v3: unchanged scroll/switch methods plus
# real 5000-line input-to-visible latency. Existing single-variable trials are
# preserved in RUN-OUTSIDE-04 evidence; rejected WebGL is not in this candidate.
python3 "$test_file" --revision ebbae7bd0 --summary "$run_dir/baseline-v3.json" > "$run_dir/baseline-v3.log" 2>&1

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
import json,math,sys
from pathlib import Path
p=Path(sys.argv[1]); results={}; problems=[]
for name in ('baseline-v3','candidate',
             'mutant-task-includes-project-terminal','mutant-duplicate-replay','mutant-inactive-input'):
    r=json.loads((p/(name+'.json')).read_text(encoding='utf-8'));m=r.get('metrics',{})
    results[name]={k:r.get(k) for k in ('status','error','failures','code_version','measurement_version','harness_version')}
    results[name].update({k:m.get(k) for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median','output_to_visible_ms')})
    if r.get('measurement_version')!=3 or r.get('harness_version')!=5 or not all(isinstance(m.get(k),(int,float)) and math.isfinite(m[k]) and m[k]>0 for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median','output_to_visible_ms')):
        problems.append(name+': missing valid metrics')
    required={'baseline-v3':'task_A_only_its_agents','mutant-task-includes-project-terminal':'task_A_only_its_agents',
              'mutant-duplicate-replay':'numbered_output_once_before_switch','mutant-inactive-input':'inactive_input_rejected'}.get(name)
    if required:
        if r['status']!='NO_GO' or required not in r['failures']: problems.append(name+': expected business red not obtained')
    elif r['status']!='PASS': problems.append(name+': not PASS')
a=json.loads((p/'t091-baseline.json').read_text());b=json.loads((p/'t091-candidate.json').read_text())
same=a['status']==b['status']=='INCOMPLETE' and a.get('error')==b.get('error') and a.get('checks')==b.get('checks')
results['t091']={'status':'PASS' if same else 'INCOMPLETE','disposition':'known preexisting failure unchanged' if same else 'failure changed; investigate',
                 'baseline_error':a.get('error'),'candidate_error':b.get('error')}
if not same: problems.append('T-091 changed failure')
for name in ('output-meter-boundaries','retained-focus','selection','layout-store','terminal-catalog','t107','t133-t107'):
    r=json.loads((p/(name+'.json')).read_text());results[name]={'status':r['status'],'error':r.get('error')}
    if r['status']!='PASS':problems.append(name+': not PASS')
baseline=results['baseline-v3'];candidate=results['candidate']
comparisons={k:{'baseline':baseline[k],'candidate':candidate[k]} for k in ('scroll_fps_median','scroll_p95_ms_median','switch_ms_median','output_to_visible_ms')}
summary={'comparisons':comparisons,'scroll_claim':'未证明改善；平均帧率受刷新率封顶。输出可见耗时须另行评估，不能代称纯滚动帧率收益。','status':'INCOMPLETE','run_checks':'PASS' if not problems else 'NO_GO','results':results,'problems':problems,
         'next':'Worker must report the final baseline/candidate output latency and joint acceptance; do not infer scrolling improvement from refresh-capped FPS.'}
(p/'COMPARISON.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
raise SystemExit(1 if problems else 0)
PY
if (( $? != 0 )); then failed=1; fi
print "结果目录：$run_dir"
print '请回传 COMPARISON.json 和结果目录；需核对最终联合验收与输出可见耗时；WebGL 已移除，平均 FPS 不作滚动收益依据。'
exit "$failed"
