import assert from "node:assert/strict";
import { join } from "node:path";

// Load the real settings navigation through Vite's web-module resolver.
// The expected page name comes from T-064 Acceptance, not a product export.
const fork = "/Users/luckye/Documents/Code/synara";
const { createServer } = await import(
  join(fork, "apps/web/node_modules/vite/dist/node/index.js")
);
const server = await createServer({
  root: join(fork, "apps/web"),
  configFile: join(fork, "apps/web/vite.config.ts"),
  cacheDir: "/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-preflight/vite",
  server: { middlewareMode: true, watch: null },
});
try {
  const navigation = await server.ssrLoadModule("/src/settingsNavigation.ts");
  const items = navigation.SETTINGS_NAV_ITEMS.map(
    (item: { id: string; label: string }) => ({ id: item.id, label: item.label }),
  );
  console.log(JSON.stringify({ expected_label: "角色权限", actual_navigation: items }));
  assert.ok(
    items.some((item: { label: string }) => item.label === "角色权限"),
    "T-064: the settings navigation must expose 角色权限",
  );
} finally {
  await server.close();
}
