import json, runpy, subprocess, sys
from pathlib import Path
root=Path(sys.argv[1])
# Manual answers from the card, including the original five inputs.
cases=[
 ("merge_unicode",[{"name":" Alice ","minutes":70},{"name":"张三","minutes":59},{"name":"Alice","minutes":55},{"name":"Bob","minutes":0}],0,
  {"entries":[{"name":"Alice","minutes":125,"duration":"2:05"},{"name":"Bob","minutes":0,"duration":"0:00"},{"name":"张三","minutes":59,"duration":"0:59"}],"total_minutes":184}),
 ("empty",[],0,{"entries":[],"total_minutes":0}),
 ("negative_single",[{"name":"A","minutes":-1}],2,{"error":"invalid_minutes"}),
 ("bool_single",[{"name":"A","minutes":True}],2,{"error":"invalid_minutes"}),
 ("blank_single",[{"name":"  ","minutes":1}],2,{"error":"invalid_name"}),
 ("nonadjacent_merge",[{"name":"Z","minutes":59},{"name":" A ","minutes":1},{"name":"Z","minutes":1},{"name":"A","minutes":59}],0,
  {"entries":[{"name":"A","minutes":60,"duration":"1:00"},{"name":"Z","minutes":60,"duration":"1:00"}],"total_minutes":120}),
 ("internal_spaces",[{"name":"AB","minutes":3},{"name":" A B ","minutes":2}],0,
  {"entries":[{"name":"A B","minutes":2,"duration":"0:02"},{"name":"AB","minutes":3,"duration":"0:03"}],"total_minutes":5}),
 ("case_sensitive_order",[{"name":"a","minutes":1},{"name":"Z","minutes":2}],0,
  {"entries":[{"name":"Z","minutes":2,"duration":"0:02"},{"name":"a","minutes":1,"duration":"0:01"}],"total_minutes":3}),
 ("control_trim",[{"name":chr(9)+"A"+chr(10),"minutes":59},{"name":"A","minutes":1},{"name":"Z","minutes":0}],0,
  {"entries":[{"name":"A","minutes":60,"duration":"1:00"},{"name":"Z","minutes":0,"duration":"0:00"}],"total_minutes":60})]
for minutes,duration in [(0,"0:00"),(59,"0:59"),(60,"1:00"),(61,"1:01"),(119,"1:59"),(120,"2:00"),(125,"2:05"),(6001,"100:01")]:
 cases.append(("duration_"+str(minutes),[{"name":"A","minutes":minutes}],0,
               {"entries":[{"name":"A","minutes":minutes,"duration":duration}],"total_minutes":minutes}))
# Finite JSON equivalence classes, independently listed in the mutation sweep.
invalid={
 "minutes":[("missing",False,None),("negative",True,-1),("negative_hour",True,-60),
            ("true",True,True),("false",True,False),("float_zero",True,0.0),
            ("float_integer",True,1.0),("fraction",True,1.5),("negative_fraction",True,-0.5),
            ("empty_string",True,""),("numeric_string",True,"5"),("zero_string",True,"0"),
            ("negative_string",True,"-1"),("fraction_string",True,"1.5"),("null",True,None),
            ("empty_array",True,[]),("array",True,[1]),("empty_object",True,{}),("object",True,{"minutes":1})],
 "name":[("missing",False,None),("empty",True,""),("spaces",True,"  "),
         ("unicode_spaces",True,"　"),("control_spaces",True,chr(9)+chr(10)),
         ("null",True,None),("true",True,True),("false",True,False),("integer",True,0),
         ("float",True,1.5),("empty_array",True,[]),("array",True,["A"]),
         ("empty_object",True,{}),("object",True,{"name":"A"})]}
for field,samples in invalid.items():
 for label,present,value in samples:
  for position,ordinal in enumerate(("first","middle","last")):
   payload=[{"name":"left","minutes":7},{"name":"middle","minutes":11},{"name":"right","minutes":13}]
   row={"name":"bad","minutes":1}
   if present: row[field]=value
   else: del row[field]
   payload[position]=row
   cases.append((field+"."+label+"."+ordinal,payload,2,{"error":"invalid_"+field}))

def exact(actual,expected,path="result"):
 # Python equality alone treats False == 0 and 0.0 == 0 as true.
 assert type(actual) is type(expected),(ident,path,"type",actual,expected)
 if isinstance(expected,dict):
  assert actual.keys()==expected.keys(),(ident,path,"keys",actual,expected)
  for key in expected: exact(actual[key],expected[key],path+"."+key)
 elif isinstance(expected,list):
  assert len(actual)==len(expected),(ident,path,"length",actual,expected)
  for i,(left,right) in enumerate(zip(actual,expected)): exact(left,right,path+"["+str(i)+"]")
 else: assert actual==expected,(ident,path,actual,expected)

normalize=runpy.run_path(str(root/"src/normalize.py"))["normalize"]
for ident,payload,code,expected in cases:
 # Save the original wire input before a function can change its argument.
 wire=json.dumps(payload,ensure_ascii=False)
 if code==0:
  exact(normalize(json.loads(wire)),expected)
 else:
  try: normalize(json.loads(wire))
  except Exception as error:
   assert type(error) is ValueError,(ident,"exception type",type(error).__name__)
   assert str(error)==expected["error"],(ident,"exception message",str(error),expected)
  else: raise AssertionError((ident,"invalid input must raise ValueError"))
 p=subprocess.run([sys.executable,"-B",str(root/"src/report.py")],input=wire.encode("utf-8"),capture_output=True,timeout=10)
 assert p.returncode==code,(ident,"exit",p.returncode,code,p.stdout,p.stderr)
 try: stdout=p.stdout.decode("utf-8")
 except UnicodeError as error: raise AssertionError((ident,"stdout encoding")) from error
 assert len(stdout.splitlines())==1,(ident,"exactly one JSON line",stdout)
 try: actual=json.loads(stdout)
 except ValueError as error: raise AssertionError((ident,"stdout JSON",stdout)) from error
 exact(actual,expected)
 # stderr may contain diagnostics; it is never a substitute result channel.
print("independent normalization oracle: %d cases passed" % len(cases))
