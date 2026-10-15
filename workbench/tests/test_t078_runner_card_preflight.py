"""Card preflight oracle: oracle_paths protect acceptance files; deny is empty."""
import argparse, json
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2]
RUNNER=SOURCE/'evidence/2026-10-11-batch13/T-078/run-09b.py'
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir()
 card={'id':'t078-09b-card','source':None,'goal':'deterministic stage target','non_goals':['model'],
       'paths':{'allow':['value.txt'],'deny':[]},'oracle_paths':['oracle/contract-09b.json'],
       'completion_conditions':[{'argv':['/bin/echo','no-candidate']}],'red_commands':[],
       'task_type':'后端逻辑','repair_target':None,'complexity':'L','executor':{'cli':'Codex','model':'gpt-6.1-sol','effort':'xhigh'},'base_commit':None,'writer':None}
 path=a.output/'card.json';path.write_text(json.dumps(card,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 runner_scope={'__name__':'t078_runner_card_preflight','__file__':str(RUNNER)}
 exec(compile(RUNNER.read_text(encoding='utf-8'),str(RUNNER),'exec'),runner_scope)
 try:
  runner_scope['validate_card_preflight'](path)
  good=True
 except Exception:
  good=False
 bad=dict(card);bad['paths']={'allow':['value.txt'],'deny':['oracle/**']};bad_path=a.output/'bad-card.json';bad_path.write_text(json.dumps(bad),encoding='utf-8')
 try:
  runner_scope['validate_card_preflight'](bad_path)
  bad_rejected=False
 except Exception:
  bad_rejected=True
 result={'status':'PASS' if good and bad_rejected else 'INCOMPLETE','checks':[{'name':'valid-card-with-oracle_paths-and-empty-deny','status':'PASS' if good else 'INCOMPLETE'},{'name':'invalid-wildcard-deny-rejected','status':'PASS' if bad_rejected else 'INCOMPLETE'}],'spawned':False,'root_created':False,'scope':'run-09b card preflight through production Node gate; no daemon/API/target'}
 (a.output/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
