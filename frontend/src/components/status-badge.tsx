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
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
      )}
      {status}
    </Badge>
  )
}
