import React from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  action?: React.ReactNode
}

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div className="flex items-end justify-between mb-10">
      <div>
        <h1 className="text-4xl font-extrabold font-headline tracking-tight mb-2">{title}</h1>
        {description && (
          <p className="text-on-surface-variant font-label text-sm uppercase tracking-widest">
            {description}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
