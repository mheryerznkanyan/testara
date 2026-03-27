'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, Zap, Clock, User } from 'lucide-react'
import { cn } from '@/lib/utils'

const items = [
  { href: '/dashboard', label: 'HOME', icon: LayoutDashboard },
  { href: '/', label: 'GEN', icon: Zap, exact: true },
  { href: '/runs', label: 'RUNS', icon: Clock },
  { href: '/settings', label: 'ME', icon: User },
]

export function MobileNav() {
  const pathname = usePathname()

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-black/80 backdrop-blur-xl border-t border-white/10 flex justify-around items-center h-16 z-50">
      {items.map((item) => {
        const isActive = item.exact
          ? pathname === item.href
          : pathname.startsWith(item.href)
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-col items-center gap-1 transition-colors',
              isActive ? 'text-primary' : 'text-zinc-500'
            )}
          >
            <Icon className="h-5 w-5" />
            <span className="text-[10px] font-label">{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
