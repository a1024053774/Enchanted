"""Controller-only widening checks. Reviewer faults are first measured red.

The review-red phase uses the previously frozen passing tracer candidate;
green phases use the current checkout snapshot. No real model path is present.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import traceback

from command_evidence import CommandLog
from run_t076_quality_red import archive_directory
from test_quality_widen_e2e import WIDE_CASES, REVIEW_RED

ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / 'evidence/2026-10-11-batch13/T-076/card-2'


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def references(source):
    for name in ('acceptance/test_recovery_e2e.py', 'scripts/score', 'scripts/record_io.py', 'scripts/launch_records.py'):
        target = source / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as stream: stream.write((ROOT / name).read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['review-red', 'wide-green', 'review-green'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    commands = CommandLog(out)
    env = {k: v for k, v in os.environ.items() if not k.startswith(('A2A_', 'CODEX_', 'GIT_CONFIG_', 'ELECTRON_'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'status': 'INCOMPLETE', 'product_status': 'INCOMPLETE', 'phase': args.phase, 'task': 'T-076-2',
              'real_codex_turns': 0, 'argv': sys.argv, 'steps': [], 'artifacts': [],
              'remaining': ['reviewer fault handling requires measured red before implementation',
                            'full 8/9/18 and T-075/T-076-1 regression after widening', 'real P-review and real delivery',
                            'T-077 joint verification and independent final review']}
    artifacts = []
    try:
        if not Path('/Volumes/WD-Elements').is_mount():
            raise RuntimeError('External disk not mounted; no install or internal cache fallback.')
        node = commands.run(['node', '--version'], cwd=ROOT, env=env)
        if node.returncode or not node.stdout.strip().startswith('v26.5.'):
            raise RuntimeError('Approved Node 26.5 unavailable.')
        audit = commands.run(['git', 'diff', 'a7f4cc3033c16d5888de50d8352da516c941f8e9', '--',
                              'acceptance/test_coop_e2e.py', 'acceptance/test_recovery_e2e.py', 'acceptance/test_run_e2e.py', 'scripts'], cwd=ROOT, env=env)
        if audit.returncode or audit.stdout:
            raise RuntimeError('Frozen acceptance/reference files changed; controller reconciliation required.')
        fixture = Path(tempfile.mkdtemp(prefix='q76wide-', dir='/tmp')).resolve()
        harness = fixture / 'candidate'
        shutil.copytree(ROOT / 'workbench', harness / 'workbench', symlinks=True,
                        ignore=shutil.ignore_patterns('node_modules', '__pycache__', '.DS_Store'))
        dependencies = (ROOT / 'workbench/node_modules').resolve()
        (harness / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
        references(harness)
        with tarfile.open(out / 'candidate-and-harness.tar.gz', 'x:gz') as archive:
            for name in ('workbench', 'acceptance', 'scripts'): archive.add(harness / name, arcname=name)
        head = commands.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, env=env)
        diff = commands.run(['git', 'diff', '--', 'workbench'], cwd=ROOT, env=env)
        if head.returncode or diff.returncode: raise RuntimeError('Source readback failed.')
        source = harness
        if args.phase == 'review-red':
            prior = CARD / 'outside-focused-tracer-01'
            if json.loads((prior / 'run.json').read_text(encoding="utf-8"))['status'] != 'PASS':
                raise RuntimeError('The declared pre-widening checkpoint did not pass its tracer checks.')
            source = fixture / 'before-review-fixes'; source.mkdir()
            with tarfile.open(prior / 'candidate-source.tar.gz', 'r:gz') as archive:
                members = []
                for member in archive.getmembers():
                    if 'node_modules' in Path(member.name).parts: continue
                    target = (source / member.name).resolve()
                    if source not in target.parents: raise RuntimeError('Archive entry escapes source.')
                    if member.issym() or member.islnk():
                        linked = ((target.parent if member.issym() else source) / member.linkname).resolve()
                        if source not in linked.parents: raise RuntimeError('Archive link escapes source.')
                    elif not (member.isfile() or member.isdir()): raise RuntimeError('Unsupported archive entry.')
                    members.append(member)
                archive.extractall(source, members=members)
            (source / 'workbench/node_modules').symlink_to(dependencies, target_is_directory=True)
            references(source)
        save(out / 'source-manifest.json', {'source_under_test': str(source), 'harness_source': str(harness),
             'head': head.stdout.strip(), 'tracked_diff': diff.stdout,
             'baseline_archive': str(CARD / 'outside-focused-tracer-01/candidate-source.tar.gz') if args.phase == 'review-red' else None,
             'real_codex_turns': 0})

        def suite(name, selected_source, group, cases=None, driver='test_quality_widen_e2e.py'):
            target = out / name
            argv = [sys.executable, '-B', harness / 'workbench/tests' / driver,
                    '--source', selected_source, '--output', target]
            if group: argv.extend(['--group', group])
            for case in cases or []: argv.extend(['--case', case])
            result = commands.run(argv, cwd=harness, env=env, timeout=600,
                                  stdout_file=out / (name + '.stdout.txt'), stderr_file=out / (name + '.stderr.txt'))
            path = target / 'run.json'
            report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            receipt = {'name': name, 'exit': result.returncode, 'command': result.evidence, 'report_path': str(path), 'report': report}
            record['steps'].append(receipt); save(out / (name + '.receipt.json'), receipt)
            if report: artifacts.append(Path(report['artifact_root']))
            if not report or any(c['outcome'] == 'harness_error' or c['cleanup_failures'] for c in report['cases']):
                raise RuntimeError('Unexpected fixture/protocol failure; preserve and report: ' + name)
            return result, report

        if args.phase == 'review-red':
            result, report = suite('reviewer-fault-baseline', source, 'review-red')
            observed = {c['case']: c for c in report['cases']}
            if result.returncode != 1 or list(observed) != list(REVIEW_RED) or any(
                observed[name]['outcome'] != 'contract_failure' or observed[name].get('failure_id') != expected
                for name, expected in REVIEW_RED.items()):
                raise RuntimeError('The explicit reviewer fault probes did not produce their specified red assertions.')
            record['scope'] = 'reviewer fault contract red only, before implementing its handling'
        elif args.phase == 'review-green':
            selections = [
                ('reviewer-fault-green', 'review-red', list(REVIEW_RED), 'test_quality_widen_e2e.py'),
                ('reviewer-normal-paths', None, ['tracer_success', 'tracer_review_needs_fix', 'tracer_run_waits'], 'test_quality_tracer_e2e.py'),
                ('completed-review-score-recovery', 'wide', ['widen_score_before_cas', 'widen_score_after_cas'], 'test_quality_widen_e2e.py'),
            ]
            for name, group, cases, driver in selections:
                result, report = suite(name, source, group, cases, driver)
                if result.returncode or report['status'] != 'PASS' or [row['case'] for row in report['cases']] != cases:
                    raise RuntimeError('Reviewer focused green failed; preserve and stop: ' + name)
            record['scope'] = 'three reviewer lifecycle fixes plus affected normal paths and restart score recovery only'
            record['remaining'][0] = 'legacy manual-claim score provenance requires controller decision before fixture migration'
        else:
            result, report = suite('widened-contracts', source, 'wide')
            if result.returncode or report['status'] != 'PASS' or [r['case'] for r in report['cases']] != WIDE_CASES:
                raise RuntimeError('Widened candidate failed; stop before mutations.')
            mutations = [
                ('red-base-zero-allowed', 'red_base_not_failing', 'RED-BASE-PASSES', 'gates/core.ts',
                 'baseResult.returncode !== null && baseResult.returncode > 0 && candidateResult.returncode === 0',
                 'baseResult.returncode !== null && candidateResult.returncode === 0'),
                ('candidate-red-failure-ignored', 'red_candidate_fails', 'RED-CANDIDATE-FAILS', 'gates/core.ts',
                 'baseResult.returncode !== null && baseResult.returncode > 0 && candidateResult.returncode === 0',
                 'baseResult.returncode !== null && baseResult.returncode > 0'),
                ('rule-failure-ignored', 'red_rules_failing', 'RED-RULES', 'gates/core.ts',
                 'requireGate(record.passed, "rule_check_failed", record);', '// Test mutant: omit rule refusal'),
                ('relative-test-path-escape-accepted', 'widen_red_manifest_paths', 'WIDE-MANIFEST-PATH', 'gates/taskCards.ts',
                 'part !== ".." && part.toLowerCase() !== ".git"', 'part.toLowerCase() !== ".git"'),
                ('symlink-test-accepted', 'widen_red_symlink', 'WIDE-RED-SYMLINK', 'gates/core.ts',
                 'requireGate(/^(100644|100755) blob [a-f0-9]+\\t/.test(tree)',
                 'requireGate(/^(100644|100755|120000) blob [a-f0-9]+\\t/.test(tree)'),
                ('project-rules-silently-disabled', 'widen_bad_project_config', 'WIDE-CONFIG-INVALID', 'gates/core.ts',
                 'if (!tree) return { source_commit: commit, path, raw: null, rule_checks: [] };',
                 'if (true) return { source_commit: commit, path, raw: null, rule_checks: [] };'),
                ('abandon-requires-scores', 'widen_abandon', 'WIDE-END-SCORE', 'gates/qualityProtocol.ts',
                 'if (command === "abandon" && (value as any)?.result === "放弃") {', 'if (false) {'),
                ('duplicate-score-import-accepted', 'widen_scores_roundtrip', 'WIDE-FORMAT-REJECT-0', 'gates/qualityProtocol.ts',
                 'requireValue(!attempts.has(identity), field + ".duplicate_attempt");', 'requireValue(true, field + ".duplicate_attempt");'),
                ('score-written-before-cas', 'widen_score_after_cas', 'WIDE-SCORE-PENDING', 'gates/core.ts',
                 'this.save(task, "integration_intent", intent);', 'this.save(task, "integration_intent", intent); this.finalScore(task, attempt, intent);'),
                ('recovery-score-changed', 'widen_score_before_cas', 'WIDE-SCORE-RECOVERY-BINDING', 'gates/core.ts',
                 'if (intent) requireGate(intent.score && JSON.stringify(intent.score.data) === JSON.stringify(score), "score_replay_mismatch");',
                 '// Test mutant: allow a different recovery score'),
                ('abandon-extra-fields-ignored', 'widen_ending_invalid_fields', 'WIDE-END-FIELDS', 'gates/qualityProtocol.ts',
                 'exact(value, ["result", "reason"], "score");', '// Test mutant: ignore extra abandonment fields'),
                ('upgrade-score-rejected', 'widen_upgrade', 'WIDE-END-SCORE', 'gates/qualityProtocol.ts',
                 'requireValue(data.result === (command === "integrate" ? "通过" : "升级"), "score.result");',
                 'requireValue(data.result === "通过", "score.result");'),
                ('truncated-score-tail-repaired', 'widen_scores_roundtrip', 'WIDE-FORMAT-TAIL', 'gates/qualityProtocol.ts',
                 'export function scoreRecords(raw: string): Record<string, any>[] {',
                 'export function scoreRecords(raw: string): Record<string, any>[] { if (raw && !raw.endsWith("\\n")) raw += "\\n";'),
            ]
            for name, case, expected, relative, before, after in mutations:
                mutant = fixture / name; shutil.copytree(source, mutant, symlinks=True)
                path = mutant / 'workbench/src' / relative; text = path.read_text(encoding='utf-8')
                if text.count(before) != 1: raise RuntimeError('Non-unique mutation target: ' + name)
                path.write_text(text.replace(before, after), encoding='utf-8')
                save(out / (name + '.mutation.json'), {'source': str(source), 'mutant': str(mutant), 'path': relative,
                     'before': before, 'after': after, 'expected_failure': expected})
                parsed = commands.run(['node', '--check', path], cwd=mutant, env=env)
                if parsed.returncode: raise RuntimeError('Invalid mutant syntax: ' + name)
                result, report = suite(name, mutant, 'wide', [case])
                row = report['cases'][0]
                if result.returncode != 1 or row['outcome'] != 'contract_failure' or row.get('failure_id') != expected:
                    raise RuntimeError('Mutant failed at the wrong boundary or escaped: ' + name)
            record['scope'] = 'widened checks and score recovery; reviewer fixes and complete legacy regression are still pending'
        record['status'] = 'PASS'
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        for index, path in enumerate(artifacts):
            try:
                archive = archive_directory(path, out / ('fixture-%02d.tar.gz' % index), out.name)
                record['artifacts'].append({'fixture': str(path), 'archive': archive})
            except Exception as error: record.update(status='INCOMPLETE', archive_error=repr(error))
        record['oversize_files'] = [str(p) for p in out.rglob('*') if p.is_file() and p.stat().st_size > 5 * 1024 * 1024]
        save(out / 'run.json', record)
        print(json.dumps({k: record[k] for k in ('status', 'product_status', 'phase', 'real_codex_turns')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
