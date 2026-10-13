"""Build rejects a configured volume that is absent, before writing caches.

Both the correct build and a guard-removal mutant are invoked through the
standard build entry. Even the mutant's writes stay on the mounted disk.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile
import traceback

from command_evidence import CommandLog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    record = {'status': 'INCOMPLETE', 'source': str(source), 'real_codex_turns': 0}
    commands = CommandLog(out)
    try:
        disk = Path('/Volumes/WD-Elements')
        if not disk.is_mount():
            raise RuntimeError('External disk is not mounted; no cache fallback')
        owned = Path(tempfile.mkdtemp(prefix='a2a-t076-volume-', dir=disk))
        volume = owned / 'absent-volume'
        assert not volume.exists()
        record.update(owned_directory=str(owned), configured_volume=str(volume))
        env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
        env.update(A2A_BUILD_VOLUME=str(volume))
        argv = ['node', source / 'workbench/app/build.mjs', '--slot', 'missing-volume']
        result = commands.run(argv, cwd=source, env=env, timeout=120)
        record.update(command=result.evidence, created_volume=volume.exists(),
                      created_files=[str(p.relative_to(owned)) for p in owned.rglob('*')])
        assert result.returncode != 0, ('An absent configured volume must reject the build', result.evidence)
        assert not volume.exists(), ('Rejected build must not create the absent volume or caches', record['created_files'])
        record.update(status='PASS', classification='business-pass')
    except AssertionError as error:
        record.update(classification='business-red', error=str(error), traceback=traceback.format_exc())
    except (OSError, ValueError, RuntimeError) as error:
        record.update(classification='harness-error', error=repr(error), traceback=traceback.format_exc())
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'classification': record.get('classification')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
