import json, sys
G, WT, R = sys.argv[1:4]
c = ['echo hi > hello.txt', 'git add hello.txt && git commit -q -m D01-add-and-commit',
     'echo 2 >> hello.txt', 'git add hello.txt; git commit -q -m D02-semicolon-pair',
     'git  commit --allow-empty -q -m D03-double-space', '\\git commit --allow-empty -q -m D04-backslash',
     'command git commit --allow-empty -q -m D05-command', '"git" commit --allow-empty -q -m D06-quoted',
     '\tgit commit --allow-empty -q -m D07-leading-tab', 'git commit --allow-empty -q -m D08-a && git commit --allow-empty -q --no-verify -m D08-b',
     'git log --format=%s main..HEAD']
json.dump([['Bash', {'command': x, 'description': 'step'}] for x in c], sys.stdout)
