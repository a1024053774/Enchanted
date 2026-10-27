import json,sqlite3,re,textwrap,sys,types,collections
src=open('/dev/stdin',encoding='utf-8').read()
a=src.index("        recheck = ('integration_compare_failed', 'review_reused')"); b=src.index("        events = {task:")
c=src.index("        def edited(rows, kind, path, value, occurrence=0):"); d=src.index("        report['observed']['refusals'] = refusals")
fx=sys.argv[1]
ns={'re':re,'json':json,'FILES':{'T-1':'a.txt','T-2':'b.txt'},'fixture':types.SimpleNamespace(dir=fx)}
exec(textwrap.dedent(src[a:b]), ns)
db=sqlite3.connect(fx+'/state/state.sqlite3')
ev={t:[dict(type=k,details=json.loads(x) if x else None) for k,x in db.execute("select type, details from events where task=? order by rowid",('demo+'+t,))] for t in ('T-1','T-2')}
sc={t:[json.loads(x) for (x,) in db.execute("select details from events where task=? and type='score_recorded'",('demo+'+t,))] for t in ('T-1','T-2')}
ns.update(events=ev,scores=sc)
print('recheck found', bool(ns['recheck_of'](ns['body'](ev['T-2']))))
diffs=ns['differences'](ev['T-1'],ev['T-2'])
print('same', not diffs, 'scores', ns['same_scores'](sc['T-1'],sc['T-2'],ev['T-1'],ev['T-2']))
def diff(x,y,p):
    if isinstance(x,dict) and isinstance(y,dict):
        for key in set(x)|set(y): diff(x.get(key),y.get(key),p+'.'+key)
    elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
        for i,(u,v) in enumerate(zip(x,y)): diff(u,v,p+'[]')
    elif x!=y: print('  ',p, repr(x)[:110],'|',repr(y)[:110])
for t,x,y in diffs[:8]:
    if t=='sequence': print('sequence differs'); break
    diff(x,y,t)
exec(textwrap.dedent(src[c:d]), ns)
print(ns['refusals'])
