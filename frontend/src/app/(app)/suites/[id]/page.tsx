'use client'

import React, { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'sonner'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import {
  ArrowLeft,
  Plus,
  Play,
  Trash2,
  Pencil,
  ChevronRight,
  Copy,
  Check,
  FolderOpen,
  AlertTriangle,
  Loader2,
  MoreVertical,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { StatusBadge } from '@/components/status-badge'
import { EmptyState } from '@/components/empty-state'
import { useSuiteDetail, useSuiteTests, formatRelativeTime } from '@/lib/hooks'
import { runTest, API_BASE } from '@/lib/api'
import type { SuiteTest } from '@/types'

function testStatusToBadge(status: string | null) {
  switch (status) {
    case 'passed': return 'Passed' as const
    case 'failed': return 'Failed' as const
    case 'running': return 'Running' as const
    default: return 'Not Run' as const
  }
}

export default function SuiteDetailPage() {
  const params = useParams()
  const router = useRouter()
  const suiteId = params.id as string

  const { suite, loading: suiteLoading, refresh: refreshSuite, updateSuite } = useSuiteDetail(suiteId)
  const { tests, loading: testsLoading, addTest, updateTest, deleteTest, refresh: refreshTests } = useSuiteTests(suiteId)

  const [expandedRow, setExpandedRow] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [runningTest, setRunningTest] = useState<string | null>(null)

  // Add test dialog
  const [showAddModal, setShowAddModal] = useState(false)
  const [newTestName, setNewTestName] = useState('')
  const [newTestDesc, setNewTestDesc] = useState('')
  const [newTestCode, setNewTestCode] = useState('')
  const [adding, setAdding] = useState(false)

  // Edit test dialog
  const [editTest, setEditTest] = useState<SuiteTest | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')
  const [editCode, setEditCode] = useState('')
  const [saving, setSaving] = useState(false)

  // Edit suite dialog
  const [showEditSuite, setShowEditSuite] = useState(false)
  const [editSuiteName, setEditSuiteName] = useState('')
  const [editSuiteDesc, setEditSuiteDesc] = useState('')

  // Delete confirmation
  const [deleteTestId, setDeleteTestId] = useState<string | null>(null)
  const [showDeleteSuite, setShowDeleteSuite] = useState(false)

  const handleCopy = (code: string, testId: string) => {
    navigator.clipboard.writeText(code)
    setCopied(testId)
    setTimeout(() => setCopied(null), 2000)
  }

  const handleAddTest = async () => {
    if (!newTestName.trim() || !newTestCode.trim()) return
    setAdding(true)
    try {
      await addTest({
        name: newTestName.trim(),
        description: newTestDesc.trim() || undefined,
        test_code: newTestCode,
      })
      toast.success('Test added to suite')
      setShowAddModal(false)
      setNewTestName('')
      setNewTestDesc('')
      setNewTestCode('')
      refreshSuite()
    } catch {
      toast.error('Failed to add test')
    }
    setAdding(false)
  }

  const handleEditTest = async () => {
    if (!editTest || !editName.trim()) return
    setSaving(true)
    try {
      await updateTest(editTest.id, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
        test_code: editCode || undefined,
      })
      toast.success('Test updated')
      setEditTest(null)
    } catch {
      toast.error('Failed to update test')
    }
    setSaving(false)
  }

  const handleDeleteTest = async () => {
    if (!deleteTestId) return
    try {
      await deleteTest(deleteTestId)
      toast.success('Test removed from suite')
      refreshSuite()
    } catch {
      toast.error('Failed to delete test')
    }
    setDeleteTestId(null)
  }

  const handleEditSuite = async () => {
    if (!editSuiteName.trim()) return
    setSaving(true)
    try {
      await updateSuite({
        name: editSuiteName.trim(),
        description: editSuiteDesc.trim() || undefined,
      })
      toast.success('Suite updated')
      setShowEditSuite(false)
    } catch {
      toast.error('Failed to update suite')
    }
    setSaving(false)
  }

  const handleDeleteSuite = async () => {
    try {
      const { apiFetch } = await import('@/lib/api')
      await apiFetch(`/db/suites/${suiteId}`, { method: 'DELETE' })
      toast.success('Suite deleted')
      router.push('/suites')
    } catch {
      toast.error('Failed to delete suite')
    }
    setShowDeleteSuite(false)
  }

  const handleRunTest = async (test: SuiteTest) => {
    setRunningTest(test.id)
    try {
      const settings = JSON.parse(localStorage.getItem('testara_settings') || '{}')
      const executionMode = (localStorage.getItem('testara_exec_mode') as 'local' | 'cloud') || 'local'

      await runTest({
        test_code: test.test_code,
        bundle_id: settings.bundleId || undefined,
        device_udid: executionMode === 'local' ? (settings.deviceUdid || '') : '',
        execution_mode: executionMode,
        cloud_device: executionMode === 'cloud' ? (localStorage.getItem('testara_cloud_device') || undefined) : undefined,
        cloud_os_version: executionMode === 'cloud' ? (localStorage.getItem('testara_cloud_os_version') || undefined) : undefined,
        suite_id: suiteId,
        suite_test_id: test.id,
      })

      toast.success(`Test "${test.name}" completed`)
      refreshTests()
      refreshSuite()
    } catch (err) {
      toast.error(`Test failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
      refreshTests()
      refreshSuite()
    }
    setRunningTest(null)
  }

  const loading = suiteLoading || testsLoading

  if (loading) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-[1400px] mx-auto p-8 space-y-6">
          <Skeleton className="h-8 w-48 bg-surface-high" />
          <Skeleton className="h-4 w-72 bg-surface-high" />
          <div className="flex gap-3">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 w-32 bg-surface-high rounded-xl" />)}
          </div>
          <Skeleton className="h-64 w-full bg-surface-high rounded-xl" />
        </div>
      </div>
    )
  }

  if (!suite) {
    return (
      <div className="h-full overflow-auto">
        <div className="max-w-[1400px] mx-auto p-8">
          <EmptyState
            icon={<FolderOpen className="h-12 w-12" />}
            title="Suite not found"
            description="This suite may have been deleted"
            action={<Button onClick={() => router.push('/suites')}><ArrowLeft className="h-4 w-4" /> Back to Suites</Button>}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1400px] mx-auto p-8 space-y-6">
        {/* Header */}
        <div>
          <Link href="/suites" className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white transition-colors font-label uppercase tracking-widest mb-4">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Suites
          </Link>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-extrabold tracking-tight font-headline text-white">{suite.name}</h1>
              <p className="text-sm text-zinc-500 mt-1">{suite.description || 'No description'}</p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEditSuiteName(suite.name)
                  setEditSuiteDesc(suite.description || '')
                  setShowEditSuite(true)
                }}
              >
                <Pencil className="h-3.5 w-3.5" />
                Edit
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteSuite(true)}
                className="text-rose-400 hover:text-rose-300 border-rose-500/20 hover:border-rose-500/40"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Total Tests', value: suite.test_count, color: 'text-white' },
            { label: 'Passed', value: suite.passed_count, color: 'text-emerald-400' },
            { label: 'Failed', value: suite.failed_count, color: 'text-rose-400' },
            { label: 'Not Run', value: suite.not_run_count, color: 'text-zinc-400' },
          ].map(({ label, value, color }) => (
            <div key={label} className="glass-card px-4 py-3">
              <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600">{label}</p>
              <p className={`text-2xl font-bold font-mono ${color}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button onClick={() => setShowAddModal(true)}>
            <Plus className="h-4 w-4" />
            Add Test
          </Button>
          <Button variant="outline" onClick={() => router.push(`/?suiteId=${suiteId}`)}>
            <Plus className="h-4 w-4" />
            Generate & Add
          </Button>
        </div>

        {/* Tests List */}
        {tests.length === 0 ? (
          <EmptyState
            icon={<FolderOpen className="h-12 w-12" />}
            title="No tests in this suite"
            description="Add tests manually or generate them with AI"
            action={
              <div className="flex gap-2">
                <Button onClick={() => setShowAddModal(true)}>
                  <Plus className="h-4 w-4" />
                  Add Test
                </Button>
                <Button variant="outline" onClick={() => router.push(`/?suiteId=${suiteId}`)}>
                  Generate Test
                </Button>
              </div>
            }
          />
        ) : (
          <div className="glass-card overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-surface-high/30">
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Test Name</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Status</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden sm:table-cell">Last Run</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest hidden md:table-cell">Quality</th>
                  <th className="px-6 py-4 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {tests.map((test) => (
                  <React.Fragment key={test.id}>
                    <tr
                      className="hover:bg-white/5 transition-colors cursor-pointer"
                      onClick={() => setExpandedRow(expandedRow === test.id ? null : test.id)}
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <ChevronRight className={`w-3.5 h-3.5 text-zinc-600 transition-transform ${expandedRow === test.id ? 'rotate-90' : ''}`} />
                          <div>
                            <span className="font-semibold text-white text-sm">{test.name}</span>
                            {test.description && (
                              <p className="text-xs text-zinc-600 mt-0.5 truncate max-w-[300px]">{test.description}</p>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {runningTest === test.id ? (
                          <Badge variant="blue" className="gap-1">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            Running
                          </Badge>
                        ) : (
                          <StatusBadge status={testStatusToBadge(test.last_status)} />
                        )}
                      </td>
                      <td className="px-6 py-4 text-zinc-500 text-xs hidden sm:table-cell">
                        {formatRelativeTime(test.last_run_at)}
                      </td>
                      <td className="px-6 py-4 hidden md:table-cell">
                        {test.quality_grade ? (
                          <Badge variant={
                            (test.quality_score ?? 0) >= 80 ? 'success' :
                            (test.quality_score ?? 0) >= 60 ? 'warning' : 'destructive'
                          }>
                            {test.quality_grade} ({test.quality_score})
                          </Badge>
                        ) : (
                          <span className="text-zinc-600 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={runningTest === test.id}
                            onClick={() => handleRunTest(test)}
                          >
                            {runningTest === test.id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <Play className="h-3 w-3" />
                            )}
                            Run
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditTest(test)
                              setEditName(test.name)
                              setEditDesc(test.description || '')
                              setEditCode(test.test_code)
                            }}
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setDeleteTestId(test.id)}
                            className="text-rose-400 hover:text-rose-300"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>

                    {expandedRow === test.id && (
                      <tr>
                        <td colSpan={5} className="p-0">
                          <div className="m-4 glass-card p-5 space-y-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-label text-zinc-500 uppercase tracking-widest">
                                  Python / Appium
                                </span>
                                {test.class_name && (
                                  <span className="text-xs text-zinc-600 font-mono">{test.class_name}</span>
                                )}
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleCopy(test.test_code, test.id)}
                              >
                                {copied === test.id ? (
                                  <><Check className="h-3.5 w-3.5 text-emerald-400" /><span className="text-emerald-400">Copied!</span></>
                                ) : (
                                  <><Copy className="h-3.5 w-3.5" />Copy</>
                                )}
                              </Button>
                            </div>
                            <div className="rounded-xl overflow-hidden ring-1 ring-white/[0.06]">
                              <SyntaxHighlighter
                                language="python"
                                style={vscDarkPlus}
                                customStyle={{ margin: 0, borderRadius: '0.75rem', fontSize: '0.8125rem', lineHeight: '1.6', background: '#0e0e0e' }}
                              >
                                {test.test_code}
                              </SyntaxHighlighter>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Add Test Dialog */}
        <Dialog open={showAddModal} onOpenChange={setShowAddModal}>
          <DialogContent onClose={() => setShowAddModal(false)}>
            <DialogHeader>
              <DialogTitle>Add Test to Suite</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Test Name</label>
                <input
                  value={newTestName}
                  onChange={(e) => setNewTestName(e.target.value)}
                  placeholder="e.g. Login with valid credentials"
                  autoFocus
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Description</label>
                <input
                  value={newTestDesc}
                  onChange={(e) => setNewTestDesc(e.target.value)}
                  placeholder="What this test verifies"
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Test Code</label>
                <textarea
                  value={newTestCode}
                  onChange={(e) => setNewTestCode(e.target.value)}
                  placeholder="Paste your Python/Appium test code here..."
                  rows={12}
                  className="w-full resize-none bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all font-mono leading-relaxed"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleAddTest} disabled={!newTestName.trim() || !newTestCode.trim() || adding} className="flex-1">
                {adding ? 'Adding...' : 'Add Test'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Test Dialog */}
        <Dialog open={!!editTest} onOpenChange={() => setEditTest(null)}>
          <DialogContent onClose={() => setEditTest(null)}>
            <DialogHeader>
              <DialogTitle>Edit Test</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Test Name</label>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Description</label>
                <input
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Test Code</label>
                <textarea
                  value={editCode}
                  onChange={(e) => setEditCode(e.target.value)}
                  rows={12}
                  className="w-full resize-none bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all font-mono leading-relaxed"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditTest(null)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleEditTest} disabled={!editName.trim() || saving} className="flex-1">
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Suite Dialog */}
        <Dialog open={showEditSuite} onOpenChange={setShowEditSuite}>
          <DialogContent onClose={() => setShowEditSuite(false)}>
            <DialogHeader>
              <DialogTitle>Edit Suite</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Suite Name</label>
                <input
                  value={editSuiteName}
                  onChange={(e) => setEditSuiteName(e.target.value)}
                  autoFocus
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Description</label>
                <input
                  value={editSuiteDesc}
                  onChange={(e) => setEditSuiteDesc(e.target.value)}
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEditSuite(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleEditSuite} disabled={!editSuiteName.trim() || saving} className="flex-1">
                {saving ? 'Saving...' : 'Save'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Test Confirmation */}
        <Dialog open={!!deleteTestId} onOpenChange={() => setDeleteTestId(null)}>
          <DialogContent onClose={() => setDeleteTestId(null)}>
            <DialogHeader>
              <DialogTitle>Delete Test</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-zinc-400 py-4">
              Remove this test from the suite? Past run history will be preserved.
            </p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteTestId(null)} className="flex-1">Cancel</Button>
              <Button variant="destructive" onClick={handleDeleteTest} className="flex-1">Delete</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Suite Confirmation */}
        <Dialog open={showDeleteSuite} onOpenChange={setShowDeleteSuite}>
          <DialogContent onClose={() => setShowDeleteSuite(false)}>
            <DialogHeader>
              <DialogTitle>Delete Suite</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-zinc-400 py-4">
              Delete &ldquo;{suite.name}&rdquo; and all {suite.test_count} tests? Past run history will be preserved.
            </p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowDeleteSuite(false)} className="flex-1">Cancel</Button>
              <Button variant="destructive" onClick={handleDeleteSuite} className="flex-1">Delete Suite</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
