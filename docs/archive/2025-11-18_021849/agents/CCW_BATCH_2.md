# CCW Agent Batch 2 - Next Priority Tasks

**Date**: 2025-11-16
**Status**: READY FOR EXECUTION
**Credits to Burn**: $750 by Tuesday

---

## IMMEDIATE PRIORITY: Fix Remaining CI Failures

CI Status as of 05:20 UTC:
- ✅ Frontend Check & Test: SUCCESS
- ✅ Security Audit: SUCCESS
- ✅ Audio System Tests: SUCCESS
- ✅ Database Integrity Tests: SUCCESS
- ✅ API Integration Tests: SUCCESS
- ❌ Rust Check (Ubuntu): FAILURE - **FIXED - libasound2-dev added**
- ❌ Fresh Install Test (macOS): FAILURE
- ❌ Fresh Install Test (Ubuntu): FAILURE

---

## Agent Tasks - Batch 2

### Agent 6: Fresh Install Test Fix (macOS)
**Task**: Debug and fix Fresh Install Test on macOS
- Check the workflow file for Fresh Install Test
- Verify all dependencies are installed
- Fix any missing setup steps
- Ensure clean environment works

### Agent 7: Fresh Install Test Fix (Ubuntu)
**Task**: Debug and fix Fresh Install Test on Ubuntu
- Same as Agent 6 but for Ubuntu
- Check for missing system dependencies
- Verify apt-get packages complete

### Agent 8: Performance Optimization
**Task**: Profile and optimize hot paths
- Run `cargo build --release` timing analysis
- Identify slow compilation units
- Optimize critical paths in Svelte components
- Reduce bundle size where possible

### Agent 9: Documentation Completion
**Task**: Complete all missing docs
- Update README.md with current feature list
- Document all 14 implemented features
- Create user guide for new features
- Add API documentation for Rust commands

### Agent 10: Security Hardening
**Task**: Security audit and fixes
- Review all API key handling
- Audit localStorage usage for sensitive data
- Check for XSS vulnerabilities in chat display
- Validate all user inputs

---

## Coordination

1. Each agent works independently
2. Push fixes to branch: `claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54`
3. Use descriptive commit messages
4. Report results back to `docs/agents/CCW_BATCH_2_REPORT.md`

---

## Git Commands

```bash
git clone https://github.com/Iamcodio/IAC-031-clear-voice-app.git
cd IAC-031-clear-voice-app
git checkout claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
git pull origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54

# After changes:
git add -A
git commit -m "fix: [your specific fix description]"
git push origin claude/overnight-chat-integration-01Bw9rfUA3zLZKNsfbNZdh54
```

---

## Success Metrics

- [ ] All CI jobs green (15/15)
- [ ] PR #22 mergeable
- [ ] Documentation complete
- [ ] No security vulnerabilities
- [ ] Bundle size under 5MB

**SPAWN THESE AGENTS NOW. BURN THE CREDITS.**
