"""Single-rule backend mutants and independent persisted-outcome checks."""
import difflib
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

CASES={
    'assign':('src/gates/core.ts',
        'requireGate(role === direction[0] && args.to === direction[1], "invalid_direction");',
        'requireGate(args.to === direction[1], "invalid_direction");',
        'worker_assign_spoof_denied'),
    'ready':('src/gates/core.ts',
        'if (args.command === "inbox_ready") {\n      requireGate(["ideation", "executor"].includes(role), "controller_required");',
        'if (args.command === "inbox_ready") {\n      // MUTANT: allow the worker to query ready tickets.',
        'worker_ready_is_role_denied'),
    'foreign-ack':('src/gates/core.ts',
        'requireGate(original.to === role, "recipient_required");',
        '// MUTANT: allow acknowledgement of another recipient\'s entry.',
        'worker_foreign_ack_is_denied'),
    'revoked':('src/daemon.ts',
        'if (!active || active.attempt_id !== bound.attempt || active.session_id !== bound.session ||\n'
        '                    active.fence !== bound.fence || current.task?.spec_rev !== bound.spec_rev || active.reclaimed) {',
        'if (false /* MUTANT: keep revoked inbox authority */) {',
        'revoked_worker_inbox_is_rejected'),
}


def prepare(source,out):
    out.mkdir(exist_ok=False)
    root=Path(tempfile.mkdtemp(prefix='t78-rule-mutants-',dir='/tmp')).resolve()
    manifest={'task':'T-078-1','root':str(root),'mutants':{},'real_model_turns':0}
    for name,(file,before,after,contract) in CASES.items():
        target=root/name;workbench=target/'workbench'
        shutil.copytree(source/'workbench/src',workbench/'src')
        shutil.copytree(source/'workbench/hooks',workbench/'hooks',symlinks=True)
        for item in ['package.json','package-lock.json','LICENSE.synara']:
            shutil.copyfile(source/'workbench'/item,workbench/item)
        # Disposable source fixture only; never link a shared build output.
        os.symlink(source/'workbench/node_modules',workbench/'node_modules',target_is_directory=True)
        path=workbench/file;original=path.read_text(encoding='utf-8')
        if original.count(before)!=1:raise RuntimeError('Expected exactly one mutation site: '+name)
        changed=original.replace(before,after,1);path.write_text(changed,encoding='utf-8')
        patch=''.join(difflib.unified_diff(original.splitlines(True),changed.splitlines(True),fromfile='candidate/'+file,tofile=name+'/'+file))
        (out/(name+'.diff')).write_text(patch,encoding='utf-8')
        manifest['mutants'][name]={'backend_source':str(target),'file':file,'contract':contract,'patch':name+'.diff'}
    with tarfile.open(out/'sources.tar.gz','x:gz') as archive:archive.add(root,arcname=root.name)
    with (out/'manifest.json').open('x',encoding='utf-8') as stream:json.dump(manifest,stream,ensure_ascii=False,indent=2)
    return manifest


def evaluate(name,out,backend):
    data=json.loads((out/'results.json').read_text(encoding='utf-8'))
    target=CASES[name][3]
    failed=[row['name'] for row in data['checks'] if row['status']!='PASS']
    check=next((row for row in data['checks'] if row['name']==target),{})
    reply=check.get('observed',{})
    entries=[json.loads(row['data']) for row in json.loads((out/'readback-inbox_records.json').read_text())]
    events=json.loads((out/'readback-orchestration_events.json').read_text())
    starts=[json.loads(row['data']) for row in events if row['type']=='daemon_started']
    loaded=any(row.get('argv',[None,None])[1]==str(backend/'workbench/src/daemon.ts') for row in starts)
    worker='worker:'+data['attempt']['thread_id']
    entry=reply.get('entry',{})
    stored=next((row for row in entries if row['id']==entry.get('id')),None)
    if name=='assign':
        violation=stored is not None and stored['kind']=='assign' and stored['from']==worker
    elif name=='ready':
        violation=reply.get('ok') is True and [row['id'] for row in reply.get('ready',[])]==['W-READY']
    elif name=='foreign-ack':
        violation=stored is not None and stored['kind']=='ack' and stored['reply_to']=='foreign-message' and stored['from']==worker
    else:
        violation=stored is not None and stored.get('title')=='MUST_NOT_APPEND_AFTER_REVOKE' and stored['from']==worker
    valid=(data.get('setup_complete') and data.get('cleanup_complete') and len(data['checks'])==14
           and failed==[target] and not data.get('setup_or_probe_error') and not data.get('cleanup_error')
           and loaded and violation)
    return {'pass':bool(valid),'classification':'business-rule-counterexample','contract':target,
            'failed_checks':failed,'mutated_backend_loaded':loaded,'forbidden_outcome_observed':bool(violation),
            'gate_response':reply,'stored_forbidden_entry':stored}


def exercise(source,out,build,run):
    manifest=prepare(source,out/'worker-rule-mutants')
    verdicts={}
    report=out/'worker-rule-verdicts.json'
    with report.open('x',encoding='utf-8') as stream:json.dump(verdicts,stream)
    for name,item in manifest['mutants'].items():
        target=out/('worker-rule-'+name);backend=Path(item['backend_source'])
        run([sys.executable,'-B',source/'workbench/tests/test_t078_input_entry.py',
             '--source',source,'--backend-source',backend,'--reuse-build',build,
             '--worker-inbox','--output',target], 'worker-rule-'+name, timeout=240, expected=1)
        verdicts[name]=evaluate(name,target,backend)
        report.write_text(json.dumps(verdicts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if not verdicts[name]['pass']:raise RuntimeError('Worker rule counterexample lacks the forbidden business outcome: '+name)
    return verdicts
