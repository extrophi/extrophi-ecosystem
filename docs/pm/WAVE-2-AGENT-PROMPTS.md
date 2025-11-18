# WAVE 2 AGENT PROMPTS - COPY/PASTE READY

**Instructions**: Copy the prompt below for each agent and paste into CCW

---

## GAMMA - Card UI (Writer Module)

```
Execute Wave 2 Agent GAMMA

Repository: extrophi/extrophi-ecosystem
Branch: writer
Issue: #50
Prompt file: .github/prompts/writer/gamma.md

Read the prompt file and implement Card UI with 6-category system:
- UNASSIMILATED (white)
- PROGRAM (blue)
- CATEGORIZED (green)
- GRIT (orange)
- TOUGH (red)
- JUNK (gray)

Build drag-and-drop card grid with Svelte 5 runes, integrate privacy scanner from BETA, use Tailwind for styling.

Duration: 4 hours
Dependencies: ALPHA #33, BETA #34 must be complete

START NOW.
```

---

## EPSILON - Terminal Panel (Writer Module)

```
Execute Wave 2 Agent EPSILON

Repository: extrophi/extrophi-ecosystem
Branch: writer
Issue: #51
Prompt file: .github/prompts/writer/epsilon.md

Read the prompt file and implement Terminal panel with xterm.js:
- Full terminal emulator
- Tauri shell command execution
- Command history (up/down arrows)
- ANSI color support
- Toggle visibility (Ctrl+`)

Build TerminalIsland.svelte component with xterm.js integration.

Duration: 2 hours
Dependencies: DELTA #35 must be complete

START NOW.
```

---

## ZETA - Git Publish (Writer Module)

```
Execute Wave 2 Agent ZETA

Repository: extrophi/extrophi-ecosystem
Branch: writer
Issue: #52
Prompt file: .github/prompts/writer/zeta.md

Read the prompt file and implement Git publish with privacy filtering:
- Filter cards by privacy level (BUSINESS + IDEAS only)
- Export to markdown files
- Git integration (libgit2-rs)
- Commit and push to remote
- One-click publish UI

CRITICAL: PRIVATE and PERSONAL cards must NEVER sync.

Duration: 3 hours
Dependencies: GAMMA #50, ETA #36 must be complete

START NOW.
```

---

## LAMBDA - Embedding Generation (Research Module)

```
Execute Wave 2 Agent LAMBDA

Repository: extrophi/extrophi-ecosystem
Branch: research
Issue: #53
Prompt file: .github/prompts/research/lambda.md

Read the prompt file and implement embedding generation:
- OpenAI ada-002 API integration
- Text chunking (512 tokens)
- Batch processing (100 chunks per request)
- Pgvector storage in PostgreSQL
- Cache layer (avoid re-embedding)
- Cost tracking

Build research/backend/embeddings/generator.py module.

Duration: 2 hours
Dependencies: KAPPA #38 must be complete

START NOW.
```

---

## MU - Enrichment Engine (Research Module)

```
Execute Wave 2 Agent MU

Repository: extrophi/extrophi-ecosystem
Branch: research
Issue: #54
Prompt file: .github/prompts/research/mu.md

Read the prompt file and implement enrichment engine:
- RAG pipeline (retrieval + generation)
- Vector similarity search (pgvector)
- Multi-platform scraping integration
- LLM analysis (GPT-4) - extract frameworks, patterns
- Suggestion generation
- Source attribution

Build research/backend/enrichment/engine.py module.

Duration: 3 hours
Dependencies: THETA #37, LAMBDA #53, IOTA #39 must be complete

START NOW.
```

---

## RHO - API Key Authentication (Backend Module)

```
Execute Wave 2 Agent RHO

Repository: extrophi/extrophi-ecosystem
Branch: backend
Issue: #55
Prompt file: .github/prompts/backend/rho.md

Read the prompt file and implement API key authentication:
- Secure key generation (32+ chars)
- SHA-256 hashed storage
- Authorization middleware (FastAPI dependency)
- Rate limiting (1000 req/hour per key)
- Key management endpoints (create, list, revoke)

Build backend/auth/api_keys.py module.

Duration: 1 hour
Dependencies: OMICRON #41 must be complete

START NOW.
```

---

## PI - Publish Endpoint (Backend Module)

```
Execute Wave 2 Agent PI

Repository: extrophi/extrophi-ecosystem
Branch: backend
Issue: #56
Prompt file: .github/prompts/backend/pi.md

Read the prompt file and implement publish endpoint:
- Accept cards from Writer module
- Privacy filtering (BUSINESS + IDEAS only)
- Markdown conversion
- URL generation (unique slugs)
- PostgreSQL storage
- $EXTROPY rewards (1 token per publish)

Build backend/api/publish.py module.

Duration: 2 hours
Dependencies: RHO #55, OMICRON #41 must be complete

