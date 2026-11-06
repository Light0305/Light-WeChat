// Run Guizang's original R1-R9 checker with portable local runtime adaptations.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const vendor = path.resolve(import.meta.dirname, '../vendor/guizang');
const original = path.join(vendor, 'validate-social-deck.mjs');
const root = path.resolve(import.meta.dirname, '..');
const playwrightPath = path.join(root, 'node_modules/playwright/index.mjs');
const moduleUrl = pathToFileURL(playwrightPath).href;
if (!fs.existsSync(playwrightPath)) {
  throw new Error('Optional cover checker dependency missing: run npm ci --ignore-scripts at the repository root');
}
// A shebang is only valid on the first line; remove it from the temporary copy
// before prepending the portability import. The pinned original stays untouched.
let source = "import {pathToFileURL as portableFileURL} from 'node:url';\n" +
  fs.readFileSync(original, 'utf8').replace(/^#![^\r\n]*(?:\r?\n|$)/, '');
source = source.replace('from "playwright"', 'from ' + JSON.stringify(moduleUrl));
source = source.replace('const url = "file://" + htmlPath;', 'const url = portableFileURL(htmlPath).href;');
source = source.replace('const browser = await chromium.launch({',
  'const browser = await chromium.launch({ ...(process.env.CHUANLAB_BROWSER ? {executablePath: process.env.CHUANLAB_BROWSER} : {}),');
source = source.replace('process.exit(totalFail > 0 ? 1 : 0);', 'process.exitCode = totalFail > 0 ? 1 : 0;');
// The checker uses fileURLToPath(import.meta.url) only for module context; run an
// adapted sibling in scripts, leaving every vendored source byte unchanged.
const adapted = path.join(import.meta.dirname, `.guizang-validator-runtime-${process.pid}.mjs`);
fs.writeFileSync(adapted, source);
try { await import(pathToFileURL(adapted)); }
finally { if (fs.existsSync(adapted)) fs.unlinkSync(adapted); }
