// Explain an observed reviewer refusal using the real gate and its saved inputs.
// Restoring only trust must make the same launch pass; unrelated failures stay incomplete.
import assert from 'node:assert/strict';
import { readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { A2AGates } from '../src/gates/core.ts';

export function explainTrustRejection(input, kind) {
  const report = { status: 'INCOMPLETE', kind };
  try {
    const { review, launch, live } = input;
    assert.equal(launch.cli, 'Codex');
    const root = JSON.stringify(realpathSync(review.candidate_workspace));
    const expected = `projects={${root}={trust_level="untrusted"}}`;
    const trust = launch.argv.filter(arg => arg.startsWith('projects=') || arg.startsWith('projects.'));
    if (kind === 'missing') assert.deepEqual(trust, []);
    else { assert.equal(kind, 'trusted'); assert.deepEqual(trust, [`projects={${root}={trust_level="trusted"}}`]); }
    const validate = row => A2AGates.prototype.reviewLaunch.call({
      launchRecord: id => id === row.id ? row : null,
      boundCard: () => ({ executor: { cli: 'Codex' } }),
    }, {}, review, live);
    let refusal;
    try { validate(launch); } catch (error) { refusal = error; }
    assert.equal(refusal?.code, 'review_launch_boundary');
    report.original_error = refusal.code;
    const restored = structuredClone(launch);
    if (kind === 'missing') restored.argv.push('-c', expected);
    else restored.argv[restored.argv.indexOf(trust[0])] = expected;
    validate(restored);
    report.restored_trust_only_launch_accepted = true;
    report.status = 'PASS';
  } catch (error) { report.error = String(error); }
  return report;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, kind, output] = process.argv.slice(2);
  const report = explainTrustRejection(JSON.parse(readFileSync(input, 'utf8')), kind);
  writeFileSync(output, JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(JSON.stringify(report));
  process.exitCode = report.status === 'PASS' ? 0 : 1;
}
