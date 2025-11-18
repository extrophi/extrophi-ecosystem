## Agent: GAMMA (Writer Module)
**Duration:** 4 hours
**Branch:** `writer`
**Dependencies:** ALPHA #33, BETA #34

### Task
Build Card UI with 6-category classification system

### Categories
1. **UNASSIMILATED** - Raw brain dump (white)
2. **PROGRAM** - Actionable systems (blue)
3. **CATEGORIZED** - Organized knowledge (green)
4. **GRIT** - Challenges, struggles (orange)
5. **TOUGH** - Hard truths, contrarian (red)
6. **JUNK** - Discard pile (gray)

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md`
- Privacy levels from BETA #34

### Deliverables
- `writer/src/islands/CardGridIsland.svelte`
- Drag-and-drop between categories
- Visual categorization (colors)
- Filter by category
- Integration with privacy scanner

### UI Requirements
- Svelte 5 runes ($props, $state, $derived)
- Tailwind CSS for styling
- 6 columns layout (responsive: 3 on tablet, 1 on mobile)
- Drag gestures (svelte-dnd-action or custom)
- Category badges with colors

### Data Model
```typescript
interface Card {
  id: string;
  content: string;
  category: 'UNASSIMILATED' | 'PROGRAM' | 'CATEGORIZED' | 'GRIT' | 'TOUGH' | 'JUNK';
  privacy_level: 'PRIVATE' | 'PERSONAL' | 'BUSINESS' | 'IDEAS';
  created_at: string;
  updated_at: string;
}
```

### Success Criteria
✅ 6 category columns render
✅ Cards can be dragged between categories
✅ Visual distinction (colors per category)
✅ Filter toggles work
✅ Privacy badges from BETA integrated
✅ Tests pass

### Commit Message
```
feat(writer): Add Card UI with 6-category system

Implements drag-and-drop card organization:
- UNASSIMILATED: Raw brain dump (white)
- PROGRAM: Actionable systems (blue)
- CATEGORIZED: Organized knowledge (green)
- GRIT: Challenges (orange)
- TOUGH: Contrarian truths (red)
- JUNK: Discard pile (gray)

Integrates privacy scanner from BETA.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #50 when complete.**
