---
title: "Semantic Search"
api: "POST /query/rag"
description: "Perform semantic search across all content using vector embeddings...."
---

## Overview

Perform semantic search across all content using vector embeddings.

## Request Body

```json
{
  "prompt": "<string>",
  "n_results": "<integer>",
  "platform_filter": "<string>",
  "author_filter": "<string>"
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/query/rag"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/query/rag \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

