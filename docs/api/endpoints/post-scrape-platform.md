---
title: "Scrape Content from Platform"
api: "POST /scrape/{platform}"
description: "Scrape content from specified platform (twitter, youtube, reddit, web)...."
---

## Overview

Scrape content from specified platform (twitter, youtube, reddit, web).

## Parameters

### `platform` **Required**

- **Type:** `string`
- **Location:** path
- **Description:** Platform to scrape from

## Request Body

```json
{
  "target": "dankoe",
  "limit": 50
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/scrape/{platform}"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/scrape/{platform} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

