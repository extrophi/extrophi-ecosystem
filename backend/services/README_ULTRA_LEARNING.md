# Ultra Learning Parser

Agent #7: Ultra Learning Parser - Transforms scraped content into structured learning format.

## Overview

The Ultra Learning Parser extracts structured learning components from scraped content using Claude Haiku 4:

- **Meta Subject**: Main topic/subject (1-5 words)
- **Concepts**: Key ideas, frameworks, principles
- **Facts**: Statistics, data points, factual claims
- **Procedures**: Step-by-step instructions, processes

## Model Details

- **Model**: `claude-haiku-4-20250514`
- **Max Tokens**: 1000 per item
- **Cost**: ~$0.00025 per item (~$1.25 for 5,000 items)
- **Batch Size**: 100 items (configurable)
- **Rate Limiting**: 1 second sleep between batches (configurable)

## Setup

### 1. Install Dependencies

```bash
cd backend
uv pip install anthropic>=0.39.0
```

### 2. Configure API Key

Add to `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Run Database Migration

```bash
cd backend
python -m backend.db.migrations.migrate apply
```

Or manually run the migration:

```bash
psql -U user -d unified_scraper -f db/migrations/003_ultra_learning_table.sql
```

## Usage

### API Endpoints

#### Parse Content

```bash
POST /api/ultra-learning/parse
```

Process scraped content into ultra learning format.

**Request Body**:

```json
{
  "limit": 100,
  "batch_size": 10,
  "sleep_between_batches": 1.0
}
```

**Example**:

```bash
# Parse first 100 unprocessed items
curl -X POST "http://localhost:8000/api/ultra-learning/parse" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100, "batch_size": 10, "sleep_between_batches": 1.0}'

# Parse ALL unprocessed items (no limit)
curl -X POST "http://localhost:8000/api/ultra-learning/parse" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 50, "sleep_between_batches": 0.5}'
```

**Response**:

```json
{
  "message": "Processed 100 items (2 failed)",
  "stats": {
    "items_processed": 98,
    "items_failed": 2,
    "total_input_tokens": 45230,
    "total_output_tokens": 12100,
    "total_cost_cents": 124,
    "concepts_extracted": 294,
    "facts_extracted": 147,
    "procedures_extracted": 98,
    "subjects": {
      "Content Marketing": 23,
      "Audience Building": 18,
      "Personal Branding": 15
    },
    "processing_time_ms": 45230,
    "total_processing_time_seconds": 123.45
  }
}
```

#### List Ultra Learning Items

```bash
GET /api/ultra-learning
```

**Query Parameters**:
- `page` (int): Page number (1-indexed)
- `page_size` (int): Items per page (max 500)
- `platform` (string): Filter by platform
- `author_id` (string): Filter by author
- `meta_subject` (string): Filter by subject (partial match)

**Examples**:

```bash
# Get first page
curl "http://localhost:8000/api/ultra-learning?page=1&page_size=20"

# Filter by platform
curl "http://localhost:8000/api/ultra-learning?platform=youtube"

# Search by subject
curl "http://localhost:8000/api/ultra-learning?meta_subject=marketing"
```

#### Get Ultra Learning by Content ID

```bash
GET /api/ultra-learning/{content_id}
```

**Example**:

```bash
curl "http://localhost:8000/api/ultra-learning/123e4567-e89b-12d3-a456-426614174000"
```

#### Get Subject Statistics

```bash
GET /api/ultra-learning/subjects/stats
```

**Query Parameters**:
- `limit` (int): Number of top subjects (max 500)
- `platform` (string): Filter by platform

**Examples**:

```bash
# Top 10 subjects
curl "http://localhost:8000/api/ultra-learning/subjects/stats?limit=10"

# Top YouTube subjects
curl "http://localhost:8000/api/ultra-learning/subjects/stats?platform=youtube&limit=20"
```

### Python SDK

```python
from backend.services.ultra_learning_parser import UltraLearningParser
from backend.db.connection import get_session

# Initialize parser
parser = UltraLearningParser(
    batch_size=100,
    sleep_between_batches=1.0
)

# Get database session
session = next(get_session())

# Process batch
result = parser.process_batch(session, limit=100)

