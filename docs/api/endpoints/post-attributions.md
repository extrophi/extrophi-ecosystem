---
title: "Create Attribution"
api: "POST /attributions"
description: "Create attribution and transfer $EXTROPY tokens. Supports citation (+0.1), remix (+0.5), and reply (..."
---

## Overview

Create attribution and transfer $EXTROPY tokens. Supports citation (+0.1), remix (+0.5), and reply (+0.05).

## Request Body

```json
{
  "source_card_id": "<string>",
  "target_card_id": "<string>",
  "attribution_type": "<string>",
  "user_id": "<string>",
  "context": "<string>",
  "excerpt": "<string>"
}
```

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/attributions"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST \
  https://api.extrophi.ai/attributions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"key": "value"}'
```

