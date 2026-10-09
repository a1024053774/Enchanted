import json, time, uuid, urllib.request, urllib.error
from pathlib import Path

class Fixture:
    def __init__(self, root):
        self.root=Path(root)
        self.origin=json.loads((self.root/'ready.json').read_text())['origin']
    def control(self, operation, **args):
        name=str(uuid.uuid4())
        (self.root/'control'/f'{name}.request.json').write_text(json.dumps(dict(operation=operation,**args)))
        result=self.root/'control'/f'{name}.result.json'
        until=time.monotonic()+60
        while time.monotonic()<until:
            if result.exists():
                body=json.loads(result.read_text())
                if not body.get('pending'):
                    assert body['ok'],body
                    return body['result']
            time.sleep(.1)
        raise TimeoutError(operation)
    def http(self,path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token: headers['Authorization']='Bearer '+token
        request=urllib.request.Request(self.origin+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
        try:
            with urllib.request.urlopen(request,timeout=60) as response: return json.load(response)
        except urllib.error.HTTPError as error:
            return dict(status=error.code,body=error.read().decode())
    def gate(self,command,**args):
        return self.http('/api/a2a',dict(command=command,**args))
