#!/bin/bash
# 主控沙箱外运行：保留审查原脚本，绑定当前提交并追加同一表单改正标题后成功的检查。
# --check 仅生成并编译复验脚本，不运行 GUI。无手动目录选择、模型或截图。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
python3 - "$@" <<'PY'
import ast,json,pathlib,subprocess,sys,tempfile
source=pathlib.Path.cwd()
original=source/'evidence/2026-10-19-batch17/T-106/REVIEW-OUTSIDE-02.sh'
text=original.read_text(encoding='utf-8')
body=text.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
old="revision = '5036a8dc32de265dc27499028f0b938db3d1a15a'"
assert body.count(old)==1,'审查脚本候选绑定已变化，请主控核对'
revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
body=body.replace(old,'revision = '+repr(revision),1)
marker='    stop_owned()\n    # 当前候选真实 GUI 五种提交后故障'
assert body.count(marker)==1,'审查脚本检查点已变化，请主控核对'
extra='''    # 追加检查；上面的原审查断言（包括空白拒收后取消）全部保留。
    view = form()
    corrected_defaults = json.loads(view['fields']['card'])
    corrected_title = '修正后的标题<独立输入>-' + uuid.uuid4().hex[:8]
    corrected_goal = '同一表单拒收空白标题后，修改标题继续注册'
    values = dict(project=project, title='   ', goal=corrected_goal, command=json.dumps(['python3', 'tests/check.py']))
    for field, value in values.items():
        win.call('fill', field=field, value=value)
    win.wait(lambda value: all(value['fields'].get(k) == v for k, v in values.items()))
    counts_before = inventory(state)
    win.call('submit')
    view = win.wait(lambda value: any('Invalid creation fields' in alert for alert in value['alerts']) and any(item['text'] == '确认并注册任务' and not item['disabled'] for item in value['buttons']))
    assert inventory(state) == counts_before
    assert any(item['text'] == '取消' and not item['disabled'] for item in view['buttons'])
    win.call('fill', field='title', value=corrected_title)
    win.wait(lambda value: value['fields'].get('title') == corrected_title)
    win.call('submit')
    view = win.wait(lambda value: not value['form'] and any(item['id'] == corrected_defaults['id'] for item in value['tasks']))
    corrected_record = gate(state, local_env, 'status', '--task', corrected_defaults['id'])['task']
    assert corrected_record['title'] == corrected_title and corrected_record['card']['goal'] == corrected_goal and corrected_record['state'] == 'ready'
    counts_after = inventory(state)
    assert counts_after == {key: value + (1 if key in ('tasks', 'task_card_versions', 'task_card_snapshots') else 0) for key, value in counts_before.items()}
    assert not title_marker.exists() and not completion_marker.exists()
    report['checks'].append('同一表单空白标题提交前拒收、五表无增长、仍可编辑取消，改正标题后成功注册')
'''
body=body.replace(marker,extra+marker,1)
ast.parse(body,feature_version=(3,9));compile(body,str(original)+' (当前提交与追加修正检查)','exec')
folder=pathlib.Path(tempfile.mkdtemp(prefix='t106-preflight-review-',dir='/private/tmp'))
probe=folder/'review-current.py';probe.write_text(body,encoding='utf-8')
print(json.dumps(dict(candidate=revision,original=str(original),probe=str(probe),check_only=sys.argv[1:]==['--check']),ensure_ascii=False),flush=True)
if sys.argv[1:]==['--check']:raise SystemExit(0)
assert not sys.argv[1:],'只接受 --check 或无参数'
subprocess.run(['git','diff','--exit-code','HEAD','--','workbench'],check=True)
raise SystemExit(subprocess.run(['python3',str(probe)]).returncode)
PY
