import sys, pathlib, subprocess, shutil, tempfile
p=pathlib.Path(sys.argv[1]); output=sys.argv[2]
def forbidden(*a, **k): raise RuntimeError('PREFLIGHT_SIDE_EFFECT_FORBIDDEN')
subprocess.run=forbidden
shutil.rmtree=forbidden
tempfile.mkdtemp=forbidden
pathlib.Path.mkdir=forbidden
source=p.read_text(encoding='utf-8')
assert source.count('parents[4]')==1
source=source.replace('parents[4]','parents[5]')
sys.argv=[str(p),'--preflight','--output',output]
exec(compile(source,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
