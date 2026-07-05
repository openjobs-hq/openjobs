#!/usr/bin/env node
export { OpenJobsMcpServer, runStdioServer } from "./server.js";
export { createToolDefinitions } from "./tools.js";
export { loadConfig, saveCredentials, clearCredentials, redactDeep, redactSecret } from "./config.js";

import { runStdioServer } from "./server.js";

if (import.meta.url === `file://${process.argv[1]}`) {
  runStdioServer().catch((err) => {
    console.error(err instanceof Error ? err.message : String(err));
    process.exitCode = 1;
  });
}
