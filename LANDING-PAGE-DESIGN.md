# Testara Landing Page Design

**Using:** [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md)  
**Purpose:** Convert visitors → pilot sign-ups

---

## 📐 **Page Structure**

```
1. Hero Section
2. Problem Statement
3. How It Works (3 steps)
4. Features Grid (6 features)
5. Live Demo / Screenshot
6. Pricing / Pilot CTA
7. FAQ
8. Footer
```

---

## 🎬 **Section 1: Hero**

### Design
```
Height: 600px
Background: Purple gradient (top-to-bottom, #7C3AED → #4F46E5)
Text: White, center-aligned
```

### Content
```html
<section class="hero">
  <h1>Stop Writing XCUITests by Hand</h1>
  <p class="subtitle">
    Generate production-ready iOS UI tests from plain English in 30 seconds.
    Testara reads your actual Swift code—no hallucinations, no guessing.
  </p>
  
  <div class="cta-group">
    <button class="btn-primary-white">Join Free Pilot</button>
    <button class="btn-ghost-white">Watch Demo (2 min)</button>
  </div>
  
  <p class="trust-line">
    ✓ Free for 3 months  •  ✓ No credit card  •  ✓ 10 teams only
  </p>
</section>
```

**Visual Elements:**
- Animated code snippet floating (subtle)
- Quality score badge (A, 92/100) in corner
- Screenshot of generated test (partial, teaser)

---

## 💔 **Section 2: Problem Statement**

### Design
```
Background: White
Padding: 96px vertical
Text: Center-aligned, Dark Slate
```

### Content
```html
<section class="problem">
  <h2>iOS UI tests are expensive to write, brittle to maintain</h2>
  
  <div class="pain-points">
    <div class="pain-card">
      ❌ Hours spent writing boilerplate
    </div>
    <div class="pain-card">
      ❌ Tests break on every refactor
    </div>
    <div class="pain-card">
      ❌ Flaky tests slow down CI
    </div>
  </div>
  
  <p class="stat">
    Most iOS teams skip UI tests entirely. <br/>
    When something breaks in production, nobody saw it coming.
  </p>
</section>
```

---

## 🚀 **Section 3: How It Works**

### Design
```
Background: Light Gray (#F8FAFC)
Layout: 3 columns (desktop), stacked (mobile)
Numbering: Purple circles with white numbers
```

### Content
```
Step 1: Describe Your Test
━━━━━━━━━━━━━━━━━━━━━━
Icon: 💬 Pencil/Chat
Title: "Tell us what to test"
Body: Type in plain English: "test login with invalid password"

Step 2: We Read Your Code
━━━━━━━━━━━━━━━━━━━━━━
Icon: 🧠 Brain/Code
Title: "RAG finds real IDs"
Body: Scans your Swift files, extracts accessibility identifiers, understands screen flow

Step 3: Get Production Code
━━━━━━━━━━━━━━━━━━━━━━
Icon: ⚡ Lightning
Title: "Copy and run"
Body: Compilable XCUITest in 30 seconds. Video-recorded on simulator.
```

---

## ✨ **Section 4: Features Grid**

### Design
```
Background: White
Layout: 3x2 grid (desktop), 1 column (mobile)
Cards: Elevated, hover lift
```

### Features
```
1. 🧠 Code-Aware
   Reads your actual Swift source code to find real accessibility IDs

2. ⚡ 30-Second Tests
   Generate tests in seconds, not hours

3. 🎯 Works Out of the Box
   Supports SwiftUI and UIKit

4. 📹 Visual Proof
   Every test run is recorded on video

5. 🔄 AI-Enriched
   Vague descriptions → precise test specifications

6. 🗺️ Navigation Context
   Understands your app's screens and flow
```

---

## 🖼️ **Section 5: Live Demo / Screenshot**

### Design
```
Background: Purple gradient (subtle)
Layout: Screenshot with code side-by-side
```

### Content
```
Left Side: Input
┌─────────────────────────────────┐
│ You type:                       │
│ "test login"                    │
└─────────────────────────────────┘

Right Side: Output (code preview)
┌─────────────────────────────────┐
│ import XCTest                   │
│                                 │
│ final class LoginTests: ...     │
│   func testLogin() {            │
│     let app = XCUIApplication() │
│     ...                         │
└─────────────────────────────────┘

Quality Score: A (92/100) ⭐
```

