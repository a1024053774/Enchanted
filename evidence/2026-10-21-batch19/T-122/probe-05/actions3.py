# Batch 3: the file tools, which the sandbox does not cover, against the worktree's .git file.
import json, sys
G, WT, R = sys.argv[1], sys.argv[2], sys.argv[3]
acts = [['Write', {'file_path': f'{WT}/.git', 'content': f'gitdir: {R}/outside\n'}],
        ['Read', {'file_path': f'{WT}/.git'}],
        ['Edit', {'file_path': f'{WT}/.git', 'old_string': 'gitdir: ', 'new_string': f'gitdir: {R}/outside #'}],
        ['Read', {'file_path': f'{G}/info/exclude'}],
        ['Write', {'file_path': f'{G}/info/exclude', 'content': 'x\n'}],
        ['Write', {'file_path': f'{WT}/ok.txt', 'content': 'ok\n'}],
        ['Bash', {'command': f'cat {WT}/.git; ls {WT}', 'description': 'readout'}]]
json.dump(acts, sys.stdout)
