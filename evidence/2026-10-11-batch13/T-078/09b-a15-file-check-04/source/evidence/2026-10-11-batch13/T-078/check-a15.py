"""File-only A15 generation and A14 cleanup/redaction checks; no live scene I/O."""
import argparse
import ast
from contextlib import closing
import copy
import importlib.util
import json
from pathlib import Path
import shlex
import sqlite3
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def cleanup_checks():
    cleanup = module('cleanup_a14_check', BASE / 'cleanup-09b-a14.py')
    redactor = module('redact_a14_check', BASE / 'redact-a14-scene.py')
    finish = module('finish_a14_check', BASE / 'finish-09b-a14-cleanup.py')
    owner = json.loads((BASE / '09b-a14-cleanup-owner.json').read_bytes())
    binding = json.loads(Path(owner['identity_reference']).read_bytes())['binding']
    identities = {}
    graph = {}
    for key, original_name in [('ideation_api', 'ideation_api'), ('executor_api', 'executor_api'), ('daemon', 'daemon'), ('target_shell', 'shell'), ('target_leader', 'leader')]:
        pid = owner['pids'][key]; before = binding['identities'][original_name]
        identities[pid] = {'pid': pid, 'started': before['lstart'], 'command': before['command']}
        graph[pid] = {'pid': pid, 'ppid': 1, 'pgid': pid, 'tpgid': -1}
    graph[48560]['ppid'] = 48461; graph[48562]['ppid'] = 48560
    for role in ['ideation', 'executor']:
        item = owner['roles'][role]; launch = json.loads(Path(item['runtime_manifest']).read_bytes())['launch']
        shell, cli = item['shell_pid'], item['cli_pid']
        identities[shell] = {'pid': shell, 'started': item['cli_lstart'], 'command': shlex.join(['/bin/zsh', *launch['shell_argv']])}
        identities[cli] = {'pid': cli, 'started': item['cli_lstart'], 'command': shlex.join(launch['argv'])}
        graph[shell] = {'pid': shell, 'ppid': 48461, 'pgid': shell, 'tpgid': cli}
        graph[cli] = {'pid': cli, 'ppid': shell, 'pgid': cli, 'tpgid': cli}
    cleanup.validate_owners(owner, identities, graph)
    negatives = []
    changed = copy.deepcopy(identities); changed[48939]['started'] = 'Fri Oct 16 00:01:05 2026'; negatives.append((changed, graph, 'reused CLI PID'))
    changed = copy.deepcopy(identities); changed[48453]['command'] = changed[48453]['command'].replace(owner['root'], '/private/tmp/foreign'); negatives.append((changed, graph, 'foreign API root'))
    changed = copy.deepcopy(identities); changed[52258]['command'] = changed[52258]['command'].replace(owner['roles']['executor']['session'], 'foreign-session'); negatives.append((changed, graph, 'foreign native session'))
    changed_graph = copy.deepcopy(graph); changed_graph[52258]['ppid'] = 1; negatives.append((identities, changed_graph, 'foreign parent'))
    changed_graph = copy.deepcopy(graph); changed_graph[999999] = {'pid': 999999, 'ppid': 48461, 'pgid': 999999, 'tpgid': -1}; negatives.append((identities, changed_graph, 'unknown descendant'))
    def require_rejections(validate):
        for ids, parents, label in negatives:
            try: validate(owner, ids, parents)
            except AssertionError: continue
            raise AssertionError('unsafe owner accepted: ' + label)
    require_rejections(cleanup.validate_owners)
    try: require_rejections(lambda *_args: None)
    except AssertionError as error: assert 'unsafe owner accepted' in str(error)
    else: raise AssertionError('known-bad owner validator survived')
    result = json.loads(Path(owner['I1_result']).read_bytes())
    pending = redactor.safe_pending(result['request_id'], result['relay_receipt'])
    protocol = json.loads((BASE / '09b-materials-01/protocol.json').read_bytes())
    argv = []
    values = {'target.thread_id': binding['attempt']['thread_id'], 'target.attempt_id': binding['attempt']['attempt_id'],
              'synthetic_user_input.id': next(ref.split(':', 1)[1] for ref in pending['entry']['refs'] if ref.startswith('input:'))}
    for token in protocol['commands']['I_SEND_STOP']['argv']:
        for key, value in values.items(): token = token.replace('{' + key + '}', value)
        if token.endswith('/roles/ideation/stop-body.txt'): token = str(redactor.ROOT / 'roles/ideation/stop-body.txt')
        argv.append(token)
    queued = {'ok': True, 'queued': True, 'delivered': False, 'request_id': result['request_id'],
              'path': str(redactor.ROOT / 'roles/ideation/requests' / (result['request_id'] + '.json')),
              'details': {'authorization': 'CREDENTIAL_SENTINEL'}}
    body = {'system': 'CREDENTIAL_SENTINEL', 'metadata': {'api_key': 'CREDENTIAL_SENTINEL'}, 'messages': [
        {'role': 'assistant', 'content': [{'type': 'tool_use', 'id': 'tool-fixture-1', 'name': 'Bash', 'input': {'command': shlex.join(argv)}}]},
        {'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': 'tool-fixture-1', 'content': json.dumps(queued)}]}]}
    projected = redactor.tool_projection({'body_raw': json.dumps(body), 'authorization': 'CREDENTIAL_SENTINEL'}, 'ideation', owner, pending)
    assert 'CREDENTIAL_SENTINEL' not in json.dumps(projected) and 'body' not in pending['entry']
    bad = copy.deepcopy(body); bad['messages'][0]['content'][0]['input']['command'] += ' ; echo CREDENTIAL_SENTINEL'
    try: redactor.tool_projection({'body_raw': json.dumps(bad)}, 'ideation', owner, pending)
    except AssertionError: pass
    else: raise AssertionError('unapproved command survived redaction')
    with tempfile.TemporaryDirectory(prefix='t078-a14-projection-check-', dir='/private/tmp') as temporary:
        out = Path(temporary); archive = out / 'scene.tar.gz'; summary = {'pending': pending, 'tools': projected}
        inventory = redactor.archive_projection(summary, out, archive)
        frozen = {'archive': str(archive), 'summary_file': str(out / 'projection/summary.json')}
        assert redactor.verify_archive(frozen) == summary and inventory['regular_files'] == 1
        def stopped_database(*_args):
            raise sqlite3.OperationalError('unable to open database file')
        unavailable = SimpleNamespace(verify_archive=redactor.verify_archive, collect=stopped_database)
        try:
            assert unavailable.collect(owner) == summary and unavailable.verify_archive(frozen) == summary
        except sqlite3.OperationalError as error:
            assert str(error) == 'unable to open database file'
        else: raise AssertionError('old post-stop database dependency was not reproduced')
        cleanup.verify_archive_after_stop(unavailable, frozen, summary)
        (out / 'projection/summary.json').write_text('changed\n', encoding='utf-8')
        try: cleanup.verify_archive_after_stop(unavailable, frozen, summary)
        except AssertionError: pass
        else: raise AssertionError('archive byte mismatch accepted')
    approval = json.loads((BASE / '09b-a14-cleanup-approval.json').read_bytes())
    prior = json.loads((BASE / '09b-a14-cleanup-01/result.json').read_bytes())
    archived = json.loads((BASE / '09b-a14-redacted-01/result.json').read_bytes())
    finish.validate_receipts(owner, approval, prior, archived)
    wrong = copy.deepcopy(prior); wrong['signals_sent'].append({'pid': 48453, 'signal': 'SIGTERM'})
    try: finish.validate_receipts(owner, approval, wrong, archived)
    except AssertionError: pass
    else: raise AssertionError('unexpected prior signal accepted')
    tree = ast.parse((BASE / 'finish-09b-a14-cleanup.py').read_text(encoding='utf-8'))
    for call in [node for node in ast.walk(tree) if isinstance(node, ast.Call)]:
        if isinstance(call.func, ast.Attribute):
            assert call.func.attr not in ['kill', 'killpg', 'collect', 'system', 'Popen'], 'finish path contains a forbidden action'
            if isinstance(call.func.value, ast.Name) and call.func.value.id == 'subprocess':
                assert call.func.attr == 'run' and isinstance(call.args[0], ast.List) and call.args[0].elts[0].value == '/bin/ps'
    observer = module('a15_observer_check', BASE / 'observe-startup-queued.py')
    captured = BASE / 'merge-main-3-outside-01/startup-entry'
    for index in range(6):
        value = json.loads((captured / 'candidate/test' / f'startup-receipt-{index}.json').read_bytes())
        observer.validate(value, value['entry_id'])
    bad = json.loads((captured / 'm5/test/startup-receipt-0.json').read_bytes())
    try: observer.validate(bad, bad['entry_id'])
    except AssertionError as error: assert 'startup refreshed receipt must remain queued' in str(error)
    else: raise AssertionError('recorded M5 survived observer')
    return {'status': 'PASS', 'owner_negative_cases': len(negatives), 'known_bad_owner_rejected': True,
            'redaction_sentinel_removed': True, 'unapproved_tool_rejected': True,
            'archive_byte_mismatch_rejected': True, 'startup_observations': 6, 'recorded_M5_rejected': True,
            'old_post_stop_DB_dependency_reproduced': True, 'archive_only_with_unavailable_DB': True,
            'finish_receipts_validated': True, 'finish_has_no_signal_daemon_or_SQLite_calls': True,
            'live_A14_access': False, 'process_probes': 0}


