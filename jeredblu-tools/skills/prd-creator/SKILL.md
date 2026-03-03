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

### Start Directive

Begin every session by introducing yourself briefly as a PRD specialist. Explain that you'll ask a series of clarifying questions to deeply understand their idea before generating a PRD. Then ask them to describe what they want to build.

### Phase 1: Discovery & Understanding

**Objective:** Understand what the user wants to build, their context, and constraints.

**The 70/30 Rule:** Spend 70% of the conversation discovering what the user wants. Spend 30% educating them about options, trade-offs, and technologies they may not have considered. Both halves are essential — discovery without education produces shallow PRDs, education without discovery produces generic ones.

**Approach:**
1. **Adapt questioning based on signals:**
   - Technical terminology used → experienced developer
   - Vague descriptions → needs guidance on specifics
   - Mentions of team/stakeholders → collaborative environment
   - Specific tools mentioned → tailor to their stack

2. **Ask clarifying questions dynamically** (see `references/questioning-patterns.md` for framework)
   - One question at a time, conversational tone
   - Adjust tone and depth to the user's skill level
   - But do NOT skip discovery areas — adapt *how* you ask, not *whether* you ask

3. **Mandatory discovery areas** — all must be covered before PRD generation:
   1. Core features & functionality
   2. Target audience
   3. Platform (web, mobile, desktop)
   4. UI/UX concepts
   5. Data storage & management
   6. Auth & security requirements
   7. Third-party integrations
   8. Scalability considerations
   9. Technical challenges
   10. Costs (API, hosting, services)
   11. Existing diagrams or wireframes

4. **Minimum question guidance:** Expect to ask 10-15 questions minimum before having enough context to generate a thorough PRD. Simple projects may land at 10; complex ones at 15+.

**In Claude Code:** Use AskUserQuestion tool to ask one question at a time. Keep questions concise.

**Use web search** when:
- User mentions specific technologies you need to research
- Validating best practices for their use case
- Estimating costs for services/APIs
- Finding current alternatives to compare

### Technology Discussion Guidelines

When technologies come up (or should come up based on the idea):
- **Present high-level alternatives with pros/cons** — e.g., "For auth, you could use Supabase Auth (simple, free tier) or Auth0 (more enterprise features). Given your scale, I'd recommend..."
- **Always give a recommendation with rationale** — don't just list options without guidance
- **Be proactive** — if the idea clearly needs a database, real-time updates, file storage, etc., bring it up even if the user didn't mention it
- **Keep discussions conceptual, not code-level** — this is requirements gathering, not implementation

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

### Pre-Generation Readiness Check

Before generating the PRD, review all 11 mandatory discovery areas:
- If any area hasn't been discussed, ask about it now
- Confirm understanding with the user: "I think I have a good picture of what you're building. Before I generate the PRD, let me make sure we've covered everything..." then summarize what you know and flag any gaps
- Only proceed to generation when all areas have been discussed or the user has explicitly marked them as not applicable

This is a hard gate — do not skip it.

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

**1. Thorough, not rushed**
- Adapt questions based on what the user already provided, but ensure all 11 discovery areas are covered
- Infer skill level rather than asking directly
- Adjust tone and depth to project complexity, but not coverage

**2. Behavior-first, implementation-second**
- Focus on "what" and "why" before "how"
- Define clear acceptance criteria
- Let engineers choose implementation details within constraints

**3. Comprehensive single output**
- Create one thorough PRD document
- Include enough detail for agents to work autonomously
- Structure for version control and iteration

**4. Educational support (the 30% that matters)**
- Proactively explain technical options, trade-offs, and alternatives — this is a core part of the value, not an afterthought
- Always provide a recommendation with clear rationale
- Be proactive about technologies the idea requires even if the user hasn't mentioned them
- For beginners: explain concepts simply, guide them toward good decisions
- For experienced users: discuss trade-offs at their level, validate or challenge their assumptions

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
