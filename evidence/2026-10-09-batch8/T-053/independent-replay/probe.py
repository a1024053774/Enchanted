import json, subprocess, sys, time
from pathlib import Path
base=Path(__file__).resolve().parent
script=base/'snapshot/scripts/inbox'
root=base/('probe-'+str(time.time_ns()))
for name in ('inbox','tickets','roles'): (root/'.project-map'/name).mkdir(parents=True,exist_ok=True)
for role in ('ideation','executor'):
    (root/'.project-map/roles'/f'{role}.md').write_text('角色卡 未见 sentinel Ω '+role+'\n',encoding='utf8')
commands=[]
checks=[]
def cli(*args, now='2026-10-09T19:00:00Z'):
    argv=[str(script),'--root',str(root),'--now',now,*args]
    p=subprocess.run(argv,text=True,capture_output=True,timeout=10)
    commands.append(dict(argv=argv,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr))
    return p
def check(name,result): checks.append({'case':name,'pass':bool(result)})
def ids(stdout): return [x.split()[1] for x in stdout.splitlines() if x.startswith('ENTRY ')]
def entry(ident,kind='report',sender='worker:unseen',to='executor',reply='',created='2026-10-09T18:00:00Z',**extra):
    data=dict(id=ident,kind=kind,**{'from':sender},to=to,reply_to=reply,refs=[],created_at=created,schema=1,**extra)
    text='---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in data.items())+'---\n\n夹具正文 Ω '+ident+'\n'
    path=root/'.project-map/inbox'/f'{ident}.md'
    path.write_text(text,encoding='utf8')
    return path
p=cli('send','--from','ideation','--to','executor','--kind','assign','--id','unseen-alpha','--body','Ω 独立正文\n第二行 café')
check('sentinel-send-id',p.returncode==0 and p.stdout=='unseen-alpha\n')
original=(root/'.project-map/inbox/unseen-alpha.md').read_bytes()
p=cli('list','--role','executor')
check('card-first-and-body-preserved',p.returncode==0 and p.stdout.startswith('角色卡 未见 sentinel Ω executor\n') and 'Ω 独立正文\n第二行 café' in p.stdout and ids(p.stdout)==['unseen-alpha'])
p=cli('ack','--role','ideation','--id','unseen-alpha')
check('wrong-recipient-ack-rejected',p.returncode==1 and not list((root/'.project-map/inbox').glob('*ack*')))
p=cli('ack','--role','executor','--id','unseen-alpha')
check('actual-recipient-ack-published',p.returncode==0)
p=cli('list','--role','executor')
check('ack-hides-original-without-mutation',ids(p.stdout)==[] and original==(root/'.project-map/inbox/unseen-alpha.md').read_bytes())
entry('handwritten'); hp=root/'.project-map/inbox/handwritten.md'; hp.write_text(hp.read_text().replace('refs: []','refs: [ticket:T-987, ticket:T-986]'),encoding='utf8')
p=cli('list','--role','executor')
check('handwritten-inline-list-visible',p.returncode==0 and ids(p.stdout)==['handwritten'] and 'ticket:T-987, ticket:T-986' in p.stdout)
entry('pending-unseen','issue',to='triage',created='2026-10-09T18:45:01Z',title='非模板 Ω',blocking=False)
entry('expired-unseen','issue',to='triage',created='2026-10-09T18:44:59Z',title='过期 Ω',blocking=False)
entry('blocking-unseen','issue',to='triage',created='2026-10-09T18:59:59Z',title='阻塞 Ω',blocking=True)
p=cli('list','--role','user')
check('user-presentation-boundaries',p.returncode==0 and ids(p.stdout)==['expired-unseen','blocking-unseen'] and p.stdout.startswith('等你决定\n'))
p=cli('send','--from','executor','--to','triage','--kind','disposition','--reply-to','pending-unseen','--action','close','--reason','sentinel 理由','--basis','sentinel 依据','--body','')
check('explicit-close-fields-preserved',p.returncode==0 and 'reason: "sentinel 理由"' in (root/'.project-map/inbox'/f'{p.stdout.strip()}.md').read_text() and 'basis: "sentinel 依据"' in (root/'.project-map/inbox'/f'{p.stdout.strip()}.md').read_text())
# Spec section 3 and ideation role card require certainty: relayed for relayed answers;
# spec section 5 requires bundle_id. These expectations come from that contract.
p=cli('send','--from','ideation','--to','executor','--kind','answer','--id','unseen-answer','--reply-to','blocking-unseen','--ref','issue:blocking-unseen','--ref','worker:unseen','--body','问题 1：阻塞 Ω\n用户答复：逐字原话 café')
check('answer-command-succeeds',p.returncode==0)
answer=(root/'.project-map/inbox/unseen-answer.md').read_text()
check('answer-certainty-field-contract','certainty: "relayed"\n' in answer or 'certainty: relayed\n' in answer)
check('answer-bundle-id-field-contract','bundle_id:' in answer.split('---\n')[1])
p=cli('send','--from','ideation','--to','executor','--kind','answer','--id','unseen-answer-fields','--reply-to','blocking-unseen','--ref','issue:blocking-unseen','--ref','worker:unseen','--bundle-id','sentinel-bundle','--certainty','relayed','--body','用户答复：相同原话')
check('explicit-required-answer-fields-available',p.returncode==0)
# Independent ready fixture uses handwritten inline lists and reversed IDs/titles.
for ident,deps in [('T-987','[T-985]'),('T-986','[]'),('T-984','[T-missing]')]:
    (root/'.project-map/tickets'/f'{ident}-sentinel.md').write_text(f'---\nid: {ident}\ntitle: Ω-{ident}\ntype: research\nstatus: open\nblocked_by: {deps}\nclaimed_by:\nready: yes\nready_by: executor\nready_rev: 9\n---\n',encoding='utf8')
(root/'.project-map/tickets/T-985-closed.md').write_text('---\nid: T-985\ntitle: dependency\ntype: task\nstatus: closed\nblocked_by: []\nclaimed_by:\nready: no\nready_by: ideation\nready_rev: 1\n---\n',encoding='utf8')
p=cli('ready')
check('ready-dependencies-with-inline-lists',p.returncode==0 and [x.split()[1] for x in p.stdout.splitlines() if x.startswith('READY ')]==['T-986','T-987'])
(root/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(root/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(root=str(root),checks=checks),ensure_ascii=False,indent=2))
