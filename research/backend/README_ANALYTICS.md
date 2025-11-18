# PHI-2 Corpus Analytics

Analytics dashboard for the Research Module providing comprehensive insights into scraped content.

## Features

### 📈 Trend Detection
- **Topics Over Time**: Track trending keywords and topics with momentum indicators (rising/stable/declining)
- **Cross-Platform Patterns**: Identify themes that appear across multiple platforms
- **Top Authors**: Rank content creators by activity and engagement
- **Platform Statistics**: Comprehensive metrics for each platform
- **Word Clouds**: Frequency data for visualization

### 😊 Sentiment Analysis
- **Corpus Sentiment**: Overall positive/negative/neutral classification
- **Sentiment Timeline**: Daily sentiment trends
- **Platform Comparison**: Sentiment distribution by platform
- **Author Sentiment**: Identify consistently positive or negative creators

## API Endpoints

### Trend Endpoints

#### GET `/api/analytics/trends/topics`
Get topics and trends over time

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `min_frequency` (int, 1-100): Minimum word frequency (default: 5)
- `platform` (str, optional): Filter by platform

**Response:**
```json
{
  "timeline": [
    {
      "date": "2024-01-15",
      "top_topics": [
        {"word": "innovation", "count": 45, "trend": "rising"}
      ],
      "content_count": 120
    }
  ],
  "top_topics": [
    {"word": "technology", "count": 234, "trend": "stable"}
  ],
  "total_content": 1500,
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-30"
  }
}
```

#### GET `/api/analytics/trends/cross-platform`
Detect topics that appear across multiple platforms

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `min_platforms` (int, 2-10): Minimum platforms (default: 2)

**Response:**
```json
[
  {
    "topic": "artificial_intelligence",
    "platforms": ["twitter", "youtube", "reddit"],
    "platform_count": 3,
    "total_mentions": 156,
    "distribution": {
      "twitter": 78,
      "youtube": 45,
      "reddit": 33
    }
  }
]
```

#### GET `/api/analytics/trends/authors`
Get top content authors by activity

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `limit` (int, 1-100): Number of authors (default: 20)
- `platform` (str, optional): Filter by platform

#### GET `/api/analytics/trends/platforms`
Get comprehensive platform statistics

**Response:**
```json
[
  {
    "platform": "twitter",
    "source_count": 250,
    "content_count": 1500,
    "avg_word_count": 45,
    "total_words": 67500,
    "first_scraped": "2024-01-01T00:00:00",
    "last_scraped": "2024-01-30T23:59:59",
    "unique_authors": 180
  }
]
```

#### GET `/api/analytics/trends/wordcloud`
Get word frequency data for word cloud visualization

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `limit` (int, 10-500): Number of words (default: 100)
- `platform` (str, optional): Filter by platform

**Response:**
```json
[
  {"word": "technology", "frequency": 234},
  {"word": "innovation", "frequency": 189}
]
```

### Sentiment Endpoints

#### GET `/api/analytics/sentiment/corpus`
Analyze overall corpus sentiment

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `platform` (str, optional): Filter by platform
- `limit` (int, optional): Limit content analyzed (for performance)

**Response:**
```json
{
  "overall": {
    "positive": 450,
    "negative": 120,
    "neutral": 430
  },
  "percentages": {
    "positive": 45.0,
    "negative": 12.0,
    "neutral": 43.0
  },
  "average_compound": 0.342,
  "overall_sentiment": "positive",
  "total_analyzed": 1000
}
```

#### GET `/api/analytics/sentiment/timeline`
Get sentiment trends over time

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `platform` (str, optional): Filter by platform

**Response:**
```json
[
  {
    "date": "2024-01-15",
    "positive": 45,
    "negative": 12,
    "neutral": 38,
    "total": 95,
    "average_compound": 0.234
  }
]
```

#### GET `/api/analytics/sentiment/platforms`
Compare sentiment across platforms

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)

#### GET `/api/analytics/sentiment/authors`
Analyze sentiment by author

**Parameters:**
- `days` (int, 1-365): Time window (default: 30)
- `limit` (int, 1-100): Number of authors (default: 20)
- `platform` (str, optional): Filter by platform

## Technology Stack

- **FastAPI**: REST API framework
- **pandas**: Data analysis and manipulation
- **vaderSentiment**: Sentiment analysis (social media optimized)
- **PostgreSQL**: Data storage with pgvector

## Installation

```bash
# Install dependencies
cd research/backend
uv pip install -r requirements.txt

# Or with pyproject.toml
cd ../../backend
uv pip install -e .
```

## Usage

```bash
# Start API server
cd research/backend
uvicorn main:app --reload --port 8000

# Access analytics endpoints
curl http://localhost:8000/api/analytics/trends/topics?days=30
curl http://localhost:8000/api/analytics/sentiment/corpus?days=30
```

## Testing

```bash
# Run analytics tests
pytest tests/test_analytics.py -v

# Run all tests
pytest
```

## Implementation Details

### Trend Analysis (`analytics/trends.py`)
- Uses TF (term frequency) for keyword extraction
- Stopword filtering (150+ common words)
- Minimum word length filter (configurable)
- Trend momentum calculation (recent vs older periods)
- Cross-platform aggregation with distribution metrics

### Sentiment Analysis (`analytics/sentiment.py`)
- **Primary**: VADER sentiment analysis (if installed)
  - Optimized for social media text
  - Compound score: -1 (negative) to +1 (positive)
  - Thresholds: >0.05 positive, <-0.05 negative
- **Fallback**: Basic keyword matching
  - Positive/negative word lists
  - Simple ratio calculation

### API Routes (`api/routes/analytics.py`)
- FastAPI router with prefix `/api/analytics`
- Pydantic models for request/response validation
- Query parameter validation with sensible defaults
- Comprehensive error handling
- Logging for all operations

## Performance Considerations

1. **Large Corpus**: Use `limit` parameter for sentiment analysis
2. **Time Windows**: Shorter time windows (7-30 days) for faster response
3. **Database Indexes**: Ensure indexes on `scraped_at` and `platform` columns
4. **Caching**: Consider Redis for frequently accessed analytics

## Future Enhancements

- [ ] Topic modeling with LDA/NMF
- [ ] Named entity recognition (NER)
- [ ] Comparative analysis (time period comparisons)
- [ ] Export to CSV/JSON for external tools
- [ ] Scheduled analytics reports
- [ ] Real-time analytics with WebSockets
- [ ] Visualization endpoints (charts, graphs)

## Examples

### Get trending topics
```bash
curl "http://localhost:8000/api/analytics/trends/topics?days=30&min_frequency=10"
```

### Analyze sentiment by platform
```bash
curl "http://localhost:8000/api/analytics/sentiment/platforms?days=30"
```

### Get cross-platform patterns
```bash
curl "http://localhost:8000/api/analytics/trends/cross-platform?days=30&min_platforms=3"
```

### Get word cloud data
```bash
curl "http://localhost:8000/api/analytics/trends/wordcloud?days=30&limit=200"
```

## Architecture

```
research/backend/
├── analytics/
│   ├── __init__.py
│   ├── trends.py          # Trend detection logic
│   └── sentiment.py       # Sentiment analysis logic
├── api/
│   └── routes/
│       ├── __init__.py
│       └── analytics.py   # API endpoints
├── main.py                # FastAPI app (includes analytics router)
└── tests/
    └── test_analytics.py  # Analytics tests
```

## License

Part of the IAC-033 Extrophi Ecosystem project.

---

**Agent**: PHI-2
**Task**: Corpus Analytics Dashboard
**Status**: ✅ Complete
