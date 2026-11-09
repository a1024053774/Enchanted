#!/usr/bin/env python3
"""Compare manually recorded visible values with independent saved Git inputs, not UI authenticity."""
import json, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
facts = json.loads((here / 'git-facts.json').read_text(encoding='utf-8'))
obs = json.loads(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else here / 'observations.json').read_text(encoding='utf-8'))
checks = []
def check(name, ok):
    checks.append((name, bool(ok)))
    print(('ok   ' if ok else 'FAIL ') + name)
rev = facts['rev_list']
check('提交顺序与 Git 标题', obs['subjects'] == facts['subjects'])
refs = {}
for line in facts['refs_before'].splitlines():
    oid, ref = line.split(' ', 1)
    refs.setdefault(oid, []).append(ref.rsplit('/', 1)[-1])
expected_refs = {facts['subjects'][i]: refs[row[0]] for i, row in enumerate(rev) if row[0] in refs}
check('可见引用标签', obs['row_refs'] == expected_refs)
check('merge 哈希', obs['merge_hash'] == rev[0][0])
check('两个父提交前缀', len(rev[0][1:]) == 2 and obs['merge_parent_prefixes'] == [x[:10] for x in rev[0][1:]])
check('普通和根提交哈希', obs['normal_hash'] == rev[1][0] and obs['root_hash'] == rev[-1][0])
check('根提交文件', obs['root_files'] == facts['root_files'])
for name, lines in obs['diff_lines'].items():
    actual = [line for line in facts['diffs'][name].splitlines() if line.startswith(('+','-')) and not line.startswith(('+++','---'))]
    check(name + ' 的单文件内容', lines == actual)
check('unborn 文件列表', obs['unborn_list'] == list(facts['unborn_files']))
for name, lines in obs['unborn_visible'].items():
    check('unborn ' + name, lines == facts['unborn_files'][name].splitlines())
check('暂存内容独立核对', facts['unborn_index'].splitlines() == obs['unborn_visible']['file[1].txt'][:1])
check('操作后引用与状态恢复', facts['refs_after'] == facts['refs_before'] and facts['status_after'] == facts['status_before'])
sys.exit(0 if all(ok for _,ok in checks) else 1)
