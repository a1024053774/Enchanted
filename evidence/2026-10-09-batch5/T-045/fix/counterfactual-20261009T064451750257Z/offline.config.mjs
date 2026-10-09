import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repo = resolve(process.env.T045_SYNARA_ROOT);
export default {
  root: dirname(fileURLToPath(import.meta.url)),
  cacheDir: join(process.env.TMPDIR, "t045-vitest-cache"),
  resolve: {
    alias: [
      { find: /^#server\//, replacement: `${repo}/apps/server/src/` },
      { find: /^@synara\/contracts$/, replacement: `${repo}/packages/contracts/src/index.ts` },
      { find: /^@synara\/shared\/(.*)$/, replacement: `${repo}/packages/shared/src/$1.ts` },
      { find: /^vitest$/, replacement: `${repo}/node_modules/vitest/dist/index.js` },
    ],
  },
  test: { include: ["offline-usage.test.ts"], maxWorkers: 1, fileParallelism: false },
};
