"""Check the Stage A receipt gate only. No prepare, runtime root or launch."""
import copy
import importlib.util
import json
from pathlib import Path
import traceback
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    gate=load('C3_gate',BASE/'c3-revalidation.py');runner=load('C3_runner',BASE/'run-09b.py')
    result={'status':'INCOMPLETE','scene_starts':0,'keys':0,'signals':0};checks=[]
    try:
        runtime=gate.receipts()['source_revision']
        binding={'regression_readbacks':[str(BASE/name/'result.json') for name in runner.REGRESSION_REPORTS],
            'harness_profile':'c3-caffeinate-v1','harness_rehearsal':str(gate.REHEARSAL/'result.json'),
            'harness_kernel_check':str(gate.KERNEL),
            'coordinator_rehearsal':str(BASE/'09c-coordinator-rehearsal-01/real-chain-outside-01/result.json'),
            'runtime_source_revision':runtime,'harness_delta_paths':['workbench/tests/'+name for name in gate.REPAIRS]+gate.META}
        static={'scene':'09C','source_paths':[],**binding};approval=copy.deepcopy(binding)
        validated=runner.validate_regression_readbacks(static,approval)
        assert validated['status']=='PASS' and validated['legacy_overall_status']=='INCOMPLETE'
        assert validated['CAS_replacement']==binding['regression_readbacks'][1] and validated['lock_completion']==binding['regression_readbacks'][2]
        checks.append('exact four regressions plus coordinator/kernel/parity-02 accepted; legacy exception explicit')
        for key,wrong in [('regression_readbacks',binding['regression_readbacks'][:2]),
            ('harness_rehearsal',str(BASE/'09c-caffeinate-parity-rehearsal-01/result.json')),
            ('harness_kernel_check','wrong-kernel.json'),('coordinator_rehearsal','wrong-coordinator.json'),
            ('runtime_source_revision','not-the-rehearsed-runtime'),('harness_delta_paths',[])]:
            bad=copy.deepcopy(approval);bad[key]=wrong
            try:runner.validate_regression_readbacks(static,bad)
            except AssertionError:checks.append('rejected:'+key)
            else:raise AssertionError('bad receipt binding accepted:'+key)
        with patch.object(gate,'REHEARSAL',BASE/'09c-caffeinate-parity-rehearsal-01'):
            try:gate.receipts()
            except AssertionError:checks.append('old overall-INCOMPLETE rehearsal still rejected')
            else:raise AssertionError('old failed cleanup accepted')
        # A changed tested function or executable-path test must not inherit the
        # old kernel PASS. Replace only the Git read transport, not the gate.
        original=gate.subprocess.check_output
        def changed(argv,**kwargs):
            data=original(argv,**kwargs)
            if argv[0:2]==['git','show'] and argv[2].endswith(':workbench/tests/t078_raw_retention.py'):
                assert 'buffer=ctypes.create_string_buffer(4096)' in data
                return data.replace('buffer=ctypes.create_string_buffer(4096)','buffer=ctypes.create_string_buffer(8192)')
            return data
        with patch.object(gate.subprocess,'check_output',changed):
            try:gate.kernel_source_binding(json.loads(gate.KERNEL.read_bytes())['source_revision'])
            except AssertionError as error:
                assert str(error)=='kernel_probe_function_source_changed';checks.append('changed kernel function text rejected')
            else:raise AssertionError('changed kernel method accepted')
        result.update(status='PASS',checks=checks,validation=validated,runtime_source_revision=runtime)
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    path=Path(__file__).with_name('gate-check.json')
    with path.open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'error':result.get('error')}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
