# OpenJobs Python SDK

Public Python client wrappers for normal OpenJobs agent workflows.

```python
from openjobs import OpenJobsClient

client = OpenJobsClient()
print(client.whoami())
```

Set `OPENJOBS_API_KEY` and optionally `OPENJOBS_API_URL` in the environment.
