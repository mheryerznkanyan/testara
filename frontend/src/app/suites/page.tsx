'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Plus, Play, FolderOpen } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import { EmptyState } from '@/components/empty-state'
import type { Suite, SuiteStatus } from '@/types'

const mockSuites: Suite[] = [
  { id: '1', name: 'Auth Suite', testCount: 8, lastStatus: 'Passed', createdAt: 'Mar 20, 2024', description: 'Login, logout, biometric auth, session management' },
  { id: '2', name: 'Checkout Suite', testCount: 12, lastStatus: 'Failed', createdAt: 'Mar 18, 2024', description: 'Cart, payment, order confirmation flows' },
  { id: '3', name: 'Profile Suite', testCount: 5, lastStatus: 'Running', createdAt: 'Mar 15, 2024', description: 'Profile editing, avatar upload, preferences' },
  { id: '4', name: 'Onboarding Suite', testCount: 6, lastStatus: 'Passed', createdAt: 'Mar 10, 2024', description: 'First launch, permissions, tutorial steps' },
  { id: '5', name: 'Search Suite', testCount: 9, lastStatus: 'Not Run', createdAt: 'Mar 8, 2024', description: 'Search queries, filters, empty states, results' },
]

export default function SuitesPage() {
  const [showNewModal, setShowNewModal] = useState(false)
  const [newSuiteName, setNewSuiteName] = useState('')
  const [newSuiteDesc, setNewSuiteDesc] = useState('')

  const handleNewSuite = () => {
    if (newSuiteName.trim()) {
      toast.success(`Suite "${newSuiteName}" created`)
      setNewSuiteName('')
      setNewSuiteDesc('')
      setShowNewModal(false)
    }
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
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

        {mockSuites.length === 0 ? (
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {mockSuites.map((suite) => (
              <Card
                key={suite.id}
                className="flex flex-col hover:shadow-card-md transition-all duration-200"
              >
                <CardContent className="pt-6 flex-1 space-y-3">
                  <div>
                    <h3 className="font-semibold text-foreground text-base leading-tight">
                      {suite.name}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
                      {suite.description}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="blue">{suite.testCount} tests</Badge>
                    <StatusBadge status={suite.lastStatus} />
                  </div>
                </CardContent>
                <CardFooter className="border-t border-border flex items-center justify-between py-3">
                  <span className="text-xs text-muted-foreground">
                    Created {suite.createdAt}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => toast.info(`Running suite: ${suite.name}`)}
                  >
                    <Play className="h-3 w-3" />
                    Run
                  </Button>
                </CardFooter>
              </Card>
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
                <label className="text-sm font-medium mb-1.5 block">Suite Name</label>
                <Input
                  value={newSuiteName}
                  onChange={(e) => setNewSuiteName(e.target.value)}
                  placeholder="e.g. Auth Suite"
                  onKeyDown={(e) => e.key === 'Enter' && handleNewSuite()}
                  autoFocus
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Description</label>
                <Input
                  value={newSuiteDesc}
                  onChange={(e) => setNewSuiteDesc(e.target.value)}
                  placeholder="Brief description of what this suite tests"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowNewModal(false)}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={handleNewSuite}
                disabled={!newSuiteName.trim()}
                className="flex-1"
              >
                Create Suite
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