def generation_case(generator, folder, *, expected_instance):
    folder.mkdir(); stage_a = folder / 'stage-a'; stage_a.mkdir(); packet = folder / 'packet'; packet.mkdir()
    root = Path(tempfile.mkdtemp(prefix='t078-2-a15-files-', dir='/private/tmp')).resolve()
    try:
        for name in ['state', 'repo', 'target/home', 'workspace']:
            (root / name).mkdir(parents=True)
        (root / 'target/home/received.bin').write_bytes(b'')
        with tarfile.open(packet / 'sources.tar.gz', 'x:gz'): pass
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=SOURCE, text=True).strip()
        ready = {'status': 'READY_FOR_APPROVAL', 'root': str(root), 'task': 'file-only-fixture', 'source_revision': revision,
                 'target_binding': {'thread_id': 'file-fixture-thread', 'attempt_id': 'file-fixture-attempt'},
                 'api_processes': [{'role': role, 'ready': {'fixture_profile': 'a14-approved-gate-history-v1'}} for role in ['ideation', 'executor']]}
        (stage_a / 'readiness.json').write_text(json.dumps(ready), encoding='utf-8')
        (packet / 'static-check.json').write_text(json.dumps({'status': 'PASS', 'revision': revision, 'protocol': True}), encoding='utf-8')
        preview = {}
        for role in ['ideation', 'executor']:
            pending = folder / 'pending-result.json'
            if role == 'executor':
                pending.write_text(json.dumps({'status': 'READY_FOR_EXECUTOR', 'pending': True, 'feedback_count': 0, 'stop_entry': {'id': 'file-only-stop'}}), encoding='utf-8')
                with closing(sqlite3.connect(root / 'state/state.sqlite3')) as db:
                    db.execute('CREATE TABLE relay_results(data TEXT)')
                    db.execute('INSERT INTO relay_results VALUES (?)', (json.dumps({'entry': {'id': 'file-only-stop'}, 'delivery': {'state': 'pending'}}),)); db.commit()
            out = folder / (role + '-p1')
            args = SimpleNamespace(instance='a15', prompt_file=BASE / '09b-a15-materials-01/i1-prompt.txt',
                stage_a=stage_a, packet=packet, output=out, role=role, result=pending if role == 'executor' else None)
            generator.prepare_role(args)
            inp = json.loads((out / 'input.json').read_bytes()); nonce = (out / 'nonce.txt').read_text(encoding='utf-8')
            assert nonce.startswith(expected_instance.upper() + '_'), 'instance nonce was reused'
            assert json.loads((out / 'scenario.json').read_bytes())['name'] == expected_instance + '-' + role
            commands = (out / 'B1-COMMANDS.txt').read_text(encoding='utf-8')
            assert '09b-' + expected_instance + '-b1-' + role in commands
            onboard = (out / 'ONBOARD-COMMANDS.txt').read_text(encoding='utf-8')
            assert '--purpose onboarding-notice' in onboard and '09b-a14-' not in commands + onboard
            assert onboard.count('observe-startup-queued.py') == (6 if role == 'executor' else 0)
            approval = json.loads((out / 'stage-b-approval.json').read_bytes())
            frozen = json.loads((BASE / 'stage-b-a12-ideation-approval-01.json').read_bytes())
            assert approval['screen_approvals'] == frozen['screen_approvals'] and approval['tool_approval'] == frozen['tool_approval']
            assert approval['approved_by'] is None and approval['approval_ref'] is None
            assert inp['api_url'] == 'http://127.0.0.1:0' and inp['turn_limit'] == (4 if role == 'ideation' else 6)
            preview[role] = {'nonce_prefix': nonce.split('_')[0], 'budget': inp['turn_limit'], 'startup_observer_commands': onboard.count('observe-startup-queued.py')}
        return preview
    finally:
        import shutil
        shutil.rmtree(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(exist_ok=False)
    frozen_files = [BASE / name for name in ['cleanup-09b-a14.py', 'finish-09b-a14-cleanup.py', 'redact-a14-scene.py', 'observe-startup-queued.py', 'prepare-a14.py',
                    'prepare-09b-executable.py', 'check-a15.py', '09b-a14-cleanup-owner.json', '09b-a15-materials-01/i1-prompt.txt']]
    frozen = {str(path.relative_to(SOURCE)): path.read_bytes() for path in frozen_files}
    for relative, raw in frozen.items():
        copy_path = args.output / 'source' / relative
        copy_path.parent.mkdir(parents=True, exist_ok=True); copy_path.write_bytes(raw)
    result = {'status': 'INCOMPLETE', 'real_CLI_starts': 0, 'API_starts': 0, 'daemon_starts': 0,
              'scope': 'Pure owner/redaction/observer checks and synthetic file-generation specimens, not live claims or runtime acceptance'}
    try:
        result['cleanup'] = cleanup_checks()
        generator = module('a15_file_generator', BASE / 'prepare-a14.py')
        generator.SOURCE, generator.BASE = SOURCE, BASE
        with tempfile.TemporaryDirectory(prefix='a15-generator-tests-', dir='/private/tmp') as temporary:
            scratch = Path(temporary)
            result['roles'] = generation_case(generator, scratch / 'candidate', expected_instance='a15')
            bad_path = scratch / 'bad-generator.py'
            original = (BASE / 'prepare-a14.py').read_text(encoding='utf-8')
            assert original.count('nonce = args.instance.upper() +') == 1
            bad_path.write_text(original.replace('nonce = args.instance.upper() +', "nonce = 'A14' +"), encoding='utf-8')
            bad = module('a15_known_bad_generator', bad_path); bad.SOURCE, bad.BASE = SOURCE, BASE
            try: generation_case(bad, scratch / 'mutant', expected_instance='a15')
            except AssertionError as error:
                assert 'instance nonce was reused' in str(error); result['known_bad_A14_instance_rejected'] = True
            else: raise AssertionError('A14 label/nonce mutant survived')
        assert all((SOURCE / relative).read_bytes() == raw for relative, raw in frozen.items())
        result.update(status='PASS', tested_source_files=list(frozen), source_unchanged=True)
    except Exception as error:
        import traceback
        result.update(error=repr(error), traceback=traceback.format_exc())
    with (args.output / 'result.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
