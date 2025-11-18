---
title: "Enrich Card Content"
api: "POST /api/enrich"
description: "Enrich card content with AI-powered suggestions using RAG pipeline...."
---

## Overview

Enrich card content with AI-powered suggestions using RAG pipeline.

## Request Body

```json
{
  "card_id": "<string>",
  "content": "<string>",
  "context": "<string>",
  "max_suggestions": "<integer>"
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/api/enrich"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/api/enrich \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

