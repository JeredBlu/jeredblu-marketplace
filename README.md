# JeredBlu Marketplace

Custom Claude Code resources from [JeredBlu's YouTube channel](https://www.youtube.com/@JeredBlu).

## Overview

This marketplace provides skills that work across multiple AI coding tools:

- **prd-creator**: Create comprehensive PRDs through conversational discovery
- **agent-skill-evaluator**: Security and safety evaluation for agent skills
- **mcp-evaluator**: Security and privacy evaluation for MCP servers

All skills utilize MCP servers for enhanced functionality and follow the open Agent Skills standard.

## Installation Options

### Option 1: Claude Code Plugin Marketplace (Recommended)

**1. Add Marketplace**
```bash
/plugin marketplace add JeredBlu/jeredblu-marketplace
```

**2. Install Plugin**
```bash
/plugin install jeredblu-tools@jeredblu-marketplace
```

### Option 2: Manual Download (All Platforms)

Download skills individually for manual installation:

| Skill | Download | Description |
|-------|----------|-------------|
| PRD Creator | [prd-creator.zip](./downloads/prd-creator.zip) | Conversational PRD generation |
| Agent Skill Evaluator | [agent-skill-evaluator.zip](./downloads/agent-skill-evaluator.zip) | Security evaluation for skills |
| MCP Evaluator | [mcp-evaluator.zip](./downloads/mcp-evaluator.zip) | Security evaluation for MCP servers |

---

## Platform-Specific Installation

### Claude Desktop

1. Download the desired `.zip` file
2. Open Claude Desktop
3. Go to **Settings > Capabilities > Upload Skill**
4. Select the downloaded zip file
5. Repeat for additional skills

### Claude Code (Local)

1. Extract the zip file
2. Move contents to `~/.claude/skills/<skill-name>/`
3. Restart Claude Code

### VS Code / GitHub Copilot

1. Extract the zip file
2. Move contents to `.github/skills/<skill-name>/` (project) or `~/.copilot/skills/<skill-name>/` (global)
3. Enable preview setting: `chat.useAgentSkills`
4. Restart VS Code

### Cursor

1. Switch to Nightly channel: **Settings > Beta > Update Channel > Nightly**
2. Extract the zip file
3. Move contents to `.cursor/skills/<skill-name>/`
4. Restart Cursor

### OpenAI Codex CLI

1. Extract the zip file
2. Move contents to `~/.codex/skills/<skill-name>/` or `.codex/skills/<skill-name>/`
3. Restart Codex

### OpenCode

1. Extract the zip file
2. Move contents to `.opencode/skills/<skill-name>/` (project) or `~/.config/opencode/skills/<skill-name>/` (global)
3. Restart OpenCode

---

## Configuration

The skills work best with MCP servers. Both are optional but highly recommended for full functionality.

### Recommended MCP Servers

**GitHub MCP Server (Recommended)**
- Enables direct GitHub repository access for analyzing skills and MCP servers
- Installation: `@modelcontextprotocol/server-github`
- Requires: GitHub Personal Access Token

**Bright Data MCP Server (Recommended)**
- Enables web scraping and Reddit access for community feedback analysis
- Installation: `@brightdata/mcp`
- Requires: Bright Data API token
- Note: Enable Pro Mode for Reddit scraping

**Context7 MCP Server (Optional)**
- Enables documentation lookup for technology research
- Installation: `@upstash/context7-mcp`

Install and configure these MCP servers following their official installation instructions.

---

## Usage

### PRD Creator

Create comprehensive Product Requirements Documents through conversational discovery:

```
/prd-creator
```

Or naturally:
```
Help me create a PRD for my new app idea
I need to document requirements for a feature
Create product requirements for [project description]
```

The skill will:
- Guide you through discovery questions (problem, users, features)
- Research relevant technologies via MCP servers
- Generate structured PRD with all sections
- Support iterative refinement

**Output includes:**
- Problem statement and goals
- User personas and stories
- Functional/non-functional requirements
- Technical considerations
- Success metrics
- Timeline and milestones

### Agent Skill Evaluator

Evaluate the security of agent skills from various sources:

```
Evaluate this skill: https://github.com/username/skill-repo
Is this skill safe? https://example.com/my-skill.zip
Security assessment for this skill please: [attach .skill file]
```

The evaluator will:
- Download and extract the skill
- Analyze SKILL.md for prompt injections
- Review scripts for malicious code
- Search community feedback
- Generate comprehensive security report with risk scoring

**Features:**
- Prompt injection detection
- Malicious code pattern matching
- Hidden instruction scanning
- Data exfiltration detection
- Community validation
- Risk scoring (0-100 scale)
- Actionable recommendations

### MCP Server Evaluator

Evaluate the security of MCP servers:

```
Evaluate this MCP server: https://github.com/username/mcp-server
Is this MCP safe to use? https://github.com/org/mcp-repo
```

The evaluator will:
- Analyze repository metadata and activity
- Review code for security vulnerabilities
- Search for alternatives and comparisons
- Gather community feedback (including Reddit with Pro Mode)
- Generate detailed assessment with recommendations

**Features:**
- Security vulnerability analysis
- Privacy risk assessment
- Code quality review
- Alternative server discovery
- Community feedback research (Reddit, forums, GitHub)
- Multi-dimensional scoring
- Usability assessment

---

## Graceful Degradation

Skills work without MCP servers but with reduced functionality:

| Scenario | Behavior |
|----------|----------|
| No GitHub MCP | Uses web scraping for repository access |
| No Bright Data | Uses built-in web search (limited) |
| No Pro Mode | No Reddit scraping, basic search only |
| No Context7 | Manual documentation lookup |

**Example: Without MCPs**
```
User: "Evaluate this MCP: https://github.com/example/server"
Claude: Uses basic web scraping, can't access private repos,
        limited Reddit data, slower analysis
```

**Example: With MCPs**
```
User: "Evaluate this MCP: https://github.com/example/server"
Claude: Direct repo access, full code review, Reddit community
        feedback, comprehensive security scan
```

---

## Requirements

- Claude Code, Claude Desktop, VS Code, Cursor, Codex, or OpenCode
- GitHub Personal Access Token (recommended)
- Bright Data API token (recommended, for Reddit scraping)

---

## Coming Soon

- Custom slash commands
- Agent definitions
- Additional skills

---

## License

MIT
