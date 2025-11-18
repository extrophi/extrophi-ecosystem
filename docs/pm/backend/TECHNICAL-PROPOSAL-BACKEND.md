# TECHNICAL PROPOSAL: BACKEND MODULE

**Budget:** ~$150  
**Timeline:** 8 hours  
**Agents:** 6 (OMICRON, RHO, PI, SIGMA, TAU, UPSILON)

## AGENTS

**OMICRON (1 hr):** Database schema (cards, users, attributions, extropy_ledger, sync_state)  
**RHO (1 hr):** Authentication (API keys)  
**PI (2 hrs):** Publish endpoint - accepts cards from Writer  
**SIGMA (2 hrs):** $EXTROPY token system - award on publish, transfer on attribution  
**TAU (2 hrs):** Attribution API - citation, remix, reply types  
**UPSILON (1 hr):** GraphQL API - OPTIONAL

## PARALLEL EXECUTION

```
OMICRON → START FIRST (1 hr)
  ↓
When done → RHO, SIGMA → PARALLEL
  ↓
When RHO done → PI
When SIGMA done → TAU
```

## INTEGRATION

- From Writer: `POST /api/publish` (receives cards)
- With Research: Shared PostgreSQL
- Returns: URLs, $EXTROPY earned

## CRITICAL

Use Decimal for money (not float)  
No negative balances possible  
Database transactions correct
