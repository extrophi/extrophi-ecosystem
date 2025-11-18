---
title: "Health Check"
api: "GET /health"
description: "Check application health status and component availability...."
---

## Overview

Check application health status and component availability.

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/health"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.get(url, headers=headers)
print(response.json())
```

### cURL

```bash
curl -X GET \
  https://api.extrophi.ai/health \
  -H "Authorization: Bearer YOUR_API_KEY"
```

