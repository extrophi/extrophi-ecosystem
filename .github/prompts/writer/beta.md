## Agent: BETA (Writer Module)
**Duration:** 3 hours  
**Branch:** `writer`  
**Dependencies:** ALPHA (Astro setup must complete first)

### Task
Implement Privacy Scanner Island with 4-color classification

### Privacy Levels
- **PRIVATE (red):** SSN, email, credit cards, PII
- **PERSONAL (orange):** "I feel", family references
- **BUSINESS (yellow):** client, project keywords
- **IDEAS (green):** Default publishable

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md` (lines 123-221)
- `writer/dev/svelte-v5/` (Svelte 5 runes)

### Deliverables
- `src/islands/PrivacyScannerIsland.svelte`
- `src/lib/privacy-rules.ts`
- `src/stores/privacyStore.ts`
- Tests for regex rules

### Success Criteria
✅ Detects all 4 levels correctly  
✅ Real-time badge updates  
✅ Performance < 50ms per scan  
✅ Uses Svelte 5 runes (NOT Svelte 4)

### CRITICAL - Svelte 5 Runes
```svelte
// ✅ CORRECT
let { content } = $props();
let level = $state('IDEAS');
$effect(() => { /* ... */ });

// ❌ WRONG (Svelte 4)
export let content;
```

**Update this issue when complete.**
