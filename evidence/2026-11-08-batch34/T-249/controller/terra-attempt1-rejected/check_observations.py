#!/usr/bin/env python3
"""Compare transcribed CU observations with retained, independently captured Git output."""
import json, sys
from pathlib import Path
p=Path(__file__).resolve().parent
g=json.loads((p/'git-oracle.json').read_text())
u=json.loads((Path(sys.argv[1]) if len(sys.argv)>1 else p/'ui-observations.json').read_text())
def eq(label, actual, expected):
    if actual != expected:
        raise AssertionError(f'{label}: UI={actual!r}; Git={expected!r}')
def diff_lines(raw, prefix):
    return [line[1:] for line in raw.splitlines() if line.startswith(prefix) and not line.startswith(prefix*3)]
try:
    eq('commit order', u['graph_subjects'],g['graph_subjects'])
    refmap={line.split()[1].split('/')[-1]:line.split()[0] for line in g['before']['alpha']['refs'].splitlines()}
    subject_by_hash={line.split()[0]:subject for line,subject in zip(g['before']['alpha']['rev_list'].splitlines(),g['graph_subjects'])}
    eq('labels',u['labels'],{name:subject_by_hash[refmap[name]] for name in u['labels']})
    eq('uncommitted files', sorted(u['uncommitted_files']), sorted(line.split()[-1] for line in g['before']['alpha']['status_v2'].splitlines() if line.startswith(('1 ','? '))))
    for name in ('root','normal','feature'):
        ui=u[name]; git=g['commits'][name]
        eq(name+' hash',ui['hash'],git['hash'])
        eq(name+' files',sorted(ui['files']),sorted(git['files']))
        if name=='root': eq('root parents',ui['parents'],git['parents'])
        else: eq(name+' parent prefixes',ui['parent_prefixes'],[x[:10] for x in git['parents']])
        if 'star_added' in ui: eq(name+' added',ui['star_added'],diff_lines(git['star_diff'],'+'))
        if 'star_removed' in ui: eq(name+' removed',ui['star_removed'],diff_lines(git['star_diff'],'-'))
    eq('working added',u['working_added'],diff_lines(g['working_diff'],'+'))
    eq('unborn files',sorted(u['unborn_files']),sorted(line.split()[-1] for line in g['before']['unborn']['status_v2'].splitlines() if line.startswith(('1 ','? '))))
    eq('unborn diff',u['unborn_bracket_added'],g['unborn_worktree_file'].splitlines())
    eq('many repositories',sorted(u['many']), sorted(str(Path(x).relative_to('/private/tmp/t249-terra-20261108-01/repos/many')) for x in g['before']['manygit']))
    print('PASS: 记录的界面事实与独立 Git 数据一致；不证明未记录的行为。')
except (AssertionError,KeyError,ValueError) as e:
    print('FAIL:',e,file=sys.stderr); sys.exit(1)
