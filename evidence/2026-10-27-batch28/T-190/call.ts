import { request } from "/Users/luckye/Documents/Code/a2a/workbench/src/transport.ts";
import { readOperatorCredential } from "/Users/luckye/Documents/Code/a2a/workbench/src/credentials.ts";
const root = "/private/tmp/t190/state";
const result = await request(root, JSON.parse(process.argv[2]), readOperatorCredential(root)!);
console.log(JSON.stringify(result));
