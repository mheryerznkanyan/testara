import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider font-label border transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-surface-high border-outline-variant/20 text-on-surface-variant',
        success: 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400',
        destructive: 'bg-rose-500/10 border-rose-500/25 text-rose-400',
        warning: 'bg-amber-500/10 border-amber-500/25 text-amber-400',
        blue: 'bg-primary/10 border-primary/20 text-primary',
        purple: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
        outline: 'bg-transparent border-outline-variant/40 text-on-surface-variant',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
