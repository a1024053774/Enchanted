#!/usr/bin/env python3
"""Read raw P1 callbacks; distinguish no callback from a callback with no bytes."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
raw = json.loads(args.input.read_text(encoding='utf-8'))
events = raw['events']
phase = [row for row in events if row.get('phase') == 'interleaved-output-input']
callbacks = [row for row in phase if row.get('kind') in ('data','empty-data')]
empty = [row for row in events if row.get('kind') in ('data','empty-data') and row.get('data') == '']
observation = {'input':str(args.input.resolve()),'source_status':raw['status'],'source_error':raw.get('error'),
               'event_count':len(events),'empty_callbacks_all_phases':empty,
               'interleaved_callback_count':len(callbacks),'interleaved_callbacks':callbacks,
               'interleaved_dom_events':[row for row in phase if row.get('kind') == 'dom'],
               'interleaved_joined_data':''.join(row['data'] for row in callbacks),
               'observed':'逐条检查实际回调，不把 join([]) 得到的空串当作 onData 空事件。'}
with args.output.open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(observation,stream,ensure_ascii=False,indent=2)
    stream.write('\n')
print(json.dumps(observation,ensure_ascii=False,indent=2))
