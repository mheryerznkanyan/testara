'use client'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import {
  ClipboardList,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
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

// --- Mock data ---

const passRateTrendData = [
  { date: 'Mar 12', rate: 82 },
  { date: 'Mar 13', rate: 85 },
  { date: 'Mar 14', rate: 79 },
  { date: 'Mar 15', rate: 88 },
  { date: 'Mar 16', rate: 91 },
  { date: 'Mar 17', rate: 87 },
  { date: 'Mar 18', rate: 93 },
  { date: 'Mar 19', rate: 90 },
  { date: 'Mar 20', rate: 95 },
  { date: 'Mar 21', rate: 92 },
  { date: 'Mar 22', rate: 89 },
  { date: 'Mar 23', rate: 94 },
  { date: 'Mar 24', rate: 97 },
  { date: 'Mar 25', rate: 96 },
]

const durationTrendData = [
  { date: 'Mar 12', duration: 14.2 },
  { date: 'Mar 13', duration: 12.8 },
  { date: 'Mar 14', duration: 16.1 },
  { date: 'Mar 15', duration: 11.5 },
  { date: 'Mar 16', duration: 9.7 },
  { date: 'Mar 17', duration: 13.4 },
  { date: 'Mar 18', duration: 10.2 },
  { date: 'Mar 19', duration: 8.9 },
  { date: 'Mar 20', duration: 7.6 },
  { date: 'Mar 21', duration: 11.3 },
  { date: 'Mar 22', duration: 15.8 },
  { date: 'Mar 23', duration: 9.1 },
  { date: 'Mar 24', duration: 6.4 },
  { date: 'Mar 25', duration: 8.2 },
]

interface TestRun {
  id: string
  testName: string
  suite: string
  status: RunStatus
  device: string
  duration: string
  date: string
}

const mockRuns: TestRun[] = [
  {
    id: '1',
    testName: 'Login with valid credentials',
    suite: 'Auth Suite',
    status: 'Passed',
    device: 'iPhone 15 Pro',
    duration: '12s',
    date: '2 hours ago',
  },
  {
    id: '2',
    testName: 'Add item to cart',
    suite: 'Checkout Suite',
    status: 'Passed',
    device: 'iPhone 14',
    duration: '8s',
    date: '2 hours ago',
  },
  {
    id: '3',
    testName: 'Payment with invalid card',
    suite: 'Checkout Suite',
    status: 'Failed',
    device: 'iPhone 15 Pro',
    duration: '5s',
    date: '3 hours ago',
  },
  {
    id: '4',
    testName: 'Profile photo upload',
    suite: 'Profile Suite',
    status: 'Running',
    device: 'iPhone 13',
    duration: '\u2014',
    date: 'Just now',
  },
  {
    id: '5',
    testName: 'Push notification opt-in',
    suite: 'Onboarding Suite',
    status: 'Passed',
    device: 'iPhone 14',
    duration: '6s',
    date: '5 hours ago',
  },
  {
    id: '6',
    testName: 'Search with empty query',
    suite: 'Search Suite',
    status: 'Failed',
    device: 'iPhone 15 Pro',
    duration: '3s',
    date: '6 hours ago',
  },
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
    <div className="rounded-lg border border-border bg-surface-1 px-3 py-2 shadow-lg">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-sm font-semibold text-foreground">
        {payload[0].value}
        {valueSuffix}
      </p>
    </div>
  )
}

// --- Stats ---

const stats = [
  {
    label: 'Total Tests',
    value: '1,284',
    trend: '+12% from last week',
    trendUp: true,
    icon: ClipboardList,
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-500/10',
  },
  {
    label: 'Passed',
    value: '1,147',
    trend: '+8% from last week',
    trendUp: true,
    icon: CheckCircle,
    iconColor: 'text-emerald-400',
    iconBg: 'bg-emerald-500/10',
  },
  {
    label: 'Failed',
    value: '94',
    trend: '-3% from last week',
    trendUp: false,
    icon: XCircle,
    iconColor: 'text-red-400',
    iconBg: 'bg-red-500/10',
  },
  {
    label: 'Avg Duration',
    value: '8.2s',
    trend: '-15% from last week',
    trendUp: false,
    icon: Clock,
    iconColor: 'text-amber-400',
    iconBg: 'bg-amber-500/10',
  },
]

// --- Page ---

export default function DashboardPage() {
  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-7xl mx-auto px-8 py-8">
        <PageHeader
          title="Dashboard"
          description="Overview of your test runs and results"
          action={
            <Button size="sm" variant="outline">
              <Activity className="w-4 h-4 mr-2" />
              View All Runs
            </Button>
          }
        />

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon
            return (
              <Card key={stat.label}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-muted-foreground font-medium">
                      {stat.label}
                    </span>
                    <div className={`rounded-lg p-2 ${stat.iconBg}`}>
                      <Icon className={`w-4 h-4 ${stat.iconColor}`} />
                    </div>
                  </div>
                  <div className="text-3xl font-bold tracking-tight text-foreground">
                    {stat.value}
                  </div>
                  <div className="flex items-center gap-1 mt-2">
                    {stat.label === 'Failed' ? (
                      // For "Failed", down is good (green) and up is bad (red)
                      stat.trendUp ? (
                        <TrendingUp className="w-3.5 h-3.5 text-red-400" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                      )
                    ) : stat.label === 'Avg Duration' ? (
                      // For "Avg Duration", down is good (green) and up is bad (red)
                      stat.trendUp ? (
                        <TrendingUp className="w-3.5 h-3.5 text-red-400" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5 text-emerald-400" />
                      )
                    ) : stat.trendUp ? (
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <TrendingDown className="w-3.5 h-3.5 text-red-400" />
                    )}
                    <span
                      className={`text-xs font-medium ${
                        stat.label === 'Failed' || stat.label === 'Avg Duration'
                          ? stat.trendUp
                            ? 'text-red-400'
                            : 'text-emerald-400'
                          : stat.trendUp
                            ? 'text-emerald-400'
                            : 'text-red-400'
                      }`}
                    >
                      {stat.trend}
                    </span>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
          {/* Pass Rate Trend */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Pass Rate Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={passRateTrendData}>
                    <defs>
                      <linearGradient id="passRateGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[60, 100]}
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v: number) => `${v}%`}
                    />
                    <Tooltip content={<ChartTooltip valueSuffix="%" />} />
                    <Area
                      type="monotone"
                      dataKey="rate"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      fill="url(#passRateGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Avg Duration */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Avg Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={durationTrendData}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="hsl(var(--border))"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(v: number) => `${v}s`}
                    />
                    <Tooltip content={<ChartTooltip valueSuffix="s" />} />
                    <Bar dataKey="duration" fill="#60a5fa" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Runs Table */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">Recent Runs</CardTitle>
              <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
                View all
                <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Test Name</TableHead>
                  <TableHead>Suite</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-medium">{run.testName}</TableCell>
                    <TableCell className="text-muted-foreground">{run.suite}</TableCell>
                    <TableCell>
                      <StatusBadge status={run.status} />
                    </TableCell>
                    <TableCell className="text-muted-foreground">{run.device}</TableCell>
                    <TableCell className="font-mono text-muted-foreground">
                      {run.duration}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{run.date}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
