import {registerHooks} from 'node:module';
import {pathToFileURL} from 'node:url';
import {statSync} from 'node:fs';
import {join} from 'node:path';
const [source,state,control,ready]=process.argv.slice(2);
const credentialURL=pathToFileURL(join(source,'workbench/src/credentials.ts')).href;
const daemonURL=pathToFileURL(join(source,'workbench/src/daemon.ts')).href;
registerHooks({load(url,context,next){
 if(url!==daemonURL)return next(url,context);
 return {format:'module',shortCircuit:true,source:`
  import {readOperatorCredential} from ${JSON.stringify(credentialURL)};
  import {statSync} from 'node:fs';
  export async function serve(root){
   const value=readOperatorCredential(root),path=process.env.A2A_OPERATOR_CREDENTIAL;
   console.log(JSON.stringify({probe:'before-socket',path:path??null,kind:value?.kind??null,
    state:value?.state??null,mode:value?(statSync(path).mode&0o777):null}));
  }`};
}});
process.argv=[process.execPath,join(source,'workbench/tests/quality_chain_host.ts'),source,state,control,ready];
await import(pathToFileURL(process.argv[1]).href);
