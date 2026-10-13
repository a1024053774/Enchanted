"""Independent readback of saved native records, gate events and owned Git refs."""
import argparse
import json
from pathlib import Path
import subprocess
import tarfile

CARD = Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    root=CARD / 'outside-real-delivery-02'; read=lambda name:json.loads((root / name).read_text(encoding='utf-8'))
    run,bindings,gate,rows=read('run.json'),read('bindings.json'),read('gate-events.json'),read('events-after-stop.json')
    report=dict(status='INCOMPLETE',product_status='INCOMPLETE',commands=[],archive_pending=run.get('archive_required',False))
    def git(*argv):
        p=subprocess.run(['git',*argv],cwd='/private/tmp/a2a-t076-real-delivery-02/repo',capture_output=True,text=True)
        report['commands'].append(dict(argv=['git',*argv],exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
        assert p.returncode==0
        return p.stdout.strip()
    native={}; turns={}; sessions={}
    for role in ('worker','reviewer'):
        launch=bindings['launches'][role]; native[role]=[r['data']['record'] for r in rows if r['type']=='native_record' and r['launch']==launch['id']]
        starts=[r['payload']['turn_id'] for r in native[role] if r['type']=='event_msg' and r['payload'].get('type')=='task_started']
        ends=[r['payload']['turn_id'] for r in native[role] if r['type']=='event_msg' and r['payload'].get('type')=='task_complete']
        assert starts==ends and len(starts)==(4 if role=='worker' else 1)
        metas=[r['payload'] for r in native[role] if r['type']=='session_meta']; assert len(metas)==1 and metas[0]['source']=='cli'
        sessions[role]=metas[0]['id']; turns[role]=starts
        contexts=[r['payload'] for r in native[role] if r['type']=='turn_context']
        assert contexts and all(c['model']=='gpt-6.1-sol' and c['effort']=='xhigh' and c['approval_policy']=='never'
            and c['sandbox_policy']['type']==('workspace-write' if role=='worker' else 'read-only') for c in contexts)
        assert [a for a in launch['argv'] if a.startswith('service_tier=')]==['service_tier="default"']
        assert not Path(launch['env']['CODEX_HOME']).exists()
    assert sessions['worker']!=sessions['reviewer']
    active=None
    for r in native['worker']:
        p=r['payload']
        if r['type']=='event_msg' and p.get('type')=='task_started': active=p['turn_id']
        if active in (turns['worker'][1],turns['worker'][3]) and r['type']=='response_item':
            assert p.get('type') not in ('function_call','custom_tool_call')
    attempt=bindings['attempt']; M,G,C1,C2=[run[k] for k in ('M','G','C1','C2')]
    assert git('rev-parse','refs/heads/main')==M
    assert git('rev-list','--parents','-n','1',M).split()==[M,G,C2]
    assert git('status','--porcelain')==''
    expected={'A2A-Task':'T-076-22','A2A-Attempt':attempt['attempt_id'],'A2A-Session':attempt['session_id'],
        'A2A-Role':'worker','A2A-Tool':'codex-cli 0.162.1','A2A-Model':'gpt-6.1-sol','A2A-Effort':'xhigh',
        'A2A-Native-Session':sessions['worker'],'A2A-Launch':bindings['launches']['worker']['id']}
    for C in (C1,C2):
        message=git('log','-1','--format=%B',C); assert message==(root / (C+'.message')).read_text().strip()
        lines=[l.partition(': ') for l in message.splitlines() if l.startswith('A2A-')]
        assert len(lines)==9 and {k:v for k,_,v in lines}==expected
    rejected=[e for e in gate if e['type']=='delivery_rejected']; assert len(rejected)==1 and rejected[0]['details']['repair']['check']=='completion'
    repairs=[e for e in rows if e['type']=='dispatch_queued' and e['data'].get('context',{}).get('kind')=='quality-repair']; assert len(repairs)==1
    submitted=[e for e in gate if e['type']=='submitted']; assert len(submitted)==2
    assert [e['details']['attempt']['turn_id'] for e in submitted]==[turns['worker'][0],turns['worker'][2]]
    review=read('integration.json')['task']['review']; assert review['state']=='passed' and review['candidate_commit']==C2
    assert review['result']['verdict']=='可合并' and review['result']['findings']==[]
    assert read('missing-score-refusal.json')['error']=='score_required'
    scores=[e['details'] for e in gate if e['type']=='score_recorded']; assert len(scores)==1 and scores[0]==read('score-payload.json')
    score=scores[0]; assert score['facts']['delivery_rounds']==2 and score['facts']['human_interventions']==0
    assert score['facts']['rejections']==dict(identity_version=0,path_boundary=0,completion=1,red_state=0,rule_checks=0,independent_review=0,commit_trailers=0)
    assert score['data']==read('executor-score.json') and score['model']=='gpt-6.1-sol' and score['effort']=='xhigh'
    assert len([e for e in gate if e['type']=='integrated'])==1
    assert not any(e['type'] in ('permission_wait','native_final_read_failed','stop_transfer_failed','event_write_failed','queue_stopped') for e in rows)
    assert run['observed_main_turns']==5 and run['home_removed'] is True
    entries=[json.loads(l) for l in (CARD / 'real-turn-budget.jsonl').read_text().splitlines()]
    delivery_outputs={str(CARD / 'outside-p-review-02'),str(root)}
    assert sum(e['observed_main_turns'] for e in entries if e['kind']=='observation'
               and e['output'] in delivery_outputs)==6
    accounted_total=sum(e['observed_main_turns'] for e in entries if e['kind']=='observation')
    assert 6<=accounted_total<=8
    pointer=read('commands.jsonl.gz.pointer.json')
    archive=json.loads((CARD / 'archive-real-log-01/run.json').read_text())
    assert archive['status']=='PASS' and archive['byte_readback'] is True and archive['source_removed'] is True
    assert Path(pointer['archive']).stat().st_size==pointer['bytes']==48122290
    report.update(status='PASS',archive_pending=False,B=run['B'],G=G,C1=C1,C2=C2,M=M,parent_order=[G,C2],sessions=sessions,turns=turns,
                  trailers=expected,score=score,accounted_total=accounted_total,budget_limit=8,home_removed=True,ack_tool_calls=0,
                  oversized_log_bytes=pointer['bytes'],log_archive=pointer['archive'])
    (args.output / 'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','archive_pending','accounted_total','oversized_log_bytes')}))


if __name__=='__main__': main()
