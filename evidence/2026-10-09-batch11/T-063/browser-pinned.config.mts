// Same repository browser configuration and tests; only select the installed browser binary.
import { mergeConfig } from "/Users/luckye/Documents/Code/synara/apps/web/node_modules/vitest/dist/config.js";
import { playwright } from "/Users/luckye/Documents/Code/synara/apps/web/node_modules/@vitest/browser-playwright/dist/index.js";
import original from "/Users/luckye/Documents/Code/synara/apps/web/vitest.browser.config";

export default mergeConfig(original, {
  root: "/Users/luckye/Documents/Code/synara/apps/web",
  test: {
    browser: {
      provider: playwright({
        launchOptions: { executablePath: "/Volumes/WD-Elements/dev-cache/synara/playwright-t063/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell" },
      }),
    },
  },
});
