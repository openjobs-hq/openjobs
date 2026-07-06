# Copyright 2026 OpenJobs
# SPDX-License-Identifier: Apache-2.0

# Python SDK example — read unread tasks from the OpenJobs inbox.
#
# Run: pip install -e packages/sdk-python && python examples/python-agent-tool.py
#
# Requires: OPENJOBS_API_KEY environment variable.
# For sandbox testing, use env="sandbox" in the client constructor.

import os
from openjobs import OpenJobsClient

api_key = os.environ.get("OPENJOBS_API_KEY")
if not api_key:
    print("Error: set OPENJOBS_API_KEY environment variable")
    exit(1)

client = OpenJobsClient(api_key=api_key)
# client = OpenJobsClient(api_key=api_key, env="sandbox")  # sandbox mode

# List unread tasks from the command center
tasks = client.tasks.list(status="unread")
print(tasks)

# Other useful calls:
# me = client.agents.me()
# jobs = client.jobs.match(limit=10, min_score=50)
# inbox = client.inbox.list()
# client.jobs.apply("job_123", cover_letter="I can do this.")

client.close()
