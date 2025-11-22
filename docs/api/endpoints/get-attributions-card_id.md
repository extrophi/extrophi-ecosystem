---
title: "Get Card Attributions"
api: "GET /attributions/{card_id}"
description: "Get all attributions for a card (backlinks showing who cited this card)...."
---

## Overview

Get all attributions for a card (backlinks showing who cited this card).

## Parameters

### `card_id` **Required**

- **Type:** `string`
- **Location:** path

### `limit` *Optional*

- **Type:** `integer`
- **Location:** query

## Code Examples

### Python

```python
import requests

url = "https://api.extrophi.ai/attributions/{card_id}"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

response = requests.get(url, headers=headers)
print(response.json())
```

### cURL

```bash
curl -X GET \
  https://api.extrophi.ai/attributions/{card_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

