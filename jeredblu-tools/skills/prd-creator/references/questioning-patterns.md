# Questioning Patterns

Dynamic discovery framework for understanding user requirements without overwhelming them with prescriptive questions.

## Core Principle

**Ask what you don't know. Don't ask what they've already told you.**

Adapt your questioning based on:
- What information they've already provided
- Signals about their experience level
- Complexity of their project
- Context clues about their environment

---

## Essential Discovery Areas

### 1. Project Scope & Type

**Determine early:**
- Is this a new full product, a feature addition, or a major refactor?
- Is this for personal use, a startup, or an enterprise?
- Is there an existing codebase or starting from scratch?

**Sample questions (adapt based on context):**
- "Tell me about your project idea at a high level."
- "What's the main problem this solves for users?"
- "Is this a new application or adding to something existing?"

### 2. Core Functionality

**Focus on the "what" and "why":**

**For vague descriptions:**
- "What are the 3-5 core features that make this valuable?"
- "Walk me through what a user would do in a typical session."
- "What's the primary action you want users to take?"

**For detailed descriptions:**
- "Which of these features are must-haves for the initial version?"
- "Are there any edge cases or special scenarios to consider?"

**Pattern: Start broad, then zoom in**
1. "What does the app do?" 
2. "Who uses it and why?"
3. "What specific features enable that?"
4. "What happens when [edge case]?"

### 3. Target Users

**Understand who this is for:**

**If not mentioned:**
- "Who are you building this for?"
- "What does a typical user look like?"

**If mentioned but vague:**
- "What problems do they currently face?"
- "How are they solving this today?"
- "What would make them switch to your solution?"

**For B2B:**
- "Is this for individual users or teams?"
- "Do different users have different roles/permissions?"

### 4. Platform & Deployment

**Determine technical context:**

**If not specified:**
- "Where do you envision users accessing this?"
- "Web app, mobile app, desktop, or multiple platforms?"

**If specified:**
- "Does it need to work offline?"
- "Any specific device or browser requirements?"
- "Are you planning to deploy this yourself or use a hosting service?"

### 5. Data & Storage

**Understand data needs:**

**Signals to ask:**
- Mentioned users, accounts → "Do users need to create accounts?"
- Mentioned tracking, history → "What data needs to be saved?"
- Mentioned sharing → "How should users share with each other?"

**Questions:**
- "What information needs to be stored long-term?"
- "Is any of this data sensitive (PII, financial, health)?"
- "Do users need to export or back up their data?"

### 6. Authentication & Security

**Only ask if relevant to the project:**

**When to ask:**
- Project has user accounts
- Handles sensitive data
- Involves payments or personal information

**Questions:**
- "How should users log in?" (Social auth, email/password, magic links?)
- "Are there different user roles with different permissions?"
- "Any specific security or compliance requirements?"

### 7. Third-Party Integrations

**Explore dependencies:**

**If they mention services:**
- "Are you already using [service] or considering alternatives?"
- "Do you have API access for [service]?"

**If not mentioned but relevant:**
- "Will this need to connect to any external services?" (payment, email, analytics, etc.)
- "Are there any tools your team already uses that this should integrate with?"

### 8. Technical Constraints

**Understand limitations and preferences:**

**Skill level signals:**
- Uses specific framework names → Experienced, ask technical details
- Vague technical terms → Beginner, provide guidance
- "I don't know much about coding" → Educational approach

**Questions based on skill level:**

**For beginners:**
- "Do you have a preference for which technologies to use, or would you like recommendations?"
- "Are you planning to code this yourself or work with a developer/AI tool?"

**For experienced:**
- "What's your tech stack preference?"
- "Any technical constraints from existing infrastructure?"
- "Performance requirements or scale targets?"

### 9. Timeline & Resources

**Understand practical constraints:**

**Questions:**
- "What's your target timeline for the first version?"
- "Is this a solo project or do you have a team?"
- "What's your budget range for tools and services?"

### 10. Success Criteria

**Define what "done" looks like:**

**Questions:**
- "How will you know if this is successful?"
- "What metrics matter most?" (users, revenue, engagement, etc.)
- "What does the MVP need to do to be useful?"

---

## Questioning Strategies

### Strategy 1: The Funnel Approach

Start broad, narrow progressively:
1. "Tell me about your idea"
2. "What are the main features?"
3. "Let's dive into [specific feature] - how should that work?"
4. "What happens if [edge case]?"

### Strategy 2: The Reflective Mirror

