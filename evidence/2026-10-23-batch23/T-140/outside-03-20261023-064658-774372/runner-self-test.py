import json,sys
from pathlib import Path
p=Path(sys.argv[sys.argv.index('--summary')+1]); mode=sys.argv[-1]
if mode=='missing': sys.exit(0)
if mode=='malformed': p.write_text('{'); sys.exit(0)
if mode=='nonobject': p.write_text('[]'); sys.exit(0)
p.write_text(json.dumps({'status':'PASS'} if mode=='valid' else {'status':'INCOMPLETE','error':'AssertionError: T-RC_shell_boundary: test'}))
sys.exit(0 if mode=='valid' else 1)
