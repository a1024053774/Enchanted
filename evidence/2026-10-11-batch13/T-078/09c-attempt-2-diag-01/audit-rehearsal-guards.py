"""Inventory scene branches and demonstrate current bypasses; no scene/process I/O."""
import argparse
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[4];BASE=SOURCE/'evidence/2026-10-11-batch13/T-078'
sys.path.insert(0,str(SOURCE/'workbench/tests'))
import t078_raw_retention as raw


def write(path,value):
    with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


class ProbeReached(Exception):pass


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    names=subprocess.check_output(['rg','--files','workbench/tests','evidence','-g','*.py','-g','*.ts','-g','*.mjs','-g','*.js'],cwd=SOURCE,text=True).splitlines()
    literal=[];branches=[]
    for relative in names:
        path=SOURCE/relative
        try:text=path.read_text(encoding='utf-8')
        except UnicodeDecodeError:continue
        lines=text.splitlines()
        for number,line in enumerate(lines,1):
            if 'REHEARSAL' in line:literal.append({'file':relative,'line':number,'text':line})
        if path.suffix!='.py':continue
        try:tree=ast.parse(text)
        except SyntaxError:continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.If,ast.IfExp)):
                expression=ast.unparse(node.test)
                if any(word in expression.lower() for word in ['scene','rehearsal','offline','dry_run','check_only']):
                    branches.append({'file':relative,'line':node.lineno,'condition':expression,
                        'classification':'candidate condition; requires semantic review, not automatically a bypass'})
    write(args.output/'literal-REHEARSAL-all-text-copies.json',{'files_scanned':len(names),'rows':literal,
        'scope':'all rg-visible source text under workbench/tests and evidence; historical textual copies included; tar members are versioned snapshots, not modified'})
    write(args.output/'scene-and-mode-branches.json',{'rows':branches,'scope':'Python AST conditions; raw literal inventory also covers TS/JS; historical copies included'})
    functions=ast.parse((SOURCE/'workbench/tests/t078_raw_retention.py').read_text(encoding='utf-8'))
    receipts=next(n for n in functions.body if isinstance(n,ast.FunctionDef) and n.name=='validate_owner_receipts')
    checks=[{'line':n.lineno,'code':ast.unparse(n)} for n in ast.walk(receipts)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require']
    write(args.output/'skipped-owner-receipt-checks.json',{'file':'workbench/tests/t078_raw_retention.py','function_line':receipts.lineno,'checks':sorted(checks,key=lambda n:n['line'])})
    owner=json.loads((BASE/'09c-attempt-2-materials-02/owner.json').read_bytes())
    class Runtime:
        def __init__(self,value):self.value=value;self.topology_calls=0
        def identities(self):return self.value['processes']
        def topology(self):self.topology_calls+=1;raise ProbeReached('topology reached')
    results=[]
    for case in ['operational-reference','rehearsal-owner-receipts','rehearsal-nine-processes','rehearsal-topology']:
        value=copy.deepcopy(owner)
        if case!='operational-reference':value['scene']='REHEARSAL'
        if case=='rehearsal-nine-processes':value['processes'].pop('executor_api')
        runtime=Runtime(value);calls=[];original=raw.validate_owner_receipts
        def observed_receipts(value):calls.append('owner receipts');return original(value)
        error=None
        with patch.object(raw,'validate_owner_receipts',observed_receipts):
            try:raw.check_identities(value,runtime)
            except ProbeReached:error='topology reached'
        if case=='operational-reference':assert calls and runtime.topology_calls==1 and error
        else:assert not calls and runtime.topology_calls==0 and error is None
        results.append({'case':case,'owner_receipt_calls':len(calls),'topology_calls':runtime.topology_calls,
            'owned_process_count':len(value['processes']),'expected_red_observed':case!='operational-reference',
            'scope':'identity/topology transport is an explicit spy; metadata receipt checks use the unchanged actual scene files'})
    write(args.output/'bypass-red.json',{'status':'INCOMPLETE','kind':'rehearsal parity contract; no fix applied',
        'checks':results,'scene_process_starts':0,'signals_sent':[],'key_writes':0,
        'missing_green':'requires proven process classification and equivalent real owner/manifest/topology inputs; do not mark PASS'})
    print(json.dumps({'status':'INCOMPLETE','inventory_written':True,'source_text_files':len(names),
        'literal_rows':len(literal),'scene_mode_branches':len(branches),'bypass_contract_red_cases':3,'scene_process_starts':0}))


if __name__=='__main__':main()