Summarize and confirm understanding:
- "So if I understand correctly, you're building [summary]. Is that accurate?"
- "It sounds like the core value is [benefit]. Does that capture it?"

This accomplishes:
- Validates your understanding
- Helps user clarify their own thinking
- Identifies gaps naturally

### Strategy 3: The Options Educator

When they're unsure, provide guided options:
- "For authentication, you could use [Option A] which is [pros/cons], or [Option B] which is [pros/cons]. Given [their context], I'd recommend [choice] because [reason]."

**Balance:** 70% discovering what they want, 30% educating about options

### Strategy 4: The Edge Case Explorer

For experienced users, probe deeper:
- "What should happen if two users try to edit the same thing simultaneously?"
- "How do you want to handle deleted items - soft delete or hard delete?"
- "Any rate limiting or usage caps to consider?"

### Strategy 5: The Assumption Surfacer

Make implicit assumptions explicit:
- "I'm assuming users can only see their own data - is that correct?"
- "Should this work on mobile browsers or do you want a dedicated app?"

---

## Inference Signals

### Skill Level Indicators

**Beginner Signals:**
- "I have an idea but I'm not technical"
- Asks "Is that possible?"
- Vague about technical details
- → Provide more guidance, explain options, educational tone

**Intermediate Signals:**
- Mentions some frameworks or technologies
- Asks comparative questions "React or Vue?"
- → Confirm their choices, provide pros/cons, validate approach

**Advanced Signals:**
- Specific technical requirements "Need sub-200ms p99 latency"
- Mentions architecture patterns, protocols
- → Ask detailed technical questions, assume knowledge, dive deep

### Project Complexity Indicators

**Simple (1-2 weeks of dev):**
- Single main feature
- No integrations
- Basic CRUD operations
- → Lightweight questioning, focus on MVP

**Medium (1-3 months):**
- Multiple features
- Some integrations
- User authentication
- → Balanced discovery, plan phases

**Complex (3+ months):**
- Many features with dependencies
- Multiple integrations
- Team collaboration needs
- Advanced data requirements
- → Deep discovery, architecture focus, risk assessment

### Context Indicators

**Solo Developer:**
- "I'm building this..."
- → Focus on sustainability, maintainability, realistic scope

**Startup Team:**
- "We're launching..."
- → Focus on speed, validation, scalability planning

**Enterprise:**
- "Our team needs..."
- → Focus on security, compliance, team collaboration, integration

---

## Question Flow Example

**User:** "I want to build a habit tracking app"

**You:** "Tell me more about how you envision users tracking their habits - what does that experience look like?"

**User:** "They can add habits they want to track, and check them off each day"

**You:** "Got it. Are you thinking of including any features beyond the basic tracking, like streaks, reminders, or analytics?"

**User:** "Yeah, showing streaks would be motivating! And maybe graphs of their progress"

**You:** "Nice! Should users be able to share their progress with friends or keep it private?"

**User:** "Private for now, but maybe social features later"

**You:** "Makes sense. Where do you want users to access this - mobile app, web, or both?"

**User:** "Mobile app, mostly iOS to start"

**You:** "Are you planning to build this yourself, or working with a developer or AI coding tool?"

**User:** "I'll use an AI coding tool like Claude Code"

**You:** "Perfect. Last few questions: Do users need accounts to save their data? And any specific design style you're going for?"

[Continue based on responses]

---

## Anti-Patterns to Avoid

**Don't:**
- Ask every question in a checklist format
- Re-ask for information already provided
- Use technical jargon with beginners
- Ask about Phase 2 features before MVP is clear
- Overwhelm with 5+ questions at once
- Ask "Do you want X?" for every possible feature

**Do:**
- Let conversation flow naturally
- Adapt to their communication style
- Ask one thoughtful question at a time
- Circle back if gaps emerge later
- Use their terminology back to them
- Offer recommendations proactively when helpful

---

## Conversation Pacing

**Phase 1 (First 3-5 questions):**
- Broad understanding
- Core functionality
- Target users
- Platform basics

**Phase 2 (Next 5-10 questions):**
- Specific features and flows
- Data requirements
- Technical preferences
- Integrations

**Phase 3 (Final questions):**
- Edge cases
- Success criteria
- Timeline/resources
- Anything missing

**Signal for PRD generation:**
- You can explain the product clearly
- You know the core features and priorities
- You understand the target users
- You have enough technical context to recommend a stack
- Major questions are answered

If in doubt, ask: "I think I have a good picture. Is there anything else important I should know before I create your PRD?"
