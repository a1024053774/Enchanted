"""Read back the frozen delivery review and local delivery checks; no model calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

CARD = Path(__file__).resolve().parent
ROOT = CARD.parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-readme-update', action='store_true')
    parser.add_argument('--allow-final-format', action='store_true')
    parser.add_argument('--record-observation', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'INCOMPLETE', 'commands': [], 'real_model_calls': 0}

    def command(argv):
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
        report['commands'].append({'argv': argv, 'exit': p.returncode,
                                   'stdout': p.stdout, 'stderr': p.stderr})
        assert p.returncode == 0, argv
        return p.stdout

    try:
        manifest = json.loads((CARD / 'delivery-review-01/manifest.json').read_text(encoding='utf-8'))
        changed = [p for p in manifest['paths'] if (ROOT / p).read_bytes() !=
                   (CARD / 'delivery-review-01/candidate' / p).read_bytes()]
        permitted = {'workbench/README.md'} if args.allow_readme_update else set()
        format_path = 'workbench/tests/controlled_quality_pty.ts'
        if args.allow_final_format:
            before = (CARD / 'delivery-review-01/candidate' / format_path).read_bytes()
            lines = before.splitlines(keepends=True)
            assert lines[12] == b'  \n'
            lines[12] = b'\n'
            assert (ROOT / format_path).read_bytes() == b''.join(lines)
            permitted.add(format_path)
        assert not set(changed) - permitted, changed
        report.update(frozen_paths=len(manifest['paths']), changed_since_review=changed,
                      product_bytes_unchanged=True,
                      test_bytes_unchanged=not any(p.startswith(('workbench/tests/', 'acceptance/')) for p in changed),
                      test_format_only_changes=[format_path] if format_path in changed else [],
                      frozen_source_head=manifest['head'])

        review = CARD / 'outside-delivery-review-01'
        setup = json.loads((review / 'setup.json').read_text(encoding='utf-8'))
        argv = setup['argv']
        tiers = [a for a in argv if a.startswith('service_tier=')]
        assert tiers == ['service_tier="default"']
        assert argv[argv.index(tiers[0]) - 1] == '-c'
        assert not Path(setup['home']).exists()
        paths = list((review / 'native-sessions').rglob('*.jsonl'))
        assert len(paths) == 1
        rows = [json.loads(line) for line in paths[0].read_text(encoding='utf-8').splitlines()]
        metas = [r['payload'] for r in rows if r['type'] == 'session_meta']
        starts = [r['payload'] for r in rows if r['type'] == 'event_msg' and
                  r['payload'].get('type') == 'task_started']
        ends = [r['payload'] for r in rows if r['type'] == 'event_msg' and
                r['payload'].get('type') == 'task_complete']
        contexts = [r['payload'] for r in rows if r['type'] == 'turn_context']
        assert len(metas) == len(starts) == len(ends) == 1
        assert metas[0]['source'] == 'cli' and metas[0]['cli_version'] == '0.162.1'
        assert starts[0]['turn_id'] == ends[0]['turn_id']
        assert starts[0]['turn_attribution']['parent_turn_id'] is None
        assert contexts and all(c['model'] == 'gpt-6.1-sol' and c['effort'] == 'xhigh'
            and c['sandbox_policy']['type'] == 'read-only' and c['approval_policy'] == 'never'
            for c in contexts)
        text = (review / 'REPORT.md').read_text(encoding='utf-8')
        assert text.rstrip() == ends[0]['last_agent_message'].rstrip()
        assert text.startswith('STATUS: PASS\n')
        assert '\nRELEASE: LIMITED_GO —' in text
        report.update(review_status='PASS', release='LIMITED_GO', home_removed=True,
                      review_native_session=metas[0]['id'], review_turn=starts[0]['turn_id'],
                      observed_review_turns=1, service_tier_requested='default',
                      service_tier_observed=contexts[0].get('service_tier'))

        ledger_path = CARD / 'real-turn-budget.jsonl'
        ledger = [json.loads(line) for line in ledger_path.read_text(encoding='utf-8').splitlines()]
        observation = [r for r in ledger if r['kind'] == 'observation' and r.get('slot') == 7]
        if args.record_observation:
            assert not observation
            assert sum(r['observed_main_turns'] for r in ledger if r['kind'] == 'observation') == 6
            assert any(r['kind'] == 'reservation' and r.get('slot') == 7 for r in ledger)
            entry = {'kind': 'observation', 'slot': 7, 'output': str(review),
                     'observed_main_turns': 1, 'status': 'PASS', 'release': 'LIMITED_GO',
                     'home_removed': True, 'native_session': metas[0]['id'],
                     'turn_id': starts[0]['turn_id'], 'model': 'gpt-6.1-sol', 'effort': 'xhigh',
                     'sandbox': 'read-only', 'service_tier_requested': 'default',
                     'service_tier_observed': None, 'readback': str(args.output / 'run.json')}
            with ledger_path.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + '\n')
            ledger.append(entry)
        total = sum(r['observed_main_turns'] for r in ledger if r['kind'] == 'observation')
        assert total == 7
        report.update(accounted_main_turns=total, budget_limit=8, unused_slots=[8])

        spec = importlib.util.spec_from_file_location('legacy_scope', ROOT / 'workbench/tests/audit_legacy_scope.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        scope = module.audit(ROOT)
        report['approved_acceptance_scope'] = {k: v for k, v in scope.items() if k != 'patch'}
        assert (ROOT / 'acceptance/test_recovery_e2e.py').read_bytes() == subprocess.check_output(
            ['git', 'show', manifest['baseline'] + ':acceptance/test_recovery_e2e.py'], cwd=ROOT)

        archive = json.loads((CARD / 'archive-real-log-01/run.json').read_text(encoding='utf-8'))
        pointer = json.loads((CARD / 'outside-real-delivery-02/commands.jsonl.gz.pointer.json').read_text(encoding='utf-8'))
        assert archive['status'] == 'PASS' and archive['byte_readback'] and archive['source_removed']
        assert Path(pointer['archive']).stat().st_size == pointer['bytes'] == 48122290
        report['archive'] = {'path': pointer['archive'], 'bytes': pointer['bytes'],
                             'prior_byte_readback': True, 'repeated_full_byte_readback': False}
        assert not list(CARD.rglob('.git'))
        assert not list(CARD.rglob('auth.json'))
        report['oversize_files'] = command(['find', str(CARD), '-type', 'f', '-size', '+5M']).splitlines()
        assert not report['oversize_files']
        command(['git', 'diff', '--check'])
        command(['python3', '/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py',
                 'status', '--root', '.'])
        report['checkout_head'] = command(['git', 'rev-parse', 'HEAD']).strip()
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        (args.output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: report.get(k) for k in ('status', 'error', 'accounted_main_turns',
                                                    'review_status', 'changed_since_review')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
