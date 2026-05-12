# Copyright 2026 OpenJobs
# SPDX-License-Identifier: Apache-2.0

from openjobs import OpenJobsClient


client = OpenJobsClient()
tasks = client.list_tasks(status="unread")
print(tasks)
