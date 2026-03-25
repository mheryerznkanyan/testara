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
  ChevronsLeft,
  ChevronsRight,
  TestTube,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface NavItem {
  href: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

interface NavGroup {
  title: string
  items: NavItem[]
}

const navGroups: NavGroup[] = [
  {
    title: 'General',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/', label: 'Generate', icon: Zap },
    ],
  },
  {
    title: 'Testing',
    items: [
      { href: '/runs', label: 'Test Runs', icon: Clock },
      { href: '/suites', label: 'Suites', icon: FolderOpen },
      { href: '/cloud', label: 'Cloud', icon: Cloud },
    ],
  },
  {
    title: 'System',
    items: [
      { href: '/settings', label: 'Settings', icon: Settings },
    ],
  },
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

  // Cmd+B / Ctrl+B shortcut
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

  if (!mounted) return <aside className="w-60 border-r border-sidebar-border bg-sidebar" />

  return (
    <aside
      className={cn(
        'group/sidebar flex flex-col border-r border-sidebar-border bg-sidebar transition-[width] duration-200 ease-in-out',
        collapsed ? 'w-[52px]' : 'w-60'
      )}
    >
      {/* ── Logo / Brand ── */}
      <div className={cn('flex h-14 items-center border-b border-sidebar-border', collapsed ? 'justify-center px-2' : 'px-4')}>
        <Link href="/" className="flex items-center gap-2.5 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white">
            <TestTube className="h-4 w-4" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-semibold leading-none">Testara</span>
              <span className="text-[10px] text-sidebar-foreground/50 leading-none mt-0.5">iOS Test Platform</span>
            </div>
          )}
        </Link>
      </div>

      {/* ── Navigation Groups ── */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-2 no-scrollbar">
        {navGroups.map((group, gi) => (
          <div key={group.title} className={cn(gi > 0 && 'mt-4')}>
            {/* Group title */}
            {!collapsed && (
              <div className="px-4 mb-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
                  {group.title}
                </span>
              </div>
            )}
            {collapsed && gi > 0 && (
              <div className="mx-2 my-2 h-px bg-sidebar-border" />
            )}

            {/* Items */}
            <div className="space-y-0.5 px-2">
              {group.items.map((item) => {
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
                      'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                      collapsed && 'justify-center px-0 py-2'
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                    {!collapsed && item.badge && (
                      <span className="ml-auto rounded-full bg-blue-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-blue-400">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* ── Collapse Toggle ── */}
      <div className="border-t border-sidebar-border p-2">
        <button
          onClick={toggleCollapse}
          className={cn(
            'flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium text-sidebar-foreground/50 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground transition-colors',
            collapsed && 'justify-center px-0'
          )}
        >
          {collapsed ? (
            <ChevronsRight className="h-4 w-4 shrink-0" />
          ) : (
            <>
              <ChevronsLeft className="h-4 w-4 shrink-0" />
              <span className="truncate">Collapse</span>
              <kbd className="ml-auto hidden lg:inline-flex items-center rounded px-1 py-0.5 text-[10px] font-mono text-sidebar-foreground/30 border border-sidebar-border">
                ⌘B
              </kbd>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
