"""重现来源提取；仅在没有 workbench 的起点 checkout 执行。"""
from pathlib import Path
import subprocess, re, json
root=Path(__file__).resolve().parents[3]
fork=root.parent/'synara'
rev='49cae984f22924de006e0f8358cb447eb881aaf6'
wb=root/'workbench'
if wb.exists():
    raise SystemExit('拒绝覆盖已有 workbench')
header='// Derived from Synara, MIT License.\n// Copyright (c) 2026 T3 Tools Inc.\n// Copyright (c) 2026 Emanuele Di Pietro\n// See ../../LICENSE.synara for the full permission notice.\n\n'
def source(path):
    return subprocess.check_output(['git','-C',str(fork),'show',rev+':'+path],text=True)
def put(path,text):
    p=wb/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8')
def ts(path,text):
    text=re.sub(r'(from "\.[^"]+)(")',r'\1.ts\2',text)
    put(path,header+text)
for name in ['core','cli','membership','rolePermissions']:
    text=source('packages/a2a-gates/src/'+name+'.ts')
    text=text.replace('"@synara/contracts"','"../contracts/index"').replace('"@synara/shared/processRuntime"','"./processRuntime"')
    ts(Path('src/gates')/(name+'.ts'),text)
for name in ['a2aGates','a2aMembership','a2aInbox','a2aRolePermissions']:
    text=source('packages/contracts/src/'+name+'.ts')
    text=text.replace('"./orchestration"','"./modelSelection"')
    if name=='a2aMembership': text=text[:text.index('export const A2AMembershipSaveRequest')]
    ts(Path('src/contracts')/(name+'.ts'),text)
base=source('packages/contracts/src/baseSchemas.ts')
text=base[:base.index('export const PositiveInt')]
text+=base[base.index('/**\n * Construct a branded identifier.'):base.index('export const SpaceId')]
provider=source('packages/contracts/src/providerInstance.ts')
text+=provider[provider.index('const PROVIDER_SLUG_MAX_CHARS'):provider.index('const ENVIRONMENT_VARIABLE_NAME_MAX_CHARS')]
text+=provider[provider.index('const ProviderSlug ='):provider.index('// Driver kind')]
text+=provider[provider.index('export const ProviderInstanceId ='):provider.index('export const ProviderInstanceRef')]
ts(Path('src/contracts/baseSchemas.ts'),text)
model=source('packages/contracts/src/model.ts')
text='import { Schema } from "effect";\nimport { TrimmedNonEmptyString } from "./baseSchemas";\n'
text+=model[model.index('export const CLAUDE_API_EFFORT_OPTIONS'):model.index('export const DROID_REASONING_EFFORT_OPTIONS')]
text+=model[model.index('export const CodexModelOptions'):model.index('export const ProviderModelOptions')]
# ModelSlug is a string alias. Keep the default values without the unrelated model catalog.
text+=model[model.index('export const DEFAULT_MODEL_BY_PROVIDER'):model.index('// Backward compatibility for existing Codex-only call sites.')].replace(': Record<ProviderWithDefaultModel, ModelSlug>','')
ts(Path('src/contracts/modelOptions.ts'),text)
orch=source('packages/contracts/src/orchestration.ts')
text='import { Effect, Schema, SchemaTransformation } from "effect";\n'
text+=orch[orch.index('import {\n  AntigravityModelOptions'):orch.index('import { ProviderInstanceId')].replace('"./model"','"./modelOptions"')
text+='import { ProviderInstanceId, TrimmedNonEmptyString } from "./baseSchemas";\n'
text+=orch[orch.index('export const ProviderKind'):orch.index('export const PersistedProviderKind')].split('/**\n * Decodes a persisted')[0]
text+=orch[orch.index('const ProviderInstanceIdForDriver'):orch.index('export const CodexProviderStartOptions')]
ts(Path('src/contracts/modelSelection.ts'),text)
put(Path('src/contracts/index.ts'), '\n'.join('export * from "./'+n+'.ts";' for n in ['baseSchemas','a2aGates','a2aMembership','a2aInbox','a2aRolePermissions'])+'\n')
put(Path('LICENSE.synara'),source('LICENSE'))
put(Path('.gitignore'),'node_modules/\n')
put(Path('package.json'),json.dumps({'name':'a2a-workbench','version':'0.1.0','private':True,'type':'module','engines':{'node':'>=26.5.0 <27'},'dependencies':{'effect':json.loads(source('package.json'))['workspaces']['catalog']['effect']}},indent=2)+'\n')
