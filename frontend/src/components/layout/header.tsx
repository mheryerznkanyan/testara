'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Search, Bell, Settings, Smartphone } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'

export function Header() {
  const { user } = useAuth()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const userInitial = user?.email?.[0]?.toUpperCase() || 'T'

  return (
    <header className="sticky top-0 z-50 glass-nav flex items-center justify-between px-6 h-16 w-full shadow-[0_0_15px_rgba(91,196,214,0.05)]">
      {/* Left: Logo */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2 md:hidden">
          <Smartphone className="h-5 w-5 text-primary" />
          <span className="text-lg font-bold tracking-tighter text-white uppercase font-headline">
            Testara AI
          </span>
        </Link>
      </div>

      {/* Right: Search + Actions */}
      <div className="flex items-center gap-6">
        {/* Search */}
        <div className="hidden lg:flex items-center bg-surface-low px-4 py-2 rounded-xl border border-outline-variant/20 focus-within:border-primary transition-all duration-300">
          <Search className="h-4 w-4 text-zinc-500" />
          <input
            className="bg-transparent border-none text-sm focus:ring-0 focus:outline-none text-white w-48 ml-2 font-label placeholder:text-zinc-600"
            placeholder="Quick search..."
            type="text"
          />
        </div>

        {/* Action Icons */}
        <div className="flex items-center gap-4">
          <button className="text-zinc-500 hover:text-primary transition-colors active:scale-95">
            <Bell className="h-5 w-5" />
          </button>
          <Link href="/settings" className="text-zinc-500 hover:text-primary transition-colors active:scale-95">
            <Settings className="h-5 w-5" />
          </Link>

          {/* Avatar */}
          {mounted && (
            <div className="w-8 h-8 rounded-full border border-primary/20 overflow-hidden flex items-center justify-center bg-primary/10 text-primary text-xs font-bold">
              {userInitial}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
