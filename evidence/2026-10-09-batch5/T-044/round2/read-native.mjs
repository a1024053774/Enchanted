// Read-only production feature-socket RPC. No command dispatch or response overrides.
const [endpoint, threadId] = process.argv.slice(2);
const negotiate = new URL("/ws/negotiate", endpoint);
for (const [key,value] of Object.entries({"x-synara-client-build":"1.0.1-beta.2","x-synara-protocol-epoch":"1",
 "x-synara-protocol-min-revision":"3","x-synara-protocol-max-revision":"3"})) negotiate.searchParams.set(key,value);
const compatibility = await (await fetch(negotiate)).json();
const url = new URL("/ws", endpoint);url.protocol="ws:";
for(const [key,value] of Object.entries({"x-synara-client-build":"1.0.1-beta.2","x-synara-protocol-epoch":String(compatibility.protocolEpoch),
 "x-synara-protocol-revision":String(compatibility.negotiatedRevision),"x-synara-server-instance":compatibility.serverInstanceId}))url.searchParams.set(key,value);
const socket=new WebSocket(url);
const result=await new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>reject(new Error("Read-only RPC timed out")),20000);
 socket.addEventListener("open",()=>socket.send(JSON.stringify({_tag:"Request",id:"1",tag:"orchestration.getThreadDetailSnapshot",payload:{threadId},headers:[]})));
 socket.addEventListener("message",event=>{const message=JSON.parse(String(event.data));if(message._tag==="Exit"&&message.requestId==="1"){clearTimeout(timer);resolve(message);}});
 socket.addEventListener("error",event=>{clearTimeout(timer);reject(event);});
});
socket.close();console.log(JSON.stringify(result));if(result.exit._tag!=="Success")process.exitCode=1;
