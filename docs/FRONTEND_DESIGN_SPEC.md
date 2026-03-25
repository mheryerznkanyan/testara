# Testara SaaS Frontend — Strategic Design Specification

_Source: Architectural design document, March 2026_

---

## Overview

This document defines the target architecture and UX design for the Testara SaaS frontend. It is informed by competitive analysis of Mabl, testRigor, LambdaTest, BrowserStack, and Sauce Labs.

---

## Competitive Intelligence Summary

| Feature Category | Mabl | testRigor | LambdaTest/BrowserStack | Sauce Labs |
|---|---|---|---|---|
| Dashboard Focus | Release Health & Coverage | Execution Efficiency | Operational Throughput | AI Failure Patterns |
| Suite Organization | Plan-Based Labels | Parent/Child Inheritance | Build & Project Tagging | Team & Application Silos |
| Execution Logging | Speed Index & DOM Snapshots | Plain English Step Logs | Command & Network Logs | Conversational Summaries |
| Environment Mgmt | Integrated Environment Picker | Variable Override Hierarchy | SDK/Capability Snippets | Data Noise Reduction |
| Visual Testing | Automatic Baseline Sync | AI Visual Validation | SmartUI (AI Diffing) | Perceptual Comparison |

---

## Priority 1: Test Execution History & Diagnostics (`/runs`)

### Layout
- **Master-Detail / Split-pane**: Left = filterable run list, Right = detail view
- Each session shows: device, OS, build name, duration

### Detail View (per run)
- **Synchronized Video Playback** — scrub to exact failure moment
- **Command Log Timeline** — vertical list of steps; clicking a step jumps video + highlights log
- **Integrated Log Suite** (tabs):
  - Console logs
  - Network (HAR) logs — highlight 4xx/5xx
  - Appium logs
- **Artifact Repository** — download raw logs, screenshots, video

### Filters
- Status: Pass | Fail | Error | Skipped
- Date range
- Tags/labels
- Environment/branch

### AI Triage Layer
At top of detail view: AI-generated summary categorizing failure as:
- Known Flaky Test
- Infrastructure Error
- Application Bug
- Visual Regression

---

## Priority 2: Cloud Execution Hub (`/cloud`)

### Device Picker
Filters for:
- Manufacturer & Model (Apple iPhone 15, etc.)
- OS & Version (iOS 17.2, Android 14)
- Resolution & Orientation

### Capability Snippet Generator
As user selects device, UI updates a JSON object:
```json
{
  "projectName": "Testara",
  "buildName": "Release-1.0",
  "deviceName": "iPhone 15 Pro",
  "osVersion": "17",
  "parallelsPerPlatform": 2
}
```

### App Management
- Drag-and-drop upload zone for `.ipa` / `.apk` / `.aab`
- List of previously uploaded apps with their URL/ID
- Real-time parallel usage indicator

### Parallelization
```
Total_Threads = Platforms × Parallels_Per_Platform
```
Visualize thread utilization in real-time.

### Cloud Connection
- Status badge (connected / not configured) — NO provider name shown
- "Validate Connection" button

---

## Priority 3: Executive Dashboard (`/dashboard`)

### KPI Scorecard
- Total Tests Executed
- Latest Pass Rate (%)
- Flakiness Rate (%)
- Infrastructure Health (cloud provider status)

### Charts
- Pass Rate Trend — 30-day line chart
- Execution Duration Trend — pipeline bloat detection
- Top Failing Tests — table with links to `/runs`

### Layout Hierarchy
1. **Top row**: Critical KPIs + high-priority alerts
2. **Middle**: Trend charts + month-over-month comparison
3. **Bottom**: Recent Runs table + New Failing Tests
4. **Sidebar/Header**: Global filters (date range, app, environment)

---

## Priority 4: Test Suite Orchestration (`/suites`)

### Suite CRUD
- List: name | test count | last status | "Run All" button
- Create: name, tags, test selection (multi-select), environment binding

### Parent/Child Inheritance (testRigor pattern)
- Suite can be a "Child" of a "Parent" suite
- Inherited tests/variables show "Inherited" badge
- Local override shows "Override" indicator

### Reusable Rules
- Rule = named sequence of steps (e.g., "Login as Admin")
- Parameter support: `sign in as "user" using "password"`
- Usage tracker: shows every test using the rule

---

## Priority 5: Settings (`/settings`)

### Tabs
| Tab | Components | Data |
|---|---|---|
| Cloud Configuration | Input fields, masked strings | Cloud API keys, app URLs |
| Environments | Editable table | Base URLs (dev/staging/prod) |
| Team & Security | User list, avatar badges | Permissions, RBAC |
| Integrations | Card toggles | Slack, Jira, GitHub webhooks |
| Global Variables | Key-value table | Project-wide constants & secrets |

### Security
- Keys masked by default, require explicit "Unlock" to view
- "Validate Connection" button (backend-to-backend call)

---

## Technical Architecture

### Stack
- **Next.js App Router** — hierarchical layouts, SSR/ISR
- **Tailwind CSS** — utility-first, `grid-cols-12` for adaptive layouts
- **SWR / React Query** — data fetching with cache + revalidation
- **WebSockets** — live log streaming during active cloud runs
- **Context API** — global state (environment, cloud config)
- **Supabase** — auth, DB (runs, suites, apps, users, cloud_config)

### Sidebar (adaptive)
- Collapses to icon-only on small viewports
- Items: Dashboard | Generate | Runs | Suites | Cloud | Settings

---

## UX Patterns

### Empty States
- `/runs` empty → illustration + "Run Your First Test" button
- Progressive disclosure: iOS selected → reveal "Upload IPA" options

### Visual Regression Tool (`/runs` detail)
Three viewing modes:
1. **Side-by-Side** — baseline vs. current
2. **Diff Overlay** — pixel-perfect highlight of changes
3. **Slider View** — draggable curtain for real-time comparison

"Ignore Areas" — define regions to skip (dynamic ads, timestamps)

### Smart Loading
- Skeleton screens for dashboards
- Optimistic updates for suite creation
- Immediate "Queued" entry in `/runs` on trigger (before device provisioned)

---

## Implementation Phases

### Phase 1 (MVP — current sprint)
- [ ] Updated sidebar
- [ ] Dashboard with mock data + basic stats
- [ ] Runs page with filter + expandable rows
- [ ] Cloud page with connection status + device selector
- [ ] Suites page (basic list)
- [ ] Settings cloud tab

### Phase 2
- [ ] Supabase auth (email + Google)
- [ ] Real runs history from DB
- [ ] Video playback in run detail
- [ ] AI triage summary

### Phase 3
- [ ] Trend charts (Chart.js or Recharts)
- [ ] Parent/child suite inheritance
- [ ] Reusable rules manager
- [ ] Visual regression diff viewer

### Phase 4
- [ ] WebSocket live logs
- [ ] Parallelization UI
- [ ] Team management + RBAC
- [ ] Integrations (Slack, Jira, GitHub)
