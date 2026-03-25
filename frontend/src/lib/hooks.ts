'use client'

import { useEffect, useState, useCallback } from 'react'
import { supabase } from './supabase'

// ── Types ────────────────────────────────────────────────────────────────────

export interface TestRun {
  id: string
  test_name: string
  suite_id: string | null
  suite_name: string | null
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
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const { data, error } = await (supabase as any)
        .from('run_stats')
        .select('*')
        .single()

      if (!error && data) {
        setStats({
          total: Number(data.total) || 0,
          passed: Number(data.passed) || 0,
          failed: Number(data.failed) || 0,
          running: Number(data.running) || 0,
          lastRunAt: data.last_run_at ?? null,
        })
      }
      setLoading(false)
    }
    load()
  }, [])

  return { stats, loading }
}

// ── Test Runs ────────────────────────────────────────────────────────────────

export function useTestRuns(filter?: 'passed' | 'failed' | 'running') {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let query = (supabase as any)
      .from('test_runs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(100)

    if (filter) query = query.eq('status', filter)

    const { data, error } = await query
    if (!error && data) setRuns(data as TestRun[])
    setLoading(false)
  }, [filter])

  useEffect(() => { load() }, [load])

  return { runs, loading, refresh: load }
}

export function useRecentRuns(limit = 5) {
  const [runs, setRuns] = useState<TestRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const { data, error } = await (supabase as any)
        .from('test_runs')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(limit)

      if (!error && data) setRuns(data as TestRun[])
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
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { data, error } = await (supabase as any)
      .from('suites')
      .select('*')
      .order('created_at', { ascending: false })

    if (!error && data) setSuites(data as Suite[])
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  const createSuite = async (name: string, description?: string) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { data, error } = await (supabase as any)
      .from('suites')
      .insert({ name, description: description || null })
      .select()
      .single()

    if (error) throw error
    if (data) setSuites(prev => [data as Suite, ...prev])
    return data as Suite
  }

  return { suites, loading, refresh: load, createSuite }
}

// ── Save a run result ─────────────────────────────────────────────────────────

export async function saveTestRun(run: Omit<TestRun, 'id' | 'created_at'>) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { data, error } = await (supabase as any)
    .from('test_runs')
    .insert(run)
    .select()
    .single()

  if (error) throw error
  return data as TestRun
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
