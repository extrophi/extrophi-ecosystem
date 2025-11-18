# Report Template System for BrainDump
**Voice-to-Professional-Document Workflow**

**Research Date**: November 16, 2025
**Status**: Design & Architecture
**Purpose**: Transform raw voice notes into polished professional documents

---

## Executive Summary

This document outlines a comprehensive template system for converting voice journaling (brain dumps) into professional reports. The system enables users to:

- **Convert raw thoughts** → structured documents (5-10 minutes)
- **Auto-detect document type** → select appropriate template
- **Fill missing sections** → AI-assisted writing
- **Export to multiple formats** → PDF, DOCX, Markdown
- **Maintain brand consistency** → template library with company guidelines

**Core Innovation**: Voice → AI Categorization → Template Selection → Section Completion → Export

---

## Table of Contents

1. [Template Library Architecture](#template-library-architecture)
2. [Professional Report Templates](#professional-report-templates)
3. [AI Prompt Patterns](#ai-prompt-patterns)
4. [Variable System Design](#variable-system-design)
5. [Export Pipeline](#export-pipeline)
6. [Implementation Roadmap](#implementation-roadmap)

---

## Template Library Architecture

### 1. Directory Structure

```
src-tauri/
├── src/
│   ├── templates/
│   │   ├── mod.rs                    # Template engine orchestration
│   │   ├── manager.rs                # Template loading & selection
│   │   ├── engine.rs                 # Variable substitution (Tera/Handlebars)
│   │   └── export.rs                 # PDF/DOCX generation
│   └── ai/
│       ├── classifier.rs             # Document type detection
│       └── writer.rs                 # Section completion prompts

assets/
└── templates/
    ├── metadata.json                 # Template registry
    ├── executive-summary/
    │   ├── template.md               # Markdown template
    │   ├── schema.json               # Required variables
    │   ├── prompts.json              # AI section prompts
    │   └── brand-settings.yaml       # Styling rules
    ├── research-report/
    ├── meeting-notes/
    ├── project-status/
    ├── weekly-review/
    ├── incident-report/
    ├── business-proposal/
    ├── technical-documentation/
    ├── sop-procedure/
    ├── case-study/
    ├── white-paper/
    └── email-summary/

frontend/
└── src/
    └── components/
        ├── TemplateSelector.svelte   # Browse & select templates
        ├── DocumentEditor.svelte     # Edit filled template
        ├── ExportDialog.svelte       # Download options
        └── TemplatePreview.svelte    # Live preview
```

### 2. Template Metadata (JSON Schema)

```json
{
  "templates": [
    {
      "id": "executive-summary",
      "name": "Executive Summary",
      "category": "business",
      "description": "One-page overview for decision makers",
      "targetAudience": ["executives", "stakeholders"],
      "estimatedReadTime": 3,
      "sections": [
        {
          "id": "overview",
          "title": "Overview",
          "required": true,
          "suggestedLength": "2-3 sentences",
          "aiGenerated": false
        },
        {
          "id": "keyFindings",
          "title": "Key Findings",
          "required": true,
          "suggestedLength": "3-5 bullet points",
          "aiGenerated": true,
          "aiPromptKey": "findings_from_notes"
        },
        {
          "id": "recommendations",
          "title": "Recommendations",
          "required": true,
          "suggestedLength": "2-4 action items",
          "aiGenerated": true,
          "aiPromptKey": "recommendations"
        },
        {
          "id": "nextSteps",
          "title": "Next Steps",
          "required": false,
          "suggestedLength": "2-3 items",
          "aiGenerated": true,
          "aiPromptKey": "next_steps"
        }
      ],
      "variables": {
        "documentTitle": "string",
        "author": "string",
        "date": "date",
        "organization": "string",
        "projectName": "optional string",
        "confidential": "boolean"
      },
      "estimatedCompletionTime": 15,
      "exportFormats": ["pdf", "docx", "markdown", "html"],
      "tags": ["summary", "business", "quick-read"],
      "version": "1.0"
    },
    {
      "id": "research-report",
      "name": "Research Report",
      "category": "academic",
      "description": "Comprehensive research findings with methodology",
      "sections": [
        {
          "id": "abstract",
          "title": "Abstract",
          "required": true,
          "suggestedLength": "150-250 words",
          "aiGenerated": true
        },
        {
          "id": "introduction",
          "title": "Introduction",
          "required": true,
          "suggestedLength": "500-800 words",
          "aiGenerated": false
        },
        {
          "id": "literature",
          "title": "Literature Review",
          "required": true,
          "suggestedLength": "800-1200 words",
          "aiGenerated": true
        },
        {
          "id": "methodology",
          "title": "Methodology",
          "required": true,
          "suggestedLength": "400-600 words",
          "aiGenerated": false
        },
        {
          "id": "findings",
          "title": "Findings & Results",
          "required": true,
          "suggestedLength": "1000+ words",
          "aiGenerated": false
        },
        {
          "id": "discussion",
          "title": "Discussion",
          "required": true,
          "suggestedLength": "600-900 words",
          "aiGenerated": true
        },
        {
          "id": "conclusion",
          "title": "Conclusion",
          "required": true,
          "suggestedLength": "300-500 words",
          "aiGenerated": true
        },
        {
          "id": "references",
          "title": "References",
          "required": false,
          "suggestedLength": "varies",
          "aiGenerated": false
        }
      ],
      "variables": {
        "researchTitle": "string",
        "author": "string",
        "institution": "string",
        "date": "date",
        "keywords": "string[]",
        "doi": "optional string"
      },
      "estimatedCompletionTime": 120,
      "exportFormats": ["pdf", "docx"],
      "tags": ["research", "academic", "detailed"]
    }
  ]
}
```

### 3. Variable System Design

```yaml
# Template Variables (assets/templates/variables-schema.yaml)
variableTypes:
  - name: "basicInfo"
    variables:
      - { key: "title", type: "string", required: true,
          description: "Document title" }
      - { key: "author", type: "string", required: true,
          description: "Author name" }
      - { key: "date", type: "date", required: true, format: "YYYY-MM-DD" }
      - { key: "organization", type: "string", required: false }
      - { key: "confidential", type: "boolean", default: false }
      - { key: "revision", type: "number", default: 1 }

  - name: "content"
    variables:
      - { key: "summary", type: "string", maxLength: 500 }
      - { key: "keyPoints", type: "string[]", maxItems: 5 }
      - { key: "recommendations", type: "string[]" }
      - { key: "risks", type: "string[]" }
      - { key: "nextSteps", type: "string[]" }

  - name: "formatting"
    variables:
      - { key: "brandColor", type: "color", default: "#1e40af" }
      - { key: "logoPath", type: "filepath", optional: true }
      - { key: "fontFamily", type: "enum",
          options: ["Arial", "Helvetica", "Georgia", "Times New Roman"] }
      - { key: "reportFormat", type: "enum",
          options: ["pdf", "docx", "html", "markdown"] }

  - name: "metadata"
    variables:
      - { key: "projectId", type: "string", optional: true }
      - { key: "sessionId", type: "string", reference: "chat_sessions" }
      - { key: "template", type: "string", enum: "[template-id]" }
      - { key: "generatedAt", type: "timestamp", autoGenerated: true }
```

---

## Professional Report Templates

### Template 1: Executive Summary

```markdown
# {{ documentTitle }}

**Author**: {{ author }} | **Date**: {{ date | date("MMM DD, YYYY") }}
**Organization**: {{ organization }}{% if confidential %} | **CONFIDENTIAL**{% endif %}

---

## Overview

{{ overview }}

---

## Key Findings

{% for finding in keyFindings %}
- {{ finding }}
{% endfor %}

---

## Recommendations

{% for rec in recommendations %}
{{ loop.index }}. {{ rec }}
{% endfor %}

{% if nextSteps %}
---

## Next Steps

{% for step in nextSteps %}
- [ ] {{ step }}
{% endfor %}

**Owner**: _______
**Target Completion**: {{ targetDate | date("MMM DD, YYYY") }}
{% endif %}

---

**Report Generated**: {{ generatedAt | date("MMMM DD, YYYY 'at' h:mm A") }}
**Template Version**: 1.0
```

### Template 2: Meeting Notes

```markdown
# Meeting Notes: {{ meetingTitle }}

| Field | Details |
|-------|---------|
| **Date** | {{ meetingDate | date("YYYY-MM-DD") }} |
| **Time** | {{ meetingTime }} (Duration: {{ duration }} min) |
| **Location** | {{ location }} |
| **Attendees** | {% for person in attendees %}{{ person }}{% if not loop.last %}, {% endif %}{% endfor %} |
| **Facilitator** | {{ facilitator }} |

---

## Agenda

{% for item in agenda %}
1. {{ item }}
{% endfor %}

---

## Discussion Summary

{{ discussionSummary }}

---

## Decisions Made

{% for decision in decisions %}
- **Decision**: {{ decision.text }}
  - **Owner**: {{ decision.owner }}
  - **Deadline**: {{ decision.deadline | date("YYYY-MM-DD") }}
{% endfor %}

---

## Action Items

| # | Task | Owner | Due Date | Priority |
|---|------|-------|----------|----------|
{% for item in actionItems %}
| {{ loop.index }} | {{ item.task }} | {{ item.owner }} | {{ item.dueDate | date("YYYY-MM-DD") }} | {{ item.priority }} |
{% endfor %}

---

## Open Questions

{% for question in openQuestions %}
- {{ question.text }}
  - *Assigned to*: {{ question.assignee }}
  - *Follow-up*: {{ question.followUpDate | date("YYYY-MM-DD") }}
{% endfor %}

---

## Next Meeting

**Date**: {{ nextMeetingDate | date("YYYY-MM-DD hh:mm A") }}
**Topic**: {{ nextMeetingTopic }}

---

**Minutes Recorded By**: {{ recordedBy }}
**Timestamp**: {{ generatedAt | date("MMMM DD, YYYY 'at' h:mm A") }}
```

### Template 3: Project Status Report

```markdown
# Project Status Report: {{ projectName }}

**Reporting Period**: {{ reportStartDate | date("MMM DD") }} - {{ reportEndDate | date("MMM DD, YYYY") }}
**Project Manager**: {{ projectManager }}
**Status**: 🟢 {% if statusColor == "green" %}On Track{% elif statusColor == "yellow" %}At Risk{% else %}Off Track{% endif %}

---

## Executive Summary

{{ executiveSummary }}

---

## Project Health Dashboard

| Metric | Status | Notes |
|--------|--------|-------|
| **Schedule** | {{ scheduleStatus }} | {{ scheduleNotes }} |
| **Budget** | {{ budgetStatus }} | ${{ budgetSpent }} / ${{ budgetTotal }} |
| **Scope** | {{ scopeStatus }} | {{ scopeNotes }} |
| **Resources** | {{ resourceStatus }} | {{ resourceNotes }} |

---

## Accomplishments This Period

{% for achievement in accomplishments %}
✅ {{ achievement }}
{% endfor %}

---

## Planned Activities (Next Period)

{% for activity in plannedActivities %}
- {{ activity.name }} (Est. completion: {{ activity.dueDate | date("MMM DD") }})
{% endfor %}

---

## Risks & Issues

### Active Risks

{% for risk in risks %}
**{{ risk.title }}** (Severity: {{ risk.severity }})
- *Impact*: {{ risk.impact }}
- *Mitigation*: {{ risk.mitigation }}
- *Owner*: {{ risk.owner }}
{% endfor %}

### Active Issues

{% for issue in issues %}
| Issue | Priority | Owner | Status |
|-------|----------|-------|--------|
{% endfor %}

---

## Key Metrics

- **Tasks Completed**: {{ tasksCompleted }} / {{ totalTasks }}
- **Progress**: {{ (tasksCompleted / totalTasks * 100) | round }}%
- **Team Capacity**: {{ teamCapacity }}%
- **Budget Burn Rate**: {{ budgetBurnRate }}%

---

## Dependencies & Blockers

{% for blocker in blockers %}
🚫 **{{ blocker.title }}**
- Resolution plan: {{ blocker.resolution }}
{% endfor %}

---

## Next Steps

1. {{ nextStep1 }}
2. {{ nextStep2 }}
3. {{ nextStep3 }}

---

**Report Date**: {{ reportDate | date("MMMM DD, YYYY") }}
**Submitted By**: {{ submittedBy }}
**Contact**: {{ contactEmail }}
```

### Template 4: Weekly Review

```markdown
# Weekly Review: {{ weekOf | date("MMM DD - MMM DD, YYYY") }}

**Reviewed By**: {{ reviewer }}
**Week #**: {{ weekNumber }} of {{ year }}

---

## What Went Well

{% for success in successes %}
🎯 {{ success }}
{% endfor %}

---

## Challenges & Learnings

{% for challenge in challenges %}
**{{ challenge.title }}**

Challenge: {{ challenge.description }}

Learning: {{ challenge.learning }}

Action: {{ challenge.action }}
{% endfor %}

---

## Weekly Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
{% for metric in metrics %}
| {{ metric.name }} | {{ metric.target }} | {{ metric.actual }} | {{ metric.status }} |
{% endfor %}

---

## Goals for Next Week

{% for goal in nextWeekGoals %}
{{ loop.index }}. {{ goal.description }}
   - Success criteria: {{ goal.criteria }}
   - Priority: {{ goal.priority }}
{% endfor %}

---

## Team Updates

{{ teamUpdates }}

---

## Personal Reflection

{{ personalReflection }}

---

**Week Ending**: {{ weekEndDate | date("YYYY-MM-DD") }}
**Next Review**: {{ nextReviewDate | date("YYYY-MM-DD") }}
```

### Template 5: Incident Report

```markdown
# Incident Report

**Incident ID**: {{ incidentId }}
**Date & Time**: {{ incidentDateTime | date("YYYY-MM-DD HH:mm") }} UTC
**Severity**: 🔴 {{ severity }} (P{{ priority }})
**Status**: {{ status }}

---

## Incident Summary

{{ summary }}

---

## Impact Analysis

| Aspect | Impact |
|--------|--------|
| **Users Affected** | {{ usersAffected }} |
| **Systems Down** | {{ systemsImpacted }} |
| **Duration** | {{ durationMinutes }} minutes |
| **Business Impact** | {{ businessImpact }} |

---

## Timeline

{% for event in timeline %}
**{{ event.time | date("HH:mm") }}** - {{ event.description }}
  - *Responder*: {{ event.responder }}
{% endfor %}

---

## Root Cause Analysis

### Initial Assessment
{{ initialAssessment }}

### Root Cause
{{ rootCause }}

### Contributing Factors
{% for factor in contributingFactors %}
- {{ factor }}
{% endfor %}

---

## Resolution

**Resolution Time**: {{ resolutionTime }} minutes
**Permanent Fix**: {{ permanentFix }}

### Immediate Actions Taken
{% for action in immediateActions %}
✓ {{ action }}
{% endfor %}

---

## Preventive Measures

{% for measure in preventiveMeasures %}
**{{ measure.title }}**
- Owner: {{ measure.owner }}
- Target Completion: {{ measure.deadline | date("YYYY-MM-DD") }}
{% endfor %}

---

## Post-Incident Review

### What We Did Right
{% for positive in whatWentWell %}
- {{ positive }}
{% endfor %}

### What We Can Improve
{% for improvement in improvements %}
- {{ improvement }}
{% endfor %}

---

**Report Date**: {{ reportDate | date("YYYY-MM-DD") }}
**Incident Commander**: {{ commanderName }}
**Reviewed By**: {{ reviewedBy }}
```

### Template 6: Business Proposal

```markdown
# Business Proposal: {{ proposalTitle }}

**Prepared For**: {{ clientName }}
**Prepared By**: {{ agencyName }}
**Date**: {{ proposalDate | date("MMMM DD, YYYY") }}
**Proposal Valid Until**: {{ expirationDate | date("MMMM DD, YYYY") }}

---

## Executive Summary

{{ executiveSummary }}

---

## Problem Statement

{{ problemStatement }}

---

## Proposed Solution

### Overview
{{ solutionOverview }}

### Key Features
{% for feature in features %}
- **{{ feature.name }}**: {{ feature.description }}
{% endfor %}

### Benefits
{% for benefit in benefits %}
✓ {{ benefit }}
{% endfor %}

---

## Deliverables

{% for deliverable in deliverables %}
**{{ deliverable.name }}**
- Description: {{ deliverable.description }}
- Timeline: {{ deliverable.timeline }}
- Acceptance Criteria: {{ deliverable.criteria }}
{% endfor %}

---

## Project Timeline

{% for milestone in milestones %}
- **{{ milestone.name }}** - {{ milestone.date | date("MMM DD, YYYY") }}
{% endfor %}

---

## Investment

### Pricing Structure

{% for component in pricingComponents %}
| Item | Quantity | Unit Price | Total |
|------|----------|-----------|-------|
| {{ component.name }} | {{ component.quantity }} | ${{ component.unitPrice }} | ${{ component.total }} |
{% endfor %}

**Total Investment**: ${{ totalInvestment }}

### Payment Terms
{{ paymentTerms }}

---

## Company Credentials

**About {{ agencyName }}**

{{ companyBackground }}

**Our Team**
{% for member in teamMembers %}
- **{{ member.name }}** - {{ member.role }} ({{ member.experience }} years)
{% endfor %}

---

## Next Steps

1. {{ nextStep1 }}
2. {{ nextStep2 }}
3. {{ nextStep3 }}

---

**Questions?**

{{ contactName }}
{{ contactTitle }}
{{ contactEmail }}
{{ contactPhone }}

---

*This proposal is confidential and intended for authorized recipients only.*
```

### Template 7: Technical Documentation

```markdown
# Technical Documentation: {{ documentTitle }}

**Version**: {{ version }}
**Last Updated**: {{ lastUpdated | date("MMMM DD, YYYY") }}
**Author**: {{ author }}
**Status**: {{ status }}

---

## Table of Contents

{% for section in tableOfContents %}
- [{{ section.title }}](#{{ section.id }})
{% endfor %}

---

## Overview

{{ overview }}

---

## Architecture

### System Diagram

{{ architectureDiagram }}

### Components

{% for component in components %}
**{{ component.name }}**
- Purpose: {{ component.purpose }}
- Technology: {{ component.technology }}
- Dependencies: {{ component.dependencies }}
{% endfor %}

---

## API Reference

{% for endpoint in endpoints %}
### {{ endpoint.method }} {{ endpoint.path }}

{{ endpoint.description }}

**Parameters**:
```json
{{ endpoint.parameterSchema }}
```

**Response**:
```json
{{ endpoint.responseSchema }}
```

**Example**:
```bash
curl -X {{ endpoint.method }} {{ endpoint.exampleUrl }}
```
{% endfor %}

---

## Database Schema

{% for table in databaseTables %}
### {{ table.name }}

| Column | Type | Constraints |
|--------|------|-----------|
{% for column in table.columns %}
| {{ column.name }} | {{ column.type }} | {{ column.constraints }} |
{% endfor %}
{% endfor %}

---

## Configuration

{{ configurationGuide }}

---

## Deployment

### Prerequisites
{% for prerequisite in prerequisites %}
- {{ prerequisite }}
{% endfor %}

### Installation Steps
{% for step in installationSteps %}
{{ loop.index }}. {{ step }}
{% endfor %}

### Troubleshooting
{% for issue in commonIssues %}
**{{ issue.problem }}**

Solution: {{ issue.solution }}
{% endfor %}

---

## Performance & Security

### Performance Considerations
{{ performanceNotes }}

### Security Guidelines
{{ securityGuidelines }}

---

**Document Version**: {{ version }}
**Last Modified**: {{ lastModified | date("YYYY-MM-DD HH:mm") }}
```

### Template 8: Standard Operating Procedure (SOP)

```markdown
# Standard Operating Procedure: {{ procedureName }}

**Procedure ID**: {{ procedureId }}
**Version**: {{ version }}
**Effective Date**: {{ effectiveDate | date("MMMM DD, YYYY") }}
**Last Reviewed**: {{ lastReviewDate | date("MMMM DD, YYYY") }}

---

## Purpose & Scope

**Purpose**: {{ purpose }}

**Scope**: This procedure applies to {{ scope }}

**Owner**: {{ owner }}

---

## Definitions & Abbreviations

{% for term in definitions %}
- **{{ term.term }}**: {{ term.definition }}
{% endfor %}

---

## Prerequisites

{% for prerequisite in prerequisites %}
- {{ prerequisite }}
{% endfor %}

---

## Step-by-Step Procedure

{% for step in procedures %}
### Step {{ loop.index }}: {{ step.title }}

**Objective**: {{ step.objective }}

**Actions**:
{% for action in step.actions %}
{{ loop.index }}. {{ action }}
{% endfor %}

**Expected Outcome**: {{ step.expectedOutcome }}

**Time Estimate**: {{ step.timeEstimate }} minutes

**Responsible Party**: {{ step.responsibleParty }}

{% if step.decision %}
**Decision Point**:
- If {{ step.decision.condition }}: {{ step.decision.yesPath }}
- Else: {{ step.decision.noPath }}
{% endif %}
{% endfor %}

---

## Quality Assurance Checklist

{% for item in qaChecklist %}
- [ ] {{ item }}
{% endfor %}

---

## Troubleshooting Guide

{% for issue in troubleshooting %}
**Issue**: {{ issue.problem }}

Cause: {{ issue.cause }}

Solution: {{ issue.solution }}

Escalation: {{ issue.escalation }}
{% endfor %}

---

## Documentation & Records

Documents to maintain:
{% for document in records %}
- {{ document.name }}: {{ document.retention }} months
{% endfor %}

---

## Compliance & Safety

{{ complianceNotes }}

---

## Approval & Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Procedure Owner | {{ owner }} | _______ | _______ |
| Manager | {{ manager }} | _______ | _______ |
| Compliance | {{ compliance }} | _______ | _______ |

---

**Next Review Date**: {{ nextReviewDate | date("MMMM DD, YYYY") }}
```

### Template 9: Case Study

```markdown
# Case Study: {{ caseTitle }}

**Industry**: {{ industry }}
**Company**: {{ companyName }}
**Time Period**: {{ startDate | date("MMMM YYYY") }} - {{ endDate | date("MMMM YYYY") }}
**Published**: {{ publishDate | date("MMMM DD, YYYY") }}

---

## Executive Overview

{{ executiveOverview }}

---

## The Challenge

{{ challenge }}

### Key Obstacles
{% for obstacle in obstacles %}
- {{ obstacle }}
{% endfor %}

### Impact Before
{{ impactBefore }}

---

## Our Solution

### Approach
{{ approach }}

### Implementation Timeline
{% for phase in implementationPhases %}
- **{{ phase.name }}** ({{ phase.duration }}): {{ phase.description }}
{% endfor %}

### Technologies Used
{% for tech in technologiesUsed %}
- {{ tech }}
{% endfor %}

---

## Results & Outcomes

### Key Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
{% for metric in metrics %}
| {{ metric.name }} | {{ metric.before }} | {{ metric.after }} | {{ metric.improvement }} |
{% endfor %}

### Quantifiable Benefits
{% for benefit in benefits %}
- {{ benefit.description }}: **{{ benefit.value }}**
{% endfor %}

---

## Client Testimonial

> "{{ clientTestimonial }}"

— **{{ testifierName }}**, {{ testifierTitle }} at {{ companyName }}

---

## Key Learnings

{% for learning in learnings %}
**{{ learning.title }}**: {{ learning.description }}
{% endfor %}

---

## Recommendations for Similar Projects

{% for recommendation in recommendations %}
{{ loop.index }}. {{ recommendation }}
{% endfor %}

---

## About Us

{{ aboutUs }}

---

**Case Study ID**: {{ caseStudyId }}
**Contact for More Info**: {{ contactEmail }}
```

### Template 10: White Paper

```markdown
# White Paper: {{ title }}

**Version**: {{ version }}
**Publication Date**: {{ publicationDate | date("MMMM YYYY") }}
**Author(s)**: {{ authors }}
**Length**: {{ estimatedReadTime }} minute read

---

## Table of Contents

{% for section in tableOfContents %}
{{ loop.index }}. [{{ section }}](#)
{% endfor %}

---

## Executive Summary

{{ executiveSummary }}

---

## Introduction

### Background
{{ background }}

### Problem Statement
{{ problemStatement }}

### Scope & Objectives
{{ scopeAndObjectives }}

---

## Current State Analysis

### Market Overview
{{ marketOverview }}

### Existing Approaches
{% for approach in existingApproaches %}
**{{ approach.name }}**: {{ approach.description }}
- Advantages: {{ approach.advantages }}
- Limitations: {{ approach.limitations }}
{% endfor %}

### Gap Analysis
{{ gapAnalysis }}

---

## Proposed Solution

### Core Concept
{{ coreConcept }}

### Key Principles
{% for principle in keyPrinciples %}
{{ loop.index }}. **{{ principle.name }}**: {{ principle.description }}
{% endfor %}

### Implementation Strategy
{{ implementationStrategy }}

---

## Technical Considerations

{{ technicalConsiderations }}

---

## Benefits & ROI

### Quantifiable Benefits
{% for benefit in benefits %}
- {{ benefit.description }}: {{ benefit.metric }}
{% endfor %}

### Return on Investment
{{ roiAnalysis }}

---

## Risk Mitigation

{% for risk in risks %}
**{{ risk.name }}**: {{ risk.mitigation }}
{% endfor %}

---

## Case Studies

{% for caseStudy in caseStudies %}
**{{ caseStudy.company }}**: {{ caseStudy.result }}
{% endfor %}

---

## Future Outlook

{{ futureOutlook }}

---

## Recommendations

{% for recommendation in recommendations %}
{{ loop.index }}. {{ recommendation }}
{% endfor %}

---

## Conclusion

{{ conclusion }}

---

## References

{% for reference in references %}
- {{ reference.citation }}
{% endfor %}

---

## About the Authors

{% for author in authors %}
**{{ author.name }}**

{{ author.bio }}
{% endfor %}

---

## Contact & Further Information

For more information, contact:

{{ contactName }}
{{ contactTitle }}
{{ contactEmail }}
{{ contactWebsite }}

---

*This white paper represents the views of the authors and may not reflect the official policy or position of the organization.*

**Document Version**: {{ version }}
**Last Updated**: {{ lastUpdated | date("MMMM DD, YYYY") }}
```

---

## AI Prompt Patterns

### 1. Document Type Detection

```json
{
  "promptTemplate": {
    "name": "detect_document_type",
    "systemPrompt": "You are a document classification expert. Analyze the user's voice notes and determine the most appropriate professional document type. Consider the content, tone, structure, and intended audience.",

    "userPromptTemplate": "Here are my raw voice notes:\n\n{{ rawNotes }}\n\nBased on this content, what type of professional document would be most appropriate? Choose from: executive-summary, research-report, meeting-notes, project-status, weekly-review, incident-report, business-proposal, technical-documentation, sop, case-study, white-paper, email-summary.\n\nRespond with ONLY the template ID and a confidence score (0-100).",

    "responseSchema": {
      "templateId": "string",
      "confidence": "number",
      "reasoning": "string",
      "suggestedSections": "string[]"
    },

    "temperature": 0.3,
    "maxTokens": 200
  }
}
```

### 2. Section Generation (Executive Summary)

```json
{
  "promptTemplate": {
    "name": "generate_findings",
    "section": "keyFindings",
    "systemPrompt": "You are an expert business analyst. Extract and summarize the most important findings from raw notes into 3-5 clear, actionable bullet points suitable for executives.",

    "userPromptTemplate": "From these notes, extract the KEY FINDINGS that would be most important to executives:\n\n{{ rawNotes }}\n\nFormat as bullet points (3-5 items), starting with action verbs. Be concise and specific.",

    "constraints": {
      "maxItems": 5,
      "minItems": 3,
      "maxCharsPerItem": 200,
      "tone": "professional",
      "audience": "executives"
    },

    "temperature": 0.7,
    "maxTokens": 400
  }
}
```

### 3. Recommendations Generation

```json
{
  "promptTemplate": {
    "name": "generate_recommendations",
    "section": "recommendations",
    "systemPrompt": "You are a strategic advisor. Convert raw notes into 2-4 specific, measurable, actionable recommendations that executives can implement.",

    "userPromptTemplate": "Based on these notes, what are the top RECOMMENDATIONS for action?\n\n{{ rawNotes }}\n\nProvide 2-4 recommendations with:\n1. Specific action to take\n2. Expected outcome\n3. Owner/responsible party\n\nBe direct and implementable.",

    "responseSchema": {
      "recommendations": [{
        "action": "string",
        "expectedOutcome": "string",
        "owner": "string",
        "estimatedTimeframe": "string"
      }]
    },

    "temperature": 0.6,
    "maxTokens": 500
  }
}
```

### 4. Missing Section Detection

```json
{
  "promptTemplate": {
    "name": "detect_missing_sections",
    "systemPrompt": "You are a document completeness analyzer. Identify which sections of the template are missing or underdeveloped based on the input content.",

    "userPromptTemplate": "Review these notes against the {{ templateId }} template:\n\n{{ rawNotes }}\n\nWhich sections are:\n1. Complete and well-developed\n2. Partially addressed\n3. Missing entirely\n4. Need expansion\n\nProvide specific suggestions for each missing/incomplete section.",

    "responseSchema": {
      "complete": "string[]",
      "partial": [{
        "section": "string",
        "content": "string",
        "suggestedExpansion": "string"
      }],
      "missing": [{
        "section": "string",
        "suggestedContent": "string",
        "importanceLevel": "high|medium|low"
      }]
    },

    "temperature": 0.4,
    "maxTokens": 800
  }
}
```

### 5. Tone & Professional Level Adjustment

```json
{
  "promptTemplate": {
    "name": "adjust_tone",
    "systemPrompt": "You are an expert editor. Adjust the tone and formality level of text to match professional standards while maintaining accuracy.",

    "userPromptTemplate": "Adjust this text to {{ targetTone }} tone for a {{ targetAudience }} audience:\n\n{{ textToAdjust }}\n\nMaintain factual accuracy while improving clarity and professionalism.",

    "parameters": {
      "targetTone": "professional|formal|approachable|executive|technical",
      "targetAudience": "executives|technical-team|board|general-staff|external",
      "preserveLength": "true|false"
    },

    "temperature": 0.7,
    "maxTokens": 1000
  }
}
```

### 6. Data Extraction for Variables

```json
{
  "promptTemplate": {
    "name": "extract_variables",
    "systemPrompt": "Extract structured data from notes to populate document variables. Return ONLY valid JSON.",

    "userPromptTemplate": "Extract these variables from the notes and return as JSON:\n\n{{ rawNotes }}\n\nRequired variables:\n{% for variable in requiredVariables %}\n- {{ variable.key }} (type: {{ variable.type }})\n{% endfor %}\n\nReturn ONLY valid JSON.",

    "responseSchema": {
      "extractedVariables": {}
    },

    "temperature": 0.1,
    "maxTokens": 500
  }
}
```

---

## Variable System Design

### 1. Tera Template Engine (Recommended for Rust)

```rust
// src-tauri/src/templates/engine.rs

use tera::{Tera, Context};
use serde_json::json;

pub struct TemplateEngine {
    tera: Tera,
}

impl TemplateEngine {
    pub fn new(template_dir: &str) -> Result<Self, Box<dyn std::error::Error>> {
        let mut tera = Tera::new(&format!("{}/**/*.md", template_dir))?;

        // Register custom filters
        tera.register_filter("date_format", date_filter);
        tera.register_filter("currency", currency_filter);
        tera.register_filter("percentage", percentage_filter);

        Ok(Self { tera })
    }

    pub fn render(
        &self,
        template_name: &str,
        variables: &serde_json::Value,
    ) -> Result<String, tera::Error> {
        let context = Context::from_value(variables)?;
        self.tera.render(template_name, &context)
    }
}

// Custom filter for date formatting
fn date_filter(
    value: &tera::Value,
    args: &HashMap<String, tera::Value>,
) -> tera::Result<tera::Value> {
    let date_str = tera::try_get_value!("value", "string", value);
    let format = args
        .get("format")
        .and_then(|v| v.as_str())
        .unwrap_or("%Y-%m-%d");

    // Parse and reformat date
    Ok(tera::Value::String(format_date(date_str, format)?))
}

fn currency_filter(
    value: &tera::Value,
    _args: &HashMap<String, tera::Value>,
) -> tera::Result<tera::Value> {
    let num = tera::try_get_value!("value", "number", value);
    Ok(tera::Value::String(format!("${:,.2}", num)))
}

fn percentage_filter(
    value: &tera::Value,
    _args: &HashMap<String, tera::Value>,
) -> tera::Result<tera::Value> {
    let num = tera::try_get_value!("value", "number", value);
    Ok(tera::Value::String(format!("{:.1}%", num)))
}
```

### 2. Variable Validation

```rust
// src-tauri/src/templates/validator.rs

use serde_json::{json, Value};
use std::collections::HashMap;

pub struct VariableValidator {
    schema: HashMap<String, VariableRule>,
}

#[derive(Debug, Clone)]
pub struct VariableRule {
    pub var_type: VariableType,
    pub required: bool,
    pub max_length: Option<usize>,
    pub min_length: Option<usize>,
    pub enum_values: Option<Vec<String>>,
    pub pattern: Option<String>, // Regex
}

#[derive(Debug, Clone)]
pub enum VariableType {
    String,
    Number,
    Integer,
    Boolean,
    Date,
    Array(Box<VariableType>),
    Object,
}

impl VariableValidator {
    pub fn validate(&self, variables: &Value) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        for (key, rule) in &self.schema {
            match variables.get(key) {
                Some(value) => {
                    if let Err(e) = self.validate_value(key, value, rule) {
                        errors.extend(e);
                    }
                }
                None if rule.required => {
                    errors.push(format!("Required field missing: {}", key));
                }
                _ => {}
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }

    fn validate_value(&self, key: &str, value: &Value, rule: &VariableRule) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        // Type validation
        match &rule.var_type {
            VariableType::String => {
                if let Some(s) = value.as_str() {
                    if let Some(max) = rule.max_length {
                        if s.len() > max {
                            errors.push(format!("{}: exceeds max length {}", key, max));
                        }
                    }
                    if let Some(pattern) = &rule.pattern {
                        if !regex::Regex::new(pattern)
                            .map(|re| re.is_match(s))
                            .unwrap_or(false)
                        {
                            errors.push(format!("{}: does not match pattern", key));
                        }
                    }
                } else {
                    errors.push(format!("{}: expected string", key));
                }
            }
            VariableType::Number => {
                if !value.is_number() {
                    errors.push(format!("{}: expected number", key));
                }
            }
            VariableType::Boolean => {
                if !value.is_boolean() {
                    errors.push(format!("{}: expected boolean", key));
                }
            }
            VariableType::Array(_) => {
                if !value.is_array() {
                    errors.push(format!("{}: expected array", key));
                }
            }
            _ => {}
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}
```

---

## Export Pipeline

### 1. Export Configuration

```yaml
# assets/templates/export-settings.yaml
exportFormats:
  pdf:
    engine: "wkhtmltopdf" # or "headless-chrome" or "weasyprint"
    options:
      pageSize: "A4"
      margins:
        top: "1in"
        bottom: "1in"
        left: "0.75in"
        right: "0.75in"
      headerSpacing: 0.5
      footerSpacing: 0.5
      fontSize: 12
    timeout: 30000 # milliseconds
    quality: "high"

  docx:
    engine: "pandoc"
    referenceDocx: "assets/templates/reference.docx"
    options:
      preserveFormatting: true
      includeStyles: true
    timeout: 20000

  html:
    engine: "markdown-to-html"
    cssFramework: "bootstrap"
    highlightCode: true
    responsiveTable: true

  markdown:
    engine: "passthrough"
    preserveMetadata: true

defaultExportFormat: "pdf"
maxExportSize: 50 # MB
```

### 2. Export Service Implementation

```rust
// src-tauri/src/templates/export.rs

use std::path::PathBuf;
use tokio::process::Command;

#[derive(Debug, Clone)]
pub enum ExportFormat {
    PDF,
    DOCX,
    HTML,
    Markdown,
}

pub struct ExportService {
    config: ExportConfig,
}

impl ExportService {
    pub async fn export(
        &self,
        content: &str,
        format: ExportFormat,
        metadata: &ExportMetadata,
    ) -> Result<Vec<u8>, String> {
        match format {
            ExportFormat::PDF => self.export_to_pdf(content, metadata).await,
            ExportFormat::DOCX => self.export_to_docx(content, metadata).await,
            ExportFormat::HTML => self.export_to_html(content).await,
            ExportFormat::Markdown => self.export_to_markdown(content, metadata).await,
        }
    }

    async fn export_to_pdf(
        &self,
        content: &str,
        metadata: &ExportMetadata,
    ) -> Result<Vec<u8>, String> {
        // Convert markdown to HTML first
        let html = self.markdown_to_html(content)?;

        // Use wkhtmltopdf or headless Chrome
        let pdf_bytes = self.html_to_pdf(&html, metadata).await?;

        Ok(pdf_bytes)
    }

    async fn export_to_docx(
        &self,
        content: &str,
        metadata: &ExportMetadata,
    ) -> Result<Vec<u8>, String> {
        // Use Pandoc for markdown to DOCX
        let output = Command::new("pandoc")
            .arg("--from=markdown")
            .arg("--to=docx")
            .arg("--reference-doc=assets/templates/reference.docx")
            .arg(&format!("--metadata=title:{}", metadata.title))
            .arg(&format!("--metadata=author:{}", metadata.author))
            .arg("-")
            .stdin(std::process::Stdio::piped())
            .output()
            .await
            .map_err(|e| e.to_string())?;

        Ok(output.stdout)
    }

    async fn export_to_html(&self, content: &str) -> Result<Vec<u8>, String> {
        let html = self.markdown_to_html(content)?;
        Ok(html.into_bytes())
    }

    async fn export_to_markdown(
        &self,
        content: &str,
        metadata: &ExportMetadata,
    ) -> Result<Vec<u8>, String> {
        // Add YAML frontmatter
        let mut output = String::new();
        output.push_str("---\n");
        output.push_str(&format!("title: {}\n", metadata.title));
        output.push_str(&format!("author: {}\n", metadata.author));
        output.push_str(&format!("date: {}\n", metadata.date));
        output.push_str("---\n\n");
        output.push_str(content);

        Ok(output.into_bytes())
    }

    fn markdown_to_html(&self, content: &str) -> Result<String, String> {
        // Use pulldown-cmark or similar
        let parser = pulldown_cmark::Parser::new(content);
        let mut html = String::new();
        pulldown_cmark::html::push_html(&mut html, parser);
        Ok(html)
    }

    async fn html_to_pdf(
        &self,
        html: &str,
        metadata: &ExportMetadata,
    ) -> Result<Vec<u8>, String> {
        // Option 1: Use wkhtmltopdf (if available)
        // Option 2: Use headless Chrome via puppeteer-rs or similar
        // For now, use a simple approach with wkhtmltopdf

        let temp_html = format!("/tmp/export_{}.html", uuid::Uuid::new_v4());
        std::fs::write(&temp_html, html).map_err(|e| e.to_string())?;

        let output = Command::new("wkhtmltopdf")
            .arg("--quiet")
            .arg("--page-size")
            .arg("A4")
            .arg("--margin-top")
            .arg("1in")
            .arg("--margin-bottom")
            .arg("1in")
            .arg(&temp_html)
            .arg("-")
            .output()
            .await
            .map_err(|e| e.to_string())?;

        std::fs::remove_file(&temp_html).ok();

        Ok(output.stdout)
    }
}

#[derive(Debug, Clone)]
pub struct ExportMetadata {
    pub title: String,
    pub author: String,
    pub date: String,
    pub organization: Option<String>,
    pub confidential: bool,
}
```

### 3. Frontend Export Dialog

```svelte
<!-- src/components/ExportDialog.svelte -->
<script>
  import { invoke } from '@tauri-apps/api/core';
  import { save } from '@tauri-apps/plugin-dialog';

  let {
    documentContent = $bindable(),
    documentMetadata = $bindable(),
    isOpen = $bindable(false)
  } = $props();

  let selectedFormat = $state('pdf');
  let isExporting = $state(false);
  let exportProgress = $state(0);

  const exportFormats = [
    { value: 'pdf', label: 'PDF (Professional)', icon: '📄' },
    { value: 'docx', label: 'Word (.docx)', icon: '📝' },
    { value: 'html', label: 'Web Page (.html)', icon: '🌐' },
    { value: 'markdown', label: 'Markdown (.md)', icon: '✏️' },
  ];

  async function handleExport() {
    isExporting = true;
    exportProgress = 0;

    try {
      // Call Tauri command to generate document
      const exportedFile = await invoke('export_document', {
        content: documentContent,
        format: selectedFormat,
        metadata: documentMetadata,
      });

      // Show save dialog
      const filePath = await save({
        defaultPath: `${documentMetadata.title}.${getFileExtension(selectedFormat)}`,
        filters: [{
          name: selectedFormat.toUpperCase(),
          extensions: [getFileExtension(selectedFormat)],
        }],
      });

      if (filePath) {
        // Save the file
        await invoke('save_exported_file', {
          filePath,
          content: exportedFile,
        });

        exportProgress = 100;
        // Show success message
        alert(`Document exported successfully to ${filePath}`);
      }
    } catch (error) {
      alert(`Export failed: ${error}`);
    } finally {
      isExporting = false;
    }
  }

  function getFileExtension(format) {
    const extensions = {
      pdf: 'pdf',
      docx: 'docx',
      html: 'html',
      markdown: 'md',
    };
    return extensions[format] || format;
  }
</script>

<div class="export-dialog" class:open={isOpen}>
  <div class="dialog-content">
    <h2>Export Document</h2>

    <div class="format-selector">
      <p>Choose export format:</p>
      {#each exportFormats as format}
        <label class="format-option">
          <input
            type="radio"
            bind:group={selectedFormat}
            value={format.value}
            disabled={isExporting}
          />
          <span>{format.icon} {format.label}</span>
        </label>
      {/each}
    </div>

    {#if isExporting}
      <div class="progress-bar">
        <div class="progress" style="width: {exportProgress}%"></div>
      </div>
      <p>Exporting... {exportProgress}%</p>
    {/if}

    <div class="dialog-actions">
      <button
        on:click={() => isOpen = false}
        disabled={isExporting}
      >
        Cancel
      </button>
      <button
        class="primary"
        on:click={handleExport}
        disabled={isExporting}
      >
        {isExporting ? 'Exporting...' : 'Export'}
      </button>
    </div>
  </div>
</div>

<style>
  .export-dialog {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
  }

  .export-dialog.open {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .dialog-content {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    max-width: 500px;
    width: 90%;
  }

  .format-selector {
    margin: 1.5rem 0;
  }

  .format-option {
    display: block;
    padding: 0.75rem;
    margin: 0.5rem 0;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .format-option:hover {
    background: #f5f5f5;
    border-color: #1e40af;
  }

  .progress-bar {
    width: 100%;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
    overflow: hidden;
    margin: 1rem 0;
  }

  .progress {
    height: 100%;
    background: #1e40af;
    transition: width 0.3s ease;
  }

  .dialog-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 1.5rem;
  }

  button {
    padding: 0.5rem 1rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    background: white;
  }

  button.primary {
    background: #1e40af;
    color: white;
    border-color: #1e40af;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Deliverables**:
1. Template engine setup (Tera integration)
2. Template metadata loader
3. Variable validator
4. 3 core templates (Executive Summary, Meeting Notes, Project Status)

**Development Steps**:
```bash
# 1. Add Tera to Cargo.toml
cargo add tera serde_json

# 2. Create template modules
mkdir -p src-tauri/src/templates
touch src-tauri/src/templates/{mod.rs,engine.rs,manager.rs,validator.rs}

# 3. Create template directory
mkdir -p assets/templates/{executive-summary,meeting-notes,project-status}

# 4. Implement core template engine
# See: src-tauri/src/templates/engine.rs
```

### Phase 2: AI Integration (Weeks 3-4)

**Deliverables**:
1. Document type detection
2. Section generation prompts
3. Missing section detection
4. Tone adjustment

**APIs Used**:
- Claude API (preferred) or OpenAI for content generation
- Existing `send_message_to_claude` command pattern

### Phase 3: Frontend UI (Weeks 5-6)

**Deliverables**:
1. TemplateSelector component
2. DocumentEditor with live preview
3. ExportDialog with format options
4. TemplatePreview component

**Integration**:
- Connect to Tauri commands
- Real-time validation
- Save/load functionality

### Phase 4: Export Pipeline (Weeks 7-8)

**Deliverables**:
1. PDF generation (wkhtmltopdf or headless Chrome)
2. DOCX export (Pandoc integration)
3. HTML export
4. Markdown export with frontmatter

**Testing**:
- Export quality validation
- File size checks
- Format compatibility

### Phase 5: Template Library Expansion (Weeks 9-12)

**Deliverables**:
1. Add remaining 7 templates
2. Brand guidelines system
3. Custom template creation
4. Template versioning

**Future**:
- User-created templates
- Template marketplace
- Enterprise templates with company branding

---

## Technical Stack Recommendations

### Backend (Rust)
```toml
[dependencies]
tera = "1.20"                    # Template engine
serde_json = "1.0"              # JSON handling
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
regex = "1.10"                  # Pattern matching
uuid = { version = "1.0", features = ["v4", "serde"] }

[optional-dependencies]
wkhtmltopdf = "0.6"            # PDF generation (external tool)
pandoc = "0.8"                 # Document conversion
```

### Frontend (Svelte 5)
```json
{
  "dependencies": {
    "marked": "^11.0.0",
    "dompurify": "^3.0.6",
    "jszip": "^3.10.1",
    "html2canvas": "^1.4.1"
  },
  "devDependencies": {
    "tailwindcss": "^3.3.0"
  }
}
```

### External Tools
```bash
# macOS setup
brew install wkhtmltopdf pandoc

# Ubuntu setup
sudo apt-get install wkhtmltopdf pandoc

# Or use Docker for consistency
docker run -v /tmp:/tmp -w /tmp \
  pandoc/latex pandoc input.md -o output.pdf
```

---

## Database Schema Extension

```sql
-- New tables for template system
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    version TEXT NOT NULL,
    schema_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    export_format TEXT,
    file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES templates(id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS document_variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    variable_key TEXT NOT NULL,
    variable_value TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES generated_documents(id)
);

CREATE TABLE IF NOT EXISTS user_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    template_content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);
```

---

## Security & Privacy Considerations

### 1. Data Handling
- Templates processed locally (no cloud by default)
- AI API calls with Anthropic/OpenAI (PII scanning before sending)
- Exported documents marked as local-only

### 2. Template Storage
```rust
// Validate template metadata before loading
fn validate_template_metadata(metadata: &TemplateMetadata) -> Result<()> {
    // Check for malicious Jinja2 code
    if metadata.template_content.contains("__import__")
        || metadata.template_content.contains("eval") {
        return Err("Potentially malicious template".into());
    }

    // Validate variable names (alphanumeric + underscore only)
    for var in &metadata.variables {
        if !var.key.chars().all(|c| c.is_alphanumeric() || c == '_') {
            return Err(format!("Invalid variable name: {}", var.key));
        }
    }

    Ok(())
}
```

### 3. Export Audit Trail
```sql
CREATE TABLE IF NOT EXISTS export_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    export_format TEXT NOT NULL,
    file_path TEXT,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exported_by TEXT,
    FOREIGN KEY (document_id) REFERENCES generated_documents(id)
);
```

---

## Testing Strategy

### Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_template_variable_substitution() {
        let engine = TemplateEngine::new("assets/templates").unwrap();
        let context = json!({
            "title": "Test Document",
            "author": "John Doe",
            "findings": vec!["Finding 1", "Finding 2"]
        });

        let result = engine.render("executive-summary/template.md", &context);
        assert!(result.is_ok());
        assert!(result.unwrap().contains("Test Document"));
    }

    #[test]
    fn test_variable_validation() {
        let validator = VariableValidator::from_schema("executive-summary");
        let variables = json!({
            "title": "Valid Title",
            "author": "John Doe"
        });

        assert!(validator.validate(&variables).is_ok());
    }

    #[test]
    fn test_export_formats() {
        // Test each export format generates valid output
    }
}
```

### Integration Tests
- Document type detection accuracy
- End-to-end export pipeline
- Multi-format compatibility

---

## Future Enhancements

1. **Template Marketplace**: Browse community templates
2. **Custom Branding**: Upload company logos & colors
3. **Advanced Automation**: Scheduled report generation
4. **Collaboration**: Share templates & documents
5. **Analytics**: Track document generation patterns
6. **Version Control**: Template change history
7. **OCR Integration**: Extract data from images
8. **Real-time Collaboration**: Multiple editors

---

## Glossary

| Term | Definition |
|------|-----------|
| **Template** | Markdown file with variables and optional AI prompts |
| **Section** | Named part of a template (e.g., "Recommendations") |
| **Variable** | Placeholder for dynamic content (e.g., `{{ title }}`) |
| **Prompt** | Instructions for AI to generate section content |
| **Export** | Convert template to PDF, DOCX, HTML, or Markdown |
| **Metadata** | Document info (title, author, date, organization) |

---

## References & Resources

### Template Engines
- Tera (Rust): https://keats.github.io/tera/
- Handlebars (Rust): https://handlebars-rust.github.io/
- Jinja2 (Python): https://jinja.palletsprojects.com/

### Document Generation
- Pandoc: https://pandoc.org/
- WeasyPrint: https://weasyprint.org/
- Headless Chrome: https://chromedevtools.github.io/devtools-protocol/

### Best Practices
- McKinsey Executive Summary Guide
- Harvard Business School Report Templates
- Professional Writing Standards (Chicago Manual of Style)

---

## Appendix A: Complete Template Registry

See `assets/templates/metadata.json` for the full registry of all professional templates with complete schema definitions.

---

**Document Version**: 1.0
**Last Updated**: November 16, 2025
**Status**: Design Phase
**Next Review**: December 1, 2025

---

## Summary

This report template system enables BrainDump users to convert raw voice notes into polished professional documents through:

1. **Smart Detection**: AI-powered classification of document type
2. **Template-Driven Generation**: 10+ professional templates with variable substitution
3. **AI-Assisted Completion**: LLM-powered section generation and tone adjustment
4. **Multi-Format Export**: PDF, DOCX, HTML, and Markdown outputs
5. **Validation & Quality**: Section completeness checking and professional standards
6. **Privacy-First Design**: Local processing with optional cloud AI services

The system is designed to be extensible, allowing users to create custom templates while maintaining brand consistency and professional quality standards.
