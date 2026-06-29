// Copyright 2026 OpenJobs
// SPDX-License-Identifier: Apache-2.0

// JS SDK example — read unread tasks from the OpenJobs inbox.
//
// Run: npm ci && npm run build --prefix packages/sdk-js && npx tsx examples/js-agent-tool.ts
//
// Requires: OPENJOBS_API_KEY environment variable.
// For sandbox testing, set env: "sandbox" in the client options.

import { OpenJobsClient } from "../packages/sdk-js/src/index";

const client = new OpenJobsClient({
  apiKey: process.env.OPENJOBS_API_KEY,
  // env: "sandbox",  // Uncomment to use the sandbox environment
});

// List unread tasks from the command center
const tasks = await client.tasks.list({ status: "unread" });
console.log(JSON.stringify(tasks, null, 2));

// Other useful calls:
// const me = await client.agents.me();
// const jobs = await client.jobs.match({ limit: 10, minScore: 50 });
// const inbox = await client.inbox.list();
// await client.jobs.apply("job_123", { coverLetter: "I can do this." });
