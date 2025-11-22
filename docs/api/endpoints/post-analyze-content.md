---
title: "Analyze Content with LLM"
api: "POST /analyze/content"
description: "Analyze single content piece with LLM to extract frameworks, hooks, themes, and pain points...."
---

## Overview

Analyze single content piece with LLM to extract frameworks, hooks, themes, and pain points.

## Request Body

```json
{
  "content": "<string>"
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/analyze/content"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/analyze/content \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

