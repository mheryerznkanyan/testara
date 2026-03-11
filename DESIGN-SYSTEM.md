# Testara Design System

**Version:** 1.0  
**Brand:** Testara — AI-Powered iOS Test Generation

---

## 🎨 **Brand Identity**

### Personality
- **Professional** yet **approachable**
- **Technical** but not intimidating
- **Fast** and **efficient**
- **Trustworthy** and **reliable**

### Voice & Tone
- Clear, concise, direct
- Avoid marketing fluff
- Emphasize speed and intelligence
- Show don't tell (demos over descriptions)

---

## 🌈 **Color Palette**

### Primary Colors
```
Electric Purple (Primary)
- Hex: #7C3AED
- RGB: 124, 58, 237
- Use: CTAs, links, accent highlights

Deep Indigo (Secondary)
- Hex: #4F46E5
- RGB: 79, 70, 229
- Use: Headers, secondary buttons

Violet Gradient
- From: #7C3AED
- To: #4F46E5
- Use: Hero sections, cards
```

### Neutral Colors
```
Dark Slate (Text)
- Hex: #0F172A
- RGB: 15, 23, 42
- Use: Body text, headers

Medium Gray (Muted)
- Hex: #64748B
- RGB: 100, 116, 139
- Use: Secondary text, captions

Light Gray (Borders)
- Hex: #E2E8F0
- RGB: 226, 232, 240
- Use: Dividers, borders

Off-White (Background)
- Hex: #F8FAFC
- RGB: 248, 250, 252
- Use: Page backgrounds
```

### Semantic Colors
```
Success (Green)
- Hex: #10B981
- Use: Test passed, success states

Warning (Amber)
- Hex: #F59E0B
- Use: Warnings, caution states

Error (Red)
- Hex: #EF4444
- Use: Test failed, errors

Info (Blue)
- Hex: #3B82F6
- Use: Info messages, tips
```

### Quality Score Colors
```
Grade A: #10B981 (Emerald)
Grade B: #3B82F6 (Blue)
Grade C: #F59E0B (Amber)
Grade D: #F97316 (Orange)
Grade F: #EF4444 (Red)
```

---

## ✏️ **Typography**

### Font Families
```
Headings: Inter (sans-serif)
- Weights: 600 (Semibold), 700 (Bold), 800 (Extrabold)
- Use: H1-H6, buttons, nav

Body: Inter (sans-serif)
- Weights: 400 (Regular), 500 (Medium)
- Use: Paragraphs, captions

Code: JetBrains Mono (monospace)
- Weight: 400, 500
- Use: Code blocks, Swift code, identifiers
```

### Type Scale
```
Hero (H1):    48px / 3rem     Bold (700)
Heading (H2): 36px / 2.25rem  Bold (700)
Subhead (H3): 24px / 1.5rem   Semibold (600)
Large (H4):   20px / 1.25rem  Semibold (600)
Body:         16px / 1rem     Regular (400)
Small:        14px / 0.875rem Regular (400)
Caption:      12px / 0.75rem  Regular (400)
```

### Line Heights
```
Tight:   1.2  (headings)
Normal:  1.5  (body)
Relaxed: 1.75 (large paragraphs)
```

---

## 📏 **Spacing System**

**Base unit:** 4px (0.25rem)

```
xs:  4px   (0.25rem)
sm:  8px   (0.5rem)
md:  16px  (1rem)
lg:  24px  (1.5rem)
xl:  32px  (2rem)
2xl: 48px  (3rem)
3xl: 64px  (4rem)
4xl: 96px  (6rem)
```

**Usage:**
- Component padding: md (16px)
- Section spacing: 2xl (48px)
- Container max-width: 1280px

---

## 🧱 **Components**

### Buttons

**Primary Button**
```
Background: Electric Purple (#7C3AED)
Text: White
Padding: 12px 24px (md lg)
Border-radius: 8px
Font: Inter Semibold 16px
Hover: Darken 10%
Shadow: 0 4px 12px rgba(124, 58, 237, 0.25)
```

**Secondary Button**
```
Background: Transparent
Border: 2px solid Electric Purple
Text: Electric Purple
Padding: 12px 24px
Border-radius: 8px
Hover: Background Purple with 10% opacity
```

**Ghost Button**
```
Background: Transparent
Text: Dark Slate
Padding: 12px 24px
Hover: Light Gray background
```

### Cards
```
Background: White
Border: 1px solid Light Gray (#E2E8F0)
Border-radius: 12px
Padding: 24px (lg)
Shadow: 0 1px 3px rgba(0, 0, 0, 0.05)
Hover: Shadow lift (0 4px 12px rgba(0, 0, 0, 0.1))
```

