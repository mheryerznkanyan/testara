# Testara Landing Page

**Apple-inspired React landing page with smooth animations**

## Features

✨ **Animations:**
- Smooth scroll with Lenis
- Framer Motion entrance animations
- Typing effect for code demo
- Glass morphism hover effects
- Parallax gradient background
- Micro-interactions everywhere

🎨 **Design:**
- Apple-minimal aesthetic
- Dark theme (black/white + blue)
- Bento grid layout
- Responsive mobile-first

## Quick Start

```bash
cd landing
npm install
npm run dev
```

Open http://localhost:3000

## Tech Stack

- Next.js 14 (App Router)
- React 18
- Framer Motion (animations)
- Tailwind CSS (styling)
- TypeScript

## Project Structure

```
landing/
├── src/
│   ├── app/
│   │   ├── page.tsx          # Main landing page
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── Hero.tsx           # Hero section with animated gradient
│   │   ├── Features.tsx       # Bento grid with hover animations
│   │   ├── Demo.tsx           # Interactive code demo with typing
│   │   ├── HowItWorks.tsx     # Scroll-triggered steps
│   │   ├── Pricing.tsx        # Glass card with blur
│   │   └── Footer.tsx         # Minimal Apple-style footer
│   └── lib/
│       └── utils.ts           # Utility functions
├── tailwind.config.ts
└── package.json
```

## Key Animations

### Hero
- Fade in + slide up on load
- Ambient gradient background (slow pulse)
- Floating code preview

### Features
- Staggered fade-in on scroll
- Card hover: lift + glow
- Icon animations

### Code Demo
- Typing animation (realistic speed)
- Syntax highlighting fade-in
- Quality score reveal

### How It Works
- Sticky scroll with step reveals
- Number animations
- Line connections

## Deployment

### Vercel (Recommended)
```bash
vercel
```

### Docker
```bash
docker build -t testara-landing .
docker run -p 3000:3000 testara-landing
```

### Static Export
```bash
npm run build
# Output in .next/
```

---

Built with ❤️ for iOS developers
