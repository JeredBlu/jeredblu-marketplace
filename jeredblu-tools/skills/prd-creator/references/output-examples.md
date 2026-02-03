# Output Examples

Example PRDs showing how to adapt the template for different project types and complexities.

---

## Example 1: Simple Feature PRD

**Project Type:** Single feature addition to existing app
**Complexity:** Low

```markdown
# Dark Mode Toggle - Product Requirements Document

**Version:** 1.0
**Date:** January 2026
**Status:** Approved
**Owner:** Product Team

## Executive Summary

**TL;DR:** Add a dark mode option to the app to reduce eye strain and improve user experience in low-light environments.

**Problem:** Users report eye strain when using the app at night. Competitors offer dark mode. User surveys show 67% want this feature.

**Solution:** Implement a system-wide dark mode toggle in settings that persists across sessions and respects system preferences.

**Success Metrics:**
- 40% of users enable dark mode within first week
- 10% reduction in user complaints about eye strain
- No performance degradation

## Scope

**In Scope:**
- Dark mode toggle in user settings
- Dark color palette for all screens
- Persist user preference
- Respect system dark mode setting

**Out of Scope:**
- Auto-scheduling (sunset/sunrise)
- Custom themes beyond light/dark
- Per-section mode switching

## User Stories

**US-1: Toggle Dark Mode**
- **Story:** As a user, I want to toggle dark mode in settings, so I can reduce eye strain
- **Acceptance Criteria:**
  - Given I'm in settings, when I toggle dark mode, then all app screens update immediately
  - Given I've enabled dark mode, when I restart the app, then dark mode persists
  - Given my system is in dark mode, when I first launch the app, then app defaults to dark mode

**US-2: Visual Consistency**
- **Story:** As a user, I want all screens to look good in dark mode, so the experience is cohesive
- **Acceptance Criteria:**
  - All text is readable (WCAG AA contrast ratio)
  - All images have appropriate contrast
  - No jarring white flashes when navigating

## Technical Implementation

**Changes Required:**
- Add `theme` field to user preferences model
- Create dark color palette (CSS variables or theme object)
- Add theme toggle component
- Apply theme throughout component tree
- Store preference in localStorage/AsyncStorage

**Recommended Approach:**
```css
/* Using CSS variables */
:root {
  --bg-primary: #ffffff;
  --text-primary: #000000;
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --text-primary: #ffffff;
}
```

**Testing:**
- Visual regression testing for all screens
- Contrast ratio validation
- Toggle functionality testing
- Persistence testing across sessions

## Implementation Plan

**Week 1:**
- Define color palette
- Set up theme system architecture
- Implement core toggle functionality

**Week 2:**
- Apply theme to all screens
- Testing and refinements
- Ship to production

## Success Metrics

- Feature adoption: 40% within 1 week
- User satisfaction: +15 NPS
- No increase in bug reports

---
```

## Example 2: Medium Complexity PRD (New Product)

**Project Type:** New standalone product
**Complexity:** Medium

```markdown
# Habit Tracker App - Product Requirements Document

**Version:** 1.0
**Status:** In Development
**Owner:** Startup Team

## Executive Summary

**TL;DR:** Mobile-first habit tracking app with streak visualization, daily reminders, and progress analytics.

**Problem:** Existing habit trackers are either too complex (Notion) or too simple (basic to-do apps). Users want something focused but powerful.

**Solution:** Clean, mobile-first app focused solely on habit building with smart defaults, beautiful visualizations, and gentle reminders.

**Success Metrics:**
- 1,000 users in first month
- 60% 7-day retention
- Average 3 habits tracked per user

## Target Users

**Primary Persona: "Self-Improver Sarah"**
- Age 25-35, working professional
- Wants to build better habits but struggles with consistency
- Uses mobile apps daily
- Values simplicity and visual feedback

## Core Features (MVP)

### F1: Habit Creation
- Users can create custom habits
- Set frequency (daily, weekly, custom)
- Choose icon and color
- Add optional notes

**Acceptance Criteria:**
- Create habit in < 30 seconds
- Supports daily, 2x/week, 3x/week, weekday frequencies
- 20 icons, 10 colors available

### F2: Daily Check-in
- See today's habits on home screen
- One-tap to mark complete
- Visual feedback (animation, streak counter)

**Acceptance Criteria:**
- Home screen loads in < 1 second
- Tap to toggle completion
- Undo last check-in

### F3: Streak Tracking
- Show current streak for each habit
- Visual calendar view (GitHub-style)
- Celebrate milestones (7, 30, 100 days)

**Acceptance Criteria:**
- Streaks update immediately
- Calendar shows last 90 days
- Milestone celebration shows once

### F4: Progress Analytics
- Weekly completion rate
- Longest streak
- Total completions

## Technical Stack

**Frontend:**
- React Native (iOS first, Android Phase 2)
- Expo for development
- React Navigation
- Zustand for state

**Backend:**
- Supabase (Postgres + Auth + Storage)
- Free tier sufficient for MVP

**Push Notifications:**
- Expo Notifications
- Opt-in reminders

## Data Model

```typescript
User {
  id: uuid
  email: string
  created_at: timestamp
}

