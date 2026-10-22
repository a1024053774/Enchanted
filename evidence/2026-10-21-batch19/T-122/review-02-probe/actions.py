import json, sys
G, R = sys.argv[1], sys.argv[2]
def py(label, code): return f'python3 -c {json.dumps(code)}; echo "{label} rc=$?"'
cmds = [
 'echo a > f.txt && git add f.txt && git commit -q -m t1; echo "01-normal-commit rc=$?"',
 'git update-ref refs/heads/main HEAD; echo "02-move-packed-main rc=$?"',
 'git update-ref refs/heads/a2a/T-2-a1 HEAD; echo "03-move-earlier-attempt rc=$?"',
 'git update-ref refs/heads/a2a/T-3-a1 HEAD; echo "04-move-later-attempt rc=$?"',
 'git branch a2a/T-1-a2; echo "05-precreate-next-attempt rc=$?"',
 'git update-ref refs/replace/$(git rev-parse main) HEAD; echo "06-replace-ref rc=$?"',
 'o=$(git rev-parse main^{tree}); f=' + G + '/objects/${o:0:2}/${o:2}; cp $f $f.n && mv -f $f.n $f; echo "07-overwrite-object rc=$?"',
 py('08-info-exclude', f"import os;os.makedirs('{G}/info',exist_ok=True);open('{G}/info/exclude','a').write('*.hidden\\n')"),
 py('09-info-attributes', f"open('{G}/info/attributes','a').write('')"),
 py('10-info-grafts', f"open('{G}/info/grafts','a').write('')"),
 py('11-shallow', f"open('{G}/shallow','a').write('')"),
 py('12-main-lock', f"open('{G}/refs/heads/main.lock','w').write('')") + f'; rm -f {G}/refs/heads/main.lock 2>/dev/null; python3 -c "import os;os.remove(\'{G}/refs/heads/main.lock\')"',
 py('13-later-gitdir-HEAD', f"p='{G}/worktrees/later/HEAD';s=open(p).read();open(p,'w').write(s)"),
 py('14-earlier-gitdir', f"open('{G}/worktrees/other/probe','w').write('x')"),
 py('15-config', f"open('{G}/config','a').write('')"),
 py('16-own-commondir', f"p='{G}/worktrees/wt/commondir';s=open(p).read();open(p,'w').write(s)"),
 'git -c core.hooksPath=/dev/null commit --allow-empty -q -m no-trailer; echo "17-no-trailer-commit rc=$?"',
 'echo x > "$TMPDIR/t122rv02"; echo "18-tmpdir rc=$?"; python3 -c "import os;os.remove(os.environ[\'TMPDIR\']+\'/t122rv02\')"',
 py('19-outside', f"open('{R}/outside/x','w').write('')"),
]
acts = [['Bash', {'command': c, 'description': c[:30]}] for c in cmds]
acts.append(['Write', {'file_path': f'{R}/outside/w.txt', 'content': 'x'}])
json.dump(acts, sys.stdout)
