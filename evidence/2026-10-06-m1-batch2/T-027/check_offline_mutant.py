#!/usr/bin/env python3
"""Prove the offline-copy tests reject the former online update instructions."""
from pathlib import Path
import json
import os
import subprocess
import tempfile

out = Path(__file__).resolve().parent / 'offline-mutant'
out.mkdir(exist_ok=False)
source = Path('muster/engine/src/update.rs')
original = source.read_bytes()
(out / 'original-update.rs').write_bytes(original)
marker = 'pub(crate) fn update_install_instruction('
text = original.decode('utf-8')
start = text.index(marker)
mutated = text[:start] + '''pub(crate) fn update_install_instruction(command: &str) -> String {
    format!("detach, run `{command}`, then run Muster again to reconnect")
}
'''
env = dict(os.environ, MUSTER_BUILD_SLOT='worker-t027')
results = []
try:
    source.write_text(mutated, encoding='utf-8')
    argv = ['./scripts/build', 'test', '--locked', '--manifest-path', 'muster/Cargo.toml', '--bin', 'muster', '--no-run']
    with (out / 'build.log').open('w') as log:
        built = subprocess.run(argv, env=env, stdout=log, stderr=subprocess.STDOUT)
    assert built.returncode == 0, 'mutant must compile before it can validate the assertions'
    # The executable path comes from Cargo's saved output, not a computed fingerprint.
    import re
    binary = re.search(r'Executable unittests .*\(([^)]+)\)', (out / 'build.log').read_text()).group(1)
    test_env = {k: v for k, v in os.environ.items() if not k.startswith(('HERDR_', 'MUSTER_'))}
    test_env['TMPDIR'] = tempfile.mkdtemp(prefix='t027-mutant-', dir='/tmp')
    for selector in ['app::actions::tests::update_ready_', 'ui::release_notes::tests::release_notes_preview_',
                     'server::headless::tests::update_notification_is_semantic_for_system_delivery',
                     'client::shell::tests::startup_overlays::update_ready_menu_opens_client_owned_release_notes_and_dismisses_by_version']:
        argv = [binary, selector, '--test-threads=1', '--nocapture']
        name = selector.replace('::', '-')
        with (out / (name + '.log')).open('w') as log:
            run = subprocess.run(argv, cwd='muster/engine', env=test_env, stdout=log, stderr=subprocess.STDOUT)
        results.append(dict(argv=argv, exit_code=run.returncode, expected_exit_code=101))
        assert run.returncode == 101, 'known-bad copy must fail the acceptance assertions'
finally:
    source.write_bytes(original)
    (out / 'result.json').write_text(json.dumps(dict(checks=results, source_restored=source.read_bytes() == original), indent=2) + '\n')
