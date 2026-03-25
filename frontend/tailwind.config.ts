import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        muted: 'hsl(var(--muted))',
        'muted-foreground': 'hsl(var(--muted-foreground))',
        border: 'hsl(var(--border))',
        accent: 'hsl(var(--accent))',
        sidebar: {
          DEFAULT: 'hsl(var(--sidebar-background))',
          foreground: 'hsl(var(--sidebar-foreground))',
          border: 'hsl(var(--sidebar-border))',
          accent: 'hsl(var(--sidebar-accent))',
          'accent-foreground': 'hsl(var(--sidebar-accent-foreground))',
        },
        'glass-bg': 'hsl(var(--glass-bg))',
        'apple-blue': '#0071E3',
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        ring: 'hsl(var(--ring))',
        input: 'hsl(var(--input))',

        // Modern blues – Vercel / Linear inspired
        blue: {
          50:  '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8f',
          950: '#0f172a',
        },

        // Accent purples – Linear / Stripe inspired
        purple: {
          50:  '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
          950: '#3b0764',
        },

        // Indigo bridge between blue & purple
        indigo: {
          400: '#818cf8',
          500: '#6366f1',
          600: '#4f46e5',
        },

        // Semantic surface tokens (dark-first SaaS)
        surface: {
          0:   'hsl(var(--surface-0))',   // page bg
          1:   'hsl(var(--surface-1))',   // cards
          2:   'hsl(var(--surface-2))',   // raised elements
          3:   'hsl(var(--surface-3))',   // hover states
        },

        // Accent alias for quick usage
        brand: {
          DEFAULT: '#3b82f6',
          hover:   '#2563eb',
          muted:   '#1e40af',
          glow:    'rgba(59,130,246,0.35)',
        },
      },

      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Menlo', 'monospace'],
        display: ['Inter', 'SF Pro Display', 'sans-serif'],
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },

      letterSpacing: {
        tighter: '-0.04em',
        tight:   '-0.02em',
        snug:    '-0.01em',
      },

      // ── Shadows ──────────────────────────────────────────────
      boxShadow: {
        // Subtle depth for cards
        'card':   '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        'card-md':'0 4px 6px -1px rgba(0,0,0,0.2), 0 2px 4px -1px rgba(0,0,0,0.16)',
        'card-lg':'0 10px 15px -3px rgba(0,0,0,0.3), 0 4px 6px -2px rgba(0,0,0,0.15)',

        // Glow accents
        'glow-blue':   '0 0 20px rgba(59,130,246,0.35), 0 0 60px rgba(59,130,246,0.12)',
        'glow-purple': '0 0 20px rgba(168,85,247,0.35), 0 0 60px rgba(168,85,247,0.12)',
        'glow-indigo': '0 0 20px rgba(99,102,241,0.35), 0 0 60px rgba(99,102,241,0.12)',

        // Inset highlight – glass edge
        'inner-highlight': 'inset 0 1px 0 rgba(255,255,255,0.08)',

        // Focus ring
        'focus-ring': '0 0 0 3px rgba(59,130,246,0.4)',
      },

      // ── Animations ───────────────────────────────────────────
      animation: {
        // Existing
        'pulse-slow': 'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer':    'shimmer 1.5s infinite',
        'float':      'float 6s ease-in-out infinite',

        // Entrance
        'fade-in':       'fadeIn 0.3s ease-out both',
        'fade-in-up':    'fadeInUp 0.4s cubic-bezier(0.16,1,0.3,1) both',
        'fade-in-down':  'fadeInDown 0.4s cubic-bezier(0.16,1,0.3,1) both',
        'slide-in-left': 'slideInLeft 0.4s cubic-bezier(0.16,1,0.3,1) both',
        'slide-up':      'slideUp 0.35s cubic-bezier(0.16,1,0.3,1) both',

        // Attention
        'glow-pulse':    'glowPulse 3s ease-in-out infinite',
        'gradient-x':    'gradientX 4s ease infinite',

        // Micro-interactions
        'pop':           'pop 0.15s cubic-bezier(0.34,1.56,0.64,1)',
        'spin-slow':     'spin 3s linear infinite',
      },

      keyframes: {
        shimmer: {
          '0%':   { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(200%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-20px)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInDown: {
          from: { opacity: '0', transform: 'translateY(-16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          from: { opacity: '0', transform: 'translateX(-24px)' },
          to:   { opacity: '1', transform: 'translateX(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(24px) scale(0.97)' },
          to:   { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%':      { backgroundPosition: '100% 50%' },
        },
        pop: {
          '0%':   { transform: 'scale(0.95)' },
          '70%':  { transform: 'scale(1.04)' },
          '100%': { transform: 'scale(1)' },
        },
      },

      // ── Transitions ──────────────────────────────────────────
      transitionTimingFunction: {
        'spring':  'cubic-bezier(0.16, 1, 0.3, 1)',
        'bounce':  'cubic-bezier(0.34, 1.56, 0.64, 1)',
        'smooth':  'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        '50':  '50ms',
        '150': '150ms',
        '250': '250ms',
        '400': '400ms',
      },

      // ── Border radius ────────────────────────────────────────
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },

      // ── Backdrop blur ────────────────────────────────────────
      backdropBlur: {
        xs:  '2px',
        '2xl': '40px',
        '3xl': '64px',
      },

      // ── Background gradients (via bg-size + animation) ───────
      backgroundSize: {
        '200%': '200% 200%',
        '300%': '300% 300%',
      },
    },
  },
  plugins: [],
}

export default config
