'use client'

import Link from 'next/link'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import {
  BarChart3,
  CheckCircle,
  XCircle,
  Timer,
  Zap,
  Smartphone,
  ArrowUpRight,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import type { RunStatus } from '@/types'
import { useRunStats, useRecentRuns, formatRelativeTime } from '@/lib/hooks'

// --- Mock chart data ---
const passRateTrendData = [
  { date: '01 Oct', rate: 78 },
  { date: '02 Oct', rate: 82 },
  { date: '04 Oct', rate: 75 },
  { date: '05 Oct', rate: 88 },
  { date: '07 Oct', rate: 85 },
  { date: '08 Oct', rate: 91 },
  { date: '09 Oct', rate: 87 },
  { date: '10 Oct', rate: 93 },
  { date: '11 Oct', rate: 89 },
  { date: '12 Oct', rate: 95 },
  { date: '13 Oct', rate: 90 },
  { date: '14 Oct', rate: 92 },
]

const durationTrendData = [
  { day: 'M', duration: 12.4 },
  { day: 'T', duration: 15.1 },
  { day: 'W', duration: 11.2 },
  { day: 'T2', duration: 18.3 },
  { day: 'F', duration: 9.1 },
  { day: 'S', duration: 16.2 },
  { day: 'S2', duration: 13.1 },
  { day: 'M2', duration: 14.3 },
  { day: 'T3', duration: 10.1 },
  { day: 'W2', duration: 17.2 },
  { day: 'T4', duration: 19.1 },
  { day: 'F2', duration: 8.1 },
]

// --- Custom chart tooltip ---
function ChartTooltip({
  active,
  payload,
  label,
  valueSuffix = '',
}: {
  active?: boolean
  payload?: Array<{ value: number }>
  label?: string
  valueSuffix?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card px-3 py-2">
      <p className="text-[10px] text-zinc-500 font-label uppercase tracking-widest mb-1">{label}</p>
      <p className="text-sm font-bold font-mono text-white">
        {payload[0].value}
        {valueSuffix}
      </p>
    </div>
  )
}

export default function DashboardPage() {
  const { stats: liveStats, loading: statsLoading } = useRunStats()
  const { runs: recentRuns, loading: runsLoading } = useRecentRuns(6)

  const statusMap: Record<string, RunStatus> = {
    passed: 'Passed',
    failed: 'Failed',
    running: 'Running',
    queued: 'Running',
  }

  const total = statsLoading ? 0 : liveStats.total
  const passed = statsLoading ? 0 : liveStats.passed
  const failed = statsLoading ? 0 : liveStats.failed
  const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : '0'
  const failRate = total > 0 ? ((failed / total) * 100).toFixed(1) : '0'

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1400px] mx-auto p-8 space-y-10">
        {/* Hero Header */}
        <PageHeader
          title="Systems Health"
          description="Global Overview"
          action={
            <Link href="/">
              <Button className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                RUN NEW SUITE
              </Button>
            </Link>
          }
        />

        {/* ── Stat Cards Grid ── */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Total Tests */}
          <div className="glass-card p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <BarChart3 className="h-16 w-16" />
            </div>
            <div className="relative z-10">
              <span className="text-zinc-500 font-label text-xs uppercase tracking-widest">Total Tests Run</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-bold font-mono">
                  {statsLoading ? '—' : total.toLocaleString()}
                </span>
                <Badge variant="blue">+12%</Badge>
              </div>
              <div className="mt-4 h-1 w-full bg-surface-high rounded-full overflow-hidden">
                <div className="h-full bg-primary w-2/3 shadow-glow-cyan-sm" />
              </div>
            </div>
          </div>

          {/* Passed */}
          <div className="glass-card p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <CheckCircle className="h-16 w-16 text-emerald-400" />
            </div>
            <div className="relative z-10">
              <span className="text-zinc-500 font-label text-xs uppercase tracking-widest">Passed</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-bold font-mono">
                  {statsLoading ? '—' : passed.toLocaleString()}
                </span>
                <Badge variant="success">{passRate}%</Badge>
              </div>
              <div className="mt-4 h-1 w-full bg-surface-high rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-400 shadow-glow-emerald"
                  style={{ width: `${passRate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Failed */}
          <div className="glass-card p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <XCircle className="h-16 w-16 text-rose-400" />
            </div>
            <div className="relative z-10">
              <span className="text-zinc-500 font-label text-xs uppercase tracking-widest">Failed</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-bold font-mono">
                  {statsLoading ? '—' : failed.toLocaleString()}
                </span>
                <Badge variant="destructive">{failRate}%</Badge>
              </div>
              <div className="mt-4 h-1 w-full bg-surface-high rounded-full overflow-hidden">
                <div
                  className="h-full bg-rose-400 shadow-glow-rose"
                  style={{ width: `${failRate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Avg Duration */}
          <div className="glass-card p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Timer className="h-16 w-16 text-amber-400" />
            </div>
            <div className="relative z-10">
              <span className="text-zinc-500 font-label text-xs uppercase tracking-widest">Avg Duration</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-bold font-mono">12.4s</span>
                <Badge variant="warning">-0.8s</Badge>
              </div>
              <div className="mt-4 flex gap-1">
                <div className="h-1 flex-1 bg-amber-400 rounded-full" />
                <div className="h-1 flex-1 bg-amber-400/50 rounded-full" />
                <div className="h-1 flex-1 bg-amber-400/30 rounded-full" />
              </div>
            </div>
          </div>
        </section>

        {/* ── Charts Section ── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pass Rate Trend */}
          <div className="glass-card p-8">
            <div className="flex justify-between items-center mb-10">
              <div>
                <h3 className="text-lg font-bold font-headline">Pass Rate Trend</h3>
                <p className="text-zinc-500 text-xs font-label uppercase tracking-widest mt-1">14-Day Velocity</p>
              </div>
              <div className="flex gap-2 items-center">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-[10px] font-mono text-zinc-400">STABILITY INDEX</span>
              </div>
            </div>
            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={passRateTrendData}>
                  <defs>
                    <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#5BC4D6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#5BC4D6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: '#525252', fontFamily: 'JetBrains Mono, monospace' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[60, 100]}
                    tick={{ fontSize: 10, fill: '#525252', fontFamily: 'JetBrains Mono, monospace' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Tooltip content={<ChartTooltip valueSuffix="%" />} />
                  <Area
                    type="monotone"
                    dataKey="rate"
                    stroke="#5BC4D6"
                    strokeWidth={2}
                    fill="url(#cyanGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Avg Duration */}
          <div className="glass-card p-8">
            <div className="flex justify-between items-center mb-10">
              <div>
                <h3 className="text-lg font-bold font-headline">Avg Duration</h3>
                <p className="text-zinc-500 text-xs font-label uppercase tracking-widest mt-1">Resource Efficiency</p>
              </div>
              <span className="text-[10px] font-mono text-primary bg-primary/10 px-2 py-1 rounded">AVG 12.4s</span>
            </div>
            <div className="h-[240px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={durationTrendData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.05)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 10, fill: '#525252', fontFamily: 'JetBrains Mono, monospace' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: '#525252', fontFamily: 'JetBrains Mono, monospace' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v: number) => `${v}s`}
                  />
                  <Tooltip content={<ChartTooltip valueSuffix="s" />} />
                  <Bar
                    dataKey="duration"
                    fill="rgba(91,196,214,0.2)"
                    radius={[4, 4, 0, 0]}
                    activeBar={{ fill: 'rgba(91,196,214,0.5)' }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        {/* ── Recent Activity Table ── */}
        <section className="glass-card overflow-hidden">
          <div className="p-6 border-b border-white/5 flex justify-between items-center">
            <div>
              <h3 className="text-lg font-bold font-headline">Recent Intelligence Activity</h3>
              <p className="text-zinc-500 text-xs font-label uppercase tracking-widest mt-1">Live streaming system logs</p>
            </div>
            <Link href="/runs" className="text-xs text-primary font-bold hover:underline uppercase tracking-widest font-label">
              View All Runs
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-high/30">
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Status</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Test Name</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Device</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Duration</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-sm">
                {runsLoading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-zinc-500 font-label text-xs uppercase tracking-widest">
                      Loading runs...
                    </td>
                  </tr>
                ) : recentRuns.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-zinc-500 font-label text-xs uppercase tracking-widest">
                      No test runs yet. Generate and run your first test!
                    </td>
                  </tr>
                ) : (
                  recentRuns.map((run) => {
                    const status = statusMap[run.status] || 'Running'
                    return (
                      <tr key={run.id} className="hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4">
                          <StatusBadge status={status} />
                        </td>
                        <td className="px-6 py-4 font-semibold text-white font-sans">{run.test_name}</td>
                        <td className="px-6 py-4 text-zinc-400 flex items-center gap-2">
                          <Smartphone className="h-4 w-4" />
                          {run.device || '—'}
                        </td>
                        <td className="px-6 py-4 text-zinc-400">
                          {run.duration ? `${run.duration}s` : '—'}
                        </td>
                        <td className="px-6 py-4 text-zinc-500 text-right text-xs uppercase">
                          {formatRelativeTime(run.created_at)}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Bottom spacer for mobile nav */}
        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
