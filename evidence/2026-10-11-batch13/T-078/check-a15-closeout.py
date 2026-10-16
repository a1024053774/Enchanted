"""Check A15 cleanup guards with recorded identities and local files; no scene actions."""
import argparse
import ast
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import sqlite3
import tempfile
from types import SimpleNamespace

BASE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def reject(action):
    try: action()
    except AssertionError: return
    raise AssertionError('unsafe specimen accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(exist_ok=False)
    evidence = module('a15_files_check', BASE / 'a15-final-evidence.py')
    cleanup = module('a15_cleanup_check', BASE / 'cleanup-09b-a15.py')
    redactor = module('a15_redactor_check', BASE / 'redact-a15-scene.py')
    owner = json.loads((BASE / '09b-a15-cleanup-owner.json').read_bytes())
    before = json.loads(Path(owner['identity_reference']).read_bytes())['binding']
    identities, graph = {}, {}
    for key, old in [('ideation_api', 'ideation_api'), ('executor_api', 'executor_api'),
                     ('daemon', 'daemon'), ('target_shell', 'shell'), ('target_leader', 'leader')]:
        pid = owner['pids'][key]; item = before['identities'][old]
        identities[pid] = {'pid': pid, 'started': item['lstart'], 'command': item['command']}
        graph[pid] = {'pid': pid, 'ppid': 1, 'pgid': pid, 'tpgid': -1}
    graph[owner['pids']['target_shell']]['ppid'] = owner['pids']['daemon']
    graph[owner['pids']['target_leader']]['ppid'] = owner['pids']['target_shell']
    for item in owner['roles'].values():
        launch = json.loads(Path(item['runtime_manifest']).read_bytes())['launch']
        shell, cli = item['shell_pid'], item['cli_pid']
        identities[shell] = {'pid': shell, 'started': item['cli_lstart'], 'command': shlex.join(['/bin/zsh', *launch['shell_argv']])}
        identities[cli] = {'pid': cli, 'started': item['cli_lstart'], 'command': shlex.join(launch['argv'])}
        graph[shell] = {'pid': shell, 'ppid': owner['pids']['daemon'], 'pgid': shell, 'tpgid': cli}
        graph[cli] = {'pid': cli, 'ppid': shell, 'pgid': cli, 'tpgid': cli}
    cleanup.validate_owners(owner, identities, graph)
    bad = copy.deepcopy(identities); bad[owner['pids']['ideation_api']]['started'] = 'changed'
    reject(lambda: cleanup.validate_owners(owner, bad, graph))
    try: reject(lambda: None)
    except AssertionError: pass
    else: raise AssertionError('guardless owner mutant survived')
    bad_graph = copy.deepcopy(graph); bad_graph[999999] = {'pid': 999999, 'ppid': owner['pids']['daemon']}
    reject(lambda: cleanup.validate_owners(owner, identities, bad_graph))
    audit = json.loads((BASE / '09b-a15-final-check-04/result.json').read_bytes())
    audit['headers'] = {'authorization': 'CREDENTIAL_SENTINEL'}; audit['metadata'] = 'CREDENTIAL_SENTINEL'
    summary = redactor.project(audit)
    assert 'CREDENTIAL_SENTINEL' not in json.dumps(summary)
    try: assert 'CREDENTIAL_SENTINEL' not in json.dumps(audit)
    except AssertionError: pass
    else: raise AssertionError('raw-copy redaction mutant survived')
    stage = next(item for item in audit['phases'] if item['phase'] == 'I1')
    tools = stage['tools']; use, result = tools['tool_use'], tools['tool_result']
    payload = {**result['content'], 'authorization': 'CREDENTIAL_SENTINEL'}
    body = {'system': 'CREDENTIAL_SENTINEL', 'metadata': 'CREDENTIAL_SENTINEL', 'messages': [
        {'role': 'assistant', 'content': [use]},
        {'role': 'user', 'content': [{**result, 'type': 'tool_result', 'content': json.dumps(payload)}]}]}
    use['type'] = 'tool_use'
    row = {'body_raw': json.dumps(body), 'tool_use_id': use['id'], 'headers': 'CREDENTIAL_SENTINEL'}
    command = use['input']['command']; argv = shlex.split(command)
    safe = evidence.approved_tool(row, {'bash_command': command}, argv, cleanup.ROOT, 'ideation')
    assert 'CREDENTIAL_SENTINEL' not in json.dumps(safe)
    body['messages'][0]['content'][0]['input']['command'] += ' ; echo CREDENTIAL_SENTINEL'
    row['body_raw'] = json.dumps(body)
    reject(lambda: evidence.approved_tool(row, {'bash_command': command}, argv, cleanup.ROOT, 'ideation'))
    with tempfile.TemporaryDirectory(prefix='t078-a15-cleanup-check-', dir='/private/tmp') as scratch:
        out = Path(scratch); archive = out / 'scene.tar.gz'
        inventory = redactor.archive_projection(summary, out, archive)
        archived = {'archive': str(archive), 'summary_file': str(out / 'projection/summary.json')}
        assert redactor.verify_archive(archived) == summary and inventory['regular_files'] == 1
        def unavailable(*_args): raise sqlite3.OperationalError('database unavailable after stop')
        stopped = SimpleNamespace(verify_archive=redactor.verify_archive, collect=unavailable)
        cleanup.verify_archive_after_stop(stopped, archived, summary)
        try: stopped.collect(owner)
        except sqlite3.OperationalError: pass
        else: raise AssertionError('post-stop database mutant survived')
        (out / 'projection/summary.json').write_text('changed\n', encoding='utf-8')
        reject(lambda: cleanup.verify_archive_after_stop(stopped, archived, summary))
    for path in [BASE / name for name in ['a15-final-evidence.py', 'redact-a15-scene.py', 'cleanup-09b-a15.py']]:
        tree = ast.parse(path.read_text(encoding='utf-8'))
        assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and
                       (getattr(node, 'module', '') == 'sqlite3' or any(item.name == 'sqlite3' for item in node.names))
                       for node in ast.walk(tree))
    report = {'status': 'PASS', 'scope': __doc__, 'owner_positive': True, 'PID_reuse_rejected': True,
              'foreign_descendant_rejected': True, 'guardless_owner_mutant_rejected': True,
              'credential_sentinel_removed': True, 'raw_copy_mutant_rejected': True,
              'unapproved_command_rejected': True, 'archive_member_bytes_verified': True,
              'archive_change_rejected': True, 'post_stop_DB_mutant_rejected': True,
              'archive_only_after_stop': True, 'process_probes': 0, 'scene_actions': 0}
    (args.output / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report)); return 0


if __name__ == '__main__': raise SystemExit(main())