Habit {
  id: uuid
  user_id: uuid (foreign key)
  name: string (max 50 chars)
  icon: string (icon key)
  color: string (hex)
  frequency: enum ['daily', '2x_week', '3x_week', 'weekdays']
  created_at: timestamp
  archived: boolean
}

Completion {
  id: uuid
  habit_id: uuid (foreign key)
  completed_at: timestamp (date only)
  notes: string (optional, max 200 chars)
}
```

## Implementation Phases

**Phase 1 (Weeks 1-2): Foundation**
- Supabase setup
- Auth flow (email/password)
- Basic data models
- Simple habit CRUD

**Phase 2 (Weeks 3-4): Core Features**
- Home screen with today's habits
- Check-in functionality
- Calendar view
- Streak calculation

**Phase 3 (Weeks 5-6): Polish**
- Progress analytics
- Push notifications
- Onboarding flow
- App Store submission

**Phase 4 (Week 7): Beta Launch**
- TestFlight release
- User feedback collection
- Bug fixes

## Success Criteria

**Launch Requirements:**
- All MVP features complete
- < 3 critical bugs
- App Store approved
- 50 beta testers onboarded

**Post-Launch Metrics:**
- 1,000 downloads in month 1
- 60% 7-day retention
- 4.5+ App Store rating
- 30% of users enable notifications

## Future Roadmap

**Phase 2 (3 months):**
- Android version
- Social features (share progress)
- Habit templates
- Notes and journaling

**Phase 3 (6 months):**
- Team/family habits
- Integrations (Apple Health, Strava)
- Premium features
- Web companion

---
```

## Example 3: Complex Enterprise PRD (Condensed)

**Project Type:** Enterprise SaaS platform
**Complexity:** High

```markdown
# Enterprise CRM Platform - Product Requirements Document

**Version:** 1.0
**Status:** Planning
**Owner:** Product Team

## Executive Summary

**TL;DR:** Multi-tenant CRM platform with advanced automation, AI-powered insights, and enterprise security compliance.

**Problem:** Mid-market companies need CRM capabilities of enterprise solutions without the complexity and cost.

**Solution:** Modern, API-first CRM with intelligent automation, customizable workflows, and SOC 2 compliance.

**Success Metrics:**
- 50 enterprise customers in year 1
- $2M ARR by month 18
- NPS > 40

## Non-Negotiable Principles

### Security
- All data encrypted at rest and in transit
- SOC 2 Type II compliance required
- RBAC for all resources
- Audit logging for all actions

### Performance
- 99.9% uptime SLA
- API response time < 200ms (p95)
- Support 10,000 concurrent users

### Architecture
- Microservices architecture
- Event-driven communication
- API-first design
- Multi-tenant with data isolation

## Core Features

### Contact Management
- Full customer profile with custom fields
- Activity timeline
- Relationship mapping
- Import/export capabilities

### Pipeline Management
- Customizable deal stages
- Weighted forecasting
- Team assignments
- Automation triggers

### Reporting & Analytics
- Real-time dashboards
- Custom report builder
- AI-powered insights
- Export to multiple formats

### Integrations
- REST API with webhooks
- Native email integration
- Calendar sync
- Third-party app marketplace

## Technical Stack

**Frontend:** React + TypeScript, TailwindCSS
**Backend:** Node.js microservices, GraphQL gateway
**Database:** PostgreSQL (primary), Redis (cache), Elasticsearch (search)
**Infrastructure:** AWS EKS, Terraform, GitHub Actions

## Data Model (Key Entities)

```typescript
Tenant {
  id: uuid
  name: string
  plan: enum ['starter', 'professional', 'enterprise']
  settings: jsonb
}

Contact {
  id: uuid
  tenant_id: uuid
  email: string (unique per tenant)
  custom_fields: jsonb
  created_at: timestamp
}

Deal {
  id: uuid
  tenant_id: uuid
  contact_id: uuid
  stage_id: uuid
  value: decimal
  probability: integer
  close_date: date
}
```

## Implementation Phases

**Phase 1 (Months 1-3):** Core platform, auth, basic CRM
**Phase 2 (Months 4-6):** Automation, reporting, integrations
**Phase 3 (Months 7-9):** AI features, advanced analytics
**Phase 4 (Months 10-12):** Enterprise features, compliance certifications

## Risk Assessment

**Technical Risks:**
- Multi-tenancy data isolation (Medium/High) - Mitigate with RLS policies
- Real-time sync performance (Medium/Medium) - Use event sourcing

**Business Risks:**
- Enterprise sales cycle length (High/Medium) - Build partner channel
- Compliance timeline (Medium/High) - Start SOC 2 early

---
```

---

## Adaptation Tips

**For Beginners:**
- More detailed explanations
- Include code examples and tutorials
- Link to learning resources
- Simpler technical choices

**For Experienced Developers:**
- Focus on architecture and trade-offs
- Assume technical knowledge
- Include advanced considerations
- Reference design patterns

**For Startups:**
- Emphasize speed and validation
- Include metrics and KPIs
- Plan for iteration
- Keep scope tight

**For Enterprise:**
- Include compliance requirements
- Detail security specifications
- Plan for scale
- Document governance
