from pathlib import Path
from argparse import Namespace
import importlib.util,json,tempfile,traceback,subprocess,shutil,sys
source=Path('/Users/luckye/Library/Application Support/a2a-orchestrator/worktrees/a2a/T-265-1-a1/workbench/tests/test_t265_review_cli_e2e.py')
base=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t265_exact_driver',source);driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
root=Path(tempfile.mkdtemp(prefix='t265-candidate-05-',dir='/private/tmp'));artifacts=base/'native-candidate-05-artifacts';artifacts.mkdir()
args=Namespace(parent=driver.BASE,node=driver.NODE,codex=str(Path('/Users/luckye/.local/bin/codex').resolve()),auth=Path.home()/'.codex/auth.json',timeout=240)
report=dict(status='INCOMPLETE',scope='原 native04 脚本未改动的 candidate case；父版真实拒绝见 native-cli-03-parent-rejection.json 与 native-cli-04 原始终端。原04整体未完成的结论保持。',command=sys.argv,source=str(source),fixture=str(root),native_version=subprocess.check_output([args.codex,'--version'],text=True).strip(),case={})
try:
 driver.case(args,root,'candidate',artifacts,report['case'])
 report['status']='PASS'
except BaseException as error:
 report.update(error=str(error),traceback=traceback.format_exc())
finally:
 files=[p for p in root.rglob('*') if p.is_file()]
 report['cleanup']=dict(directory=str(root),files=len(files),bytes=sum(p.stat().st_size for p in files),removed=False)
 driver.save(artifacts/'before-cleanup.json',report)
 if report['case'].get('process',{}).get('cleanup',{}).get('complete'):
  shutil.rmtree(root);report['cleanup']['removed']=not root.exists()
 driver.save(base/'native-candidate-05.json',report)
print(json.dumps(dict(status=report['status'],summary=str(base/'native-candidate-05.json'))))
raise SystemExit(0 if report['status']=='PASS' else 1)
