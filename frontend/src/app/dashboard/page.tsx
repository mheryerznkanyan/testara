'use client'

import { useState } from 'react'

type RunStatus = 'Passed' | 'Failed' | 'Running'

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
    duration: '—',
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

function StatusBadge({ status }: { status: RunStatus }) {
  const styles: Record<RunStatus, string> = {
    Passed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
    Failed: 'bg-red-500/15 text-red-400 border border-red-500/25',
    Running: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/25',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

export default function DashboardPage() {
  const totalTests = mockRuns.length
  const passed = mockRuns.filter((r) => r.status === 'Passed').length
  const failed = mockRuns.filter((r) => r.status === 'Failed').length
  const lastRun = mockRuns[0].date

  const stats = [
    {
      label: 'Total Tests',
      value: totalTests,
      color: 'text-foreground',
      icon: (
        <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
    },
    {
      label: 'Passed',
      value: passed,
      color: 'text-emerald-400',
      icon: (
        <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: 'Failed',
      value: failed,
      color: 'text-red-400',
      icon: (
        <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: 'Last Run',
      value: lastRun,
      color: 'text-foreground',
      icon: (
        <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ]

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-1">Dashboard</h1>
          <p className="text-muted text-sm">Overview of your test runs and results</p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-border bg-surface-1 p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-muted font-medium">{stat.label}</span>
                {stat.icon}
              </div>
              <div className={`text-2xl font-bold tracking-tight ${stat.color}`}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Recent Runs Table */}
        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <h2 className="text-base font-semibold">Recent Runs</h2>
            <span className="text-xs text-muted">{mockRuns.length} runs</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2/50">
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Test Name</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Suite</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Device</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Duration</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody>
                {mockRuns.map((run, idx) => (
                  <tr
                    key={run.id}
                    className={`border-b border-border last:border-0 hover:bg-surface-2/30 transition-colors ${
                      idx % 2 === 0 ? '' : 'bg-surface-0/50'
                    }`}
                  >
                    <td className="px-6 py-4 font-medium text-foreground">{run.testName}</td>
                    <td className="px-6 py-4 text-muted">{run.suite}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-6 py-4 text-muted">{run.device}</td>
                    <td className="px-6 py-4 text-muted font-mono">{run.duration}</td>
                    <td className="px-6 py-4 text-muted">{run.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
