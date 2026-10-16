"""只把已核对的实际 B1 产物路径写进新增独立命令；不发输入。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
for role in ['ideation', 'executor']:
    p1 = BASE / ('09c-c1-b1-' + role + '-p1-01')
    binding = json.loads((p1 / 'launch-binding.json').read_bytes())
    inp = json.loads((p1 / 'input.json').read_bytes())
    manifest = Path(binding['process_manifest'])
    actual = json.loads(manifest.read_bytes())
    assert all(inp[key] == actual[key] for key in ['launch', 'session'])
    assert manifest.parent.parent == p1 and manifest.parent.name == binding['launch_label']
    for path in p1.rglob('*COMMAND*.txt'):
        value = path.read_text(encoding='utf-8')
        fixed = value.replace('LAUNCH_LABEL', binding['launch_label']).replace('LAUNCH_MANIFEST', str(manifest))
        if fixed != value:
            path.write_text(fixed, encoding='utf-8')
print(json.dumps({'status': 'PASS', 'business_actions': 0, 'bindings': 'actual B1 manifests'}))
