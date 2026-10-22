"""T-088 archive: copy a run directory to the external disk, check file count and bytes, leave a manifest, remove the original.
Usage: python3 archive.py <evidence dir relative to repo root> "<replay command>"."""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
original, replay = Path(sys.argv[1]), sys.argv[2]
source = ROOT / original
target = Path('/Volumes/WD-Elements/a2a-evidence') / original.relative_to('evidence')
assert source.is_dir() and not target.exists(), (source, target)
count = lambda root: (sum(1 for p in root.rglob('*') if p.is_file()), sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, target, symlinks=True)
files, size = count(source)
assert count(target) == (files, size), 'copy mismatch'
manifest = source.with_name(source.name + '.archive.json')
manifest.write_text(json.dumps(dict(original=str(original), archive=str(target), files=files, bytes=size, replay=replay), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
shutil.rmtree(source)
print(manifest.name, files, size)
