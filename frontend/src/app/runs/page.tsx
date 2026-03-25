'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/components/ui/table'
import { Input } from '@/components/ui/input'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import { EmptyState } from '@/components/empty-state'
import {
  Play,
  ChevronRight,
  Image,
  FileText,
  AlertTriangle,
  RotateCcw,
  Search,
} from 'lucide-react'
import { toast } from 'sonner'
import type { TestRun, RunStatus } from '@/types'

type FilterTab = 'All' | RunStatus

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
    logs: '2024-03-25 10:02:01 [INFO] Starting test: Login with valid credentials\n2024-03-25 10:02:01 [INFO] Launching app on iPhone 15 Pro (iOS 17.2)\n2024-03-25 10:02:03 [INFO] App launched successfully\n2024-03-25 10:02:04 [INFO] Tapping on "Login" button\n2024-03-25 10:02:05 [INFO] Entering email: test@example.com\n2024-03-25 10:02:06 [INFO] Entering password\n2024-03-25 10:02:07 [INFO] Tapping "Sign In"\n2024-03-25 10:02:10 [INFO] Dashboard loaded successfully\n2024-03-25 10:02:10 [INFO] \u2713 Test PASSED in 12s',
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
    logs: '2024-03-25 10:05:00 [INFO] Starting test: Add item to cart\n2024-03-25 10:05:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 10:05:03 [INFO] Navigating to product page\n2024-03-25 10:05:04 [INFO] Tapping "Add to Cart"\n2024-03-25 10:05:05 [INFO] Cart updated: 1 item\n2024-03-25 10:05:06 [INFO] Verifying cart count badge\n2024-03-25 10:05:07 [INFO] \u2713 Test PASSED in 8s',
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
    errorMessage:
      'Element not found: XCUIElementTypeStaticText with label "Invalid card number". The error banner was not displayed after submitting an invalid card number.',
  },
  {
    id: '4',
    testName: 'Profile photo upload',
    suite: 'Profile Suite',
    status: 'Running',
    device: 'iPhone 13',
    os: 'iOS 15.8',
    duration: '\u2014',
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
    logs: '2024-03-25 07:00:00 [INFO] Starting test: Push notification opt-in\n2024-03-25 07:00:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 07:00:03 [INFO] Onboarding flow started\n2024-03-25 07:00:04 [INFO] Notification permission dialog appeared\n2024-03-25 07:00:05 [INFO] Tapping "Allow"\n2024-03-25 07:00:06 [INFO] \u2713 Test PASSED in 6s',
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
    errorMessage:
      'Application crashed. Received signal SIGABRT. The app did not handle empty search query gracefully.',
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
    logs: '2024-03-25 04:00:00 [INFO] Starting test: Dark mode toggle\n2024-03-25 04:00:01 [INFO] Launching app on iPhone 13 (iOS 15.8)\n2024-03-25 04:00:02 [INFO] Opening Settings\n2024-03-25 04:00:03 [INFO] Toggling dark mode switch\n2024-03-25 04:00:03 [INFO] UI updated to dark theme\n2024-03-25 04:00:04 [INFO] \u2713 Test PASSED in 4s',
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
    logs: '2024-03-25 04:05:00 [INFO] Starting test: Logout and session clear\n2024-03-25 04:05:01 [INFO] Launching app on iPhone 14 (iOS 16.7)\n2024-03-25 04:05:02 [INFO] User already logged in\n2024-03-25 04:05:03 [INFO] Tapping "Log Out"\n2024-03-25 04:05:05 [INFO] Verifying redirect to login screen\n2024-03-25 04:05:06 [INFO] Session cleared from keychain\n2024-03-25 04:05:07 [INFO] \u2713 Test PASSED in 7s',
  },
  {
    id: '9',
    testName: 'Biometric authentication',
    suite: 'Auth Suite',
    status: 'Running',
    device: 'iPhone 15 Pro',
    os: 'iOS 17.2',
    duration: '\u2014',
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
    errorMessage:
      'Timeout: Data sync did not complete within the expected 5 second window after network restoration. Expected sync indicator to disappear but it remained visible.',
  },
]

