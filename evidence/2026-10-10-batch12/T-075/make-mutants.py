"""隔离变异体，不改候选；从同一门禁源码产生三份最小变更。"""
from pathlib import Path
import argparse
import difflib
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
p=argparse.ArgumentParser()
p.add_argument('--output', default='mutants')
args=p.parse_args()
destination=BASE/args.output
destination.mkdir(exist_ok=False)
gates=ROOT/'workbench/src/gates'
core=(gates/'core.ts').read_text(encoding='utf-8')
cli=(gates/'cli.ts').read_text(encoding='utf-8')
changes={
'fence':('        requireGate(args.fence === attempt.fence, "stale_fence");','        // MUTANT: omit the delivery fence check.'),
'cas':('argv: ["git", "-C", task.repo, "update-ref", REF, v.M, v.G],','argv: ["git", "-C", task.repo, "update-ref", REF, v.M],'),
'lock':('      lock.exec("BEGIN IMMEDIATE");\n      return lock;','      // MUTANT: omit the operation-lock transaction.\n      return lock;'),
}
def imports(text):
    for old,new in [('../contracts/index.ts',str(destination/'contracts/index.ts')),('./membership.ts',str(destination/'support/membership.ts')),('./rolePermissions.ts',str(destination/'support/rolePermissions.ts')),('effect',str(ROOT/'workbench/node_modules/effect/dist/index.js'))]:
        text=text.replace('from "'+old+'"','from "'+new+'"')
    return text
for folder, files in [('contracts', (ROOT/'workbench/src/contracts').glob('*.ts')),
                      ('support', [gates/'membership.ts', gates/'rolePermissions.ts'])]:
    (destination/folder).mkdir()
    for source in files:
        (destination/folder/source.name).write_text(imports(source.read_text(encoding='utf-8')),encoding='utf-8')
(destination/'package.json').write_text('{"type":"module"}\n',encoding='utf-8')
for name,(old,new) in changes.items():
    assert core.count(old)==1,(name,core.count(old))
    out=destination/name
    out.mkdir(parents=True,exist_ok=False)
    changed=core.replace(old,new)
    (out/'mutation.patch').write_text(''.join(difflib.unified_diff(core.splitlines(True),changed.splitlines(True),fromfile='candidate/core.ts',tofile=name+'/core.ts')),encoding='utf-8')
    (out/'core.ts').write_text(imports(changed),encoding='utf-8')
    (out/'cli.ts').write_text(imports(cli),encoding='utf-8')
    (out/'package.json').write_text('{"type":"module"}\n',encoding='utf-8')
