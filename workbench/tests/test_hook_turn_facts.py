"""Actual-turn trailer contract through Git's real prepare-commit-msg hook.

The fixture supplies native records independently. It does not run Codex or
claim that these records establish its sandbox permissions or write timing.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import traceback

from command_evidence import CommandLog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    out = args.output.resolve()
    root = Path(tempfile.mkdtemp(prefix='h76-', dir='/tmp')).resolve()
    commands = CommandLog(out)
    results = []
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'A2A_', 'CODEX_'))}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_AUTHOR_NAME='T076 independent fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
               GIT_COMMITTER_NAME='T076 independent fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')

    def run(argv, cwd, command_env):
        return commands.run(argv, cwd=cwd, env=command_env)

    cases = [
        ('matching-request', [('a', 'gpt-6.1-sol', 'xhigh')], False, 'gpt-6.1-sol', 'xhigh'),
        ('different-request', [('a', 'observed-sentinel-model', 'medium')], False, 'observed-sentinel-model', 'medium'),
        ('latest-turn', [('a', 'older-model', 'low'), ('b', 'latest-sentinel-model', 'high')], False, 'latest-sentinel-model', 'high'),
        ('auxiliary-ignored', [('a', 'root-sentinel-model', 'medium')], True, 'root-sentinel-model', 'medium'),
        ('current-context-missing', [('a', 'older-model', 'low'), ('b', None, None)], False, 'unknown', 'unknown'),
    ]
    for name, turns, auxiliary, model, effort in cases:
        case = root / name
        repo, home, hooks = case / 'repo', case / 'home', case / 'hooks'
        repo.mkdir(parents=True); (home / 'sessions').mkdir(parents=True); hooks.mkdir()
        (hooks / 'prepare-commit-msg').symlink_to(source / 'workbench/hooks/hook.py')
        native = 'root-' + name
        records = [{'type': 'session_meta', 'payload': {'source': 'cli', 'id': native}}]
        for turn, observed_model, observed_effort in turns:
            records.append({'type': 'event_msg', 'payload': {'type': 'task_started', 'turn_id': turn}})
            if observed_model is not None:
                records.append({'type': 'turn_context', 'payload': {'turn_id': turn,
                                'model': observed_model, 'effort': observed_effort}})
        log = home / 'sessions' / ('rollout-' + native + '.jsonl')
        log.write_text(''.join(json.dumps(r) + '\n' for r in records), encoding='utf-8')
        if auxiliary:
            (home / 'sessions/rollout-auxiliary.jsonl').write_text(
                json.dumps({'type': 'session_meta', 'payload': {'source': {'subagent': {}}, 'id': 'auxiliary'}}) + '\n' +
                json.dumps({'type': 'turn_context', 'payload': {'model': 'auxiliary-model', 'effort': 'low'}}) + '\n', encoding='utf-8')
        record = {'case': name, 'expected': {'model': model, 'effort': effort},
                  'native': native, 'log': str(log), 'fixture_records': records, 'status': 'INCOMPLETE'}
        try:
            initialized = run(['git', 'init', '-b', 'main'], repo, env)
            if initialized.returncode:
                raise RuntimeError({'fixture_git_init_failed': initialized.evidence})
            (repo / 'value.txt').write_text(name + '\n', encoding='utf-8')
            staged = run(['git', 'add', 'value.txt'], repo, env)
            if staged.returncode:
                raise RuntimeError({'fixture_git_add_failed': staged.evidence})
            hook_env = {**env, 'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.hooksPath',
                        'GIT_CONFIG_VALUE_0': str(hooks), 'CODEX_HOME': str(home), 'CODEX_THREAD_ID': native,
                        'A2A_TASK': 'T076-' + name, 'A2A_ATTEMPT': 'attempt-' + name,
                        'A2A_SESSION': 'session-' + name, 'A2A_ROLE': 'worker',
                        'A2A_TOOL': 'codex-cli 0.162.1', 'A2A_LAUNCH': 'launch-' + name,
                        'A2A_MODEL_REQUESTED': 'gpt-6.1-sol', 'A2A_EFFORT_REQUESTED': 'xhigh'}
            commit = run(['git', 'commit', '-m', 'Independent native-turn fixture'], repo, hook_env)
            if commit.returncode:
                raise RuntimeError({'hook_commit_failed': commit.evidence})
            readback = run(['git', 'log', '-1', '--format=%B'], repo, env)
            if readback.returncode:
                raise RuntimeError({'fixture_log_failed': readback.evidence})
            record['message'] = readback.stdout
            (out / (name + '.message.txt')).write_text(readback.stdout, encoding='utf-8')
            values = {}
            for line in readback.stdout.splitlines():
                if line.startswith('A2A-'):
                    key, _, value = line.partition(': ')
                    values.setdefault(key, []).append(value)
            record['observed'] = values
            assert values.get('A2A-Model') == [model], ('Latest root turn supplies the model', model, values)
            assert values.get('A2A-Effort') == [effort], ('Latest root turn supplies the effort', effort, values)
            assert values.get('A2A-Native-Session') == [native], ('Trailer binds the root native session', values)
            assert len(values) == 9 and all(len(v) == 1 for v in values.values())
            record.update(status='PASS', classification='business-pass')
        except AssertionError as error:
            record.update(classification='business-red', error=str(error), traceback=traceback.format_exc())
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            record.update(classification='harness-error', error=repr(error), traceback=traceback.format_exc())
        results.append(record)
        with (out / (name + '.json')).open('x', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    record = {'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'INCOMPLETE',
              'argv': list(map(str, __import__('sys').argv)), 'source': str(source), 'fixture': str(root),
              'model_turns': 0, 'cases': results,
              'limitations': ['Synthetic native records; real sandbox readability and timing remain unproved.']}
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'cases': [(r['case'], r.get('classification')) for r in results]}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
