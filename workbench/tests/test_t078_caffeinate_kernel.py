"""Outside-sandbox OS executable-path check; two bounded owned helper processes, no roles/models."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time
import traceback
from t078_raw_retention import NativeRuntime,save,require


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={'status':'INCOMPLETE','role_CLIs':0,'model_turns':0,'signals_sent':[],'checks':[],
        'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip()};children=[]
    try:
        with tempfile.TemporaryDirectory(prefix='t078-caff-kernel-',dir='/private/tmp') as tmp:
            root=Path(tmp).resolve();source=root/'fake.c';binary=root/'caffeinate'
            source.write_text('#include <unistd.h>\nint main(void){sleep(2);return 0;}\n',encoding='utf-8')
            built=subprocess.run(['/usr/bin/clang',str(source),'-o',str(binary)],capture_output=True,timeout=20)
            (a.output/'compile.stdout.bin').write_bytes(built.stdout);(a.output/'compile.stderr.bin').write_bytes(built.stderr)
            require(built.returncode==0,'owned fake compilation')
            runtime=NativeRuntime({})
            for executable,n,expected in [('/usr/bin/caffeinate','2',True),(str(binary),'300',False)]:
                child=subprocess.Popen(['caffeinate','-i','-t',n],executable=executable,
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True);children.append(child)
                try:
                    first=runtime.helper_identity(child.pid);path=runtime.executable_path(child.pid)
                    second=runtime.helper_identity(child.pid);path2=runtime.executable_path(child.pid)
                    require(first is not None and first==second and path==path2,'stable owned fixture PID')
                    accepted=path=='/usr/bin/caffeinate';require(accepted==expected,'kernel path distinguishes identical argv0')
                    result['checks'].append({'pid':child.pid,'identity':first,'kernel_executable':path,'expected_system_binary':expected,'status':'PASS'})
                finally:child.wait(timeout=5)
            result.update(status='PASS',scratch_removed=True,scope='actual proc_pidpath and ps; owned short-lived processes, not a role/daemon rehearsal')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    finally:
        for child in children:require(child.poll() is not None,'owned helper exit required')
    save(a.output/'result.json',result);print(json.dumps({'status':result['status'],'checks':len(result['checks'])}));return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
