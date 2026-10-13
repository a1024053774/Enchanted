"""Freeze the unapproved five-turn instance, validate syntax, test only the oracle."""
import argparse
import ast
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import traceback

CARD = Path(__file__).resolve().parent
ROOT = CARD.parents[3]
BUNDLE = CARD / 'real-delivery-02'
MATERIALS = ['launch-policy.json','WORKER.md','REVIEWER.md','CONTRACT.txt','oracle.py',
             'worker.rules','worker-config.toml','reviewer-config.toml','worker-argv.txt','reviewer-argv.txt']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    report = dict(status='INCOMPLETE',product_status='INCOMPLETE',real_model_started=False,auth_copied=False,commands=[])
    def command(argv, expected=0, cwd=ROOT):
        p=subprocess.run(list(map(str,argv)),cwd=cwd,capture_output=True,text=True)
        report['commands'].append(dict(argv=list(map(str,argv)),cwd=str(cwd),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
        if p.returncode!=expected: raise RuntimeError('Static command failed: '+str(argv))
        return p.stdout.strip()
    try:
        policy=json.loads((BUNDLE / 'launch-policy.json').read_text())
        if (BUNDLE / 'APPROVED.json').exists() or Path(policy['root']).exists(): raise RuntimeError('Never regenerate an approved or started instance.')
        entries=[json.loads(l) for l in (CARD / 'real-turn-budget.jsonl').read_text().splitlines() if l.strip()]
        assert sum(r['reserved'] for r in entries if r['kind']=='reservation')==1
        assert [r['observed_main_turns'] for r in entries if r['kind']=='observation']==[1]
        if not Path('/Volumes/WD-Elements').is_mount(): raise RuntimeError('External disk is not mounted.')
        report['head']=command(['git','rev-parse','HEAD'])
        paths=sorted(str(p.relative_to(ROOT)) for folder in ('src','hooks','tests') for p in (ROOT / 'workbench' / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store')
        paths+=['workbench/package.json','workbench/package-lock.json','workbench/LICENSE.synara']; paths.sort()
        production=[p for p in paths if p.startswith(('workbench/src/','workbench/hooks/'))]
        tier_before = '"-c", `model_reasoning_effort=${JSON.stringify(effort)}`,'
        tier_after = tier_before + ' "-c", \'service_tier="default"\','
        with tarfile.open(CARD / 'real-delivery-01/source-snapshot.tar.gz','r:gz') as baseline:
            for name in production:
                expected=baseline.extractfile(name).read()
                if name=='workbench/src/panes.ts':
                    assert expected.count(tier_before.encode())==1
                    expected=expected.replace(tier_before.encode(),tier_after.encode())
                assert expected==(ROOT / name).read_bytes(), name
        with tarfile.open(BUNDLE / 'source-snapshot.tar.gz','w:gz',dereference=True) as archive:
            for name in paths: archive.add(ROOT / name,arcname=name,recursive=False)
        with tarfile.open(BUNDLE / 'approval-materials.tar.gz','w:gz') as archive:
            for name in sorted(MATERIALS): archive.add(BUNDLE / name,arcname=name,recursive=False)
        manifest=dict(head=report['head'],paths=paths,production_matches='real-delivery-01/source-snapshot.tar.gz',
                      matched_production_paths=[p for p in production if p!='workbench/src/panes.ts'],
                      approved_production_change=dict(path='workbench/src/panes.ts',before=tier_before,after=tier_after,authorization='controller #82'),
                      materials=sorted(MATERIALS),real_model_started=False,auth_copied=False)
        (BUNDLE / 'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
        for role in ('worker','reviewer'):
            item=policy[role]; assert shlex.split((BUNDLE / (role+'-argv.txt')).read_text())==item['argv']
            assert [a for a in item['argv'] if a.startswith('service_tier=')]==['service_tier="default"']
            assert item['argv'][item['argv'].index('service_tier="default"')-1]=='-c'
            assert item['argv'][item['argv'].index('-m')+1]=='gpt-6.1-sol'
            assert item['argv'][item['argv'].index('--sandbox')+1]==item['sandbox']
            assert 'model_reasoning_effort="xhigh"' in item['argv']
            assert (BUNDLE / (role+'-config.toml')).read_text()=='[projects."'+policy['repo']+'"]\ntrust_level="trusted"\n'
        assert policy['slots']==[2,3,4,5,6] and policy['global_turn_limit']==5
        assert (BUNDLE / 'worker.rules').read_text()=='prefix_rule(pattern=["git", "add"], decision="allow")\nprefix_rule(pattern=["git", "commit"], decision="allow")\n'
        for name in ('workbench/tests/run_t076_quality_real.py','workbench/tests/run_t076_launch_policy.py',
                     'workbench/tests/test_quality_tracer_e2e.py',str((BUNDLE / 'oracle.py').relative_to(ROOT))):
            ast.parse((ROOT / name).read_text(encoding='utf-8'),filename=name)
        command([policy['node'],'--check',ROOT / 'workbench/tests/quality_real_host.ts'])
        command([policy['node'],'--check',ROOT / 'workbench/src/panes.ts'])
        command(['zsh','-n',CARD / 'outside-sandbox.sh']); command(['git','diff','--check'])
        command(['python3','/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py','status','--root','.'])
        assert (BUNDLE / 'oracle.py').read_bytes()==(CARD / 'real-delivery-01/oracle.py').read_bytes()
        oracle_report=json.loads((CARD / 'real-delivery-preparation-04/run.json').read_text())
        assert oracle_report['status']=='PASS'
        report['unchanged_oracle_evidence']='real-delivery-preparation-04/run.json; identical oracle bytes, not rerun'
        for path in [BUNDLE / 'WORKER.md',BUNDLE / 'REVIEWER.md',CARD / 'REAL-DELIVERY-APPROVAL-02.md',CARD / 'RESULTS.md']:
            raw=path.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf') and b'\r' not in raw and '\ufffd' not in raw.decode('utf-8')
        report.update(status='PASS',frozen_source_files=len(paths),production_files_matching_old_approval=len(production)-1,
                      approved_production_change=manifest['approved_production_change'],accounted_real_turns=1,
                      reserved_new_turns=0,oversize_files=[str(p) for p in CARD.rglob('*') if p.is_file() and p.stat().st_size>5*1024*1024])
        assert not report['oversize_files']
    except Exception as error: report.update(status='INCOMPLETE',error=repr(error),traceback=traceback.format_exc())
    (args.output / 'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','product_status','real_model_started','auth_copied')}))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__': raise SystemExit(main())
