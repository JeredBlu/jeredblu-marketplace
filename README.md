# JeredBlu Marketplace

Custom Claude Code resources from [JeredBlu's YouTube channel](https://www.youtube.com/@JeredBlu).

## Overview

This marketplace provides skills that work across multiple AI coding tools:

- **prd-creator**: Create comprehensive PRDs through conversational discovery
- **agent-skill-evaluator**: Security and safety evaluation for agent skills
- **mcp-evaluator**: Security and privacy evaluation for MCP servers
- **repo-evaluator**: Is this GitHub project safe to install? Checks what it does to your computer, who it talks to, and whether it's shady — without ever installing or running it
- **frugal-fable**: Keep a premium model (Fable/Opus) on the judgment and delegate token-heavy work to cheaper models (Haiku/Sonnet) — for research, building, testing, and debugging. Have Codex CLI too? It can offload slices to GPT-5.6 (Sol/Terra/Luna) as a **second quota pool** — consent-gated, and zero Claude usage for the offloaded work

Most skills utilize MCP servers for enhanced functionality and follow the open Agent Skills standard. **frugal-fable** additionally needs Claude Code's workflow + sub-agent orchestration for its full feature set (see the platform note under [Usage](#frugal-fable-1)).

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
| Repo Evaluator | [repo-evaluator.zip](./downloads/repo-evaluator.zip) | Pre-install safety check for any GitHub project |
| Frugal Fable | [frugal-fable.zip](./downloads/frugal-fable.zip) | Premium-model orchestration + cheap-model delegation, incl. cross-CLI Codex offload (full features: Claude Code) |

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
2. Drop unzipped folder to `~/.claude/skills` in your project directory or global Claude config
3. Restart Claude Code


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
- [See Github Page for Install Instructions](https://github.com/github/github-mcp-server)
- Requires: GitHub Personal Access Token

**Bright Data MCP Server (Recommended)**
- Enables web scraping and Reddit access for community feedback analysis
- [See Github Page for Install Instructions](https://github.com/brightdata/brightdata-mcp)
- Requires: Bright Data API token
- [Create BRD Account with my Link (you might get some extra free credits)](https://tinyurl.com/jeredwebmcp)

**Bright Data CLI (alternative to the MCP)**
- `npm i -g @brightdata/cli`, then `bdata login` — used by repo-evaluator for web search (`bdata search`)

**GitHub CLI (`gh`) — required for repo-evaluator**
- [Install](https://cli.github.com/), then `gh auth login`

**Context7 MCP Server (Optional)**
- Enables documentation lookup for technology research
- [See Github Page for Install Instructions](https://github.com/upstash/context7)

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
- Interview you one question at a time (typically 12–20 questions) across 11 areas — features, users, platform, data, sign-in & privacy, integrations, scale, risks, budget/timeline/who's building, design, existing materials — and follow up on the details that matter
- Offer options with plain-language trade-offs and a recommendation for the big decisions (platform, data, sign-in, build vs. buy)
- Research current pricing and free-tier limits so the plan fits your budget
- Confirm a summary with you before writing, then generate a right-sized PRD with acceptance criteria, data models, and an Assumptions & Open Questions section
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

### Repo Evaluator

Check any open-source project on GitHub **before** you install it:

```
Is this safe to install? https://github.com/owner/project
Evaluate this repo before I brew install it: https://github.com/owner/tool
The README says to run a curl | sh command — is that safe? https://github.com/owner/repo
```

The evaluator will:
- Clone the repo inertly (no hooks, no submodules) — it never installs, builds, or runs anything
- Evaluate the install path you'd actually use (Homebrew recipe, `curl | sh` script, npm/pip package, release download)
- Scan for 20+ danger categories and list every web address the code references
- Check dependencies for known vulnerabilities (OSV.dev) and risky sources
- Check the maintainer, releases, security advisories, look-alike repos, and community reviews
- Optionally inspect a release .zip/.dmg/.pkg without opening it (asks before downloading)

**Features:**
- Install-time hooks, start-at-login, sudo/admin use, Gatekeeper/quarantine bypass
- Phone-home, telemetry (and whether it's on by default + how to turn it off)
- Credential access, keylogging, screen/clipboard capture
- Self-promo: affiliate links, auto-starring your GitHub, branding injected into your output
- Obfuscation, hidden Unicode, committed binaries, crypto-miners
- "Is the binary you install the source that was reviewed?" (CI-built vs built on someone's laptop)
- Plain-English verdict: what it is, what it does to your computer, who it talks to, should you install

**Requires:** GitHub CLI (`gh`) logged in (`gh auth login`). Web search via Bright Data CLI or MCP recommended; falls back to built-in search.

### Frugal Fable

> **Platform note:** Full functionality requires **Claude Code** (a Fable-class runtime with workflow + sub-agent orchestration). On Claude Desktop, Codex, or OpenCode the written delegation guidance still applies, but the bundled budget-capped research workflow won't run.

Keep your most capable model on the thinking and push token-heavy volume to cheaper models:

```
/frugal-fable
```

Or naturally:
```
Be efficient with Fable on this — don't burn tokens
Research X but delegate the searching to cheaper agents
Build this feature but keep Fable on the architecture and review
```

The skill will:
- Keep the session model (Fable/Opus) on decomposition, architecture, synthesis, and review
- Delegate scans, fetches, bounded patches, and tests to Haiku/Sonnet with a conservative quality floor
- Use a file-based "context firewall" so sub-agent output doesn't bloat the orchestrator's context
- Reach for the bundled budget-capped `frugal-research.js` workflow for cost-bounded deep research

**Lanes:** research · build/dev · testing · debugging. As with any delegation, the orchestrator reviews delegated work before relying on it (the built-in quality gate) — so you stay in control of what ships.

**Note:** "Fable" is just the marquee example — the skill uses *whatever model your session starts on* as the orchestrator (Opus works identically) and delegates down from there.

#### Cross-CLI: Codex as a second pool (new in 1.2.0)

If you also have [OpenAI's Codex CLI](https://developers.openai.com/codex) installed and logged in, frugal-fable can delegate slices to Codex models — **GPT-5.6 Sol / Terra / Luna**, tier-mapped onto the same routing rules (Sol ≈ Opus-class, Terra ≈ Sonnet, Luna ≈ Haiku). Why this is more than a nice-to-have:

- **It's a separate quota.** Codex runs on your ChatGPT subscription, so every slice routed there costs *zero* Claude usage — the frugal move isn't just "cheaper model," it's "different bill."
- **Consent-gated.** The skill never routes to Codex on its own: it detects the CLI, asks you once per session, and stays silent on machines without Codex. If you're away when it would ask, it proceeds on Claude models and mentions the offer in its summary.
- **Battle-tested mechanics.** Delegation uses synchronous `codex exec` with file-based reports (no context bloat), verified recipes for build slices, adversarial second opinions, repo/PR reviews, and same-session amendments — including fixes for real gotchas we hit (resumed Codex sessions silently revert to your config defaults; the recipes re-pin the sandbox every time).

Try it naturally:
```
Delegate the heavy parts of this refactor to Codex
Get a second opinion from Codex on this diff
Build this, keep Claude on architecture, offload grunt work to my Codex quota
```

Requires: Claude Code as the orchestrator + `codex` CLI on PATH. Without Codex, nothing changes — the skill behaves exactly as before.

---

## Graceful Degradation

Skills work without MCP servers but with reduced functionality:

| Scenario | Behavior |
|----------|----------|
| No GitHub MCP | Uses web scraping for repository access |
| No Bright Data | Uses built-in web search (limited) |
| No Pro Mode | No Reddit scraping, basic search only |
| No Context7 | Manual documentation lookup |
| No `gh` login (repo-evaluator) | Stops and asks you to run `gh auth login` |

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
- GitHub CLI (`gh`) logged in (required for repo-evaluator)
- Bright Data API token (recommended, for Reddit scraping)

---

## Coming Soon

- Custom slash commands
- Agents
- Additional skills

