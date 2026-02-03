---
name: prd-creator
description: Create comprehensive PRDs through conversational discovery. Use when users want to plan software projects, document requirements, or prepare specifications. Supports beginners to experienced PMs. Asks clarifying questions to gather requirements, researches technologies, and produces structured markdown PRDs.
---

# PRD Creator

Create comprehensive Product Requirements Documents (PRDs) through structured conversation and research.

## Overview

This skill transforms product ideas into detailed, actionable specifications through guided discovery. It produces a single comprehensive PRD that serves as the source of truth for development.

**Output:** `docs/PRD.md` (single file, comprehensive enough for planning agents to break down)

## Environment Handling

**In Claude Code:**
- Use AskUserQuestion tool for discovery questions (one question at a time)
- Save PRD to `docs/PRD.md` in project root
- Create `docs/` folder if it doesn't exist

**In Claude Desktop:**
- Use conversation for discovery
- Create PRD as artifact
- Present as downloadable file when complete

## Core Workflow

### Phase 1: Discovery & Understanding

**Objective:** Understand what the user wants to build, their context, and constraints.

**Approach:**
1. **Infer context from initial description** - Don't ask what's already provided
2. **Adapt questioning based on signals:**
   - Technical terminology used → experienced developer
   - Vague descriptions → needs guidance on specifics
   - Mentions of team/stakeholders → collaborative environment
   - Specific tools mentioned → tailor to their stack

3. **Ask clarifying questions dynamically** (see `references/questioning-patterns.md` for framework)
   - One question at a time, conversational tone
   - Focus 70% on understanding, 30% on educating about options
   - Prioritize: scope, core features, users, platform, must-haves vs nice-to-haves

4. **Determine scope early:**
   ```
   Is this a:
   - Single feature addition?
   - New full product/application?
   - Major refactor/redesign?
   ```
   Adapt depth of questioning accordingly.

**In Claude Code:** Use AskUserQuestion tool to ask one question at a time. Keep questions concise.

**Use web search** when:
- User mentions specific technologies you need to research
- Validating best practices for their use case
- Estimating costs for services/APIs
- Finding current alternatives to compare

### Phase 2: Research & Validation

**Objective:** Validate technical choices, research unknowns, fill gaps.

**When to research:**
- User mentions unfamiliar technologies
- Need to compare technical options
- Validating security/architecture patterns
- Estimating implementation complexity

**Tool priority:**
1. MCP-based search tools (see `references/tool-integration.md`)
2. Built-in WebSearch (fallback)
3. Built-in knowledge for well-established patterns

**See `references/tool-integration.md` for detailed tool usage patterns.**

### Phase 3: PRD Generation

**Objective:** Create structured, comprehensive PRD.

**Structure:**
1. **Load the PRD template** from `references/prd-template.md`
2. **Populate all sections** with gathered information
3. **Include implementation-ready details:**
   - Clear acceptance criteria for each feature
   - Data models with explicit field definitions
   - Technical constraints and integration points
   - Organized feature groupings

**Output:**
- Single file: `PRD.md`
- Comprehensive enough for a planning agent to break into tasks later
- No supplementary artifacts (TASKS.md, DEVELOPMENT_GUIDE.md, etc.)

### Phase 4: Review & Refinement

**Objective:** Iterate with user to finalize specifications.

**Approach:**
1. Present the PRD and explain what was created
2. **Ask specific, targeted questions** rather than general "any feedback?"
   - "Does the technical stack align with your team's expertise?"
   - "Are the user stories capturing the core use cases?"
   - "Is the phased approach feasible for your timeline?"
3. Make targeted updates with clear explanations
4. Present revised version

## Output Delivery

**In Claude Code:**
```bash
# Create docs folder if needed
mkdir -p docs

# Save PRD
# File: docs/PRD.md
```

**In Claude Desktop:**
- Create as artifact
- Offer download option

## Key Principles

**1. Dynamic, not prescriptive**
- Adapt questions based on what user already provided
- Infer skill level rather than asking directly
- Scale depth to project complexity

**2. Behavior-first, implementation-second**
- Focus on "what" and "why" before "how"
- Define clear acceptance criteria
- Let engineers choose implementation details within constraints

**3. Comprehensive single output**
- Create one thorough PRD document
- Include enough detail for agents to work autonomously
- Structure for version control and iteration

**4. Educational support**
- Explain technical options when user needs guidance
- Provide recommendations with rationale
- Keep beginners supported without overwhelming

## Reference Materials

- **`references/prd-template.md`** - Complete PRD structure with all sections
- **`references/questioning-patterns.md`** - Dynamic discovery framework
- **`references/tool-integration.md`** - How to use MCP servers and web search
- **`references/output-examples.md`** - Example PRDs for different project types

## Important Notes

- Never generate actual code in the PRD (leave for implementation phase)
- Always use available tools (search, MCP servers) to provide current, validated information
- Keep tone friendly and supportive, especially for beginners
- For complex projects, expect 10-20 minute conversation before PRD generation
- PRDs are living documents - encourage iteration
