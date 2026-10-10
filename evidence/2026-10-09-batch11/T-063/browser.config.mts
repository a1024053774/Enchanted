// Same repository browser configuration and tests; only select the installed browser binary.
import { mergeConfig } from "/Users/luckye/Documents/Code/synara/apps/web/node_modules/vitest/dist/config.js";
import { playwright } from "/Users/luckye/Documents/Code/synara/apps/web/node_modules/@vitest/browser-playwright/dist/index.js";
import original from "/Users/luckye/Documents/Code/synara/apps/web/vitest.browser.config";

export default mergeConfig(original, {
  root: "/Users/luckye/Documents/Code/synara/apps/web",
  test: {
    browser: {
      provider: playwright({
        launchOptions: { executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" },
      }),
    },
  },
});
