'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import { EmptyState } from '@/components/empty-state'
import {
  Play,
  ChevronRight,
  AlertTriangle,
  RotateCcw,
  Search,
  FileText,
  Image,
} from 'lucide-react'
import { toast } from 'sonner'
import { useTestRuns, useSuites, formatRelativeTime, type TestRun } from '@/lib/hooks'
import { useSearchParams } from 'next/navigation'

type FilterTab = 'all' | 'passed' | 'failed' | 'running'

function mapStatus(s: string): 'Passed' | 'Failed' | 'Running' {
  if (s === 'passed') return 'Passed'
  if (s === 'failed') return 'Failed'
  return 'Running'
}

export default function RunsPage() {
  const searchParams = useSearchParams()
  const initialSuiteId = searchParams.get('suite_id') || ''

  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [expandedRow, setExpandedRow] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [suiteFilter, setSuiteFilter] = useState(initialSuiteId)

  const statusFilter = activeTab === 'all' ? undefined : activeTab as 'passed' | 'failed' | 'running'
  const { runs, loading, refresh } = useTestRuns(statusFilter, suiteFilter || undefined)
  const { suites } = useSuites()

  const filteredRuns = runs.filter((r) => {
    if (searchQuery === '') return true
    return r.test_name.toLowerCase().includes(searchQuery.toLowerCase())
  })

  const tabCounts: Record<FilterTab, number | undefined> = {
    all: undefined,
    passed: undefined,
    failed: undefined,
    running: undefined,
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1400px] mx-auto p-8 space-y-6">
        <PageHeader
          title="Test Runs"
          description="All test executions across your suites"
        />

        {/* Filters row */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          {/* Status tabs */}
          <div className="flex gap-1 border-b border-white/5 pb-0">
            {(['all', 'passed', 'failed', 'running'] as FilterTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2.5 text-xs font-label uppercase tracking-widest transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === tab
                    ? 'text-primary border-primary'
                    : 'text-zinc-500 border-transparent hover:text-zinc-300'
                }`}
              >
                {tab === 'all' ? 'All' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {/* Suite filter */}
          <select
            value={suiteFilter}
            onChange={(e) => setSuiteFilter(e.target.value)}
            className="bg-surface-low border border-outline-variant/20 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-primary transition-all"
          >
            <option value="">All Suites</option>
            {suites.map((s) => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-600" />
          <input
            placeholder="Search by test name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-surface-low border border-outline-variant/20 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all font-label"
          />
        </div>

        {/* Table */}
        {loading ? (
          <div className="glass-card p-6 space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex gap-4 items-center">
                <Skeleton className="h-4 w-48 bg-surface-high" />
                <Skeleton className="h-4 w-24 bg-surface-high" />
                <Skeleton className="h-5 w-16 bg-surface-high rounded-full" />
                <Skeleton className="h-4 w-32 bg-surface-high" />
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            {filteredRuns.length > 0 ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-surface-high/30">
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Test Name</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden sm:table-cell">Suite</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Status</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden md:table-cell">Device</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden md:table-cell">Duration</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden lg:table-cell">Date</th>
                    <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Mode</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredRuns.map((run) => (
                    <React.Fragment key={run.id}>
                      <tr
                        className="hover:bg-white/5 transition-colors cursor-pointer"
                        onClick={() => setExpandedRow(expandedRow === run.id ? null : run.id)}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <ChevronRight className={`w-3.5 h-3.5 text-zinc-600 transition-transform ${expandedRow === run.id ? 'rotate-90' : ''}`} />
                            <span className="font-semibold text-white text-sm">{run.test_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 hidden sm:table-cell">
                          {run.suite_id ? (
                            <Link
                              href={`/suites/${run.suite_id}`}
                              onClick={(e) => e.stopPropagation()}
                              className="text-sm text-primary/80 hover:text-primary transition-colors"
                            >
                              {run.suite_name || 'View Suite'}
                            </Link>
                          ) : (
                            <span className="text-zinc-600 text-sm">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4"><StatusBadge status={mapStatus(run.status)} /></td>
                        <td className="px-6 py-4 text-zinc-400 text-sm hidden md:table-cell">{run.device || '—'}</td>
                        <td className="px-6 py-4 text-zinc-400 font-mono text-sm hidden md:table-cell">
                          {run.duration != null ? `${run.duration.toFixed(1)}s` : '—'}
                        </td>
                        <td className="px-6 py-4 text-zinc-500 text-xs uppercase hidden lg:table-cell">
                          {formatRelativeTime(run.created_at)}
                        </td>
                        <td className="px-6 py-4">
                          <Badge variant={run.execution_mode === 'cloud' ? 'blue' : 'default'} className="text-[10px]">
                            {run.execution_mode}
                          </Badge>
                        </td>
                      </tr>

                      {expandedRow === run.id && (
                        <tr>
                          <td colSpan={7} className="p-0">
                            <div className="m-4 glass-card p-5 space-y-4">
                              {run.logs && (
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <FileText className="w-4 h-4 text-zinc-500" />
                                    <h4 className="text-[10px] font-label text-zinc-500 uppercase tracking-widest">Execution Logs</h4>
                                  </div>
                                  <pre className="bg-surface-low border border-white/5 rounded-xl p-4 text-xs font-mono text-zinc-500 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                                    {run.logs}
                                  </pre>
                                </div>
                              )}
                              {run.error_message && (
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <AlertTriangle className="w-4 h-4 text-rose-400" />
                                    <h4 className="text-[10px] font-label text-rose-400 uppercase tracking-widest">Error</h4>
                                  </div>
                                  <div className="bg-rose-500/5 border border-rose-500/20 rounded-xl p-4 text-sm text-rose-300">
                                    {run.error_message}
                                  </div>
                                </div>
                              )}
                              {run.screenshot_url && (
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <Image className="w-4 h-4 text-zinc-500" />
                                    <h4 className="text-[10px] font-label text-zinc-500 uppercase tracking-widest">Screenshot</h4>
                                  </div>
                                  <div className="rounded-xl overflow-hidden ring-1 ring-rose-500/20 bg-black">
                                    <img
                                      src={run.screenshot_url}
                                      alt="Test screenshot"
                                      className="w-full h-auto object-contain max-h-[300px]"
                                    />
                                  </div>
                                </div>
                              )}
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                {[
                                  { label: 'Device', value: run.device || '—' },
                                  { label: 'OS', value: run.os_version || '—' },
                                  { label: 'Duration', value: run.duration != null ? `${run.duration.toFixed(2)}s` : '—' },
                                  { label: 'Mode', value: run.execution_mode },
                                ].map(({ label, value }) => (
                                  <div key={label} className="bg-surface-low rounded-xl px-3 py-2 border border-white/[0.04]">
                                    <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">{label}</p>
                                    <p className="text-sm text-white font-medium">{value}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            ) : (
              <EmptyState
                icon={<Search className="w-10 h-10" />}
                title={`No ${activeTab === 'all' ? '' : activeTab + ' '}runs found`}
                description={searchQuery ? `No results matching "${searchQuery}"` : 'Test runs will appear here after execution'}
              />
            )}
          </div>
        )}

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
