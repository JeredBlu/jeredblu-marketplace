# Tool Integration Guide

How to effectively use MCP servers and built-in capabilities during PRD creation.

---

## Web Search (Required)

Use MCP-based search tools when available (preferred), fall back to built-in only if no MCPs installed:

**Priority order:**
1. Bright Data Web MCP (preferred - deep research, scraping)
2. Brave Search MCP (fast, reliable)
3. Exa MCP (AI-powered search)
4. Perplexity MCP (research assistant)
5. Context7 MCP (for docs/library lookup)
6. Any other web search MCP available
7. Built-in WebSearch tool (fallback only)

**Always search for:**
- Technology pricing validation
- Current best practices
- Tool compatibility verification
- API documentation

---

## MCP Tool Detection

At the start of PRD creation, check which tools are available:
- If Bright Data Web MCP → use for comprehensive research
- If Brave/Exa/Perplexity MCP → use for quick searches
- If Context7 MCP → use for library/framework docs
- If none → fall back to built-in WebSearch

**Never apologize for lack of tools** - Work with what's available and provide the best answer possible.

---

## Bright Data Web MCP

**Best for:** Deep technical research, pricing comparison, documentation scraping

### When to Use

**Deep technical research:**
- Need detailed documentation for a specific technology
- Researching API capabilities in depth
- Finding specific implementation examples

**Structured data extraction:**
- Pricing comparison across multiple services
- Feature comparison between tools
- Extracting data from documentation sites

**GitHub exploration:**
- Finding relevant open-source projects
- Checking repository activity and maintenance
- Reviewing implementation examples

### How to Use

**For documentation:**
```
"I'll research the detailed Supabase documentation..."

[scrape_as_markdown: https://supabase.com/docs/guides/auth]
[Extract relevant information]
[Provide informed recommendation]
```

**For comparison:**
```
[Use search_engine to find comparison articles]
[Use scrape_as_markdown to extract detailed info]
[Synthesize into clear recommendation]
```

---

## Context7 MCP

**Best for:** Library documentation, framework guides, API references

### When to Use

- User mentions a specific library or framework
- Need current documentation for a technology
- Validating API patterns or usage

### How to Use

```
"Let me check the current React documentation..."

[Use Context7 to query library docs]
[Extract relevant patterns]
[Recommend based on official guidance]
```

---

## Built-In WebSearch (Fallback)

Use when no MCP search tools are available.

### When to Use

**Technology validation:**
- User mentions a framework you need current info about
- Need to verify best practices have changed
- Checking if a library/tool is still maintained

**Cost estimation:**
- Pricing for APIs and services
- Hosting cost estimates
- Tool subscription costs

**Comparison research:**
- "Should I use X or Y?" questions
- Finding alternatives to a technology
- Benchmarking performance characteristics

### When NOT to Use

- For well-established knowledge (don't search for "what is React")
- For user-specific information (their preferences, their constraints)
- For basic programming concepts
- Mid-conversation unless genuinely needed

### How to Use

**Tell the user what you're doing:**
- "Let me research the latest pricing for Stripe to give you accurate estimates..."
- "I'll look up current best practices for mobile authentication..."

**Keep searches focused:**
- Search for specific technologies, not general concepts
- One search per specific question
- Use results to inform recommendations, don't just parrot them

---

## Tool Usage Workflow

### During Discovery Phase

1. **Use AskUserQuestion** (Claude Code) or conversation (Desktop) to gather requirements
2. **Use web search** if user mentions unfamiliar technology
3. **Check Context7** for library-specific documentation

### During Research Phase

1. **Use MCP search tools** for technology validation (Bright Data preferred)
2. **Use Context7** for documentation lookup
3. **Fall back to WebSearch** if no MCPs available
4. **Synthesize findings** into clear recommendations

### During PRD Generation

1. Reference research findings in recommendations
2. Include validated pricing/costs
3. Link to relevant documentation where helpful

---

## Best Practices

### Do:
- Tell user when you're using a tool ("Let me research that...")
- Explain what you're searching for and why
- Synthesize results into clear recommendations
- Use tools to validate your recommendations
- Balance tool use with direct answers

### Don't:
- Use tools unnecessarily for basic knowledge
- Search for information user already provided
- Over-rely on tools when your knowledge is sufficient
- Get distracted by irrelevant search results
- Apologize for not having tools

---

## Error Handling

### If MCP Tool Unavailable

Try the next tool in the priority list. If all MCPs unavailable, use built-in WebSearch.

### If Search Returns Poor Results

- Try reformulated query
- Use your existing knowledge
- Be transparent: "The search didn't return great results, but based on standard practices..."

### If Too Many Options

- Apply user's constraints to filter
- Present top 2-3 options with clear reasoning

---

## Examples of Effective Tool Use

### Example 1: Tech Stack Decision

```
User: "What's the best database for my app?"

[Check available tools - Bright Data MCP found]
[Use search_engine: "PostgreSQL vs MySQL vs MongoDB 2026 comparison"]
[Analyze results against user requirements]

Response: "Based on your requirements [list them], I recommend PostgreSQL
because [specific reasons tied to their needs]. Here's why..."
```

### Example 2: Integration Research

```
User: "I need payment processing for my SaaS app"

[Use Bright Data MCP to search pricing pages]
[scrape_as_markdown on Stripe and alternatives]

Response: "For transactional payments, here are your main options:
- Stripe: [pros/cons, pricing]
- AWS SES: [pros/cons, pricing]

Given that you're [their context], I recommend [choice] because..."
```

### Example 3: Documentation Lookup

```
User: "How should I handle auth in Next.js?"

[Check Context7 MCP availability]
[Query Next.js auth documentation]

Response: "Based on the current Next.js documentation, the recommended
approach is [method]. Here's the pattern..."
```

---

## Integration Checklist

Before using any tool, ask:
- [ ] Do I actually need this information?
- [ ] Can I answer this from existing knowledge?
- [ ] Will this improve my recommendation?
- [ ] Have I told the user what I'm doing?
- [ ] Am I searching for the right thing?

After using a tool:
- [ ] Did I get useful information?
- [ ] Have I synthesized it into actionable advice?
- [ ] Does it tie back to the user's specific needs?
- [ ] Have I explained my recommendation clearly?
