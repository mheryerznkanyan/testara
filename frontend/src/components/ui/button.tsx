import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-bold transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-void disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground hover:shadow-glow-cyan active:scale-[0.98]',
        destructive:
          'bg-error/10 text-error border border-error/25 hover:bg-error/20',
        outline:
          'border border-outline-variant/20 bg-transparent hover:bg-surface-highest hover:text-white text-on-surface-variant',
        secondary:
          'bg-surface-container text-white border border-outline-variant/20 hover:bg-surface-high',
        ghost:
          'text-on-surface-variant hover:bg-white/5 hover:text-white',
        link: 'text-primary underline-offset-4 hover:underline',
        success:
          'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 active:bg-emerald-600',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-lg px-3 text-xs',
        lg: 'h-11 rounded-xl px-8 text-base',
        icon: 'h-9 w-9',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
