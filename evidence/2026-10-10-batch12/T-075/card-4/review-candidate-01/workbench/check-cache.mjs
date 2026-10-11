import { statSync } from "node:fs";

const mount = "/Volumes/WD-Elements";
if (statSync(mount).dev === statSync("/Volumes").dev) {
  throw new Error("依赖安装要求挂载 /Volumes/WD-Elements；不回退到内置盘。");
}
if (process.env.npm_config_cache !== `${mount}/a2a-t075-npm-cache`) {
  throw new Error("npm 缓存必须使用外置盘上的 a2a-t075-npm-cache。");
}