START NOW.
```

---

## SIGMA - $EXTROPY Token System (Backend Module)

```
Execute Wave 2 Agent SIGMA

Repository: extrophi/extrophi-ecosystem
Branch: backend
Issue: #57
Prompt file: .github/prompts/backend/sigma.md

Read the prompt file and implement $EXTROPY token system:
- Award tokens (publish, citation, remix)
- Transfer tokens (user-to-user)
- Balance tracking with DECIMAL precision
- Ledger audit trail (immutable log)
- Negative balance prevention

CRITICAL REQUIREMENTS:
- Use DECIMAL for money (NOT float)
- Database transactions for atomic operations
- NO negative balances allowed (CHECK constraint)
- Audit trail for all transfers

Build backend/tokens/extropy.py module.

Duration: 2 hours
Dependencies: OMICRON #41 must be complete

START NOW.
```

---

## TAU - Attribution API (Backend Module)

```
Execute Wave 2 Agent TAU

Repository: extrophi/extrophi-ecosystem
Branch: backend
Issue: #58
Prompt file: .github/prompts/backend/tau.md

Read the prompt file and implement attribution API:
- Citation tracking (+0.1 $EXTROPY to author)
- Remix rewards (+0.5 $EXTROPY to author)
- Reply threading (+0.05 $EXTROPY to author)
- Automatic $EXTROPY transfers
- Attribution graph (who cited who)
- Backlinks (where your content is cited)

Build backend/api/attributions.py module.

Duration: 2 hours
Dependencies: SIGMA #57, OMICRON #41 must be complete

START NOW.
```

---

## UPSILON - GraphQL API (Backend Module) - OPTIONAL

```
Execute Wave 2 Agent UPSILON (OPTIONAL)

Repository: extrophi/extrophi-ecosystem
Branch: backend
Issue: #59
Prompt file: .github/prompts/backend/upsilon.md

PRIORITY: OPTIONAL - Defer if time-constrained

Read the prompt file and implement GraphQL API:
- Strawberry GraphQL (Python)
- Card, User, Attribution types
- Query and mutation resolvers
- Nested relationship queries
- GraphiQL playground at /graphql

Build backend/graphql/schema.py module.

Duration: 1 hour
Dependencies: PI #56, TAU #58 must be complete

START NOW.
```

---

## PSI - Integration Tests (Orchestrator Module)

```
Execute Wave 2 Agent PSI

Repository: extrophi/extrophi-ecosystem
Branch: orchestrator
Issue: #60
Prompt file: .github/prompts/orchestrator/psi.md

⚠️ CRITICAL: WAIT FOR ALL OTHER AGENTS TO COMPLETE FIRST

Check that issues #50-#58 are ALL CLOSED before starting.

Read the prompt file and implement integration tests:
- Writer → Research enrichment flow
- Writer → Backend publish flow
- Backend attribution → $EXTROPY transfer flow
- Health monitoring for all services
- Database schema compatibility checks

Build orchestrator/tests/test_integration.py module.

Duration: 2 hours
Dependencies: ALL Wave 2 agents (#50-#58) must be complete

START NOW.
```

---

## OMEGA - Service Registry (Orchestrator Module) - OPTIONAL

```
Execute Wave 2 Agent OMEGA (OPTIONAL)

Repository: extrophi/extrophi-ecosystem
Branch: orchestrator
Issue: #61
Prompt file: .github/prompts/orchestrator/omega.md

PRIORITY: OPTIONAL - Defer if time-constrained

Read the prompt file and implement service registry:
- Service registration/deregistration
- Dynamic service discovery
- Health-based instance selection
- Automatic failover
- Round-robin load balancing

Build orchestrator/registry/service_registry.py module.

Duration: 1 hour
Dependencies: PHI #42, CHI #43 must be complete

START NOW.
```

---

## EXECUTION ORDER (Recommended)

### Phase 1: Foundation (Run in Parallel)
- GAMMA #50 (Writer Card UI)
- EPSILON #51 (Writer Terminal)
- LAMBDA #53 (Research Embeddings)
- RHO #55 (Backend Auth)
- SIGMA #57 (Backend $EXTROPY)

### Phase 2: Integration (After Phase 1)
- ZETA #52 (Writer Git Publish) - needs GAMMA
- MU #54 (Research Enrichment) - needs LAMBDA
- PI #56 (Backend Publish) - needs RHO
- TAU #58 (Backend Attribution) - needs SIGMA

### Phase 3: Optional (If Time Permits)
- UPSILON #59 (Backend GraphQL)
- OMEGA #61 (Orchestrator Service Registry)

### Phase 4: Final Validation (After All Core Agents)
- PSI #60 (Orchestrator Integration Tests) - WAITS for #50-#58

---

**Total**: 12 agents, ~22 hours estimated (10 core + 2 optional)
