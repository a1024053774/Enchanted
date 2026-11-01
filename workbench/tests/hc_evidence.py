"""Read-only user-core observations and the evidence boundary for isolated hc tests.

hc registry files contain terminal environment secrets. They stay in private test
fixtures; only selected, token-free observations may enter an evidence directory.
"""
import base64
import json
import os
from pathlib import Path
import pwd
import subprocess
import tarfile


def user_core_snapshot():
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    directory = home / '.local/state/herdr-core'
    listing = sorted(str(p.relative_to(directory)) for p in directory.rglob('*')) if directory.exists() else []
    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid=,lstart=,comm='], text=True).splitlines()
    processes = []
    for row in rows:
        parts = row.strip().split(None, 6)
        if len(parts) != 7:
            continue
        pid, started, executable = int(parts[0]), ' '.join(parts[1:6]), parts[6]
        if Path(executable).name != 'herdr-core':
            continue
        # These are test-owned binaries, never the user's installed hc.
        if executable.startswith(('/private/tmp/', '/tmp/', '/var/folders/', '/private/var/folders/')):
            continue
        processes.append(dict(pid=pid, started=started, executable=executable))
    return dict(directory=str(directory), listing=listing, processes=processes)


def private_tokens(state):
    tokens = set()
    for path in (state / 'hc/state/herdr-core').glob('*/terminals.json'):
        data = json.loads(path.read_text(encoding='utf-8'))
        for terminal in data.get('terminals', {}).values():
            token = terminal.get('restart_env', {}).get('A2A_TERMINAL_TOKEN')
            if token:
                tokens.add(token)
    return tokens


def private_hc_path(name):
    parts = Path(name).parts
    return Path(name).name in ('terminals.json', 'core.json') or any(
        parts[i:i+2] in (('hc', 'state'), ('hc', 'config')) for i in range(len(parts)-1))


def assert_public_evidence(root, tokens):
    files = [path for path in root.rglob('*') if path.is_file()]
    private = [str(path.relative_to(root)) for path in files if private_hc_path(str(path.relative_to(root)))]
    assert not private, f'hc private state in evidence: {private}'
    matches = 0
    for path in files:
        if path.name.endswith(('.tar.gz', '.tgz', '.tar')):
            with tarfile.open(path) as archive:
                assert not any(private_hc_path(name) for name in archive.getnames()), 'hc private state in evidence archive'
            continue
        raw = path.read_bytes()
        matches += sum(token.encode() in raw for token in tokens)
        if path.suffix in ('.json', '.jsonl'):
            # A legacy transport transcript may carry the same bytes as base64.
            def inspect(value):
                nonlocal matches
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key == 'data_base64' and isinstance(child, str):
                            decoded = base64.b64decode(child)
                            matches += sum(token.encode() in decoded for token in tokens)
                        else:
                            inspect(child)
                elif isinstance(value, list):
                    for child in value:
                        inspect(child)
            for line in ([raw.decode('utf-8')] if path.suffix == '.json' else raw.decode('utf-8').splitlines()):
                inspect(json.loads(line))
    assert matches == 0, 'terminal bearer token in evidence (values withheld)'
    return dict(private_hc_state_files=0, known_token_plaintext_matches=matches, checked_files=len(files))
