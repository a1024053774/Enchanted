"""One unchanged acceptance oracle for good and known-bad real-process captures.

Expected checked=a2a_raise, unchecked=a2a_submit comes from decision 02 and
the recorded scripted input. This script does not read the driver's verdict.
"""
import json
from pathlib import Path
import sys

root=Path(sys.argv[1])
def read(name): return json.loads((root/(name+'.json')).read_text(encoding='utf-8'))
thread=read('thread-id')['thread']
native=read('thread-observed')
raw=read('runtime-events')
core=read('gateway-core-records')
provider=read('thread-id')['provider']
assert native['session']['status']=='running' and native['latestTurn']['state']=='running'
assert native['session']['runtimeMode']==('approval-required' if provider=='codex' else 'full-access')
assert len([e for e in raw if e['type']=='turn.started'])==1
issues=[json.loads(r['data']) for r in core['issue_records']]
assert len(issues)==1, 'Checked a2a_raise must execute without a pending approval'
issue=issues[0]
assert issue['thread_id']==thread and issue['turn_id']==native['latestTurn']['turnId']
completed=[e for e in raw if e['type']=='item.completed' and e.get('payload',{}).get('itemType')=='mcp_tool_call']
assert len(completed)==1,'One checked MCP write must complete'
if provider=='codex':
    tool=completed[0]['raw']['payload']['item']
    assert tool['server']=='synara' and tool['tool']=='a2a_raise' and tool['error'] is None
    result=json.loads(tool['result']['content'][0]['text'])
else:
    tool=completed[0]['payload']['data']
    assert tool['toolName']=='mcp__synara__a2a_raise'
    result=json.loads(tool['result']['content'][0]['text'])
assert result['ok'] is True and result['id']==issue['id']
requests=[e for e in raw if e['type']=='request.opened']
assert len(requests)==1 and native['hasPendingApprovals'] is True
request=requests[0]
assert request['threadId']==thread and request['turnId']==native['latestTurn']['turnId']
if provider=='codex':
    assert request['raw']['source']=='codex.app-server.request'
    assert request['raw']['method']=='mcpServer/elicitation/request'
    args=request['payload']['args']
    assert args['serverName']=='synara' and args['_meta']['codex_approval_kind']=='mcp_tool_call'
    assert args['message']=='Allow the synara MCP server to run tool "a2a_submit"?'
    assert args['_meta']['tool_params']==dict(task='t064-real',attempt='not-an-attempt',session='not-a-session',fence=1,spec_rev=1,commit='0'*40)
else:
    assert request['raw']['source']=='claude.sdk.permission'
    assert request['raw']['method']=='canUseTool/request'
    assert request['payload']['args']['toolName']=='mcp__synara__a2a_submit'
    assert request['providerRefs']['providerItemId']=='t064-script-1'
print(json.dumps(dict(status='PASS',provider=provider,thread=thread,turn=issue['turn_id'],checked_result_id=issue['id'],unchecked_request=request['requestId'],native_method=request['raw']['method']),ensure_ascii=False))
