"""Independent result oracle, no auth or product helper imports. No model grant."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pwd
import resource
import stat
import sys

EXPECTED = {'none':None,'home-references-empty':'home_path_injection_must_be_reported',
 'scanner-zero':'credential_injection_must_be_detected','counts-always-match':'missing_raw_request_must_be_detected',
 'drop-first-record':'forwarder_record_count_must_match_upstream','empty-credential-cases':'credential_injection_cases_must_not_be_empty'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guarded',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--candidate',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('results',type=Path,nargs='+')
    args=parser.parse_args()
    home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if any(Path('/private/tmp') not in path.resolve().parents for path in [args.output,*args.results]):parser.error('results and output must be under /private/tmp')
    if not args.guarded:
        for descriptor in (1,2):
            if stat.S_ISREG(os.fstat(descriptor).st_mode):
                raw=fcntl.fcntl(descriptor,50,bytes(1024));path=Path(os.fsdecode(raw.split(b'\0',1)[0])).resolve()
                if path==home or home in path.parents:os.close(descriptor);os._exit(2)
        limit=resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if limit==resource.RLIM_INFINITY:parser.error('finite descriptor limit required')
        os.closerange(3,limit)
        policy='(version 1)(allow default)(deny file-write* (subpath '+json.dumps(str(home))+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
        os.execve('/usr/bin/sandbox-exec',['sandbox-exec','-p',policy,'/usr/bin/python3','-I','-S','-B',str(Path(__file__).resolve()),'--guarded',*sys.argv[1:]],{'PATH':'/usr/bin:/bin','LANG':'C'})
    if args.output.exists() or home in args.output.resolve().parents:parser.error('select a new output outside real HOME')
    cases=[];seen=set()
    for path in args.results:
        value=json.loads(path.read_text());kind=value.get('mutation');expected=EXPECTED.get(kind,'unknown')
        good=kind in EXPECTED and kind not in seen and value.get('candidate')==args.candidate
        seen.add(kind)
        good=good and value.get('primary_failure')==expected and value.get('status')==('PASS' if expected is None else 'INCOMPLETE')
        good=good and value.get('cleanup_failures')==[] and value.get('fixture_removed') is True
        good=good and all(value.get(k)==0 for k in ('real_model_turns','real_cli_starts','real_upstream_requests','real_auth_reads','git_index_credential_hits'))
        if kind=='none':
            raw=value.get('forwarder_raw_records',[]);requests=[r for r in raw if r.get('kind')=='request'];outcomes=[r for r in raw if r.get('kind')=='outcome']
            receipts=value.get('independent_upstream_receipts',[]);facts=value.get('facts',{});counter=value.get('counterexamples',{})
            good=good and [r.get('sequence') for r in requests]==[1,2] and [r.get('status') for r in outcomes]==[400,200]
            good=good and len(receipts)==2 and all(r.get('recorded_before_receipt') and r.get('bearer_matches_copy') and r.get('messages_present') and r.get('prompt_matches_fixture') for r in receipts)
            good=good and facts.get('counts',{}).get('model_requests')==2 and facts.get('counts',{}).get('counts_match') is True
            good=good and facts.get('isolated_home_removed') is True and facts.get('credential_scan',{}).get('hits')==0
            good=good and facts.get('inventory',{}).get('collection_complete') is True and facts.get('inventory',{}).get('pass_condition') is False
            good=good and facts.get('inventory',{}).get('before_phase')=='before_original_auth_read'
            initial=counter.get('preflight',{})
            good=good and initial.get('phase')=='before_cli_input' and initial.get('counts',{}).get('model_requests')==0 and initial.get('counts',{}).get('counts_match') is True and initial.get('credential_scan',{}).get('hits')==0 and initial.get('credential_scan',{}).get('launch_record_hits')==0 and initial.get('inventory',{}).get('comparison_pending') is True
            good=good and counter.get('synthetic_guard',{}).get('mutant_rejected') is True
            good=good and counter.get('forwarder',{}).get('unconfigured_upstream',{}).get('denied') is True and counter.get('cli',{}).get('upstream_bypass',{}).get('denied') is True
            good=good and len(counter.get('credential_injections',[]))==6 and all(r.get('hits',0)>0 for r in counter.get('credential_injections',[]))
            good=good and counter.get('missing_record',{}).get('counts',{}).get('counts_match') is False
            good=good and facts.get('cleanup',{}).get('cleanup_failures')==[] and facts.get('cleanup',{}).get('primary_failure') is None
            parent=counter.get('parent_home_write',{});f=counter.get('forwarder',{});cli=counter.get('cli',{});helpers=counter.get('protected_helpers',[])
            for boundary in (counter.get('home_read_boundary_C',{}),f.get('home_read_boundary',{})):
                target=boundary.get('target')
                good=good and isinstance(target,str) and Path(target).name=='AGENTS.md' and home in Path(target).parents
                metadata=boundary.get('metadata',[])
                good=good and len(metadata)==2 and {v.get('path') for v in metadata}=={str(home),str(Path(target).parent) if isinstance(target,str) else None} and all(v.get('is_directory') is True for v in metadata)
                good=good and boundary.get('entry_resolved') is True and boundary.get('content',{}).get('denied') is True and boundary.get('content',{}).get('bytes_read')==0 and boundary.get('ancestor_directory_entries',{}).get('denied') is True
                good=good and boundary.get('content',{}).get('code') in ('EPERM','EACCES') and boundary.get('ancestor_directory_entries',{}).get('code') in ('EPERM','EACCES')
            home_guards=[parent,f.get('real_home_write',{}),cli.get('real_home_write',{}),*[v.get('real_home_write',{}) for v in helpers]]
            good=good and len(helpers)==3 and all(g.get('denied') is True and g.get('created') is False and isinstance(g.get('errno'),int) and abs(g['errno']) in (1,13) for g in home_guards)
            good=good and f.get('outside_records_write',{}).get('denied') is True and f.get('other_listener',{}).get('denied') is True and f.get('fork',{}).get('denied') is True
            good=good and cli.get('source_home')=={'r':True,'a':True} and cli.get('config_matches') is True
            good=good and all(v.get('fork',{}).get('denied') is True and sorted(v.get('security',{}).values())==[1100,1100] for v in helpers)
            synthetic=counter.get('synthetic_guard',{});base=synthetic.get('baseline',{});mutant=synthetic.get('mutant',{});written=mutant.get('synthetic_write',{})
            good=good and base.get('primary_failure') is None and base.get('synthetic_write',{}).get('denied') is True
            good=good and mutant.get('primary_failure')=='home_write_must_be_denied' and all(written.get(k) is True for k in ('created','deleted','absent_after'))
            good=good and all(v.get('real_home_write',{}).get('denied') is True and v.get('real_home_write',{}).get('created') is False for v in (base,mutant))
            expected_paths=[g.get('path') for g in home_guards]+[base.get('real_home_write',{}).get('path'),mutant.get('real_home_write',{}).get('path')]
            observed=facts.get('processes',{}).get('D',{}).get('home_probe_paths',[])
            good=good and len(expected_paths)==8 and len(observed)==8 and set(expected_paths)=={v.get('path') for v in observed} and all(v.get('absent') is True for v in observed)
            good=good and all(isinstance(p,str) and Path(p).parent==home and Path(p).name.startswith('.a2a-t093-deny-') for p in expected_paths)
        cases.append({'case':kind if kind in EXPECTED else 'unknown','pass':bool(good),'expected_primary':expected if kind in EXPECTED else None,'primary_matched':value.get('primary_failure')==expected})
    result={'status':'PASS' if seen==set(EXPECTED) and all(c['pass'] for c in cases) else 'INCOMPLETE','candidate':args.candidate,'cases':cases,
            'scope':'Independent fixture verdict only. No authorization to start a model turn.','profile':'V; no HOME writes, network or Security'}
    with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'status':result['status'],'cases':len(cases)}));return 0 if result['status']=='PASS' else 2

if __name__=='__main__':raise SystemExit(main())
