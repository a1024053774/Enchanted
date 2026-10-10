"""No-model contract red: controller presets must supply the first role card.

The real server runs with all providers disabled. This proves the setup boundary,
not Claude behavior. Every run uses a new label and preserves its fixture.
"""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import uuid

out = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara')
label = sys.argv[1]
assert label.replace('-', '').replace('_', '').isalnum()
result = out / label
result.mkdir()
root = Path('/Volumes/WD-Elements/dev-cache/synara/instances/s11-t059-' + label)
root.mkdir(mode=0o700)
for name in ('os-home', 'codex-empty', 'claude-empty'):
    (root / name).mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ('PATH', 'SHELL', 'LANG', 'LC_ALL')}
env.update(HOME=str(root / 'os-home'), CODEX_HOME=str(root / 'codex-empty'),
           CLAUDE_CONFIG_DIR=str(root / 'claude-empty'), A2A_SYNARA_SLOT='s11-t059-' + label,
           T058_ROOT=str(root), T058_FORK=str(fork),
           T058_SOURCE_REVISION=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip())
argv = ['./a2a/scripts/bun', 'run', str(out.parent / 'T-058/server-fixture-05.ts')]

def save(name, value):
    with (result / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def control(operation, **args):
    key = str(uuid.uuid4())
    request = dict(operation=operation, **args)
    with (root / 'control' / (key + '.request.json')).open('x', encoding='utf-8') as stream:
        json.dump(request, stream)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        path = root / 'control' / (key + '.result.json')
        if path.exists():
            value = json.loads(path.read_text(encoding='utf-8'))
            if not value.get('pending'):
                save('control-' + key + '.json', dict(request=request, result=value))
                assert value['ok'], value
                return value['result']
        time.sleep(.1)
    raise TimeoutError(operation)

calls = []
def gate(**request):
    req = urllib.request.Request(origin + '/api/a2a', data=json.dumps(request).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=45)
    except urllib.error.HTTPError as failure:
        response = failure
    with response:
        value = json.load(response)
        calls.append(dict(path='/api/a2a', request=request, status=response.status, result=value))
        save(f'gate-{len(calls):02d}.json', calls[-1])
        return value

def git(*args):
    genv = dict(env, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
    proc = subprocess.run(['git', '-C', str(repo), *args], env=genv, text=True, capture_output=True)
    save('git-' + str(uuid.uuid4()) + '.json', dict(argv=proc.args, exit_code=proc.returncode,
                                                stdout=proc.stdout, stderr=proc.stderr))
    proc.check_returncode()
    return proc.stdout.strip()

process = None
try:
    with (result / 'server.log').open('x', encoding='utf-8') as log:
        process = subprocess.Popen(argv, cwd=fork, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    save('launch.json', dict(argv=argv, cwd=str(fork), pid=process.pid, root=str(root),
                            source_revision=env['T058_SOURCE_REVISION'], environment=env,
                            start_new_session=True, started=dt.datetime.now(dt.timezone.utc).isoformat()))
    deadline = time.monotonic() + 45
    while not (root / 'ready.json').exists():
        if process.poll() is not None:
            raise RuntimeError('Isolated fixture exited; log preserved')
        if time.monotonic() >= deadline:
            raise TimeoutError('Isolated fixture startup')
        time.sleep(.1)
    origin = json.loads((root / 'ready.json').read_text(encoding='utf-8'))['origin']
    settings = json.loads((root / 'userdata/settings.json').read_text(encoding='utf-8'))['settings']
    enabled = {key: value['enabled'] for key, value in settings['providers'].items()}
    assert not any(enabled.values()), enabled
    save('provider-isolation.json', dict(enabled=enabled, model_calls=0,
                                        controlled_session_setup_calls=0, credential_issuance_calls=0))
    repo = root / 'repo'
    repo.mkdir()
    git('init')
    git('config', 'user.name', 'T059 independent fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    (repo / 'fixture.txt').write_text('T059 original Ω\n', encoding='utf-8')
    git('add', 'fixture.txt')
    git('-c', 'core.hooksPath=/dev/null', 'commit', '-m', 'Independent fixture baseline')
    (root / 'control-instructions.txt').write_text('Controlled setup, no model.\n', encoding='utf-8')
    (root / 'oracle.py').write_text('from pathlib import Path\nimport sys\nassert Path(sys.argv[1], "fixture.txt").read_text(encoding="utf-8")=="T059 original Ω\\n"\n', encoding='utf-8')
    created = gate(command='create', task='t059-control', title='控制', project='t059-project',
                   repo=str(repo), base=git('rev-parse', 'HEAD'), oracle=str(root / 'oracle.py'),
                   instructions=str(root / 'control-instructions.txt'))
    assert created['ok'], created
    # Positive control: existing T-058 attach accepts both capability presets
    # when the caller supplies the entire prompt. It is not missing wholesale.
    controls = []
    for preset in ('ideation', 'executor'):
        response = gate(command='attach', task='t059-control', role='controller', preset=preset,
                        modelSelection=dict(provider='claudeAgent', model='sonnet'),
                        runtimeMode='approval-required', instructions=str(root / 'control-instructions.txt'))
        assert response['ok'], response
        thread = response['attachment']['thread_id']
        detail = control('thread', thread=thread)
        controls.append(dict(preset=preset, receipt=response, native_projection=detail))
    save('existing-presets-positive-control.json', dict(observed=controls, real_claude_sessions=False,
        explanation='Provider-disabled orchestration projection only; no SDK query or model behavior proof'))
    missing_cards = []
    for preset in ('ideation', 'executor'):
        response = gate(command='attach', task='t059-control', role='controller', preset=preset,
                        modelSelection=dict(provider='claudeAgent', model='sonnet'),
                        runtimeMode='approval-required')
        missing_cards.append(dict(preset=preset, observed=response,
            expected='Preset supplies its first role card without a caller-authored instructions file'))
    save('contract-observation.json', dict(source='T-059 Acceptance second item; role card injected by preset',
        observed=missing_cards, expected_both_setup_receipts_ok=True,
        existing_capability_presets_work_with_manual_prompt=True, real_model_turns=0))
    save('domain-events.json', control('events'))
    assert all(item['observed'].get('ok') for item in missing_cards), 'Controller presets do not supply the first role card'
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        code = process.wait(timeout=45)
        save('cleanup.json', dict(owned_pid=process.pid, exit_code=code, stopped=True,
                                 user_instances_touched=False, model_turns=0))
    if (root / 'userdata/a2a-gates').exists():
        with tarfile.open(result / 'retained-fixture.tar.gz', 'x:gz') as archive:
            for name in ('repo', 'userdata/a2a-gates', 'control-instructions.txt', 'oracle.py'):
                archive.add(root / name, arcname=name)
        save('retention.json', dict(original_root=str(root), original_preserved=True,
             archive='retained-fixture.tar.gz', excludes=['provider homes', 'native logs', 'tokens'],
             embedded_git_registered_as_gitlink=False))