# Print report
print(parser.get_report())
```

## Output Format

Each parsed item produces:

```json
{
  "id": "uuid",
  "content_id": "uuid",
  "title": "How to Build an Audience in 2025",
  "link": "https://youtube.com/watch?v=...",
  "platform": "youtube",
  "author_id": "channel_id",
  "meta_subject": "Audience Building",
  "concepts": [
    "Content pillars",
    "Consistency over perfection",
    "Value-first mindset"
  ],
  "facts": [
    "90% of creators quit within 3 months",
    "Daily posting increases reach by 300%"
  ],
  "procedures": [
    "1. Choose a specific niche",
    "2. Define 3-5 content pillars",
    "3. Post daily for 90 days",
    "4. Engage with comments within 1 hour"
  ],
  "llm_model": "claude-haiku-4-20250514",
  "tokens_used": 1245,
  "cost_cents": 0,
  "processing_time_ms": 1234,
  "created_at": "2025-11-22T12:00:00Z",
  "updated_at": "2025-11-22T12:00:00Z"
}
```

## Database Schema

```sql
CREATE TABLE ultra_learning (
    id UUID PRIMARY KEY,
    content_id UUID UNIQUE REFERENCES contents(id),

    -- Metadata
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    author_id VARCHAR(255) NOT NULL,

    -- Ultra Learning Data
    meta_subject TEXT NOT NULL,
    concepts TEXT[] DEFAULT '{}',
    facts TEXT[] DEFAULT '{}',
    procedures TEXT[] DEFAULT '{}',

    -- Processing Metadata
    llm_model VARCHAR(100) DEFAULT 'claude-haiku-4-20250514',
    tokens_used INTEGER,
    cost_cents INTEGER,
    processing_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Cost Estimation

Based on Claude Haiku pricing (as of 2025-11-22):
- **Input**: $0.80 per million tokens
- **Output**: $4.00 per million tokens

**Typical Content Item**:
- Input tokens: ~400-600
- Output tokens: ~100-150
- Cost per item: ~$0.00025

**Batch Estimates**:
- 1,000 items: ~$0.25
- 5,000 items: ~$1.25
- 10,000 items: ~$2.50
- 50,000 items: ~$12.50

## Performance

**Processing Speed**:
- ~100 items per minute (with 1s batch sleep)
- ~200 items per minute (with 0.5s batch sleep)
- ~500 items per minute (with no sleep, rate limits permitting)

**Recommendations**:
- Use batch_size=100 for balanced performance
- Use sleep_between_batches=1.0 to avoid rate limits
- Process during off-peak hours for large batches

## Error Handling

The parser handles errors gracefully:

- **API Key Missing**: Raises `ValueError` immediately
- **Rate Limit Exceeded**: Automatic retry with exponential backoff (via Anthropic SDK)
- **Invalid Response**: Logs error, continues with next item
- **Duplicate Content**: Skips (IntegrityError on unique constraint)
- **Network Errors**: Logs error, continues with next item

All errors are tracked in `stats["errors"]` array.

## Monitoring

The parser provides detailed statistics:

```
╔══════════════════════════════════════════════════════════════╗
║         ULTRA LEARNING PARSER - PROCESSING REPORT             ║
╚══════════════════════════════════════════════════════════════╝

📊 SUMMARY
  Items Processed:  98
  Items Failed:     2
  Success Rate:     98.0%

📚 EXTRACTED CONTENT
  Concepts:         294
  Facts:            147
  Procedures:       98
  Total Items:      539

💰 COST ANALYSIS
  Input Tokens:     45,230
  Output Tokens:    12,100
  Total Tokens:     57,330
  Total Cost:       $1.24
  Avg Cost/Item:    $0.0013

⏱️  PERFORMANCE
  Total Time:       123.45s
  Avg Time/Item:    1234ms

🎯 TOP SUBJECTS
   1. Content Marketing                      (23 items)
   2. Audience Building                      (18 items)
   3. Personal Branding                      (15 items)
```

## Example Use Cases

### 1. Parse YouTube Transcripts

```bash
# First, scrape YouTube content
curl -X POST "http://localhost:8000/api/scrape/youtube" \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "UC...", "limit": 100}'

# Then, parse into ultra learning format
curl -X POST "http://localhost:8000/api/ultra-learning/parse" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

### 2. Analyze Learning Patterns

```bash
# Get subject statistics
curl "http://localhost:8000/api/ultra-learning/subjects/stats?limit=50"

# Filter by platform
curl "http://localhost:8000/api/ultra-learning?platform=youtube&meta_subject=marketing"
```

### 3. Export to CSV

```python
import csv
import requests

# Fetch all ultra learning data
response = requests.get("http://localhost:8000/api/ultra-learning?page_size=500")
data = response.json()

# Export to CSV
with open("ultra_learning.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "meta_subject", "concepts", "facts", "procedures"])
    writer.writeheader()

    for item in data["items"]:
        writer.writerow({
            "title": item["title"],
            "meta_subject": item["meta_subject"],
            "concepts": "; ".join(item["concepts"]),
            "facts": "; ".join(item["facts"]),
            "procedures": "; ".join(item["procedures"])
        })
```

## Testing

Run tests:

```bash
cd backend
pytest tests/test_ultra_learning_parser.py -v
```

## Rollback

To remove the ultra learning table:

```bash
psql -U user -d unified_scraper -f db/migrations/003_ultra_learning_table_rollback.sql
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: See `backend/services/ultra_learning_parser.py`

---

**Agent #7: Ultra Learning Parser**
**Status**: ✅ Complete
**Date**: 2025-11-22
**Model**: claude-haiku-4-20250514
