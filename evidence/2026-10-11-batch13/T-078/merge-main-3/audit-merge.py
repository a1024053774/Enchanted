"""Compare the resolved merge with both frozen parents without running services."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import traceback

ROOT = Path('/Users/luckye/Documents/Code/a2a-wt-t078')
OURS = '150ef6516f6ef5aaa6855631b770ce262991ffbf'
THEIRS = '0e6c2b833f6da64243f71d670ea45bb9116fda4d'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def text(revision, path):
    if revision == 'working-tree':
        return (ROOT / path).read_text(encoding='utf-8')
    return subprocess.check_output(['git', 'show', revision + ':' + path], cwd=ROOT).decode('utf-8')


def span(value, start, end):
    assert value.count(start) == 1 and value.count(end) == 1, ('ambiguous source region', start, end)
    return value[value.index(start):value.index(end)]


def audit():
    rows = []

    def same_region(path, reference, start, end, name):
        current = span(text('working-tree', path), start, end)
        original = span(text(reference, path), start, end)
        assert current == original, ('merged source region differs', name)
        rows.append({'name': name, 'path': path, 'reference': reference, 'start': start,
                     'end': end, 'comparison': 'exact source bytes', 'status': 'PASS'})

    core = 'workbench/src/gates/core.ts'
    panes = 'workbench/src/panes.ts'
    same_region(core, THEIRS, '  private reviewAttempt(', '  private scoreData(', 'T082 review request, copy, launch, result binding, reclaim and end check')
    same_region(core, THEIRS, '      if (args.command === "review_submit") {', '      if (args.command === "submit") {', 'T082 review_submit validates the full report and actual candidate workspace')
    same_region(core, THEIRS, '      if (args.command === "integrate") {', '      requireGate(args.command === "reclaim",', 'T082 integration keeps the locked requireReviewed precondition')
    same_region(core, OURS, '  private inboxRecords()', '  async call(raw:', 'T078 append-only inbox, pending/resume, refresh, ack and emergency-stop contracts')
    same_region(core, OURS, '  registerController(', '  private saveAttachment(', 'T078 controller membership registration')
    same_region(panes, THEIRS, '  async createReview(', '  private async createPane(', 'T082 fresh reviewer uses candidate_workspace')
    same_region(panes, THEIRS, '    const hook = ', '    mkdirSync(join(this.root, "traces", launch)', 'T082 reviewer argv, sandbox, network/tmp exclusion and launch record')
    same_region(panes, OURS, '  startController(', '  // T-078-1/#49:', 'T078 controller startup and isolated profile')
    same_region(panes, OURS, '  async dispatch(', '  status(thread:', 'T078 dispatch/wake/receipt/drain/release and all startup-key guards')
    same_region(panes, OURS, '  async signal(', '  authenticate(identity:', 'T078 Claude UPS/Stop and injection matching')
    for path, reference in [('workbench/src/daemon.ts', OURS), ('workbench/src/store.ts', OURS),
                            ('workbench/src/claudeLaunch.ts', OURS), ('workbench/src/hookTrace.ts', OURS),
                            ('workbench/src/gates/qualityProtocol.ts', THEIRS)]:
        assert text('working-tree', path) == text(reference, path), ('whole-file mismatch', path)
        rows.append({'name': 'whole-file preservation', 'path': path, 'reference': reference,
                     'comparison': 'exact source bytes', 'status': 'PASS'})
    relay = text('working-tree', 'workbench/src/relay.ts')
    old = '? { review_submit: ["review_id", "candidate_commit", "verdict", "findings"] }'
    new = '? { review_submit: ["review_id", "candidate_commit", "verdict", "findings", "review_requirements", "report"] }'
    original = text(OURS, 'workbench/src/relay.ts')
    assert original.count(old) == 1 and relay == original.replace(old, new), 'Unexpected relay resolution change'
    rows.append({'name': 'relay resolves to the T078 file plus exactly the two T082 review fields',
                 'path': 'workbench/src/relay.ts', 'status': 'PASS'})
    markers = []
    for path in (ROOT / 'workbench/src').rglob('*.ts'):
        if re.search(r'^(?:<<<<<<< |=======\s*$|>>>>>>> )', path.read_text(encoding='utf-8'), re.M):
            markers.append(str(path.relative_to(ROOT)))
    assert not markers, ('merge markers remain', markers)
    return {'status': 'PASS', 'HEAD': git('rev-parse', 'HEAD'), 'parents': [OURS, THEIRS],
            'checks': rows, 'source_merge_markers': markers,
            'scope': 'Static source preservation across both parents; not runtime or independent acceptance'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = audit()
    except Exception as error:
        report = {'status': 'INCOMPLETE', 'error': repr(error), 'traceback': traceback.format_exc()}
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
