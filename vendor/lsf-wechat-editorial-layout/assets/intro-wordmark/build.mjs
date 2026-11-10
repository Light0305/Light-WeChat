import { createRequire } from 'node:module';
import { dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { build } = require('esbuild');
const nodeModules = dirname(dirname(require.resolve('esbuild/package.json')));

await build({
  absWorkingDir: fileURLToPath(new URL('.', import.meta.url)),
  entryPoints: ['wordmark.jsx'],
  outfile: 'wordmark.bundle.js',
  bundle: true,
  minify: true,
  format: 'iife',
  jsx: 'automatic',
  loader: { '.woff2': 'dataurl', '.webp': 'dataurl' },
  // The vendored effect modules sit beside this directory and share its React.
  nodePaths: [nodeModules],
});
