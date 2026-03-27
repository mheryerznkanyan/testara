'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Plus, Play, FolderOpen, MoreVertical, Trash2 } from 'lucide-react'
import { CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { PageHeader } from '@/components/page-header'
import { EmptyState } from '@/components/empty-state'
import { useSuites, formatRelativeTime } from '@/lib/hooks'

function suiteStatusBadge(suite: { test_count?: number; passed_count?: number; failed_count?: number }) {
  const count = suite.test_count ?? 0
  const passed = suite.passed_count ?? 0
  const failed = suite.failed_count ?? 0
  if (count === 0) return <Badge variant="default">Not Run</Badge>
  if (failed > 0) return <Badge variant="destructive">Failed</Badge>
  if (passed === count) return <Badge variant="success">Passed</Badge>
  return <Badge variant="default">Not Run</Badge>
}

export default function SuitesPage() {
  const router = useRouter()
  const { suites, loading, createSuite, deleteSuite } = useSuites()
  const [showNewModal, setShowNewModal] = useState(false)
  const [newSuiteName, setNewSuiteName] = useState('')
  const [newSuiteDesc, setNewSuiteDesc] = useState('')
  const [creating, setCreating] = useState(false)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState<string | null>(null)

  const handleNewSuite = async () => {
    if (!newSuiteName.trim()) return
    setCreating(true)
    try {
      const suite = await createSuite(newSuiteName.trim(), newSuiteDesc.trim() || undefined)
      toast.success(`Suite "${newSuiteName}" created`)
      setNewSuiteName('')
      setNewSuiteDesc('')
      setShowNewModal(false)
      router.push(`/suites/${suite.id}`)
    } catch (err) {
      toast.error('Failed to create suite')
    }
    setCreating(false)
  }

  const handleDelete = async () => {
    if (!deleteId) return
    try {
      await deleteSuite(deleteId)
      toast.success('Suite deleted')
    } catch {
      toast.error('Failed to delete suite')
    }
    setDeleteId(null)
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1400px] mx-auto p-8">
        <PageHeader
          title="Test Suites"
          description="Organize and run groups of related tests"
          action={
            <Button onClick={() => setShowNewModal(true)}>
              <Plus className="h-4 w-4" />
              New Suite
            </Button>
          }
        />

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-6 space-y-3">
                <Skeleton className="h-5 w-32 bg-surface-high" />
                <Skeleton className="h-3 w-48 bg-surface-high" />
                <div className="flex gap-2">
                  <Skeleton className="h-5 w-16 bg-surface-high rounded-full" />
                  <Skeleton className="h-5 w-16 bg-surface-high rounded-full" />
                </div>
              </div>
            ))}
          </div>
        ) : suites.length === 0 ? (
          <EmptyState
            icon={<FolderOpen className="h-12 w-12" />}
            title="No test suites yet"
            description="Create your first suite to organize related tests together"
            action={
              <Button onClick={() => setShowNewModal(true)}>
                <Plus className="h-4 w-4" />
                New Suite
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {suites.map((suite: any) => (
              <Link
                key={suite.id}
                href={`/suites/${suite.id}`}
                className="glass-card flex flex-col hover:border-primary/20 transition-all duration-300 group"
              >
                <CardContent className="pt-6 flex-1 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-bold text-white text-base leading-tight font-headline">
                        {suite.name}
                      </h3>
                      <p className="text-xs text-zinc-500 mt-1.5 leading-relaxed">
                        {suite.description || 'No description'}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        setMenuOpen(menuOpen === suite.id ? null : suite.id)
                      }}
                      className="p-1 rounded-lg hover:bg-white/5 text-zinc-600 hover:text-zinc-300 transition-colors"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                  {menuOpen === suite.id && (
                    <div className="absolute right-4 top-12 z-10 bg-surface-high border border-white/10 rounded-xl shadow-lg py-1 min-w-[140px]">
                      <button
                        onClick={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          setMenuOpen(null)
                          setDeleteId(suite.id)
                        }}
                        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:bg-white/5 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Delete Suite
                      </button>
                    </div>
                  )}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="blue">{suite.test_count ?? 0} tests</Badge>
                    {suiteStatusBadge(suite)}
                  </div>
                </CardContent>
                <div className="flex items-center justify-between py-3 px-6 border-t border-white/5">
                  <span className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">
                    {formatRelativeTime(suite.created_at)}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      router.push(`/suites/${suite.id}`)
                    }}
                  >
                    <Play className="h-3 w-3" />
                    Open
                  </Button>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* New Suite Dialog */}
        <Dialog open={showNewModal} onOpenChange={setShowNewModal}>
          <DialogContent onClose={() => setShowNewModal(false)}>
            <DialogHeader>
              <DialogTitle>New Test Suite</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Suite Name</label>
                <input
                  value={newSuiteName}
                  onChange={(e) => setNewSuiteName(e.target.value)}
                  placeholder="e.g. Auth Suite"
                  onKeyDown={(e) => e.key === 'Enter' && handleNewSuite()}
                  autoFocus
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Description</label>
                <input
                  value={newSuiteDesc}
                  onChange={(e) => setNewSuiteDesc(e.target.value)}
                  placeholder="Brief description of what this suite tests"
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button onClick={handleNewSuite} disabled={!newSuiteName.trim() || creating} className="flex-1">
                {creating ? 'Creating...' : 'Create Suite'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
          <DialogContent onClose={() => setDeleteId(null)}>
            <DialogHeader>
              <DialogTitle>Delete Suite</DialogTitle>
            </DialogHeader>
            <p className="text-sm text-zinc-400 py-4">
              Are you sure you want to delete this suite and all its tests? Past run history will be preserved.
            </p>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteId(null)} className="flex-1">
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDelete} className="flex-1">
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
