import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        default:
          'bg-blue-500 text-white shadow-lg shadow-blue-500/20 hover:bg-blue-400 active:bg-blue-600',
        destructive:
          'bg-red-500/10 text-red-400 border border-red-500/25 hover:bg-red-500/20',
        outline:
          'border border-border bg-transparent hover:bg-surface-2 hover:text-foreground text-muted-foreground',
        secondary:
          'bg-surface-2 text-foreground border border-border hover:bg-surface-3',
        ghost:
          'text-muted-foreground hover:bg-surface-2 hover:text-foreground',
        link: 'text-blue-400 underline-offset-4 hover:underline',
        success:
          'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 active:bg-emerald-600',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-11 rounded-lg px-8 text-base',
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
