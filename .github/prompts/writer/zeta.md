## Agent: ZETA (Writer Module)
**Duration:** 3 hours
**Branch:** `writer`
**Dependencies:** GAMMA #50, ETA #36

### Task
Implement Git publish - selective sync of BUSINESS + IDEAS cards only

### Privacy Rules
- **PRIVATE**: NEVER sync (stays local only)
- **PERSONAL**: NEVER sync (stays local only)
- **BUSINESS**: Sync to GitHub (public or private repo)
- **IDEAS**: Sync to GitHub (public or private repo)

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md`
- Privacy levels from BETA #34

### Deliverables
- `writer/src-tauri/src/git/mod.rs`
- Git integration (libgit2-rs or Command)
- Selective export by privacy level
- Commit message generation
- Push to remote

### Workflow
```rust
// 1. Filter cards by privacy level
let publishable_cards = cards.iter()
    .filter(|c| c.privacy_level == "BUSINESS" || c.privacy_level == "IDEAS")
    .collect();

// 2. Export to markdown files
for card in publishable_cards {
    write_to_file(format!("content/{}.md", card.id), &card.content)?;
}

// 3. Git add, commit, push
git_add("content/")?;
git_commit("Update published cards")?;
git_push("origin", "main")?;
```

### UI Component
- `writer/src/islands/PublishIsland.svelte`
- Shows publishable card count
- One-click publish button
- Git status display
- Last sync timestamp

### Success Criteria
✅ Filters cards by privacy (BUSINESS + IDEAS only)
✅ Exports to markdown files
✅ Git commits created
✅ Push to remote works
✅ UI shows publish status
✅ Tests pass (mock git operations)

### Commit Message
```
feat(writer): Add Git publish with privacy filtering

Implements selective sync:
- BUSINESS cards → Git repository
- IDEAS cards → Git repository
- PRIVATE/PERSONAL → Stay local only

Features:
- Markdown export
- Git integration (libgit2-rs)
- One-click publish UI
- Last sync tracking

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Update issue #52 when complete.**
