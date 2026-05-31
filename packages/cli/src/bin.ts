/**
 * Binary entrypoint. The build step prepends `#!/usr/bin/env node`
 * to the emitted CJS so this file stays valid TypeScript.
 */
import { run } from "./index.js";

run(process.argv.slice(2)).catch((err: any) => {
  process.stderr.write(`fatal: ${err?.stack ?? err?.message ?? err}\n`);
  process.exit(1);
});
