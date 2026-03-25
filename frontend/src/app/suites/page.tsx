'use client'

import { useState } from 'react'

type SuiteStatus = 'Passed' | 'Failed' | 'Running' | 'Not Run'

interface Suite {
  id: string
  name: string
  testCount: number
  lastStatus: SuiteStatus
  createdAt: string
  description: string
}

const mockSuites: Suite[] = [
  {
    id: '1',
    name: 'Auth Suite',
    testCount: 8,
    lastStatus: 'Passed',
    createdAt: 'Mar 20, 2024',
    description: 'Login, logout, biometric auth, session management',
  },
  {
    id: '2',
    name: 'Checkout Suite',
    testCount: 12,
    lastStatus: 'Failed',
    createdAt: 'Mar 18, 2024',
    description: 'Cart, payment, order confirmation flows',
  },
  {
    id: '3',
    name: 'Profile Suite',
    testCount: 5,
    lastStatus: 'Running',
    createdAt: 'Mar 15, 2024',
    description: 'Profile editing, avatar upload, preferences',
  },
  {
    id: '4',
    name: 'Onboarding Suite',
    testCount: 6,
    lastStatus: 'Passed',
    createdAt: 'Mar 10, 2024',
    description: 'First launch, permissions, tutorial steps',
  },
  {
    id: '5',
    name: 'Search Suite',
    testCount: 9,
    lastStatus: 'Not Run',
    createdAt: 'Mar 8, 2024',
    description: 'Search queries, filters, empty states, results',
  },
]

function StatusBadge({ status }: { status: SuiteStatus }) {
  const styles: Record<SuiteStatus, string> = {
    Passed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
    Failed: 'bg-red-500/15 text-red-400 border border-red-500/25',
    Running: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/25',
    'Not Run': 'bg-surface-3 text-muted border border-border',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

export default function SuitesPage() {
  const [showNewModal, setShowNewModal] = useState(false)
  const [newSuiteName, setNewSuiteName] = useState('')

  const handleNewSuite = () => {
    if (newSuiteName.trim()) {
      alert(`Suite "${newSuiteName}" created! (Not persisted — backend integration pending)`)
      setNewSuiteName('')
      setShowNewModal(false)
    }
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-1">Test Suites</h1>
            <p className="text-muted text-sm">Organize and run groups of related tests</p>
          </div>
          <button
            onClick={() => setShowNewModal(true)}
            className="btn-primary"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Suite
          </button>
        </div>

        {/* Suite Grid */}
        <div className="grid grid-cols-3 gap-4">
          {mockSuites.map((suite) => (
            <div
              key={suite.id}
              className="rounded-xl border border-border bg-surface-1 p-6 flex flex-col gap-4 hover:border-border/70 hover:bg-surface-2/50 transition-colors"
            >
              {/* Header row */}
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-foreground text-base leading-tight">{suite.name}</h3>
                  <p className="text-xs text-muted mt-1 leading-relaxed">{suite.description}</p>
                </div>
              </div>

              {/* Badges row */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  {suite.testCount} tests
                </span>
                <StatusBadge status={suite.lastStatus} />
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-auto pt-2 border-t border-border">
                <span className="text-xs text-muted">Created {suite.createdAt}</span>
                <button
                  onClick={() => alert(`Running suite: ${suite.name}`)}
                  className="text-xs px-3 py-1.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors font-medium"
                >
                  Run Suite
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* New Suite Modal */}
        {showNewModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="rounded-xl border border-border bg-surface-1 p-6 w-full max-w-md shadow-card-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">New Test Suite</h2>
                <button
                  onClick={() => setShowNewModal(false)}
                  className="text-muted hover:text-foreground transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5">Suite Name</label>
                  <input
                    type="text"
                    value={newSuiteName}
                    onChange={(e) => setNewSuiteName(e.target.value)}
                    placeholder="e.g. Auth Suite"
                    className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                    onKeyDown={(e) => e.key === 'Enter' && handleNewSuite()}
                    autoFocus
                  />
                </div>
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => setShowNewModal(false)}
                    className="flex-1 btn-ghost border border-border"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleNewSuite}
                    disabled={!newSuiteName.trim()}
                    className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Create Suite
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