### Badges
```
Quality A: Green background, white text
Quality B: Blue background, white text
Quality C: Amber background, white text
Quality D: Orange background, white text
Quality F: Red background, white text

Border-radius: 9999px (pill shape)
Padding: 4px 12px (xs md)
Font: Inter Medium 14px
```

### Input Fields
```
Background: White
Border: 1px solid Light Gray
Border-radius: 8px
Padding: 12px 16px
Focus: Border Electric Purple, shadow 0 0 0 3px rgba(124, 58, 237, 0.1)
Font: Inter Regular 16px
```

### Code Editor (Monaco)
```
Theme: VS Code Light (day) / VS Code Dark (night)
Font: JetBrains Mono 14px
Line height: 1.5
Border-radius: 12px
Background: #1E1E1E (dark) / #FFFFFF (light)
```

---

## 🖼️ **Layout Patterns**

### Hero Section (Landing Page)
```
Height: 600px minimum
Background: Purple gradient (top to bottom)
Text: White
Center-aligned
CTA button: White background, Purple text
Padding: 4xl vertical, 2xl horizontal
```

### Feature Grid
```
3 columns on desktop
1 column on mobile
Gap: 2xl (48px)
Each feature:
  - Icon (48px, Purple)
  - Heading (H3, Dark Slate)
  - Description (Body, Medium Gray)
  - Card background
```

### App Layout
```
Sidebar: 280px width, Light Gray background
Main: Flex-grow, White background
Header: 64px height, border-bottom
Content padding: 2xl (48px)
```

---

## 🎬 **Animations**

### Transitions
```
Default: all 0.2s ease
Button hover: transform 0.15s ease
Card hover: shadow 0.3s ease
```

### Entrance Animations
```
Fade in: opacity 0 → 1, 0.4s
Slide up: translateY(20px) → 0, 0.5s
```

---

## 📱 **Responsive Breakpoints**

```
Mobile:  < 640px
Tablet:  640px - 1024px
Desktop: > 1024px
```

**Rules:**
- Mobile: Single column, stack everything
- Tablet: 2 columns for features
- Desktop: 3+ columns, sidebar layouts

---

## 🌙 **Dark Mode**

### Color Adjustments
```
Background: #0F172A (Dark Slate)
Surface: #1E293B (Lighter Slate)
Text: #F8FAFC (Off-White)
Muted: #94A3B8 (Light Gray)
Borders: #334155 (Medium Slate)
```

**Toggle:** Moon/Sun icon in header

---

## ✅ **Usage Examples**

### Landing Page Hero
```html
<section class="bg-gradient-purple h-[600px] flex items-center justify-center">
  <div class="max-w-4xl text-center text-white px-8">
    <h1 class="text-5xl font-bold mb-6">
      AI-Powered iOS Test Generation
    </h1>
    <p class="text-xl mb-8 text-purple-100">
      Generate production-ready XCUITest code from plain English in 30 seconds
    </p>
    <button class="bg-white text-purple-600 px-8 py-4 rounded-lg font-semibold shadow-lg hover:shadow-xl">
      Start Free Trial
    </button>
  </div>
</section>
```

### App Header
```html
<header class="h-16 border-b border-gray-200 flex items-center justify-between px-6">
  <div class="flex items-center gap-2">
    <span class="text-2xl">⚡</span>
    <span class="font-bold text-xl">Testara</span>
  </div>
  <div class="flex items-center gap-4">
    <button class="btn-ghost">Docs</button>
    <button class="btn-secondary">Upgrade</button>
    <div class="w-8 h-8 bg-purple-600 rounded-full"></div>
  </div>
</header>
```

---

## 🎯 **Design Principles**

1. **Clarity over cleverness** — Every element has a clear purpose
2. **Speed over perfection** — Fast load times, instant feedback
3. **Consistency breeds trust** — Same patterns everywhere
4. **Progressive disclosure** — Show advanced features when needed
5. **Mobile-first** — Works perfectly on all devices

---

## 📦 **Component Library (Tailwind)**

All components use Tailwind CSS classes for consistency:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'purple': {
          primary: '#7C3AED',
          secondary: '#4F46E5',
        },
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
}
```

---

**This design system ensures:**
- ✅ Landing page + app look cohesive
- ✅ Easy to maintain and extend
- ✅ Professional, modern aesthetic
- ✅ Fast to implement (Tailwind CSS)
