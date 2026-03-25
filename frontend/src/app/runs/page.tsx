'use client'

import { useState } from 'react'

type RunStatus = 'Passed' | 'Failed' | 'Running'
type FilterTab = 'All' | RunStatus

interface TestRun {
  id: string
  testName: string
  suite: string
  status: RunStatus
  device: string
  os: string
  duration: string
  date: string
  logs: string
  errorMessage?: string
}

const mockRuns: TestRun[] = [
  {
    id: '1',
    testName: 'Login with valid credentials',
    suite: 'Auth Suite',
    status: 'Passed',
    device: 'iPhone 15 Pro',
    os: 'iOS 17.2',
    duration: '12s',
    date: '2 hours ago',
    logs: '2024-03-25 10:02:01 [INFO] Starting test: Login with valid credentials\n2024-03-25 10:02:01 [INFO] Launching app on iPhone 15 Pro (iOS 17.2)\n2024-03-25 10:02:03 [INFO] App launched successfully\n2024-03-25 10:02:04 [INFO] Tapping on "Login" button\n2024-03-25 10:02:05 [INFO] Entering email: test@example.com\n2024-03-25 10:02:06 [INFO] Entering password\n2024-03-25 10:02:07 [INFO] Tapping "Sign In"\n2024-03-25 10:02:10 [INFO] Dashboard loaded successfully\n2024-03-25 10:02:10 [INFO] ✓ Test PASSED in 12s',
  },
  {
    id: '2',
    testName: 'Add item to cart',
    suite: 'Checkout Suite',
    status: 'Passed',
    device: 'iPhone 14',
    os: 'iOS 16.7',
    duration: '8s',
    date: '2 hours ago',
    logs: '2024-03-25 10:05:00 [INFO] Starting test: Add item to cart\n2024-03-25 10:05:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 10:05:03 [INFO] Navigating to product page\n2024-03-25 10:05:04 [INFO] Tapping "Add to Cart"\n2024-03-25 10:05:05 [INFO] Cart updated: 1 item\n2024-03-25 10:05:06 [INFO] Verifying cart count badge\n2024-03-25 10:05:07 [INFO] ✓ Test PASSED in 8s',
  },
  {
    id: '3',
    testName: 'Payment with invalid card',
    suite: 'Checkout Suite',
    status: 'Failed',
    device: 'iPhone 15 Pro',
    os: 'iOS 17.2',
    duration: '5s',
    date: '3 hours ago',
    logs: '2024-03-25 09:30:00 [INFO] Starting test: Payment with invalid card\n2024-03-25 09:30:01 [INFO] Launching app on iPhone 15 Pro (iOS 17.2)\n2024-03-25 09:30:03 [INFO] Navigating to checkout\n2024-03-25 09:30:04 [INFO] Entering invalid card: 4111-0000-0000-0000\n2024-03-25 09:30:04 [ERROR] Expected error banner "Invalid card number" not found\n2024-03-25 09:30:05 [FAIL] Test FAILED after 5s',
    errorMessage: 'Element not found: XCUIElementTypeStaticText with label "Invalid card number". The error banner was not displayed after submitting an invalid card number.',
  },
  {
    id: '4',
    testName: 'Profile photo upload',
    suite: 'Profile Suite',
    status: 'Running',
    device: 'iPhone 13',
    os: 'iOS 15.8',
    duration: '—',
    date: 'Just now',
    logs: '2024-03-25 12:00:00 [INFO] Starting test: Profile photo upload\n2024-03-25 12:00:01 [INFO] Launching app on iPhone 13 (iOS 15.8)\n2024-03-25 12:00:03 [INFO] Navigating to profile settings\n2024-03-25 12:00:04 [INFO] Tapping "Change Photo"...',
  },
  {
    id: '5',
    testName: 'Push notification opt-in',
    suite: 'Onboarding Suite',
    status: 'Passed',
    device: 'iPhone 14',
    os: 'iOS 16.7',
    duration: '6s',
    date: '5 hours ago',
    logs: '2024-03-25 07:00:00 [INFO] Starting test: Push notification opt-in\n2024-03-25 07:00:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 07:00:03 [INFO] Onboarding flow started\n2024-03-25 07:00:04 [INFO] Notification permission dialog appeared\n2024-03-25 07:00:05 [INFO] Tapping "Allow"\n2024-03-25 07:00:06 [INFO] ✓ Test PASSED in 6s',
  },
  {
    id: '6',
    testName: 'Search with empty query',
    suite: 'Search Suite',
    status: 'Failed',
    device: 'iPhone 15 Pro',
    os: 'iOS 17.2',
    duration: '3s',
    date: '6 hours ago',
    logs: '2024-03-25 06:00:00 [INFO] Starting test: Search with empty query\n2024-03-25 06:00:01 [INFO] Launching app on iPhone 15 Pro (iOS 17.2)\n2024-03-25 06:00:02 [INFO] Tapping search bar\n2024-03-25 06:00:03 [ERROR] App crashed when search was submitted with empty string\n2024-03-25 06:00:03 [FAIL] Test FAILED after 3s',
    errorMessage: 'Application crashed. Received signal SIGABRT. The app did not handle empty search query gracefully.',
  },
  {
    id: '7',
    testName: 'Dark mode toggle',
    suite: 'Settings Suite',
    status: 'Passed',
    device: 'iPhone 13',
    os: 'iOS 15.8',
    duration: '4s',
    date: '8 hours ago',
    logs: '2024-03-25 04:00:00 [INFO] Starting test: Dark mode toggle\n2024-03-25 04:00:01 [INFO] Launching app on iPhone 13 (iOS 15.8)\n2024-03-25 04:00:02 [INFO] Opening Settings\n2024-03-25 04:00:03 [INFO] Toggling dark mode switch\n2024-03-25 04:00:03 [INFO] UI updated to dark theme\n2024-03-25 04:00:04 [INFO] ✓ Test PASSED in 4s',
  },
  {
    id: '8',
    testName: 'Logout and session clear',
    suite: 'Auth Suite',
    status: 'Passed',
    device: 'iPhone 14',
    os: 'iOS 16.7',
    duration: '7s',
    date: '8 hours ago',
    logs: '2024-03-25 04:05:00 [INFO] Starting test: Logout and session clear\n2024-03-25 04:05:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 04:05:02 [INFO] User already logged in\n2024-03-25 04:05:03 [INFO] Tapping "Log Out"\n2024-03-25 04:05:05 [INFO] Verifying redirect to login screen\n2024-03-25 04:05:06 [INFO] Session cleared from keychain\n2024-03-25 04:05:07 [INFO] ✓ Test PASSED in 7s',
  },
  {
    id: '9',
    testName: 'Biometric authentication',
    suite: 'Auth Suite',
    status: 'Running',
    device: 'iPhone 15 Pro',
    os: 'iOS 17.2',
    duration: '—',
    date: 'Just now',
    logs: '2024-03-25 12:00:10 [INFO] Starting test: Biometric authentication\n2024-03-25 12:00:11 [INFO] Launching app on iPhone 15 Pro (iOS 17.2)\n2024-03-25 12:00:12 [INFO] Triggering Face ID prompt...',
  },
  {
    id: '10',
    testName: 'Offline mode sync',
    suite: 'Network Suite',
    status: 'Failed',
    device: 'iPhone 13',
    os: 'iOS 15.8',
    duration: '15s',
    date: '1 day ago',
    logs: '2024-03-24 14:00:00 [INFO] Starting test: Offline mode sync\n2024-03-24 14:00:01 [INFO] Launching app on iPhone 13 (iOS 15.8)\n2024-03-24 14:00:02 [INFO] Disabling network\n2024-03-24 14:00:05 [INFO] Performing actions in offline mode\n2024-03-24 14:00:10 [INFO] Re-enabling network\n2024-03-24 14:00:14 [ERROR] Sync did not complete within 5 second timeout\n2024-03-24 14:00:15 [FAIL] Test FAILED after 15s',
    errorMessage: 'Timeout: Data sync did not complete within the expected 5 second window after network restoration. Expected sync indicator to disappear but it remained visible.',
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
      {status === 'Running' && (
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-yellow-400 mr-1 animate-pulse" />
      )}
      {status}
    </span>
  )
}

