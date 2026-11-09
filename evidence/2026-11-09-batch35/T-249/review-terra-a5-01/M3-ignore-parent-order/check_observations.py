#!/usr/bin/env python3
"""Compare transcribed CU values with preserved independent Git/file facts."""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
facts = json.loads((HERE / 'git-facts.json').read_text(encoding='utf-8'))
obs = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')) if len(sys.argv) > 1 else json.loads((HERE / 'observations.json').read_text(encoding='utf-8'))
errors = []
def check(condition, name):
    print(('ok   ' if condition else 'FAIL ') + name)
    if not condition:
        errors.append(name)

revs = [line.split() for line in facts['alpha_rev_list'].splitlines()]
log = [line.split('\t', 1) for line in facts['alpha_log'].splitlines()]
check(obs['rows'] == [row[1] for row in log] and [r[0] for r in revs] == [r[0] for r in log], '提交顺序')
def visible_parent_matches(short, full):
    return isinstance(short, str) and re.fullmatch(r'[0-9a-f]{10}', short) is not None and short == full[:10]

check(obs['merge'] == revs[0][0] and len(revs[0][1:]) == 2 and len(obs['merge_parents']) == 2 and all(visible_parent_matches(short, full) for full, short in zip(sorted(revs[0][1:]), sorted(obs['merge_parents']))), '合并哈希和两个父提交')
check(obs['normal'] == revs[1][0] and visible_parent_matches(obs['normal_parent'], revs[1][1]), '普通提交和父提交')
check(obs['root'] == revs[-1][0] and len(revs[-1]) == 1 and obs['root_parent'] is None, '根提交')
refs = {name.rsplit('/',1)[-1]: oid for oid,name in (line.split() for line in facts['alpha_refs'].splitlines())}
check(obs['labels'] == refs, '分支和标签')
check(set(obs['alpha_uncommitted']) == {'first.txt', 'untracked.txt'} and all(name in facts['alpha_status'] for name in obs['alpha_uncommitted']), '未提交文件')
f = facts['files']
expected = {
 'alpha/root/file*.txt': facts['alpha_root_star'].splitlines(),
 'alpha/normal/file*.txt': facts['alpha_root_star'].splitlines()+facts['alpha_normal_star'].splitlines(),
 'alpha/merge/feature.txt': f['alpha/feature.txt'].splitlines(),
 'alpha/uncommitted/first.txt': f['alpha/first.txt'].splitlines(),
 'alpha/uncommitted/untracked.txt': f['alpha/untracked.txt'].splitlines(),
 'unborn/file[1].txt': f['unborn/file[1].txt'].splitlines(),
 'unborn/staged.txt': f['unborn/staged.txt'].splitlines(),
 'unborn/untracked.txt': f['unborn/untracked.txt'].splitlines(),
 'unborn/file*.txt': f['unborn/file*.txt'].splitlines(),
}
for name, content in expected.items():
    check(obs['diffs'].get(name) == content, 'diff ' + name)
check(facts['alpha_normal_decoy'].strip() not in obs['diffs']['alpha/normal/file*.txt'], '字面星号未混入相邻文件')
check(facts['unborn_index_bracket'].splitlines() == ['bracket staged'] and facts['unborn_index_staged'] == f['unborn/staged.txt'], '暂存原始内容')
check(set(obs['unborn_files']) == {'file[1].txt','staged.txt','binary.bin','empty.txt','file*.txt','untracked.txt'} and all(n in facts['unborn_status'] for n in obs['unborn_files']), '首次提交前文件')
check(f['unborn/empty.txt'] == '' and obs['empty_message'] == '空文件，没有文本内容。', '空文件提示')
check('00' in facts['unborn_binary_hex'] and 'Binary files' in obs['binary_message'] and 'binary.bin differ' in obs['binary_message'], '二进制提示')
check(sorted(obs['many']) == sorted(facts['many']), '多仓库列表')
sys.exit(bool(errors))
