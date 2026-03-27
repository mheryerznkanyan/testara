import { Badge } from '@/components/ui/badge'
import type { RunStatus, SuiteStatus } from '@/types'

const statusVariantMap: Record<string, 'success' | 'destructive' | 'warning' | 'default'> = {
  Passed: 'success',
  Failed: 'destructive',
  Running: 'warning',
  'Not Run': 'default',
}

export function StatusBadge({ status }: { status: RunStatus | SuiteStatus }) {
  return (
    <Badge variant={statusVariantMap[status] || 'default'}>
      {status === 'Running' && (
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
      )}
      {status === 'Passed' && (
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
      )}
      {status === 'Failed' && (
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
      )}
      {status}
    </Badge>
  )
}
