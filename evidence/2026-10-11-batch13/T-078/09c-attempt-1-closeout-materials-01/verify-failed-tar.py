"""只读失败场次 tar；不打开现场 SQLite，不停机，不把失败改判为业务通过。"""
import argparse
import json
from pathlib import Path
import sys
import tarfile
import traceback

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE.parents[2] / 'workbench/tests'))
from t078_raw_retention import verify_archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['archive','readback','output']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    result={'status':'INCOMPLETE','scene_status':'INCOMPLETE','archive':str(args.archive),
            'signals_sent':[],'SQLite_reads':0}
    try:
        owner=json.loads((BASE/'09c-materials-01/owner.json').read_bytes())
        bundle=json.loads((args.archive.parent/'bundle.archive.json').read_bytes())
        signed=json.loads(args.readback.read_bytes())
        assert bundle['status']==bundle['byte_readback']=='PASS'
        assert bundle['archive']==signed['archive']==str(args.archive)
        assert bundle['root']==owner['root'] and bundle['source_revision']==owner['source_revision']
        inventory=verify_archive(bundle['staging'],args.archive)
        assert inventory==bundle['inventory'] and args.archive.stat().st_size==bundle['archive_bytes']
        with tarfile.open(args.archive) as tar:
            members={item.name:item for item in tar.getmembers()}
            assert len(members)==len(tar.getmembers())
            def raw(name):return tar.extractfile(name).read()
            def load(name):return json.loads(raw(name))
            snapshot=load('snapshot.json');live=load('live-rows.json')
            assert snapshot['root']==owner['root'] and snapshot['source_revision']==owner['source_revision']
            counts={};http_errors=[];hooks={}
            for role in ['ideation','executor']:
                prefix='files/roles/'+role+'/'
                requests=[name for name in members if name.startswith(prefix+'http-exchanges/') and name.endswith('.request.bin')]
                counted=0
                for name in requests:
                    meta=load(name.replace('.request.bin','.meta.json'))
                    response=raw(name.replace('.request.bin','.response.bin'))
                    assert meta['method']=='POST' and meta['path'].split('?')[0]=='/v1/messages'
                    assert len(raw(name))==meta['request_bytes'] and len(response)==meta['response_bytes']
                    counted+=1
                    if meta.get('error') or not meta.get('complete'):http_errors.append({'role':role,'sequence':meta['sequence'],'status':meta.get('status'),'complete':meta.get('complete'),'error':meta.get('error')})
                native=[load(name) for name in members if name.startswith(prefix+'hooks/') and name.endswith('/stdin.bin')]
                roots={(item['session_id'],item['prompt_id']) for item in native if item['hook_event_name']=='UserPromptSubmit'}
                permissions=[item for item in native if item['hook_event_name']=='PermissionRequest']
                counts[role]={'POST':counted,'roots':len(roots),'PermissionRequest':len(permissions)}
                assert counted==signed['counts']['Messages_POST'][role]
                assert len(roots)==signed['counts']['roots'][role]
                assert len(permissions)==len(signed['counts']['permission_requests'][role])
                hooks[role]=len(native)
            assert http_errors, '失败场次的错误/不完整原件不能丢失'
            assert any(item['role']=='ideation' and item['error']=='C_actual_delivery_required' for item in http_errors)
            records=[json.loads(row['data']) for row in live['inbox_records']]
            stop=[item for item in records if item['id']=='fe5603b6-1abf-4045-b267-031e32f762ce']
            assert len(stop)==1 and stop[0]['created_at']=='2026-10-16T22:35:52.492Z'
            assert stop[0]['from']=='ideation' and stop[0]['to']=='executor'
            assert not any(item.get('kind')=='ack' and item.get('reply_to')==stop[0]['id'] for item in records)
            delivered=[json.loads(row['data']) for row in live['inbox_deliveries'] if row['entry']==stop[0]['id'] and json.loads(row['data'])['state']=='delivered']
            assert len(delivered)==1
            request=[row for row in live['relay_requests'] if row['request_id']=='2926ba23-f599-4a54-a4ab-72d256cd8e85']
            assert len(request)==1
            relay=[json.loads(row['data']) for row in live['relay_results'] if row['key']==request[0]['key']]
            assert len(relay)==1 and relay[0]['entry']['id']==stop[0]['id'] and relay[0]['delivery']==delivered[0]
            assert 'request_id' not in relay[0]
            events=[{**row,'data':json.loads(row['data'])} for row in live['orchestration_events']]
            written=[row for row in events if row['type']=='terminal_input_written' and row['data'].get('request_id')=='82ac3820-b39a-4843-90da-06e9b6f6b170']
            assert len(written)==1
            assert raw('files/target/received.bin')==raw('files/target/baseline.bin')
            assert not [row for row in live['events'] if row['type']=='emergency_interrupt_requested']
            # 直接从第二条原 HTTP 请求抽出真实 queued tool_result，关联同一 request_id。
            body=load('files/roles/ideation/http-exchanges/0002.request.bin')
            blocks=[block for message in body['messages'] if isinstance(message.get('content'),list)
                    for block in message['content'] if block.get('type')=='tool_result']
            queued=[]
            for block in blocks:
                content=block['content']
                text=content if isinstance(content,str) else '\n'.join(item['text'] for item in content if item.get('type')=='text')
                try:value=json.loads(text)
                except ValueError:continue
                if value.get('request_id')==request[0]['request_id']:queued.append(value)
            assert len(queued)==1 and queued[0]['queued'] is True and queued[0]['delivered'] is False
        result.update(status='PASS',scope='仅失败原件完整性与已发生链路；不是 09C 通过',root=owner['root'],source_revision=owner['source_revision'],
                      counts=counts,hook_invocations=hooks,HTTP_errors=http_errors,archive_bytes=bundle['archive_bytes'],members=len(inventory),
                      stop_id=stop[0]['id'],created_at=stop[0]['created_at'],original_request_id=request[0]['request_id'],target_delta_hex='',no_ack=True,
                      first_result='已被覆盖的事实保留；不伪造恢复原文件',byte_readback='PASS')
    except Exception as error:result.update(error=repr(error),traceback=traceback.format_exc())
    with args.output.open('x',encoding='utf-8') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'scene_status':'INCOMPLETE','signals_sent':[]}))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
