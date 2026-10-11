#!/usr/bin/env python3
"""Real database inbox client; no controller CLI, terminal, model or hook.

A pre-existing logical handoff is fixture input, not evidence of a Claude send.
Only the daemon can append its ack. Missing recipients remain undelivered.
"""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import time
import traceback

from command_evidence import CommandLog, command_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output.resolve()
    root = Path(tempfile.mkdtemp(prefix='t78-inbox-',dir='/tmp')).resolve()
    repo, state = root/'repo', root/'state'
    repo.mkdir(); state.mkdir()
    tickets = repo/'.project-map/tickets'; tickets.mkdir(parents=True)
    env = {key:value for key,value in os.environ.items() if not key.startswith(('A2A_','GIT_','CODEX_','CLAUDE_','ANTHROPIC_'))}
    credential = root/'operator.credential.json'
    env.update(A2A_OPERATOR_CREDENTIAL=str(credential), GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.hooksPath',GIT_CONFIG_VALUE_0=os.devnull,
               GIT_CONFIG_KEY_1='commit.gpgsign',GIT_CONFIG_VALUE_1='false',
               GIT_AUTHOR_NAME='T078 fixture',GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T078 fixture',GIT_COMMITTER_EMAIL='fixture@example.invalid')
    node=shutil.which('node')
    gate=[node,source/'workbench/src/gates/cli.ts','--state',state]
    inbox=[node,source/'workbench/bin/inbox','--state',state]
    log=CommandLog(out)
    record={'status':'INCOMPLETE','task':'T-078-1','argv':sys.argv,'fixture':str(root),'checks':[],
            'real_model_turns':0,'claude_fixture':False,'cleanup_complete':False,
            'limitations':['没有实际主控接收者，送达路径尚未验证；预置 handoff 只是持久化输入夹具。']}
    started=False
    failure=False

    def save():
        (out/'results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def run(argv, *, allowed=(0,), child_env=None):
        p=log.run(argv,cwd=source,env=env if child_env is None else child_env,timeout=30)
        if p.returncode not in allowed:
            raise RuntimeError({'unexpected_command_exit':p.evidence})
        return p

    def call(command,*values):
        value=command_json(run([*gate,command,*values]))
        if not value.get('ok'): raise RuntimeError(value)
        return value

    def rows(table):
        with closing(sqlite3.connect((state/'state.sqlite3').as_uri()+'?mode=ro',uri=True)) as db:
            return [json.loads(row[0]) for row in db.execute('SELECT data FROM '+table+' ORDER BY rowid')]

    def check(name,passed,observed):
        record['checks'].append({'name':name,'status':'PASS' if passed else 'INCOMPLETE','observed':observed});save()
        if not passed: raise AssertionError(name)

    try:
        if not node: raise RuntimeError('Node required')
        run(['git','-C',repo,'init','-b','main'])
        (repo/'value.txt').write_text('inbox fixture\n',encoding='utf-8')
        run(['git','-C',repo,'add','value.txt']);run(['git','-C',repo,'commit','-m','T078 inbox fixture'])
        original={'id':'fixture-handoff','schema':1,'from':'ideation','to':'executor','kind':'assign',
                  'reply_to':None,'refs':[],'created_at':'2026-10-11T00:00:00Z','body':'预置交接输入，不是 Claude 的真实发送。'}
        with closing(sqlite3.connect(state/'state.sqlite3')) as db:
            db.execute('CREATE TABLE inbox_records(id TEXT PRIMARY KEY,data TEXT NOT NULL)')
            db.execute('INSERT INTO inbox_records VALUES (?,?)',(original['id'],json.dumps(original,ensure_ascii=False)))
            db.commit()
        record['seeded_handoff']=original
        record['daemon']=call('daemon_start');started=True
        card=call('card_template','--task','inbox-task','--repo',repo)['card']
        card.update(goal='限定项目的收件箱查询',non_goals=['不启动 agent'],paths={'allow':['value.txt'],'deny':[]},
                    completion_conditions=[{'argv':[sys.executable,'-I','-c',"from pathlib import Path; assert Path('value.txt').read_text() == 'inbox fixture\\n'"]}],
                    task_type='后端逻辑',complexity='L',executor={'cli':'Codex','model':'gpt-6-astra','effort':'xhigh'})
        card_file=root/'card.json';card_file.write_text(json.dumps(card,ensure_ascii=False),encoding='utf-8')
        call('card_save','--task','inbox-task','--card',card_file,'--expected-version','0')
        call('create','--task','inbox-task','--repo',repo,'--project','inbox-project','--branch','refs/heads/main','--card-version','1')
        for ident,status,claimed,blocked in [('Q-ready','open','','[]'),('Q-closed','closed','','[]'),
                                            ('Q-claimed','open','someone','[]'),('Q-blocked','open','','[Q-missing]')]:
            (tickets/(ident+'.md')).write_text(f'---\nid: {ident}\ntitle: {ident}\ntype: build\nstatus: {status}\nclaimed_by: {claimed}\nblocked_by: {blocked}\nready: yes\nready_by: ideation\nready_rev: 1\n---\n',encoding='utf-8')
        ready=command_json(run([*inbox,'ready','--project','inbox-project']))
        check('ready_only_bound_executable_ticket',ready.get('ok') is True and [item['id'] for item in ready.get('ready',[])]==['Q-ready'],ready)
        foreign=command_json(run([*inbox,'ready','--project','not-bound'],allowed=(1,)))
        check('unknown_project_rejected',foreign.get('error')=='unknown_project',foreign)
        listed=command_json(run([*inbox,'list','--role','ideation']))
        check('list_role_from_credential',listed.get('ok') is True and [item['entry']['id'] for item in listed['entries']]==['fixture-handoff'],listed)
        body=root/'body.txt';body.write_text('报告正文：不应变成用户输入。\n',encoding='utf-8')
        sent=command_json(run([*inbox,'send','--from','user','--to','ideation','--kind','report','--body-file',body],allowed=(1,)))
        check('send_records_actual_actor_without_claiming_delivery',sent.get('entry',{}).get('from')=='executor'
              and sent['entry']['body']=='报告正文：不应变成用户输入。\n'
              and sent.get('delivery',{}).get('state')=='undelivered' and not rows('user_inputs'),sent)
        first=command_json(run([*inbox,'ack','--id','fixture-handoff'],allowed=(1,)))
        second=command_json(run([*inbox,'ack','--id','fixture-handoff','--role','user'],allowed=(1,)))
        acks=[item for item in rows('inbox_records') if item['kind']=='ack']
        check('ack_once_by_real_recipient',len(acks)==1 and acks[0]['from']=='executor'
              and first.get('entry',{}).get('id')==second.get('entry',{}).get('id')==acks[0]['id'],{'first':first,'second':second,'acks':acks})
        remaining=command_json(run([*inbox,'list']))
        check('ack_removes_original_from_unconfirmed',remaining.get('entries')==[],remaining)
        before=rows('inbox_records')
        anonymous={key:value for key,value in env.items() if not key.startswith('A2A_')}
        denied=command_json(run([*inbox,'send','--from','ideation','--to','executor','--kind','assign','--body-file',body],allowed=(1,),child_env=anonymous))
        check('anonymous_send_cannot_create_entry',denied.get('error')=='caller_identity_required' and rows('inbox_records')==before,denied)
        (tickets/'Q-bad.md').write_text('---\nid: Q-bad\ntype: build\nstatus: open\nready: yes\nready_by: ideation\nblocked_by: []\n---\n',encoding='utf-8')
        invalid=command_json(run([*inbox,'ready','--project','inbox-project'],allowed=(1,)))
        check('invalid_ready_metadata_is_reported',invalid.get('error')=='invalid_ready_tickets'
              and any('Q-bad' in line for line in invalid.get('diagnostics',[])),invalid)
        record['readback']={table:rows(table) for table in ['inbox_records','inbox_deliveries','user_inputs']}
        record['status']='PASS'
    except Exception as error:
        failure=True;record['error']={'message':str(error),'traceback':traceback.format_exc()}
    finally:
        try:
            if started:
                call('daemon_stop')
                deadline=time.monotonic()+10
                while (state/'daemon.pid').exists() and time.monotonic()<deadline: time.sleep(0.05)
                if (state/'daemon.pid').exists(): raise RuntimeError('Own daemon shutdown was not confirmed')
            if credential.exists(): credential.unlink()
            record['cleanup_complete']=True
        except Exception as error:
            failure=True;record['cleanup_error']=str(error)
        with tarfile.open(out/'fixture.tar.gz','x:gz') as archive:
            archive.add(root,arcname=root.name,filter=lambda item:None if item.name==root.name+'/operator.credential.json' else item)
        if failure:record['status']='INCOMPLETE'
        save()
    print(json.dumps({'status':record['status'],'checks':[{k:item[k] for k in ['name','status']} for item in record['checks']]},ensure_ascii=False))
    return 1 if failure else 0


if __name__=='__main__':raise SystemExit(main())
