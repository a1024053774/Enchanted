"""冻结候选及独立变异体；只在本卡证据目录和 /tmp 新目录中写入。"""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
parser = argparse.ArgumentParser()
parser.add_argument('--label', default='mutants-01')
args = parser.parse_args()
if Path(args.label).name != args.label or not args.label.startswith('mutants-'):
    parser.error('label 必须为新的 mutants-* 目录名')
OUT = BASE / args.label
OUT.mkdir(exist_ok=False)
source = ROOT / 'workbench/src/gates'
core = (source / 'core.ts').read_text(encoding='utf-8')
mutation_root = Path(tempfile.mkdtemp(prefix='a2a-card2-mutants-', dir='/tmp'))
shutil.copytree(ROOT / 'workbench/src/contracts', mutation_root / 'contracts')
shutil.copyfile(ROOT / 'workbench/package.json', mutation_root / 'package.json')
shutil.copyfile(ROOT / 'workbench/package-lock.json', mutation_root / 'package-lock.json')
os.symlink(ROOT / 'workbench/node_modules', mutation_root / 'node_modules', target_is_directory=True)
changes = {
    'path': ('const forbidden = [...paths].filter((path) => !pathAllowed(card, path));',
             'const forbidden: string[] = [];'),
    'trailer': ('if (trailers.task?.some((value) => value !== task.task_id)) error = "trailer_task_mismatch";',
                'if (trailers.task?.some((value) => value !== task.task_id)) error = null;'),
    'cas': ('${intent.M} ${intent.G}\\nprepare\\n', '${intent.M}\\nprepare\\n'),
    'fast-forward': ('requireGate(await this.ancestor(task.task_id, task.repo, intent.G, intent.M), "integration_not_fast_forward");',
                     '/* mutation: omit the fast-forward check */'),
}
start = core.index('      if (intent.worktree) {', core.index('private async advanceWorkBranch'))
end = core.index('      await this.checkIntegrationHead(task, intent.worktree);', start)
changes['dirty'] = (core[start:end], '      /* mutation: omit the checked-out worktree update and its protection */\n')
records = []
for name, (before, after) in changes.items():
    assert core.count(before) == 1, (name, core.count(before))
    target = mutation_root / name
    shutil.copytree(source, target)
    changed = core.replace(before, after, 1)
    (target / 'core.ts').write_text(changed, encoding='utf-8')
    patch = ''.join(difflib.unified_diff(core.splitlines(True), changed.splitlines(True),
                                       fromfile='candidate/core.ts', tofile=name + '/core.ts'))
    (OUT / (name + '.patch')).write_text(patch, encoding='utf-8')
    records.append({'name': name, 'gate': str(target / 'cli.ts'), 'core': str(target / 'core.ts')})
with tarfile.open(OUT / 'sources.tar.gz', 'w:gz') as archive:
    archive.add(mutation_root, arcname=mutation_root.name)
with (OUT / 'manifest.json').open('x', encoding='utf-8') as out:
    json.dump({'root': str(mutation_root), 'mutants': records,
               'head': subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(),
               'scope': 'candidate working tree captured with each mutation patch'}, out, ensure_ascii=False, indent=2)
    out.write('\n')
diff = subprocess.check_output(['git','diff','--','workbench','acceptance'],cwd=ROOT,text=True)
(OUT / 'candidate-tracked.diff').write_text(diff,encoding='utf-8')
print(json.dumps({'root': str(mutation_root), 'mutants': records},ensure_ascii=False))
