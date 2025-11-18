# CCW Fix YouTube Transcript Type Error

**URGENT: 1 test failing, blocking merge**

---

## Error

```
backend/scrapers/adapters/youtube.py:115: in normalize
    word_count=len(transcript.split()),
AttributeError: 'list' object has no attribute 'split'
```

## File: backend/scrapers/adapters/youtube.py

### Line 115 - Fix the transcript type handling

```python
# CHANGE line 115:
word_count=len(transcript.split()),

# TO:
word_count=len(transcript.split()) if isinstance(transcript, str) else 0,
```

The `transcript` variable from `raw_data.get("transcript", "")` can be either:
- A string (already joined transcript)
- A list (raw segments not joined)

The fix handles both cases safely.

---

## Commands

```bash
# 1. Fix the file
# Edit backend/scrapers/adapters/youtube.py line 115

# 2. Run tests locally
pytest tests/unit/test_scrapers.py::TestYouTubeScraper::test_normalize_transcript -v

# 3. Commit and push
git add backend/scrapers/adapters/youtube.py
git commit -m "fix: Handle both string and list transcript types in YouTube scraper"
git push origin claude/ccw-orchestrator-agents-01PWLwtQasQujQbA1QrAw72S
```

---

**Once this passes, CI will be GREEN and PR #19 can merge.**

GO.
