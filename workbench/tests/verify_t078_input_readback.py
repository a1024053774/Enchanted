#!/usr/bin/env python3
"""Independent readback of the fixed input contract; imports no product code."""
import argparse
import json
from pathlib import Path
import sys
import tarfile

parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
read=lambda name:json.loads((args.input/name).read_text(encoding='utf-8'))
inputs=[json.loads(row['data']) for row in read('readback-user_inputs.json')]
events=read('readback-events.json')
raw=read('readback-orchestration_events.json')
messages=[item for item in inputs if item.get('form')=='message' and item.get('text')=='T078：中文输入与来源']
interventions=[json.loads(row['details']) for row in events if row['type']=='human_intervention']
empty=[json.loads(row['data']) for row in raw if row['type']=='terminal_input_empty']
empty_ids={item['request_id'] for item in empty}
with tarfile.open(args.input/'fixture.tar.gz') as archive:
    secrets=[name for name in archive.getnames() if name.endswith('/operator-credential.json')]
checks={
    'raw_bytes_equal_independent_literal':(args.input/'observed-input.bin').read_bytes()==('\x1b[200~T078：中文输入与来源\x1b[201~\r').encode('utf-8'),
    'one_message_record':len(messages)==1,
    'one_matching_intervention':len(messages)==1 and sum(row.get('input_id')==messages[0]['id'] for row in interventions)==1,
    'one_empty_observation':len(empty)==1,
    'empty_has_no_user_input':not any(row.get('source_ref',{}).get('command_id') in empty_ids for row in inputs),
    'empty_has_no_write':not any(row['type']=='terminal_input_write_intent' and json.loads(row['data']).get('request_id') in empty_ids for row in raw),
    'empty_has_no_intervention':not any(row.get('event_id') in empty_ids for row in interventions),
    'anonymous_did_not_append':read('readback-inbox_records.json')==[],
    'credential_not_archived':not secrets,
}
result={'status':'PASS' if all(checks.values()) else 'INCOMPLETE','argv':sys.argv,
        'scope':'只核对输入与凭据的四项合同，不读被测程序的结论','checks':checks}
with args.output.open('x',encoding='utf-8',newline='\n') as out:
    json.dump(result,out,ensure_ascii=False,indent=2);out.write('\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result['status']=='PASS' else 1)
