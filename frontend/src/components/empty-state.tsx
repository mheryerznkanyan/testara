import React from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="text-zinc-700 mb-4">{icon}</div>
      <p className="text-sm font-medium text-on-surface-variant mb-1 font-label uppercase tracking-widest">{title}</p>
      {description && (
        <p className="text-xs text-zinc-600 max-w-sm mb-4">{description}</p>
      )}
      {action}
    </div>
  )
}
