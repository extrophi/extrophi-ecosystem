---
title: "Publish Cards"
api: "POST /publish"
description: "Publish cards from Writer module with privacy filtering and $EXTROPY rewards...."
---

## Overview

Publish cards from Writer module with privacy filtering and $EXTROPY rewards.

## Request Body

```json
{
  "cards": "<array>"
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/publish"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/publish \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

