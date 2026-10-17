"""Replay the recorded native s13 at the actual idle observer; no live ps/API/CLI."""
import argparse
import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch
import t078_topology_probe as probe

SOURCE=Path(__file__).resolve().parents[2]
FIXTURE=SOURCE/'evidence/2026-10-11-batch13/T-078/09c-topology-probe-run-01/ideation-p1/a365-ideation-s13-screen'


def frame(draft='',mode='manual mode on'):
    return ('\r\n'+'─'*60+'\r\n❯ '+draft+'\r\n'+'─'*60+'\r\n⏸ '+mode+' · ? for shortcuts\r\n').encode()


def run(module,out,only_positive):
    raw=(FIXTURE/'screen.bin').read_bytes();meta=json.loads((FIXTURE/'screen.json').read_bytes())
    assert raw==base64.b64decode(meta['output']['data_base64'])
    assert len(raw)==meta['capture']['total_bytes']==8799 and b'manual mode on' not in raw
    cases=[('recorded-native-s13',raw,len(raw),True)]
    if not only_positive:
        prompt=raw.rfind('❯'.encode())+len('❯'.encode());manual=raw.rfind(b'manual')
        assert prompt>0 and manual>prompt
        cases += [('recorded-inline-draft',raw[:prompt]+b'kept draft'+raw[prompt:],None,False),
                  ('recorded-inline-plan',raw[:manual]+b'plan'+raw[manual+len(b'manual'):],None,False),
                  ('nonempty-prompt',raw+frame('unfinished draft'),None,False),
                  ('multiline-nonempty-prompt',raw+frame('\r\nkeep this draft'),None,False),
                  ('non-manual-historical-manual',raw+frame(mode='plan mode on'),None,False),
                  ('manual-off',raw+frame(mode='manual mode off'),None,False),
                  ('truncated-transport',raw[:-40],len(raw),False),
                  ('missing-editor-end',raw+('\r\n'+'─'*60+'\r\n❯ ').encode(),None,False),
                  ('complete-empty-manual-frame',raw+frame(),None,True)]
    results=[]
    for label,payload,total,expected in cases:
        with tempfile.TemporaryDirectory(prefix='t078-idle-replay-',dir='/private/tmp') as tmp:
            root=Path(tmp).resolve();(root/'roles/ideation/http-exchanges').mkdir(parents=True)
            folder=root/'probe';folder.mkdir();output=root/'new-output';output.mkdir()
            launch=meta['launch'];calls=[];sample=[]
            def gate(root_arg,command,*args):
                assert command=='pane_output','idle must not issue a write/control command'
                offset=int(args[args.index('--offset')+1]);part=payload[offset:offset+4096]
                calls.append({'command':command,'offset':offset})
                return {'launch':launch,'start_offset':offset,'next_offset':offset+len(part),
                    'total_bytes':len(payload) if total is None else total,'data_base64':base64.b64encode(part).decode()}
            args=SimpleNamespace(mode='idle',probe=folder,output=output)
            identity={'root':str(root),'processes':{},'scope':'explicit saved-I/O replay, not live process proof'}
            value=None;error=None
            with patch.object(module,'load_probe',return_value=({},root,folder,{'launch':launch},identity)), \
                 patch.object(module,'gate',gate),patch.object(module,'sample_for',side_effect=lambda *a:sample.append(a[2])):
                try:value=module.observe(args)
                except (ValueError,AssertionError) as ex:error=repr(ex)
            accepted=bool(value and value['status']=='PASS')
            row={'case':label,'expected_accept':expected,'accepted':accepted,'error':error,
                'sampler_calls':len(sample),'gate_calls':calls,'key_writes':0,'ps_calls':0}
            results.append(row)
            with (out/(label+'.json')).open('x',encoding='utf-8') as stream:stream.write(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
            assert accepted==expected,(label,error)
            assert len(sample)==(1 if expected else 0),'a rejected screen must stop before ps sampling/owner journaling'
            assert (folder/'probe-original-role.json').exists()==expected
            assert all(row['command']=='pane_output' for row in calls)
    return results


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-file',type=Path);parser.add_argument('--only-positive',action='store_true')
    parser.add_argument('--mutant',choices=['marker-only']);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','source_fixture':str(FIXTURE),'scene_starts':0,'scope':'actual idle observe entry; recorded PTY gate pages and explicit process transport spy'}
    try:
        module=probe
        if args.source_file:
            spec=importlib.util.spec_from_file_location('old_topology_probe',args.source_file)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            result['loaded_source']=str(args.source_file)
        if args.mutant=='marker-only':
            def marker_only(raw,capture):
                if '❯' not in raw.decode('utf-8'):raise ValueError('prompt_marker_required')
                return {'mode':'manual','editor':{'empty':True},'scope':'known-bad marker-only mutant'}
            module.empty_manual_prompt=marker_only
            result['mutant']=args.mutant
        result.update(checks=run(module,args.output,args.only_positive),status='PASS')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    with (args.output/'result.json').open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(result.get('checks',[])),'error':result.get('error'),'scene_starts':0}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
