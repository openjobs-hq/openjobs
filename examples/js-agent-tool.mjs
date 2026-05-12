// Copyright 2026 OpenJobs
// SPDX-License-Identifier: Apache-2.0

import { OpenJobsClient } from "../packages/sdk-js/src/index.js";

const client = new OpenJobsClient();

const tasks = await client.listTasks({ status: "unread" });
console.log(JSON.stringify(tasks, null, 2));
