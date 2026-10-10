// Real task-window route, real event query, isolated Chromium and dev server.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const fork = "/Users/luckye/Documents/Code/synara";
const run = process.argv[2]!;
const root = process.argv[3]!;
const identity = JSON.parse(readFileSync(join(run, "../red02/identity.json"), "utf8"));
const currentIdentity = JSON.parse(readFileSync(join(run, "ui-expectations.json"), "utf8"));
const backend = JSON.parse(readFileSync(join(root, "ready.json"), "utf8")).origin;
process.env.VITE_WS_URL = backend.replace("http:", "ws:");
process.env.PORT = process.env.T066_WEB_PORT!;
const { createServer } = await import(join(fork, "apps/web/node_modules/vite/dist/node/index.js"));
const server = await createServer({ root: join(fork, "apps/web"), configFile: join(fork, "apps/web/vite.config.ts"),
  cacheDir: join(root, "vite"), server: { host: "127.0.0.1", port: Number(process.env.T066_WEB_PORT), strictPort: true } });
await server.listen();
const address = server.httpServer!.address() as {port: number};
const web = `http://127.0.0.1:${address.port}`;
const { chromium } = createRequire(join(fork, "apps/web/package.json"))("playwright");
const context = await chromium.launchPersistentContext(join(root, "browser"), { headless: true,
  executablePath: "/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell",
  viewport: { width: 1280, height: 900 } });
const page = context.pages()[0];
const requests: string[] = [];
page.on("request", (request: any) => { if (request.url().includes("/api/a2a")) requests.push(request.url()); });
function assert(value: unknown, message: string) { if (!value) throw new Error(message); }
try {
  await page.goto(web + "/a2a", { waitUntil: "domcontentloaded" });
  await page.locator("main[aria-label='任务窗口']").waitFor({state:"attached",timeout:60000});
  const readyBy=Date.now()+60000;
  while (Date.now()<readyBy) {
    const importer=page.getByRole("button",{name:"Not now",exact:true});
    if(await importer.isVisible().catch(()=>false)) await importer.click();
    const tour=page.getByRole("button",{name:"Skip tour",exact:true});
    if(await tour.isVisible().catch(()=>false)) await tour.click();
    if(await page.getByRole("button",{name:/紧急停止记录/}).isVisible().catch(()=>false)) break;
    await page.waitForTimeout(250);
  }
  await page.getByRole("navigation",{name:"项目与任务"}).getByRole("button",{name:"t066",exact:true}).click({timeout:60000});
  const toggle=page.getByRole("button",{name:/紧急停止记录/});
  await toggle.click({timeout:60000});
  const list=page.locator("ul").filter({hasText:"调用者 thread"});
  await list.waitFor();
  const rows=await list.locator("li").allTextContents();
  const legacy=rows.find((row: string)=>row.includes(identity.threads.worker));
  assert(legacy && legacy.includes("ideation") && legacy.split("未记录").length===3,"Legacy caller identities must both display 未记录");
  const current=rows.find((row: string)=>row.includes("executor"));
  assert(current && !current.includes("未记录") && current.includes(currentIdentity.threads.executor) &&
    current.includes(currentIdentity.turns.executor) && current.includes(currentIdentity.threads.worker),"Current stop must display credential thread/turn and separate target");
  assert(requests.some((url)=>url.includes("/api/a2a")),"Task window must use actual server event query");
  await page.screenshot({path:join(run,"ui-stop-history.png"),fullPage:true});
  await list.evaluate((element: HTMLElement) => { element.scrollTop = element.scrollHeight; });
  await page.screenshot({path:join(run,"ui-stop-history-scrolled.png"),fullPage:true});
  writeFileSync(join(run,"ui-observations.json"),JSON.stringify({status:"PASS",web,requests,rows,legacy_target:identity.threads.worker},null,2)+"\n",{flag:"wx"});
  console.log("PASS real task window: current identities and legacy 未记录");
} catch (error) {
  await page.screenshot({path:join(run,"ui-failure.png"),fullPage:true});
  writeFileSync(join(run,"ui-failure.txt"),String(error),{flag:"wx"});
  throw error;
} finally { await context.close(); await server.close(); }
