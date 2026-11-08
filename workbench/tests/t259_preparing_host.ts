// Only fault injection: the first identity read following a real pane creation fails.
// Transport, launch, input registration, state recovery and reclaim are production code.
import { existsSync, readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { publishReady } from './ready_file.ts';
const [source, state, configFile, ready] = process.argv.slice(2);
const load = (file: string) => import(pathToFileURL(join(source, 'workbench/src', file)).href);
const { serve } = await load('daemon.ts');
const { A2AGates } = await load('gates/core.ts');
const { createOperatorCredential, readOperatorCredential } = await load('credentials.ts');
if (!existsSync(process.env.A2A_OPERATOR_CREDENTIAL!)) createOperatorCredential(state);
readOperatorCredential(state);
await serve(state, JSON.parse(readFileSync(configFile, 'utf8')), (root: string, runtime: any) => {
  const create = runtime.createThread.bind(runtime), read = runtime.readThread.bind(runtime);
  const created = new Set<string>();
  runtime.createThread = async (...args: any[]) => { await create(...args); created.add(args[1].thread_id); };
  runtime.readThread = async (thread: string) => {
    if (created.delete(thread)) throw new SyntaxError('T259 injected first read failure after real pane creation');
    return read(thread);
  };
  return new A2AGates(root, runtime);
});
publishReady(ready, { pid: process.pid, source, state, fault: 'first read after createThread', model_calls: 0 });
