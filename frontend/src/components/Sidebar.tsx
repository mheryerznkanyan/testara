'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect, useCallback } from 'react'
import {
  LayoutDashboard,
  Zap,
  Clock,
  FolderOpen,
  Cloud,
  Settings,
  Smartphone,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

const mainNav: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/', label: 'Generator', icon: Zap },
  { href: '/runs', label: 'Runs', icon: Clock },
  { href: '/suites', label: 'Suites', icon: FolderOpen },
  { href: '/cloud', label: 'Cloud Config', icon: Cloud },
]

const footerNav: NavItem[] = [
  { href: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const stored = localStorage.getItem('testara_sidebar_collapsed')
    if (stored === 'true') setCollapsed(true)
  }, [])

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev
      localStorage.setItem('testara_sidebar_collapsed', String(next))
      return next
    })
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
        e.preventDefault()
        toggleCollapse()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [toggleCollapse])

  if (!mounted) return <aside className="hidden md:flex w-64 glass-sidebar" />

  return (
    <aside
      className={cn(
        'hidden md:flex flex-col h-full glass-sidebar transition-[width] duration-200 ease-kinetic',
        collapsed ? 'w-[60px]' : 'w-64'
      )}
    >
      {/* ── Logo / Brand ── */}
      <div className={cn('px-6 py-6 mb-6', collapsed && 'px-3')}>
        <Link href="/dashboard" className="flex items-center gap-3 overflow-hidden">
          <div className="shrink-0 p-2 bg-primary/10 rounded-lg">
            <Smartphone className="h-4 w-4 text-primary" />
          </div>
          {!collapsed && (
            <div>
              <div className="text-white font-black text-sm uppercase tracking-wider font-headline">
                Testara AI
              </div>
              <div className="text-[10px] text-zinc-500 font-label tracking-widest">
                V-ALPHA 2.0
              </div>
            </div>
          )}
        </Link>
      </div>

      {/* ── Main Navigation ── */}
      <nav className="flex-1 space-y-1 px-3 overflow-y-auto no-scrollbar">
        {mainNav.map((item) => {
          const isActive =
            item.href === '/'
              ? pathname === '/'
              : pathname.startsWith(item.href)
          const Icon = item.icon

          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                'group flex items-center gap-3 px-4 py-2.5 rounded-r-lg text-xs uppercase tracking-widest font-label transition-all duration-300',
                isActive
                  ? 'bg-primary/10 text-primary border-r-2 border-primary'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5',
                collapsed && 'justify-center px-2 rounded-lg border-r-0',
                collapsed && isActive && 'border-r-0 border-b-2'
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0 group-hover:translate-x-0.5 transition-transform" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* ── Footer Navigation ── */}
      <div className="px-3 mt-auto pt-6 border-t border-white/5 pb-4 space-y-1">
        {footerNav.map((item) => {
          const isActive = pathname.startsWith(item.href)
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              className={cn(
                'group flex items-center gap-3 px-4 py-2.5 text-xs uppercase tracking-widest font-label transition-all duration-300',
                isActive
                  ? 'text-primary'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/5',
                collapsed && 'justify-center px-2'
              )}
            >
              <Icon className="h-[18px] w-[18px] shrink-0 group-hover:translate-x-0.5 transition-transform" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          )
        })}

        {/* Collapse toggle */}
        <button
          onClick={toggleCollapse}
          className={cn(
            'flex w-full items-center gap-3 px-4 py-2.5 text-xs uppercase tracking-widest font-label text-zinc-600 hover:text-zinc-400 transition-colors',
            collapsed && 'justify-center px-2'
          )}
        >
          {collapsed ? (
            <ChevronsRight className="h-[18px] w-[18px] shrink-0" />
          ) : (
            <>
              <ChevronsLeft className="h-[18px] w-[18px] shrink-0" />
              <span className="truncate">Collapse</span>
              <kbd className="ml-auto text-[10px] font-mono text-zinc-700">
                {'\u2318'}B
              </kbd>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
