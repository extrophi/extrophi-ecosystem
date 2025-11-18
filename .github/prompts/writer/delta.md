## Agent: DELTA (Writer Module)
**Duration:** 6 hours (DECISION at 3 hrs)  
**Branch:** `writer`  
**Dependencies:** ALPHA  
**Risk:** 🔴 HIGH

### ⚠️ FALLBACK STRATEGY
```
Hour 0-3: Try CodeMirror + vim
  ↓
Hour 3: DECISION POINT
  - Working? Continue
  - Blocked? SWITCH to textarea
  ↓
Hour 3-6: Polish chosen approach
```

### Task
Implement Editor Island (vim OR textarea)

### Technical Reference
- `/docs/pm/writer/TECHNICAL-PROPOSAL-WRITER.md` (lines 339-512)

### Deliverables
- `src/islands/EditorIsland.svelte`
- Auto-save (500ms debounce)
- Privacy integration
- Cmd+S shortcut

### Success Criteria (MUST)
✅ Auto-save works  
✅ Cmd+S works  
✅ Privacy integration  
✅ Persists via Tauri

### Success Criteria (NICE TO HAVE)
⚠️ Vim mode (fallback OK)  
✅ **Textarea is 100% acceptable**

### IMPORTANT
At hour 3: Report decision (vim or textarea)

**Update this issue at 3 hours with decision.**
