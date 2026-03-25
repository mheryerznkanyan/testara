'use client'

import { useEffect, useState } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun, Search, Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function Header() {
  const { theme, setTheme } = useTheme()
  const [scrolled, setScrolled] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const main = document.querySelector('main')
    if (!main) return
    const handler = () => setScrolled(main.scrollTop > 10)
    main.addEventListener('scroll', handler, { passive: true })
    return () => main.removeEventListener('scroll', handler)
  }, [])

  return (
    <header
      className={cn(
        'sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/80 px-6 backdrop-blur-lg transition-shadow',
        scrolled ? 'border-border shadow-sm' : 'border-transparent'
      )}
    >
      {/* Search trigger */}
      <button
        className="flex h-8 flex-1 max-w-sm items-center gap-2 rounded-lg border border-border bg-surface-2/50 px-3 text-sm text-muted-foreground transition-colors hover:bg-surface-2"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="flex-1 text-left">Search...</span>
        <kbd className="hidden sm:inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground/50 border border-border">
          ⌘K
        </kbd>
      </button>

      <div className="flex-1" />

      {/* Right side actions */}
      <div className="flex items-center gap-1">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground">
          <Bell className="h-4 w-4" />
        </Button>

        {/* Theme toggle */}
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="h-8 w-8 text-muted-foreground"
          >
            {theme === 'dark' ? (
              <Moon className="h-4 w-4" />
            ) : (
              <Sun className="h-4 w-4" />
            )}
          </Button>
        )}

        {/* User avatar */}
        <button className="ml-1 flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white hover:bg-blue-500 transition-colors">
          M
        </button>
      </div>
    </header>
  )
}
