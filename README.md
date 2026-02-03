# JeredBlu Marketplace

Custom Claude Code resources from [JeredBlu's YouTube channel](https://www.youtube.com/@JeredBlu).

## What's Included

### Skills
- **PRD Creator** - Create comprehensive PRDs through conversational discovery
- **Agent Skill Evaluator** - Evaluate Claude Code skills for security and quality
- **MCP Evaluator** - Evaluate MCP servers for security and best practices

*Coming soon: commands, agents, more skills*

## Installation

### Option 1: Marketplace (Recommended)
```bash
/plugin marketplace add JeredBlu/jeredblu-marketplace
/plugin install jeredblu-tools@jeredblu-marketplace
```

### Option 2: Manual Download
Download individual skills from the [downloads/](./downloads/) folder:
- [prd-creator.zip](./downloads/prd-creator.zip)
- [agent-skill-evaluator.zip](./downloads/agent-skill-evaluator.zip)
- [mcp-evaluator.zip](./downloads/mcp-evaluator.zip)

Extract to your `.claude/skills/` folder.

## Usage

### PRD Creator
```
/prd-creator
```
Guides you through creating a comprehensive Product Requirements Document.

### Agent Skill Evaluator
```
/agent-skill-evaluator
```
Evaluates Claude Code skills for security vulnerabilities and best practices.

### MCP Evaluator
```
/mcp-evaluator
```
Evaluates MCP servers for security patterns and implementation quality.

## Recommended MCP Servers

These skills work great with:
- [Context7 MCP](https://github.com/upstash/context7) - Documentation lookup
- [Bright Data MCP](https://github.com/luminati-io/brightdata-mcp) - Web scraping
- [GitHub MCP](https://github.com/github/github-mcp-server) - GitHub integration

## License

MIT
