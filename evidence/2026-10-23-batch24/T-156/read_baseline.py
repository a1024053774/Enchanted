import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.input.read_text(encoding='utf-8'))
    result = {key: raw[key] for key in ('task', 'attempt', 'source_revision', 'ending_revision',
              'source', 'raw_artifact_root', 'started_at', 'ended_at', 'node_version',
              'python_version', 'real_model_turns')}
    result['source_summary'] = str(args.input)
    result['status'] = 'INCOMPLETE'
    result['runs'] = []
    for row in raw['runs']:
        report = row['report']
        item = {key: row[key] for key in ('name', 'command', 'exit_code', 'report_path')}
        item['status'] = report['status']
        if row['name'] == 'legacy-runner':
            item.update(error=report.get('error'), traceback=report.get('traceback'),
                        mutation_fixture_root=report['mutation_fixture_root'],
                        mutation_fixture_removed=report['mutation_fixture_removed'],
                        not_run=['readonly-argv', 'wrong-workspace', 'network-enabled', 'tmp-writable'])
            item['steps'] = [{
                'name': step['name'], 'exit_code': step['returncode'],
                'status': step['report']['status'], 'report_path': step['report_path'],
                'fixture_archive': step.get('fixture_archive'),
                'cases': [{key: case.get(key) for key in ('case', 'outcome', 'failure_id', 'cleanup_failures')}
                          | {'assertions': [{'id': a['id'], 'passed': a['passed']} for a in case['assertions']]}
                          for case in step['report']['cases']],
            } for step in report['steps']]
        else:
            item.update(checks=report['checks'], scope=report['scope'],
                        daemon_starts=report['daemon_starts'], scratch_removed=report['scratch_removed'])
        result['runs'].append(item)
    result['limitation'] = 'Legacy runner is INCOMPLETE; baseline capture success does not imply product success. Raw artifacts and original summary remain unchanged for controller archive.'
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