**Interactive Element:**
- Click to see full generated code
- OR embed live widget (type → generate)

---

## 💰 **Section 6: Pricing / Pilot CTA**

### Design
```
Background: White
Layout: Center card (elevated, shadow)
```

### Content
```
┌────────────────────────────────────────┐
│  Pilot Program                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                        │
│  Free for 3 months                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ Unlimited test generation           │
│  ✓ Direct founder support              │
│  ✓ Priority feature requests           │
│  ✓ Your feedback shapes the product    │
│                                        │
│  Limited to 10 teams                   │
│                                        │
│  [Request Access →]                    │
│                                        │
│  After pilot: $100/mo per team         │
└────────────────────────────────────────┘
```

---

## ❓ **Section 7: FAQ**

### Design
```
Background: Light Gray
Layout: 2 columns (desktop), accordion (mobile)
```

### Questions
```
Q: Do I need to write accessibility IDs first?
A: Ideally yes, but Testara works with existing IDs. We'll show you where to add more.

Q: Does it work with SwiftUI and UIKit?
A: Yes, both are fully supported.

Q: How accurate are the generated tests?
A: 85%+ compile and run on first try. We score each test (A-F) so you know quality upfront.

Q: Can I customize the generated code?
A: Absolutely. Copy it to Xcode and edit as needed.

Q: What LLM does it use?
A: Claude Sonnet 3.5 (Anthropic) by default. OpenAI support coming soon.

Q: Is my code safe?
A: Yes. Self-hosted option available. Your code never leaves your machine.
```

---

## 📧 **Section 8: Footer**

### Design
```
Background: Dark Slate (#0F172A)
Text: Light Gray
Layout: 4 columns (desktop), stacked (mobile)
```

### Content
```
Column 1: Brand
━━━━━━━━━━━━━
⚡ Testara
AI-Powered iOS Test Generation

Column 2: Product
━━━━━━━━━━━━━
Features
Pricing
Documentation
Changelog

Column 3: Company
━━━━━━━━━━━━━
About
Blog
Twitter
GitHub

Column 4: Legal
━━━━━━━━━━━━━
Privacy Policy
Terms of Service
```

**Bottom Bar:**
```
© 2026 Testara. Built by Mher Yerznkanyan.
```

---

## 📱 **Mobile Responsive**

### Changes for Mobile (<640px)
- Hero: 400px height, larger text
- Features: 1 column, cards stack
- How It Works: Vertical timeline
- Demo: Screenshot only (no side-by-side)
- Pricing: Full-width card
- FAQ: Accordion (collapsed by default)

---

## 🎨 **Color Usage**

```
Hero: Purple gradient
Sections: Alternate White / Light Gray
CTAs: Electric Purple (#7C3AED)
Text: Dark Slate (#0F172A)
Accents: Quality badges (Green/Blue/Amber)
```

---

## ⚡ **Micro-Interactions**

1. **Button hover:** Lift + darken
2. **Card hover:** Shadow lift
3. **Scroll:** Fade-in sections
4. **CTA pulse:** Subtle glow animation
5. **Code preview:** Syntax highlight on load

---

## 🎯 **Conversion Optimization**

### Above the Fold
- Clear value prop: "Generate tests in 30 seconds"
- Trust signals: "Free pilot, no credit card"
- Strong CTA: "Join Free Pilot" (high contrast)

### Social Proof (Add Later)
- Testimonials from pilot users
- Logos of companies using it
- GitHub stars count

### Multiple CTAs
- Hero: Primary CTA
- After features: Secondary CTA
- After demo: Tertiary CTA
- Sticky header: "Join Pilot" always visible

---

## 📊 **Metrics to Track**

```
- Conversion rate (visitor → pilot sign-up)
- Scroll depth (how far down the page)
- CTA click rate
- Demo watch rate
- Time on page
```

---

**Next Steps:**
1. Build this landing page (HTML/CSS)
2. Build app UI (React) using same design system
3. Deploy both
4. A/B test CTAs and messaging
