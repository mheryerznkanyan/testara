'use client'

import { useEffect, useState, useCallback } from 'react'
import { apiFetch } from './api'
import type { SuiteTest, SuiteWithStats } from '@/types'

// ── Types ────────────────────────────────────────────────────────────────────

export interface TestRun {
  id: string
  test_name: string
  suite_id: string | null
  suite_name: string | null
  suite_test_id: string | null
  status: 'passed' | 'failed' | 'running' | 'queued'
  device: string | null
  os_version: string | null
  duration: number | null
  logs: string | null
  error_message: string | null
  screenshot_url: string | null
  execution_mode: 'local' | 'cloud'
  created_at: string
}

export interface Suite {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface RunStats {
  total: number
  passed: number
  failed: number
  running: number
  lastRunAt: string | null
}

// ── Run Stats ────────────────────────────────────────────────────────────────

export function useRunStats() {
  const [stats, setStats] = useState<RunStats>({ total: 0, passed: 0, failed: 0, running: 0, lastRunAt: null })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<any>('/db/run-stats')
        setStats({
          total: Number(data.total) || 0,
          passed: Number(data.passed) || 0,
          failed: Number(data.failed) || 0,
          running: Number(data.running) || 0,
          lastRunAt: data.last_run_at ?? null,
        })
      } catch {
        // keep defaults
      }
      setLoading(false)
    }
    load()
  }, [])

  return { stats, loading }
}

// ── Test Runs ────────────────────────────────────────────────────────────────

export function useTestRuns(filter?: 'passed' | 'failed' | 'running', suiteId?: string) {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filter) params.set('status', filter)
      if (suiteId) params.set('suite_id', suiteId)
      const qs = params.toString()
      const data = await apiFetch<TestRun[]>(`/db/test-runs${qs ? `?${qs}` : ''}`)
      setRuns(data)
    } catch {
      // keep empty
    }
    setLoading(false)
  }, [filter, suiteId])

  useEffect(() => { load() }, [load])

  return { runs, loading, refresh: load }
}

export function useRecentRuns(limit = 5) {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<TestRun[]>(`/db/test-runs?limit=${limit}`)
        setRuns(data)
      } catch {
        // keep empty
      }
      setLoading(false)
    }
    load()
  }, [limit])

  return { runs, loading }
}

// ── Suites ───────────────────────────────────────────────────────────────────

export function useSuites() {
  const [suites, setSuites] = useState<Suite[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Suite[]>('/db/suites')
      setSuites(data)
    } catch {
      // keep empty
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const createSuite = async (name: string, description?: string) => {
    const data = await apiFetch<Suite>('/db/suites', {
      method: 'POST',
      body: JSON.stringify({ name, description: description || null }),
    })
    setSuites(prev => [data, ...prev])
    return data
  }

  const deleteSuite = async (suiteId: string) => {
    await apiFetch(`/db/suites/${suiteId}`, { method: 'DELETE' })
    setSuites(prev => prev.filter(s => s.id !== suiteId))
  }

  return { suites, loading, refresh: load, createSuite, deleteSuite }
}

// ── Suite Detail ─────────────────────────────────────────────────────────────

export function useSuiteDetail(suiteId: string) {
  const [suite, setSuite] = useState<SuiteWithStats | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<SuiteWithStats>(`/db/suites/${suiteId}`)
      setSuite(data)
    } catch {
      setSuite(null)
    }
    setLoading(false)
  }, [suiteId])

  useEffect(() => { load() }, [load])

  const updateSuite = async (updates: { name?: string; description?: string }) => {
    const data = await apiFetch<SuiteWithStats>(`/db/suites/${suiteId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    })
    setSuite(prev => prev ? { ...prev, ...data } : prev)
    return data
  }

  return { suite, loading, refresh: load, updateSuite }
}

// ── Suite Tests ──────────────────────────────────────────────────────────────

export function useSuiteTests(suiteId: string) {
  const [tests, setTests] = useState<SuiteTest[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<SuiteTest[]>(`/db/suites/${suiteId}/tests`)
      setTests(data)
    } catch {
      // keep empty
    }
    setLoading(false)
  }, [suiteId])

  useEffect(() => { load() }, [load])

  const addTest = async (data: {
    name: string
    description?: string
    test_code: string
    class_name?: string
    quality_score?: number
    quality_grade?: string
  }) => {
    const created = await apiFetch<SuiteTest>(`/db/suites/${suiteId}/tests`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
    setTests(prev => [...prev, created])
    return created
  }

  const updateTest = async (testId: string, data: {
    name?: string
    description?: string
    test_code?: string
    class_name?: string
  }) => {
    const updated = await apiFetch<SuiteTest>(`/db/suites/${suiteId}/tests/${testId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    setTests(prev => prev.map(t => t.id === testId ? updated : t))
    return updated
  }

  const deleteTest = async (testId: string) => {
    await apiFetch(`/db/suites/${suiteId}/tests/${testId}`, { method: 'DELETE' })
    setTests(prev => prev.filter(t => t.id !== testId))
  }

  return { tests, loading, refresh: load, addTest, updateTest, deleteTest }
}

// ── Save a run result ─────────────────────────────────────────────────────────

export async function saveTestRun(run: Omit<TestRun, 'id' | 'created_at'>) {
  return apiFetch<TestRun>('/db/test-runs', {
    method: 'POST',
    body: JSON.stringify(run),
  })
}

// ── Helpers ──────────────────────────────────────────────────────────────────

export function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never'
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
