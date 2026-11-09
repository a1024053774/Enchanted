import { downloadArtifact } from '/private/tmp/a2a-t262-v4-package-20261109/workbench/node_modules/@electron/get/dist/index.js';
import { getArtifactFileName } from '/private/tmp/a2a-t262-v4-package-20261109/workbench/node_modules/@electron/get/dist/artifact-utils.js';
const cacheRoot='/private/tmp/t262-electron-prefetch-20261109/cache';
const nonce=Date.now();
const result=await downloadArtifact({version:'43.4.1',artifactName:'electron',platform:'darwin',arch:'arm64',cacheRoot,tempDirectory:'/private/tmp/t262-electron-prefetch-20261109',mirrorOptions:{resolveAssetURL:async details=>'https://github.com/electron/electron/releases/download/'+details.version+'/'+getArtifactFileName(details)+'?a2a_download='+nonce}});
console.log(JSON.stringify({file:result,verifiedBy:'@electron/get default checksum validation',officialOrigin:'https://github.com/electron/electron/releases/download/v43.4.1/'}));
