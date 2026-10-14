"""T-080 #145：真实 score CLI 的混合 schema 记录；只写 /tmp 夹具。"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback


V1 = ['identity_version', 'path_boundary', 'completion', 'red_state',
      'rule_checks', 'independent_review', 'commit_trailers']
V2 = ['identity_version', 'path_boundary', 'oracle', 'completion', 'red_state',
      'rule_checks', 'independent_review', 'commit_trailers']
DATA = {'result': '通过', 'boundary_discipline': 3, 'boundary_reason': 'independent fixture',
        'engineering_taste': 2, 'engineering_reason': 'independent fixture', 'notes': ''}
FLAGS = ['--boundary-discipline', '3', '--boundary-reason', 'independent fixture',
         '--engineering-taste', '2', '--engineering-reason', 'independent fixture', '--notes', '']


class ContractFailure(AssertionError):
    pass


def save(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, out = args.source.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix='t80score-', dir='/tmp')).resolve()
    records = fixture / 'records'
    records.mkdir()
    logfile = records / 'scores.jsonl'
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    main_history = source / 'records/scores.jsonl'
    main_before = main_history.read_bytes() if main_history.is_file() else None
    report = {'status': 'INCOMPLETE', 'scope': '打分 schema 读写契约；无 daemon/Git/模型',
              'command': sys.argv, 'source': str(source), 'fixture': str(fixture),
              'checks': [], 'commands': [], 'real_model_calls': 0}

    def check(name, passed, expected, actual):
        report['checks'].append({'id': name, 'passed': bool(passed), 'expected': expected, 'actual': actual})
        if not passed:
            raise ContractFailure(name)

    def run(label, argv):
        argv = list(map(str, argv))
        p = subprocess.run(argv, cwd=source, env=env, capture_output=True, text=True, timeout=30)
        row = {'label': label, 'argv': argv, 'cwd': str(source), 'exit': p.returncode,
               'stdout': p.stdout, 'stderr': p.stderr}
        report['commands'].append(row)
        save(out / (label + '.command.json'), row)
        return p

    def readers(label, rows, accepted):
        path = fixture / (label + '.jsonl')
        path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        before = path.read_bytes()
        js = '''const {scoreRecords,QualityProtocolError}=await import(process.argv[1]);
const {readFileSync}=await import('node:fs');
try{const rows=scoreRecords(readFileSync(process.argv[2],'utf8'));process.stdout.write(JSON.stringify({ok:true,rows})+'\\n');}
catch(e){if(!(e instanceof QualityProtocolError))throw e;process.stdout.write(JSON.stringify({ok:false,error:e.field})+'\\n');process.exitCode=1;}'''
        py = '''import json,runpy,sys
sys.path.insert(0,sys.argv[1]);m=runpy.run_path(sys.argv[1]+"/score",run_name="reader")
rows=[json.loads(l) for l in open(sys.argv[2],encoding="utf-8")]
try:
 m["validate_scores"](rows)
except ValueError as error:
 print(json.dumps({"ok":False,"error":str(error)}));sys.exit(1)
print(json.dumps({"ok":True,"rows":rows}))
'''
        for runtime, argv in [('node', ['node', '--input-type=module', '-e', js,
                                        (source / 'workbench/src/gates/qualityProtocol.ts').as_uri(), path]),
                              ('python', [sys.executable, '-B', '-c', py, source / 'scripts', path])]:
            result = run(label + '-' + runtime, argv)
            actual = json.loads(result.stdout)
            check(label + '-' + runtime, result.returncode == (0 if accepted else 1)
                  and actual.get('ok') is accepted and (not accepted or actual['rows'] == rows),
                  {'accepted': accepted, 'no_backfill_or_rewrite': True}, actual)
        check(label + '-bytes', path.read_bytes() == before, 'input bytes unchanged', 'unchanged' if path.read_bytes() == before else 'changed')

    def score(label, flags, ok=True, expected_error=None):
        before = logfile.read_bytes()
        p = run(label, [sys.executable, '-B', source / 'scripts/score', '--root', fixture, *flags])
        if ok:
            row = json.loads(p.stdout)
            after = logfile.read_bytes()
            appended = after[len(before):] if after.startswith(before) else b''
            check(label, p.returncode == 0 and row['schema'] == 2
                  and after.startswith(before) and appended.endswith(b'\n')
                  and len(appended.splitlines()) == 1 and json.loads(appended) == row,
                  {'exit': 0, 'schema': 2, 'old_bytes_preserved': True, 'one_durable_row_matches_receipt': True},
                  {'exit': p.returncode, 'row': row, 'appended_bytes': len(appended)})
            return row
        check(label, p.returncode == 1 and expected_error in p.stderr and logfile.read_bytes() == before,
              {'exit': 1, 'error_contains': expected_error, 'no_append': True}, {'exit': p.returncode, 'stderr': p.stderr})

    try:
        legacy = {'schema': 1, 'score_id': 'historical-v1-executor', 'created_at': '2026-10-13T00:00:00Z',
                  'source': 'executor', 'launch_id': 'historical-launch', 'project': 'fixture',
                  'task': 'historical-task', 'attempt': 'historical-attempt', 'cli': 'fixture-codex',
                  'model': 'gpt-6.1-sol', 'effort': 'xhigh', 'data': DATA,
                  'facts': {'task_type': '测试', 'complexity': 'M', 'delivery_rounds': 1,
                            'elapsed_seconds': 2, 'human_interventions': 0, 'rejections': dict.fromkeys(V1, 0)}}
        legacy_user = {k: copy.deepcopy(v) for k, v in legacy.items() if k != 'facts'}
        legacy_user.update(score_id='historical-v1-user', source='user', score_of=legacy['score_id'],
                           data={k: v for k, v in DATA.items() if k != 'result'})
        seed = [legacy, legacy_user]
        logfile.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in seed), encoding='utf-8')
        seed_bytes = logfile.read_bytes()
        readers('v1-history', seed, True)
        # On the pre-change writer this reaches the business assertion with schema=1.
        user_v1 = score('new-user-for-v1', ['--source', 'user', '--score-of', legacy['score_id'], *FLAGS])
        check('user-v1-reference', user_v1['score_of'] == legacy['score_id'] and user_v1['task'] == 'historical-task'
              and 'facts' not in user_v1, 'v2 user score points to v1 executor without facts', user_v1)
        context = {'schema': 1, 'launch_id': 'new-launch', 'created_at': '2026-10-14T00:00:00Z',
                   'project': 'fixture', 'task': 'new-task', 'attempt': 'new-attempt', 'session': 'fixture-session',
                   'role': 'worker', 'cli': 'Codex', 'cli_version': 'fixture-codex', 'model': 'gpt-6.1-sol',
                   'effort': 'xhigh', 'service_tier_requested': 'default', 'cwd': str(fixture),
                   'project_commit': 'fixture-version', 'launcher_commit': 'fixture-version',
                   'role_card': 'fixture-role', 'role_card_version': 'fixture-version',
                   'argv': ['not-executed'], 'native_session': 'unknown'}
        (records / 'launches.jsonl').write_text(''.join(json.dumps({**context, 'phase': phase}) + '\n'
                                                      for phase in ('prepared', 'started')), encoding='utf-8')
        facts = {'task_type': '测试', 'complexity': 'M', 'delivery_rounds': 2, 'elapsed_seconds': 3,
                 'human_interventions': 0, 'rejections': dict.fromkeys(V2, 0)}
        facts['rejections']['oracle'] = 2
        missing = copy.deepcopy(facts)
        del missing['rejections']['oracle']
        save(fixture / 'missing-facts.json', missing)
        score('writer-rejects-missing-oracle', ['--launch', 'new-launch', '--facts', fixture / 'missing-facts.json',
              '--result', '通过', *FLAGS], ok=False, expected_error='oracle')
        save(fixture / 'complete-facts.json', facts)
        executor = score('new-v2-executor', ['--launch', 'new-launch', '--facts', fixture / 'complete-facts.json', '--result', '通过', *FLAGS])
        check('writer-facts', executor['facts'] == facts, 'exact supplied facts including oracle=2', executor['facts'])
        user_v2 = score('new-user-for-v2', ['--source', 'user', '--score-of', executor['score_id'], *FLAGS])
        check('user-v2-reference', user_v2['score_of'] == executor['score_id'] and user_v2['task'] == 'new-task'
              and 'facts' not in user_v2, 'v2 user score points to v2 executor without facts', user_v2)
        complete = copy.deepcopy(legacy)
        complete.update(schema=2, score_id='independent-v2', task='independent-task', facts=copy.deepcopy(facts))
        readers('v2-complete', [complete], True)
        bad = copy.deepcopy(complete)
        del bad['facts']['rejections']['oracle']
        readers('v2-missing-oracle', [bad], False)
        bad_v1 = copy.deepcopy(legacy)
        bad_v1['facts']['rejections']['oracle'] = 0
        readers('v1-unexpected-oracle', [bad_v1], False)
        for schema in (3, '2', True):
            bad_schema = copy.deepcopy(complete)
            bad_schema['schema'] = schema
            readers('unknown-schema-' + str(schema), [bad_schema], False)
        mixed = [json.loads(line) for line in logfile.read_text(encoding='utf-8').splitlines()]
        readers('mixed-v1-v2-users', mixed, True)
        check('mixed-schemas', [r['schema'] for r in mixed] == [1, 1, 2, 2, 2],
              [1, 1, 2, 2, 2], [r['schema'] for r in mixed])
        check('legacy-prefix-preserved', logfile.read_bytes().startswith(seed_bytes), 'original v1 bytes unchanged', True)
        # Exercise the real CLI's whole-history validation on an unknown version.
        bad_root = fixture / 'unknown-history'
        (bad_root / 'records').mkdir(parents=True)
        bad_history = bad_root / 'records/scores.jsonl'
        bad = copy.deepcopy(complete)
        bad['schema'] = 99
        bad_history.write_text(''.join(json.dumps(r) + '\n' for r in [legacy, bad]), encoding='utf-8')
        before = bad_history.read_bytes()
        p = run('cli-unknown-history', [sys.executable, '-B', source / 'scripts/score', '--root', bad_root,
                '--source', 'user', '--score-of', legacy['score_id'], *FLAGS])
        check('cli-unknown-history', p.returncode == 1 and '版本' in p.stderr and bad_history.read_bytes() == before,
              'unknown schema refuses without append', {'exit': p.returncode, 'stderr': p.stderr})
        report.update(status='PASS', outcome='passed')
    except ContractFailure as error:
        report.update(outcome='contract_failure', failure_id=str(error), traceback=traceback.format_exc())
    except Exception as error:
        report.update(outcome='harness_error', error=repr(error), traceback=traceback.format_exc())
    finally:
        main_after = main_history.read_bytes() if main_history.is_file() else None
        untouched = main_after == main_before and not (main_history.exists() and not main_history.is_file())
        if not untouched:
            report.update(status='INCOMPLETE', outcome='harness_error', error='主仓分数记录发生变化；停止核对')
        report['main_records_not_written'] = untouched
        save(out / 'run.json', report)
    print(json.dumps({'status': report['status'], 'outcome': report['outcome'],
                      'failure_id': report.get('failure_id'), 'fixture': str(fixture)}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