export default function RunsPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('All')
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  const tabs: FilterTab[] = ['All', 'Passed', 'Failed', 'Running']

  const filteredRuns =
    activeTab === 'All' ? mockRuns : mockRuns.filter((r) => r.status === activeTab)

  const tabCounts: Record<FilterTab, number> = {
    All: mockRuns.length,
    Passed: mockRuns.filter((r) => r.status === 'Passed').length,
    Failed: mockRuns.filter((r) => r.status === 'Failed').length,
    Running: mockRuns.filter((r) => r.status === 'Running').length,
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-1">Test Runs</h1>
            <p className="text-muted text-sm">All test executions across your suites</p>
          </div>
          <button className="btn-primary">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Run All
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1 mb-6 p-1 rounded-lg bg-surface-2 w-fit">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                activeTab === tab
                  ? 'bg-surface-1 text-foreground shadow-sm'
                  : 'text-muted hover:text-foreground'
              }`}
            >
              {tab}
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full ${
                  activeTab === tab
                    ? 'bg-accent text-foreground'
                    : 'bg-surface-3 text-muted'
                }`}
              >
                {tabCounts[tab]}
              </span>
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2/50">
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Test Name</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Suite</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Status</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Device</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">OS</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Duration</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Date</th>
                  <th className="text-left px-6 py-3 text-xs font-medium text-muted uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((run) => (
                  <>
                    <tr
                      key={run.id}
                      className="border-b border-border last:border-0 hover:bg-surface-2/30 transition-colors cursor-pointer"
                      onClick={() => setExpandedRow(expandedRow === run.id ? null : run.id)}
                    >
                      <td className="px-6 py-4 font-medium text-foreground">
                        <div className="flex items-center gap-2">
                          <svg
                            className={`w-3.5 h-3.5 text-muted transition-transform ${
                              expandedRow === run.id ? 'rotate-90' : ''
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                          {run.testName}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-muted">{run.suite}</td>
                      <td className="px-6 py-4">
                        <StatusBadge status={run.status} />
                      </td>
                      <td className="px-6 py-4 text-muted">{run.device}</td>
                      <td className="px-6 py-4 text-muted">{run.os}</td>
                      <td className="px-6 py-4 text-muted font-mono">{run.duration}</td>
                      <td className="px-6 py-4 text-muted">{run.date}</td>
                      <td className="px-6 py-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            alert(`Re-running: ${run.testName}`)
                          }}
                          className="text-xs px-2.5 py-1 rounded-md border border-border text-muted hover:text-foreground hover:bg-surface-2 transition-colors"
                        >
                          Re-run
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Row */}
                    {expandedRow === run.id && (
                      <tr key={`${run.id}-expanded`} className="border-b border-border bg-surface-0/50">
                        <td colSpan={8} className="px-6 py-5">
                          <div className="space-y-4">
                            {/* Logs */}
                            <div>
                              <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                                Execution Logs
                              </h4>
                              <pre className="bg-surface-0 border border-border rounded-lg p-4 text-xs font-mono text-muted-foreground overflow-x-auto whitespace-pre-wrap leading-relaxed">
                                {run.logs}
                              </pre>
                            </div>

                            {/* Error Message */}
                            {run.errorMessage && (
                              <div>
                                <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-2">
                                  Error
                                </h4>
                                <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4 text-sm text-red-300">
                                  {run.errorMessage}
                                </div>
                              </div>
                            )}

                            {/* Screenshot Placeholder */}
                            <div>
                              <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">
                                Screenshot
                              </h4>
                              <div className="w-48 h-32 bg-surface-2 border border-border rounded-lg flex items-center justify-center">
                                <div className="text-center">
                                  <svg className="w-8 h-8 text-muted mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                  </svg>
                                  <span className="text-xs text-muted">No screenshot</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          {filteredRuns.length === 0 && (
            <div className="py-16 text-center text-muted">
              <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm">No {activeTab.toLowerCase()} runs found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
