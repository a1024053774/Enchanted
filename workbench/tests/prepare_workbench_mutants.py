"""Five single-site product mutants in disposable source copies, never dist.

The caller passes an immutable source directory and a fresh output directory.
The function preserves the patches and shares only the existing dependencies.
"""
import argparse
import difflib
import json
from pathlib import Path
import shutil
import tarfile
import tempfile


def prepare(source, output):
    source, output = source.resolve(), output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix='w76-mut-', dir='/tmp')).resolve()
    changes = {
        'omitted_bytes': ('workbench/src/panes.ts',
            'const read = readSync(fd, bytes, 0, bytes.length, offset);',
            'const read = readSync(fd, bytes, 0, bytes.length, offset === 65536 ? offset + 1 : offset);'),
        'window_stops_daemon': ('workbench/app/main.ts',
            "app.on('window-all-closed', () => app.quit());",
            "app.on('window-all-closed', async () => { await request(options.state, { command: 'daemon_stop' }); app.quit(); });"),
        'unknown_is_idle': ('workbench/src/panes.ts',
            'return { thread, launch: record.id, state: "unknown", lifecycle:',
            'return { thread, launch: record.id, state: "idle", lifecycle:'),
        'restart_success': ('workbench/src/daemon.ts',
            'return { ok: true, daemon, task: result.task, launch, pane, user_input_observer: result.user_input_observer };',
            'if (pane?.historical) result.task.state = "accepted";\n      return { ok: true, daemon, task: result.task, launch, pane, user_input_observer: result.user_input_observer };'),
        'missing_volume_builds': ('workbench/app/build.mjs',
            "if (!lstatSync(volume).isDirectory() || realpathSync(volume) !== volume ||\n"
            "    statSync(volume).dev === statSync(dirname(volume)).dev) {\n"
            "  throw new Error('构建要求真实挂载的外置盘；不回退到内置盘。');\n}"
            , '// MUTANT: omit the external-volume guard.'),
    }
    records = {}
    for name, (relative, before, after) in changes.items():
        original = (source / relative).read_text(encoding='utf-8')
        if original.count(before) != 1:
            raise RuntimeError('Mutation must select exactly one source site: ' + name)
        target = root / name
        shutil.copytree(source / 'workbench', target / 'workbench', symlinks=True,
                        ignore=shutil.ignore_patterns('node_modules'))
        (target / 'workbench/node_modules').symlink_to((source / 'workbench/node_modules').resolve(), target_is_directory=True)
        changed = original.replace(before, after, 1)
        (target / relative).write_text(changed, encoding='utf-8')
        patch = ''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True),
                         fromfile='candidate/' + relative, tofile=name + '/' + relative))
        (output / (name + '.patch')).write_text(patch, encoding='utf-8')
        records[name] = {'source': str(target), 'site': relative, 'patch': str(output / (name + '.patch'))}
    with tarfile.open(output / 'sources.tar.gz', 'x:gz') as archive:
        archive.add(root, arcname=root.name)
    manifest = {'source': str(source), 'root': str(root), 'mutants': records,
                'dependency_source': str((source / 'workbench/node_modules').resolve()), 'real_codex_turns': 0}
    with (output / 'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2); stream.write('\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
