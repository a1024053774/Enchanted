"""Mechanical delivery checks, not another independent acceptance review."""
import ast
import json
from pathlib import Path
import re
import sqlite3
import subprocess

out=Path(__file__).resolve().parent
fork=Path('/Users/luckye/Documents/Code/synara')
expected='49cae984f22924de006e0f8358cb447eb881aaf6'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=fork,text=True).strip()==expected
assert subprocess.check_output(['git','status','--short','--untracked-files=no'],cwd=fork,text=True)==''
paths=subprocess.check_output(['git','ls-files','--others','--exclude-standard','--',str(out)],text=True).splitlines()
paths += subprocess.check_output(['git','diff','--name-only','HEAD','--',str(out)],text=True).splitlines()
paths += ['.project-map/tickets/T-064-role-permission-settings.md',str(out/'RESULTS.md')]
checked=[]
for value in paths:
    p=Path(value)
    if p.suffix not in ('.py','.ts','.md','.json','.jsonl','.log'): continue
    raw=p.read_bytes(); text=raw.decode('utf-8')
    assert not raw.startswith(b'\xef\xbb\xbf') and '\ufffd' not in text,p
    if p.suffix=='.py': ast.parse(text,filename=str(p))
    if p.suffix=='.json': json.loads(text)
    if p.suffix=='.jsonl':
        for line in text.splitlines(): json.loads(line)
    # These checks identify secret formats, never classify prose or outcomes.
    assert re.search(r'Bearer\s+sagw_[A-Za-z0-9_-]+',text) is None,p
    assert re.search(r'"(?:access_token|refresh_token|id_token|bearerToken)"\s*:\s*"[^"\s]+"',text) is None,p
    checked.append(str(p))
for source in (out/'RESULTS.md',out/'preparation-failures-48.md'):
    for target in re.findall(r'\]\(([^)]+)\)',source.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'): continue
        if target=='delivery-final-audit-57.json': continue  # Created below; checked after writing.
        assert (source.parent/target.split('#',1)[0]).exists(),target
turns=[]; processes=[]
for label in ('claude-good40','claude-bad41','codex-good53','codex-bad54'):
    result=out/(label+'-real')
    launch=json.loads((result/'launch.json').read_text(encoding='utf-8'))
    cleanup=json.loads((result/'auth-cleanup.json').read_text(encoding='utf-8'))
    assert launch['source_revision']==expected and launch['tracked_status']==''
    assert not Path(cleanup['home']).exists()
    assert subprocess.run(['ps','-p',str(launch['pid']),'-o','stat='],capture_output=True).returncode!=0
    processes.append(dict(label=label,pid=launch['pid'],stopped=True,temporary_home_removed=True))
    if label.startswith('codex-'):
        actual=json.loads((result/'actual-native-home.json').read_text(encoding='utf-8'))
        native_cleanup=json.loads((result/'native-home-cleanup.json').read_text(encoding='utf-8'))
        assert actual['actual_home_in_tmp'] and actual['auth_links_to_owned_source']
        assert not Path(native_cleanup['home']).exists()
        assert all(Path(x).is_relative_to(Path('/tmp').resolve()) for x in actual['observed_cli_CODEX_HOME'] if x)
    if label.startswith('codex-'):
        root=Path(launch['root'])
        with sqlite3.connect('file:'+str(root/'userdata/state.sqlite')+'?mode=ro',uri=True) as db:
            rows=[json.loads(r[0]) for r in db.execute("SELECT event_json FROM provider_runtime_events WHERE event_type='turn.started'")]
        assert len(rows)==1,(label,len(rows))
        turns += [dict(label=label,thread=e['threadId'],turn=e['turnId']) for e in rows]
    contract=json.loads((out/(label+('-contract55.json' if label.startswith('codex-') else '-contract46.json'))).read_text(encoding='utf-8'))
    assert contract['matched'] and contract['exit']==(1 if '-bad' in label else 0)
budget=[json.loads(line) for line in (out/'codex-turn-budget-42.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(turns)==2 and len(budget)==4
for label in ('codex-good44','codex-bad45'):
    result=out/(label+'-real');launch=json.loads((result/'launch.json').read_text(encoding='utf-8'))
    with sqlite3.connect('file:'+str(Path(launch['root'])/'userdata/state.sqlite')+'?mode=ro',uri=True) as db:
        rows=[json.loads(r[0]) for r in db.execute("SELECT event_json FROM provider_runtime_events WHERE event_type='turn.started'")]
    assert len(rows)==1
    turns += [dict(label=label,thread=e['threadId'],turn=e['turnId'],isolation_location_gap_preserved=True) for e in rows]
assert len(turns)==4
stop=json.loads((out/'codex-good44-real/stop-address-record.json').read_text(encoding='utf-8'))
assert stop['caller_credential']['thread']==stop['caller_thread'] and stop['caller_credential']['a2aPermissions']['role']=='executor'
assert 'a2a:stop' in stop['caller_credential']['capabilities']
assert stop['core_record']['details']['actor']=='ideation' and stop['elapsed_seconds']>120
sdk=json.loads((fork/'apps/server/node_modules/@anthropic-ai/claude-agent-sdk/package.json').read_text(encoding='utf-8'))['version']
with (out/'delivery-final-audit-57.json').open('x',encoding='utf-8') as f:
    json.dump(dict(status='PASS',mechanical_check_only=True,source_revision=expected,checked_files=checked,processes=processes,codex_real_turns=turns,codex_used=4,codex_limit=4,claude_sdk=sdk,stop_address_record_checked=True,skill_sources=[dict(name=n,path='/Users/luckye/.agents/skills/'+n+'/SKILL.md',version='No version field declared') for n in ('project-map','evidence-first-testing','document-writing','behavioral-acceptance-review')],unknowns=['Actual supplier Fast tier','User visual acceptance','Native interrupted / projection completed discrepancy'],second_independent_review=False),f,ensure_ascii=False,indent=2)
print('PASS delivery mechanics: UTF-8/JSON/syntax/links, no bearer/auth records, clean frozen product, 4/4 Codex turns, stopped processes and deleted homes')
assert (out/'delivery-final-audit-57.json').exists()
