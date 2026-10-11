"""隔离复现 Node WAL 文件关闭后的 Python 只读打开。"""
import json, sqlite3, subprocess, tempfile
from pathlib import Path
root=Path(tempfile.mkdtemp(prefix='t075-sqlite-probe-'))
for mode in ['DELETE','WAL']:
 for creator in ['node','python']:
  p=root/(creator+' '+mode+'.sqlite')
  if creator=='node':
   code='import {DatabaseSync} from "node:sqlite";const db=new DatabaseSync(process.argv[1]);db.exec("PRAGMA journal_mode='+mode+';CREATE TABLE x (a TEXT)");db.close();'
   subprocess.run(['node','--input-type=module','-e',code,str(p)],check=True)
  else:
   db=sqlite3.connect(str(p));db.execute('PRAGMA journal_mode='+mode);db.execute('CREATE TABLE x (a TEXT)');db.close()
  for suffix in ['?mode=ro','?mode=rw']:
   try:
    db=sqlite3.connect(p.as_uri()+suffix,uri=True)
    result=db.execute('select name from sqlite_master').fetchall();db.close()
    print(creator,mode,suffix,'PASS',result)
   except sqlite3.Error as exc: print(creator,mode,suffix,'ERROR',str(exc))
print('Python SQLite',sqlite3.sqlite_version,'fixture',root)
