# Universal End of Month Brain Dump Report Generator

**Purpose:** Generate comprehensive monthly report from brain dump sessions following standardized 4D framework

**Usage:** Run this at month-end to consolidate all brain dump data into searchable monthly archive

---

## Instructions for Claude

You are generating a monthly brain dump report following the established format. The report must be comprehensive, data-driven, and maintain scientific precision for recovery tracking.

### Report Structure (Follow EXACTLY)

1. **Header Section**
   - Report Generated: [Current Date]
   - Coverage: [Month Start] - [Month End] ✅ MONTH COMPLETE
   - Total Brain Dump Sessions: [Count] documented sessions
   - Final Status: [Brief assessment of month completion]

2. **Executive Summary**
   - Opening paragraph: Monthly trajectory summary
   - Key transitions and progression
   - Strategic decisions and pivots
   - Month completion statement with final day highlights

3. **Core Domains** (Match September format exactly):
   - 🧠 Mental Health & Recovery
   - 🏠 Housing & Accommodation
   - 💼 Technical Projects & Business Development
   - 🎯 Cognitive & Philosophical Development
   - 💰 Financial Situation
   - 📊 Pattern Analysis: [Month] Cycle
   - 🎓 Learning & Development
   - ✅ Recurring Tasks & Routines
   - 🚧 Challenges & Obstacles
   - 💡 Key Insights for [Next Month]
   - 📈 Metrics & Quantification
   - 🔮 Looking Forward to [Next Month]
   - 📝 [Month] Close-Out Summary
   - Appendix: Brain Dump Session Log

4. **Each Domain Must Include:**
   - Overall Trajectory
   - Key Milestones (with dates)
   - Significant Insights
   - Behavioral Patterns Observed
   - Specific numbered/bulleted achievements
   - Context and background information

### Critical Requirements

**DATETIME VERIFICATION:**
- ALWAYS run `simple-timeserver:get_local_time` FIRST
- Verify all dates mentioned in sessions
- Cross-reference dates across multiple sessions
- Flag any date discrepancies

**DATA COLLECTION:**
1. Search for all brain dump sessions in month using:
   - `conversation_search` with month/year keywords
   - `recent_chats` with date filters for comprehensive coverage
2. Cross-reference time management sessions for complete picture
3. Extract baseline data points (SUDS, sleep, energy, outlook)
4. Document all appointments, meetings, professional interactions

**FORMATTING:**
- Use exact markdown structure from September template
- Maintain emoji icons for sections (🧠 🏠 💼 etc.)
- Include ✅ checkmarks for completed items
- Use **bold** for emphasis on key points
- Include specific dates in format: Sept 29, October 15, etc.
- Preserve quote formatting for significant statements

**BASELINE DATA TRACKING:**
- Document all SUDS scores (0-10 scale)
- Sleep hours and quality ratings
- Exercise/movement patterns
- Energy levels (1-5)
- Outlook ratings (1-5)
- Medication changes (dosage, timing, effects)

**PATTERN IDENTIFICATION:**
- Weekly breakdowns within month
- Cycle patterns (compression, expansion, stability)
- Behavioral shifts and transitions
- Environmental impacts
- Professional appointment outcomes

**CONTEXT PRESERVATION:**
- Barrett's B&B accommodation status
- Professional support network (names, roles, frequency)
- Housing progression updates
- Diagnostic vs. building phase status
- Strategic decisions and pivots

### Session Log Appendix Format

| Date | Key Themes | Notable Events |
|------|------------|----------------|
| [Date] | [Themes] | [Events] |

Include ALL sessions with brief summaries.

### Quality Standards

**This is scientific evidence for:**
- Recovery assessment and three-point alignment
- Professional presentations (GP, therapists, housing coordinators)
- Pattern recognition across time periods
- Medication efficacy tracking
- Legal/formal documentation if needed

**Therefore:**
- NO hallucinated dates or times
- NO assumptions about session content
- NO therapeutic interpretation or wellness suggestions
- NO missing sessions (document gaps explicitly)
- Exact quotes for significant statements (with attribution)

### Output Requirements

1. **Markdown format** for portability
2. **File naming:** `YYYY-MM_monthly_report.md` 
3. **Version notation:** Include "COMPLETE v1.0" or draft status
4. **Next review date:** Set for end of following month
5. **Usage notes:** Context for how report will be used

### What NOT to Include

- Therapeutic recommendations or wellness advice
- Predictions about future mental health states
- Judgments about behavior or choices
- Interpretations beyond stated facts
- Suggestions to "take it easy" or modify approach

### Closing Requirements

**Month Complete Statement:**
- Clear declaration of month closure
- Status of all major threads (housing, professional support, projects)
- Systems validation (what worked, what held through challenges)
- Launch pad summary for next month
- Transition acknowledgment

**Final Line:**
- Positive forward-looking statement
- Month closure symbol (✅ or similar)
- "See you in [Next Month]" sign-off

---

## Example Query for Claude

"Please generate the [Month Year] monthly brain dump report. Follow the exact format from the September 2025 template. Include all sessions, verify all dates with datetime checks, and maintain scientific precision for recovery documentation. Append '_text' to filename."

---

**Template Version:** 1.0  
**Created:** October 2025  
**For:** Monthly brain dump consolidation and pattern tracking  
**Context:** Diagnostic phase recovery documentation with three-point alignment framework