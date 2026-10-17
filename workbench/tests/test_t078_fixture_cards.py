"""Execute actual T-078 card producers, then validate their schema without a daemon."""
import argparse,ast,json,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
source=Path(__file__).resolve().parents[2];cards=[]
for name in ['test_t078_input_entry.py','run_t078_p1.py']:
 path=source/'workbench/tests'/name;tree=ast.parse(path.read_text(encoding='utf-8'))
 assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Dict) and any(isinstance(t,ast.Name) and t.id=='card' for t in n.targets))
 card=eval(compile(ast.Expression(assignment.value),str(path),'eval'),{'sys':sys,'task':'input-contract','approval':{'input':{'task':'t078-p1-fixture-card'}}})
 cards.append({'producer':name,'card':card})
path=source/'workbench/tests/test_t078_inbox_entry.py';tree=ast.parse(path.read_text(encoding='utf-8'))
update=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='card' and n.func.attr=='update')
fields={kw.arg:eval(compile(ast.Expression(kw.value),str(path),'eval'),{'sys':sys}) for kw in update.keywords}
cards.append({'producer':path.name,'template_id':'inbox-task','update':fields})
(args.output/'produced.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
js='''import {readFileSync} from 'node:fs';import {taskCardTemplate,validateTaskCard} from './workbench/src/gates/taskCards.ts';
const inputs=JSON.parse(readFileSync(process.argv[1],'utf8'));const checks=[];
for(const input of inputs){const card=input.card??Object.assign(taskCardTemplate(input.template_id),input.update);try{
 const value=validateTaskCard(card,card.id);if(JSON.stringify(value.oracle_paths)!==JSON.stringify(['value.txt']))throw Error('expected fixed fixture oracle value.txt');
 checks.push({producer:input.producer,status:'PASS',oracle_paths:value.oracle_paths});
}catch(e){checks.push({producer:input.producer,status:'INCOMPLETE',error:String(e),field:e.field});}}
console.log(JSON.stringify({status:checks.every(v=>v.status==='PASS')?'PASS':'INCOMPLETE',checks}));process.exitCode=checks.every(v=>v.status==='PASS')?0:1;
'''
argv=['node','--input-type=module','-e',js,str(args.output/'produced.json')];r=subprocess.run(argv,cwd=source,capture_output=True,text=True)
(args.output/'stdout.bin').write_text(r.stdout,encoding='utf-8');(args.output/'stderr.bin').write_text(r.stderr,encoding='utf-8')
result=json.loads(r.stdout);result.update(argv=argv,exit_code=r.returncode,scope='Actual card-producer expressions and production schema; no claim/daemon/UI/CLI/model start; oracle starting-file existence is for outside entry check')
(args.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');(args.output/'probe.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'status':result['status'],'checks':result['checks']},ensure_ascii=False));raise SystemExit(r.returncode)