export default function RunsPage() {
  const [activeTab, setActiveTab] = useState<FilterTab>('All')
  const [expandedRow, setExpandedRow] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const tabCounts: Record<FilterTab, number> = {
    All: mockRuns.length,
    Passed: mockRuns.filter((r) => r.status === 'Passed').length,
    Failed: mockRuns.filter((r) => r.status === 'Failed').length,
    Running: mockRuns.filter((r) => r.status === 'Running').length,
  }

  const filteredRuns = mockRuns.filter((r) => {
    const matchesTab = activeTab === 'All' || r.status === activeTab
    const matchesSearch =
      searchQuery === '' ||
      r.testName.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesTab && matchesSearch
  })

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-7xl mx-auto px-8 py-8">
        <PageHeader
          title="Test Runs"
          description="All test executions across your suites"
          action={
            <Button onClick={() => toast.info('Running all tests...')}>
              <Play className="w-4 h-4 mr-2" />
              Run All
            </Button>
          }
        />

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as FilterTab)}
          className="mb-6"
        >
          <TabsList>
            {(['All', 'Passed', 'Failed', 'Running'] as FilterTab[]).map(
              (tab) => (
                <TabsTrigger key={tab} value={tab} className="gap-2">
                  {tab}
                  <Badge variant="default" className="text-xs px-1.5 py-0">
                    {tabCounts[tab]}
                  </Badge>
                </TabsTrigger>
              )
            )}
          </TabsList>
        </Tabs>

        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by test name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          {filteredRuns.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Test Name</TableHead>
                  <TableHead>Suite</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead>OS</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRuns.map((run) => (
                  <>
                    <TableRow
                      key={run.id}
                      className="cursor-pointer"
                      onClick={() =>
                        setExpandedRow(expandedRow === run.id ? null : run.id)
                      }
                    >
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <ChevronRight
                            className={`w-3.5 h-3.5 text-muted-foreground transition-transform ${
                              expandedRow === run.id ? 'rotate-90' : ''
                            }`}
                          />
                          {run.testName}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {run.suite}
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={run.status} />
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {run.device}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {run.os}
                      </TableCell>
                      <TableCell className="text-muted-foreground font-mono">
                        {run.duration}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {run.date}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            toast.info(`Re-running: ${run.testName}`)
                          }}
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                          Re-run
                        </Button>
                      </TableCell>
                    </TableRow>

                    {expandedRow === run.id && (
                      <TableRow key={`${run.id}-expanded`}>
                        <TableCell colSpan={8} className="p-0">
                          <Card className="m-4 border border-border">
                            <CardContent className="p-5 space-y-4">
                              {/* Logs */}
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <FileText className="w-4 h-4 text-muted-foreground" />
                                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    Execution Logs
                                  </h4>
                                </div>
                                <pre className="bg-muted/50 border border-border rounded-lg p-4 text-xs font-mono text-muted-foreground overflow-x-auto whitespace-pre-wrap leading-relaxed">
                                  {run.logs}
                                </pre>
                              </div>

                              {/* Error Message */}
                              {run.errorMessage && (
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <AlertTriangle className="w-4 h-4 text-red-400" />
                                    <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider">
                                      Error
                                    </h4>
                                  </div>
                                  <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4 text-sm text-red-300">
                                    {run.errorMessage}
                                  </div>
                                </div>
                              )}

                              {/* Screenshot Placeholder */}
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <Image className="w-4 h-4 text-muted-foreground" />
                                  <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                    Screenshot
                                  </h4>
                                </div>
                                <div className="w-48 h-32 bg-muted/50 border border-border rounded-lg flex items-center justify-center">
                                  <div className="text-center">
                                    <Image className="w-8 h-8 text-muted-foreground mx-auto mb-1" />
                                    <span className="text-xs text-muted-foreground">
                                      No screenshot
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </TableCell>
                      </TableRow>
                    )}
                  </>
                ))}
              </TableBody>
            </Table>
          ) : (
            <EmptyState
              icon={<Search className="w-10 h-10" />}
              title={`No ${activeTab === 'All' ? '' : activeTab.toLowerCase() + ' '}runs found`}
              description={
                searchQuery
                  ? `No results matching "${searchQuery}"`
                  : undefined
              }
            />
          )}
        </div>
      </div>
    </div>
  )
}
