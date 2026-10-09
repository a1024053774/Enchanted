"""Reproduce the recorded fixture overhead without altering run deadlines or business assertions."""
import importlib.util,json,os,sys,time,unittest
from pathlib import Path
source,label=sys.argv[1:]
out=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('controlled_run_fixture',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
original=module.RunCLI.events
observations=[]
def slow_events(self,*args,**kwargs):
    start=time.time();time.sleep(8.2)
    observations.append({'test':self.id(),'method':'events','start':start,'end':time.time(),'delay_seconds':8.2})
    return original(self,*args,**kwargs)
module.RunCLI.events=slow_events
suite=unittest.TestSuite(module.RunCLI(name) for name in ['test_run_entry_point_completes_registered_task',
    'test_matching_reclaim_guard_is_idempotent_after_automatic_success'])
result=unittest.TextTestRunner(verbosity=2,resultclass=module.EvidenceResult).run(suite)
record={'source':str(Path(source).resolve()),'argv':sys.argv,'results':module.TEST_RESULTS,
    'observations':observations,'commands':module.COMMANDS,'artifacts':module.ARTIFACTS,
    'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}
with (out/(label+'.json')).open('x',encoding='utf-8') as stream:json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
raise SystemExit(0 if result.wasSuccessful() else 1)
