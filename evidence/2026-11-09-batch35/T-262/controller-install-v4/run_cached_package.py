"""Use a verified official Electron archive as standard packager cache input; keep all original validation."""
import argparse,json,os,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--slot',required=True);p.add_argument('--variant',choices=['release','test'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
node='/opt/homebrew/Cellar/node/26.5.0/bin/node'
prefetch=Path('/Users/luckye/Documents/Code/a2a/evidence/2026-11-09-batch35/T-262/controller-install-v4/prefetch-03.log')
verified=json.loads(prefetch.read_text().strip().splitlines()[-1]);archive=Path(verified['file']);assert archive.is_file()
slot=Path(os.environ['TMPDIR'])/('a2a-build-'+a.slot);assert not slot.exists()
a.output.mkdir(parents=True,exist_ok=False)
argv=[node,str(a.source/'workbench/app/package.mjs'),'--slot',a.slot,'--variant',a.variant]
revision=subprocess.check_output(['git','-C',str(a.source),'rev-parse','HEAD'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(a.source),'status','--porcelain','--','workbench'],text=True).strip()
(a.output/'command.json').write_text(json.dumps(dict(argv=argv,cwd=str(a.source),revision=revision,cache_input=verified,validation='Standard package.mjs unchanged; @electron/get independently downloads official SHASUMS256.txt and validates cache on use'),indent=2)+'\n')
cache=slot/'work/cache/electron'
with (a.output/'package.log').open('x') as log:
    child=subprocess.Popen(argv,cwd=a.source,stdout=log,stderr=subprocess.STDOUT)
    deadline=time.monotonic()+20
    while not slot.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.05)
    if slot.exists() and child.poll() is None:
        cache.mkdir(parents=True,exist_ok=True)
        seed=slot/'work/electron-seed.zip';shutil.copyfile(archive,seed)
        module=a.source/'workbench/node_modules/@electron/get/dist/Cache.js'
        js='import { Cache } from '+json.dumps(str(module))+'; const c=new Cache('+json.dumps(str(cache))+'); console.log(await c.putFileInCache("https://github.com/electron/electron/releases/download/v43.4.1/electron-v43.4.1-darwin-arm64.zip",'+json.dumps(str(seed))+',"electron-v43.4.1-darwin-arm64.zip"));'
        seeded=subprocess.run([node,'--input-type=module','-e',js],text=True,capture_output=True)
        (a.output/'cache-seed.json').write_text(json.dumps(dict(exit=seeded.returncode,stdout=seeded.stdout,stderr=seeded.stderr),indent=2)+'\n')
    code=child.wait()
(a.output/'exit.json').write_text(json.dumps(dict(exit=code))+'\n')
if code==0:
    result=json.loads((a.output/'package.log').read_text().strip().splitlines()[-1]);(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(exit=code,revision=revision,slot=str(slot))))
raise SystemExit(code)
