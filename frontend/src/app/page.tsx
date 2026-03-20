'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

/* ─────────────────────────── types ─────────────────────────── */

interface TestResult {
  test_code: string
  test_type: string
  class_name: string
  metadata?: {
    quality_report?: {
      overall_score: number
      grade: string
      confidence: string
      recommendations: string[]
    }
    enrichment?: {
      original_description: string
      enriched_description: string
    }
  }
}

interface ExecutionResult {
  success: boolean
  test_id: string
  video_url: string | null
  screenshot: string | null
  logs: string
  duration: number
  device: string
  ios_version: string
  error?: string
}

type ResultTab = 'code' | 'quality' | 'enrichment'

/* ─────────────────────────── helpers ───────────────────────── */

const EXAMPLES = [
  'Test login with valid credentials navigates to home screen',
  'Verify signup form validation shows errors for invalid email',
  'Test settings screen toggle switches persist after app restart',
]

const Spinner = () => (
  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

const ScoreBadge = ({ score, grade }: { score: number; grade: string }) => {
  const color =
    score >= 80
      ? 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10'
      : score >= 60
      ? 'text-amber-400 border-amber-400/30 bg-amber-400/10'
      : 'text-red-400 border-red-400/30 bg-red-400/10'

  return (
    <div className={`flex items-center gap-3 border rounded-xl px-4 py-3 ${color}`}>
      <span className="text-3xl font-bold tabular-nums">{grade}</span>
      <div className="text-sm leading-tight">
        <p className="font-semibold">{score}/100</p>
        <p className="opacity-70">quality score</p>
      </div>
    </div>
  )
}

/* ─────────────────────────── component ─────────────────────── */

export default function TestGenerator() {
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<ResultTab>('code')
  const [copied, setCopied] = useState(false)

  const [executionLoading, setExecutionLoading] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)

  const [settings, setSettings] = useState({
    deviceName: 'iPhone 15 Pro',
    deviceUdid: '',
    iosVersion: '17.0',
    appName: 'YourApp',
    bundleId: '',
  })

  const resultsRef = useRef<HTMLDivElement>(null)
  const executionRef = useRef<HTMLDivElement>(null)

  /* ── settings ── */
  const loadSettings = () => {
    const stored = localStorage.getItem('testara_settings')
    if (!stored) return
    try {
      const p = JSON.parse(stored)
      setSettings({
        deviceName: p.deviceName || p.device || 'iPhone 15 Pro',
        deviceUdid: p.deviceUdid || '',
        iosVersion: p.iosVersion || '17.0',
        appName: p.appName || 'YourApp',
        bundleId: p.bundleId || '',
      })
    } catch (_) {}
  }

  useEffect(() => {
    loadSettings()
    const onVisibility = () => { if (!document.hidden) loadSettings() }
    const onStorage = (e: StorageEvent) => { if (e.key === 'testara_settings') loadSettings() }
    document.addEventListener('visibilitychange', onVisibility)
    window.addEventListener('storage', onStorage)
    return () => {
      document.removeEventListener('visibilitychange', onVisibility)
      window.removeEventListener('storage', onStorage)
    }
  }, [])

  /* ── scroll helpers ── */
  const scrollTo = (ref: React.RefObject<HTMLDivElement>) => {
    setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
  }

  /* ── generate ── */
  const handleGenerate = async () => {
    if (!description.trim()) { setError('Please provide a test description'); return }
    setLoading(true)
    setError(null)
    setResult(null)
    setExecutionResult(null)

    try {
      const res = await fetch('http://localhost:8000/generate-test-with-rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_description: description,
          test_type: 'ui',
          include_comments: true,
          discovery_enabled: true,
          bundle_id: settings.bundleId || undefined,
          device_udid: settings.deviceUdid || undefined,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        throw new Error(err?.detail || 'Failed to generate test')
      }
      const data = await res.json()
      setResult(data)
      setActiveTab('code')
      scrollTo(resultsRef)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate test')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate()
  }

  /* ── copy ── */
  const handleCopy = () => {
    if (!result) return
    navigator.clipboard.writeText(result.test_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  /* ── run ── */
  const handleRunTest = async () => {
    if (!result) return
    setExecutionLoading(true)
    setError(null)
    setExecutionResult(null)

    try {
      const res = await fetch('http://localhost:8000/run-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_code: result.test_code,
          bundle_id: settings.bundleId || undefined,
          device_udid: settings.deviceUdid || '',
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => null)
        throw new Error(err?.detail || 'Failed to run test')
      }
      const data = await res.json()
      setExecutionResult(data)
      scrollTo(executionRef)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test')
    } finally {
      setExecutionLoading(false)
    }
  }

  /* ── available tabs ── */
  const tabs: { id: ResultTab; label: string; available: boolean }[] = [
    { id: 'code', label: 'Code', available: true },
    { id: 'quality', label: 'Quality', available: !!result?.metadata?.quality_report },
    { id: 'enrichment', label: 'Enrichment', available: !!result?.metadata?.enrichment },
  ]

  /* ─────────────── render ─────────────── */
  return (
    <div className="min-h-full bg-background">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">

        {/* ── Device bar ── */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass rounded-xl px-4 py-2.5 flex items-center justify-between text-xs"
        >
          <div className="flex items-center gap-3 text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="text-sm">📱</span>
              <span className="font-medium">{settings.deviceName}</span>
            </span>
            <span className="opacity-30">·</span>
            <span>iOS {settings.iosVersion}</span>
            {settings.deviceUdid && (
              <>
                <span className="opacity-30">·</span>
                <span className="flex items-center gap-1 text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  Physical device
                </span>
              </>
            )}
          </div>
          <a
            href="/settings"
            className="flex items-center gap-1.5 text-muted-foreground hover:text-white transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Configure
          </a>
        </motion.div>

        {/* ── Hero ── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
        >
          <h1 className="text-3xl font-bold tracking-tight">Generate iOS Test</h1>
          <p className="mt-1.5 text-muted-foreground text-sm">
            Describe what you want to test in plain English — Testara handles the rest.
          </p>
        </motion.div>

        {/* ══════════════ SECTION 1 — Input ══════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass rounded-2xl p-6 space-y-4"
        >
          {/* label */}
          <div className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/15 text-blue-400 text-xs font-bold">1</span>
            <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Describe your test</span>
          </div>

          {/* textarea */}
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. Test login with invalid password shows error message"
            rows={5}
            className="w-full resize-none rounded-xl bg-black/30 border border-white/[0.06] px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:ring-1 focus:ring-blue-500/60 focus:border-blue-500/40 transition-all leading-relaxed"
          />

          {/* example chips */}
          <div className="space-y-1.5">
            <p className="text-xs text-muted-foreground/60 font-medium">Quick examples</p>
            <div className="flex flex-col gap-1.5">
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setDescription(ex)}
                  className="text-left text-xs text-muted-foreground hover:text-white hover:bg-white/[0.04] px-3 py-1.5 rounded-lg transition-all border border-transparent hover:border-white/[0.06]"
                >
                  <span className="text-blue-400/60 mr-1.5">→</span>{ex}
                </button>
              ))}
            </div>
          </div>

          {/* generate button */}
          <motion.button
            onClick={handleGenerate}
            disabled={loading || !description.trim()}
            whileHover={{ scale: loading || !description.trim() ? 1 : 1.015 }}
            whileTap={{ scale: loading || !description.trim() ? 1 : 0.985 }}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-blue-500 hover:bg-blue-400 disabled:bg-white/[0.06] disabled:text-white/20 disabled:cursor-not-allowed text-white text-sm font-semibold py-3 transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:shadow-none"
          >
            {loading ? (
              <><Spinner />Generating…</>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Generate Test
                <kbd className="ml-1 hidden sm:inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-white/10 text-white/40 font-mono">⌘↵</kbd>
              </>
            )}
          </motion.button>

          {/* error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
                  <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* ══════════════ SECTION 2 — Results ══════════════ */}
        <AnimatePresence>
          {(result || loading) && (
            <motion.div
              ref={resultsRef}
              key="results-section"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45 }}
              className="glass rounded-2xl overflow-hidden"
            >
              {/* section header */}
              <div className="px-6 pt-5 pb-0 flex items-center gap-2 mb-4">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-500/15 text-purple-400 text-xs font-bold">2</span>
                <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Generated test</span>
                {result && (
                  <span className="ml-auto text-xs text-muted-foreground/50 font-mono">{result.class_name}</span>
                )}
              </div>

              {/* skeleton while loading */}
              {loading && (
                <div className="px-6 pb-6 space-y-3">
                  {[70, 50, 85, 40, 60].map((w, i) => (
                    <div
                      key={i}
                      className="h-3 rounded-full bg-white/[0.05] animate-pulse"
                      style={{ width: `${w}%` }}
                    />
                  ))}
                </div>
              )}

              {/* tabs */}
              {result && (
                <>
                  <div className="px-6 flex gap-0.5 border-b border-white/[0.06]">
                    {tabs.map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => tab.available && setActiveTab(tab.id)}
                        disabled={!tab.available}
                        className={`relative px-4 py-2.5 text-xs font-semibold transition-colors ${
                          activeTab === tab.id
                            ? 'text-white'
                            : tab.available
                            ? 'text-muted-foreground hover:text-white/70'
                            : 'text-white/15 cursor-not-allowed'
                        }`}
                      >
                        {tab.label}
                        {activeTab === tab.id && (
                          <motion.div
                            layoutId="tab-underline"
                            className="absolute bottom-0 left-0 right-0 h-px bg-white"
                          />
                        )}
                      </button>
                    ))}
                  </div>

                  {/* tab panels */}
                  <div className="p-6">
                    <AnimatePresence mode="wait">

                      {/* ── Code tab ── */}
                      {activeTab === 'code' && (
                        <motion.div
                          key="code"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-xs text-muted-foreground/60">Swift / XCUITest</span>
                            <button
                              onClick={handleCopy}
                              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-white transition-colors"
                            >
                              {copied ? (
                                <>
                                  <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                  <span className="text-emerald-400">Copied!</span>
                                </>
                              ) : (
                                <>
                                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                  Copy
                                </>
                              )}
                            </button>
                          </div>
                          <div className="rounded-xl overflow-hidden ring-1 ring-white/[0.06]">
                            <SyntaxHighlighter
                              language="python"
                              style={vscDarkPlus}
                              customStyle={{ margin: 0, borderRadius: '0.75rem', fontSize: '0.8125rem', lineHeight: '1.6' }}
                            >
                              {result.test_code}
                            </SyntaxHighlighter>
                          </div>
                        </motion.div>
                      )}

                      {/* ── Quality tab ── */}
                      {activeTab === 'quality' && result.metadata?.quality_report && (
                        <motion.div
                          key="quality"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="space-y-5"
                        >
                          <div className="flex items-center gap-4">
                            <ScoreBadge
                              score={result.metadata.quality_report.overall_score}
                              grade={result.metadata.quality_report.grade}
                            />
                            <div className="text-sm text-muted-foreground">
                              Confidence: <span className="text-white font-medium capitalize">{result.metadata.quality_report.confidence}</span>
                            </div>
                          </div>

                          {result.metadata.quality_report.recommendations.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60 mb-3">Recommendations</p>
                              <ul className="space-y-2.5">
                                {result.metadata.quality_report.recommendations.map((rec, i) => (
                                  <li key={i} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                                    <svg className="w-4 h-4 mt-0.5 shrink-0 text-blue-400/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                    {rec}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </motion.div>
                      )}

                      {/* ── Enrichment tab ── */}
                      {activeTab === 'enrichment' && result.metadata?.enrichment && (
                        <motion.div
                          key="enrichment"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="space-y-4"
                        >
                          <div className="space-y-1.5">
                            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60">Original</p>
                            <p className="text-sm text-muted-foreground leading-relaxed bg-white/[0.03] rounded-xl px-4 py-3 border border-white/[0.04]">
                              {result.metadata.enrichment.original_description}
                            </p>
                          </div>
                          <div className="flex justify-center">
                            <svg className="w-4 h-4 text-purple-400/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                          <div className="space-y-1.5">
                            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60 flex items-center gap-1.5">
                              <span className="text-purple-400">✦</span> AI Enriched
                            </p>
                            <p className="text-sm text-white leading-relaxed bg-purple-500/[0.06] rounded-xl px-4 py-3 border border-purple-500/[0.12]">
                              {result.metadata.enrichment.enriched_description}
                            </p>
                          </div>
                        </motion.div>
                      )}

                    </AnimatePresence>
                  </div>

                  {/* ── Run button (inside results card) ── */}
                  {!executionResult && (
                    <div className="px-6 pb-6">
                      <div className="h-px bg-white/[0.06] mb-5" />
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                        <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex-1">Run in simulator</span>
                      </div>
                      <p className="text-xs text-muted-foreground/50 mt-1.5 mb-4">
                        Execute on <span className="text-white/60">{settings.deviceName}</span> · iOS {settings.iosVersion}
                      </p>
                      <motion.button
                        onClick={handleRunTest}
                        disabled={executionLoading}
                        whileHover={{ scale: executionLoading ? 1 : 1.015 }}
                        whileTap={{ scale: executionLoading ? 1 : 0.985 }}
                        className="w-full flex items-center justify-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:bg-white/[0.06] disabled:text-white/20 disabled:cursor-not-allowed text-white text-sm font-semibold py-3 transition-all duration-200 shadow-lg shadow-emerald-500/20 disabled:shadow-none"
                      >
                        {executionLoading ? (
                          <><Spinner />Running in Simulator…</>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Run in Simulator
                          </>
                        )}
                      </motion.button>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* ══════════════ SECTION 3 — Execution ══════════════ */}
        <AnimatePresence>
          {executionResult && (
            <motion.div
              ref={executionRef}
              key="execution-section"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45 }}
              className="glass rounded-2xl overflow-hidden"
            >
              {/* header */}
              <div className="px-6 pt-5 pb-4 flex items-center gap-3 border-b border-white/[0.06]">
                <div className="flex items-center gap-2 flex-1">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Execution</span>
                </div>
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${
                  executionResult.success
                    ? 'bg-emerald-500/15 text-emerald-400'
                    : 'bg-red-500/15 text-red-400'
                }`}>
                  {executionResult.success ? (
                    <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>Passed</>
                  ) : (
                    <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" /></svg>Failed</>
                  )}
                </span>
              </div>

              <div className="p-6 space-y-6">
                {/* video — fixed 16:9 container, never causes layout shift */}
                {executionResult.video_url ? (
                  <div className="rounded-xl overflow-hidden bg-black ring-1 ring-white/[0.06]">
                    {/* 16:9 aspect ratio box */}
                    <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
                      <video
                        controls
                        playsInline
                        className="absolute inset-0 w-full h-full object-contain"
                        src={`http://localhost:8000${executionResult.video_url}`}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="rounded-xl ring-1 ring-white/[0.06] bg-white/[0.02] flex items-center justify-center" style={{ height: '280px' }}>
                    <p className="text-sm text-muted-foreground/40">No recording available</p>
                  </div>
                )}

                {/* meta grid */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Device', value: executionResult.device },
                    { label: 'iOS', value: executionResult.ios_version },
                    { label: 'Duration', value: `${executionResult.duration.toFixed(2)}s` },
                    { label: 'Test ID', value: executionResult.test_id, mono: true },
                  ].map(({ label, value, mono }) => (
                    <div key={label} className="bg-white/[0.03] rounded-xl px-4 py-3 border border-white/[0.04]">
                      <p className="text-xs text-muted-foreground/60 mb-0.5">{label}</p>
                      <p className={`text-sm text-white truncate ${mono ? 'font-mono text-xs' : 'font-medium'}`}>{value}</p>
                    </div>
                  ))}
                </div>

                {/* error banner */}
                {executionResult.error && (
                  <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
                    <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {executionResult.error}
                  </div>
                )}

                {/* failure screenshot */}
                {executionResult.screenshot && (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60">Failure Screenshot</p>
                    <div className="rounded-xl overflow-hidden ring-1 ring-red-500/20 bg-black">
                      <img
                        src={`http://localhost:8000${executionResult.screenshot}`}
                        alt="Failure screenshot"
                        className="w-full h-auto object-contain max-h-[500px]"
                      />
                    </div>
                  </div>
                )}

                {/* logs */}
                {executionResult.logs && (
                  <details className="group">
                    <summary className="cursor-pointer text-xs font-semibold text-muted-foreground/60 hover:text-white transition-colors flex items-center gap-1.5 select-none">
                      <svg className="w-3.5 h-3.5 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      View logs
                    </summary>
                    <pre className="mt-3 bg-black/40 rounded-xl px-4 py-3 text-xs text-white/50 overflow-x-auto leading-relaxed max-h-60 overflow-y-auto font-mono ring-1 ring-white/[0.04]">
                      {executionResult.logs}
                    </pre>
                  </details>
                )}

                {/* run again */}
                <button
                  onClick={() => {
                    setExecutionResult(null)
                    handleRunTest()
                  }}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-white/[0.06] hover:bg-white/[0.09] text-sm font-semibold py-3 text-white/70 hover:text-white transition-all duration-200"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Run Again
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* bottom padding */}
        <div className="h-8" />
      </div>
    </div>
  )
}
