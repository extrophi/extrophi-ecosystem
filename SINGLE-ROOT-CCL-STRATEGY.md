# SINGLE ROOT CCL STRATEGY
## One Agent, Multiple Sub-Agents (More Efficient)

**REVISED APPROACH:**

## OLD (EXPENSIVE):
```
4 separate CCL instances in tmux windows
→ Burns 4x Max Plan usage
→ Context duplication
→ Coordination overhead
```

## NEW (EFFICIENT):
```
1 ROOT CCL at project root
→ Spawns sub-agents as needed
→ Sub-agents work in module folders
→ Much cheaper (1 instance vs 4)
→ Better coordination
```

---

## ROOT CCL LOCATION

```bash
Location: /Users/kjd/01-projects/IAC-033-extrophi-ecosystem/
Command: claude --dangerously-skip-permissions

Role: Project orchestrator
Job: Spawn sub-agents for each task
```

---

## ORCHESTRATOR MODULE LOCATION

**CLARIFICATION NEEDED:**

**Option A:** Orchestrator stays at root (no subfolder)
- Root = orchestrator code + project management
- writer/, research/, backend/ are subfolders
- Root CCL IS the orchestrator

**Option B:** Orchestrator has own subfolder
- orchestrator/ subfolder exists
- Root = project management only
- Root CCL manages all 4 modules

**RECOMMENDED: Option A**
- Simpler structure
- Root CCL = orchestrator agent
- Fewer directories to manage

---

## SUB-AGENT WORKFLOW

### Root CCL spawns:
```
Sub-agent: Writer-Cleanup
Task: Clean writer module
Folder: writer/
Duration: 30 min

Sub-agent: Writer-Privacy
Task: Build privacy linter
Folder: writer/
Duration: 3 hrs

Sub-agent: Research-Scraper
Task: Implement scrapers
Folder: research/
Duration: 4 hrs

[etc for all tasks]
```

### Coordination:
- Root CCL monitors all sub-agents
- Sub-agents report to root
- Root makes decisions
- Root enforces quality

---

## COST COMPARISON

**4 CCL instances:**
- 4 × context windows
- 4 × monitoring overhead
- Estimated: 40% Max Plan usage

**1 ROOT CCL + sub-agents:**
- 1 context window
- Sub-agents are cheap (focused tasks)
- Estimated: 10-15% Max Plan usage

**Savings: ~60-70% of Max Plan credits**

---

## EXECUTION

```bash
cd /Users/kjd/01-projects/IAC-033-extrophi-ecosystem
claude --dangerously-skip-permissions
```

Then:
```
I am ROOT CCL for IAC-033 Extrophi Ecosystem.

1. Execute cleanup (CLEANUP_PLAN_UPDATED.md)
2. Download + convert documentation
3. Spawn sub-agents for module work
4. Monitor and coordinate
5. Enforce quality standards

Start with Task 1: Cleanup.
Wait for my approval before proceeding.
```
