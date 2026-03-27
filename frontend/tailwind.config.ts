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
      /* ── Kinetic Vault Color Architecture ─────────────────── */
      colors: {
        // Surface hierarchy (tonal layering)
        'void':                '#000000',
        background:            '#0e0e0e',
        foreground:            '#ffffff',
        surface: {
          DEFAULT:             '#0e0e0e',
          low:                 '#131313',
          container:           '#191919',
          high:                '#1f1f1f',
          highest:             '#262626',
          bright:              '#2c2c2c',
        },

        // Primary accent — cyan
        primary: {
          DEFAULT:             '#5BC4D6',
          dim:                 '#4AABB8',
          container:           '#3D9DAD',
          foreground:          '#0A3A42',
        },

        // Secondary
        secondary: {
          DEFAULT:             '#e5e2e1',
          dim:                 '#d6d4d3',
          container:           '#474746',
          foreground:          '#525151',
        },

        // Outline / borders
        outline: {
          DEFAULT:             '#757575',
          variant:             '#484848',
        },

        // On-surface variants
        'on-surface':          '#ffffff',
        'on-surface-variant':  '#ababab',

        // Error / destructive
        error: {
          DEFAULT:             '#ff716c',
          dim:                 '#d7383b',
          container:           '#9f0519',
        },

        // Semantic aliases
        muted:                 '#191919',
        'muted-foreground':    '#ababab',
        border:                'rgba(255,255,255,0.1)',
        input:                 '#262626',
        ring:                  '#5BC4D6',

        // Card
        card: {
          DEFAULT:             '#191919',
          foreground:          '#ffffff',
        },

        // Popover
        popover: {
          DEFAULT:             '#191919',
          foreground:          '#ffffff',
        },

        // Destructive
        destructive: {
          DEFAULT:             '#ff716c',
          foreground:          '#ffffff',
        },

        // Sidebar
        sidebar: {
          DEFAULT:             'rgba(9,9,11,0.8)',
          foreground:          '#ffffff',
          border:              'rgba(63,63,70,0.5)',
          accent:              'rgba(91,196,214,0.1)',
          'accent-foreground': '#5BC4D6',
        },

        // Accent
        accent: {
          DEFAULT:             '#191919',
          foreground:          '#ffffff',
        },
      },

      /* ── Typography ──────────────────────────────────────── */
      fontFamily: {
        sans:      ['var(--font-inter)', 'Inter', 'SF Pro Display', '-apple-system', 'sans-serif'],
        mono:      ['var(--font-mono)', 'JetBrains Mono', 'SF Mono', 'Menlo', 'monospace'],
        label:     ['var(--font-label)', 'Space Grotesk', 'sans-serif'],
        headline:  ['var(--font-inter)', 'Inter', 'SF Pro Display', 'sans-serif'],
      },

      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },

      letterSpacing: {
        tighter:  '-0.04em',
        tight:    '-0.02em',
        snug:     '-0.01em',
        widest:   '0.1em',
      },

      /* ── Border Radius ───────────────────────────────────── */
      borderRadius: {
        DEFAULT:  '0.125rem',
        lg:       '0.5rem',
        xl:       '0.75rem',
        '2xl':    '1rem',
        '4xl':    '2rem',
      },

      /* ── Shadows (Luminous Occlusion) ────────────────────── */
      boxShadow: {
        'glow-cyan':    '0 0 15px rgba(91,196,214,0.4)',
        'glow-cyan-sm': '0 0 8px rgba(91,196,214,0.6)',
        'glow-emerald': '0 0 8px rgba(52,211,153,0.6)',
        'glow-rose':    '0 0 8px rgba(251,113,133,0.6)',
        'glow-amber':   '0 0 8px rgba(251,191,36,0.6)',
        'luminous':     '0 0 40px rgba(91,196,214,0.06)',
        'card':         '0 4px 24px rgba(0,0,0,0.3)',
        'inner-highlight': 'inset 0 1px 0 rgba(255,255,255,0.06)',
      },

      /* ── Backdrop Blur ───────────────────────────────────── */
      backdropBlur: {
        xs:   '2px',
        '2xl': '40px',
        '3xl': '64px',
      },

      /* ── Animations ──────────────────────────────────────── */
      animation: {
        'fade-in':       'fadeIn 0.3s ease-out both',
        'fade-in-up':    'fadeInUp 0.4s cubic-bezier(0.16,1,0.3,1) both',
        'slide-up':      'slideUp 0.35s cubic-bezier(0.16,1,0.3,1) both',
        'glow-pulse':    'glowPulse 3s ease-in-out infinite',
        'pulse-slow':    'pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float':         'float 6s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        fadeInUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(24px) scale(0.97)' },
          to:   { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        glowPulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-20px)' },
        },
      },

      transitionTimingFunction: {
        'kinetic': 'cubic-bezier(0.16, 1, 0.3, 1)',
      },
    },
  },
  plugins: [],
}

export default config
