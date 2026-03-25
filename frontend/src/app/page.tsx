'use client'

import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Zap,
  Copy,
  Check,
  ChevronRight,
  AlertCircle,
  Play,
  RefreshCw,
  Settings,
  Loader2,
  Smartphone,
  ChevronDown,
} from 'lucide-react'
import type { TestResult, ExecutionResult } from '@/types'
import { generateTest, runTest, API_BASE } from '@/lib/api'

/* ─────────────────────────── types ─────────────────────────── */

type ResultTab = 'code' | 'quality' | 'enrichment'

/* ─────────────────────────── helpers ───────────────────────── */

const EXAMPLES = [
  'Test login with valid credentials navigates to home screen',
  'Verify signup form validation shows errors for invalid email',
  'Test settings screen toggle switches persist after app restart',
]

const ScoreBadge = ({ score, grade }: { score: number; grade: string }) => {
  const variant = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'destructive'

  return (
    <Badge variant={variant} className="flex items-center gap-3 rounded-xl px-4 py-3 text-base">
      <span className="text-3xl font-bold tabular-nums">{grade}</span>
      <div className="text-sm leading-tight">
        <p className="font-semibold">{score}/100</p>
        <p className="opacity-70">quality score</p>
      </div>
    </Badge>
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
      const data = await generateTest({
        test_description: description,
        test_type: 'ui',
        include_comments: true,
        discovery_enabled: true,
        bundle_id: settings.bundleId || undefined,
        device_udid: settings.deviceUdid || undefined,
      })
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
      const data = await runTest({
        test_code: result.test_code,
        bundle_id: settings.bundleId || undefined,
        device_udid: settings.deviceUdid || '',
        langsmith_run_id: result.metadata?.langsmith_run_id || undefined,
      })
      setExecutionResult(data)
      scrollTo(executionRef)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test')
    } finally {
      setExecutionLoading(false)
    }
  }

  /* ── available tabs ── */
  const hasQuality = !!result?.metadata?.quality_report
  const hasEnrichment = !!result?.metadata?.enrichment

  /* ─────────────── render ─────────────── */
  return (
    <div className="min-h-full bg-background">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">

        {/* ── Device bar ── */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <Card className="px-4 py-2.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-3 text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <Smartphone className="h-3.5 w-3.5" />
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
              <Settings className="h-3.5 w-3.5" />
              Configure
            </a>
          </Card>
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

        {/* ══════════════ SECTION 1 -- Input ══════════════ */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="p-6 space-y-4">
            {/* label */}
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-500/15 text-blue-400 text-xs font-bold">1</span>
              <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Describe your test</span>
            </div>

            {/* textarea */}
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. Test login with invalid password shows error message"
              rows={5}
              className="resize-none leading-relaxed"
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
                    <ChevronRight className="inline h-3 w-3 text-blue-400/60 mr-1.5" />
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            {/* generate button */}
            <Button
              onClick={handleGenerate}
              disabled={loading || !description.trim()}
              variant="default"
              className="w-full py-3 h-auto text-sm font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4" />
                  Generate Test
                  <kbd className="ml-1 hidden sm:inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-white/10 text-white/40 font-mono">
                    ⌘↵
                  </kbd>
                </>
              )}
            </Button>

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
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </motion.div>

        {/* ══════════════ SECTION 2 -- Results ══════════════ */}
        <AnimatePresence>
          {(result || loading) && (
            <motion.div
              ref={resultsRef}
              key="results-section"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45 }}
            >
              <Card className="overflow-hidden">
                {/* section header */}
                <CardHeader className="pb-0 flex-row items-center gap-2 space-y-0">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-500/15 text-purple-400 text-xs font-bold">2</span>
                  <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Generated test</span>
                  {result && (
                    <span className="ml-auto text-xs text-muted-foreground/50 font-mono">{result.class_name}</span>
                  )}
                </CardHeader>

                {/* skeleton while loading */}
                {loading && (
                  <CardContent className="pt-4 space-y-3">
                    {[70, 50, 85, 40, 60].map((w, i) => (
                      <Skeleton
                        key={i}
                        className="h-3 rounded-full"
                        style={{ width: `${w}%` }}
                      />
                    ))}
                  </CardContent>
                )}

                {/* tabs */}
                {result && (
                  <>
                    <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ResultTab)}>
                      <div className="px-6 pt-4">
                        <TabsList>
                          <TabsTrigger value="code">Code</TabsTrigger>
                          <TabsTrigger value="quality" disabled={!hasQuality}>Quality</TabsTrigger>
                          <TabsTrigger value="enrichment" disabled={!hasEnrichment}>Enrichment</TabsTrigger>
                        </TabsList>
                      </div>

                      {/* tab panels */}
                      <CardContent className="pt-4">
                        <AnimatePresence mode="wait">

                          {/* ── Code tab ── */}
                          <TabsContent value="code">
                            <motion.div
                              key="code"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              <div className="flex items-center justify-between mb-3">
                                <span className="text-xs text-muted-foreground/60">Swift / XCUITest</span>
                                <Button variant="ghost" size="sm" onClick={handleCopy}>
                                  {copied ? (
                                    <>
                                      <Check className="h-3.5 w-3.5 text-emerald-400" />
                                      <span className="text-emerald-400">Copied!</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="h-3.5 w-3.5" />
                                      Copy
                                    </>
                                  )}
                                </Button>
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
                          </TabsContent>

                          {/* ── Quality tab ── */}
                          <TabsContent value="quality">
                            {result.metadata?.quality_report && (
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
                                          <ChevronRight className="h-4 w-4 mt-0.5 shrink-0 text-blue-400/60" />
                                          {rec}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </motion.div>
                            )}
                          </TabsContent>

                          {/* ── Enrichment tab ── */}
                          <TabsContent value="enrichment">
                            {result.metadata?.enrichment && (
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
                                  <ChevronDown className="h-4 w-4 text-purple-400/40" />
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
                          </TabsContent>

                        </AnimatePresence>
                      </CardContent>
                    </Tabs>

                    {/* ── Run button (inside results card) ── */}
                    {!executionResult && (
                      <CardFooter className="flex-col items-stretch border-t border-border pt-6">
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                          <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground flex-1">Run in simulator</span>
                        </div>
                        <p className="text-xs text-muted-foreground/50 mt-1.5 mb-4">
                          Execute on <span className="text-white/60">{settings.deviceName}</span> · iOS {settings.iosVersion}
                        </p>
                        <Button
                          onClick={handleRunTest}
                          disabled={executionLoading}
                          variant="success"
                          className="w-full py-3 h-auto text-sm font-semibold"
                        >
                          {executionLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              Running in Simulator...
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4" />
                              Run in Simulator
                            </>
                          )}
                        </Button>
                      </CardFooter>
                    )}
                  </>
                )}
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ══════════════ SECTION 3 -- Execution ══════════════ */}
        <AnimatePresence>
          {executionResult && (
            <motion.div
              ref={executionRef}
              key="execution-section"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.45 }}
            >
              <Card className="overflow-hidden">
                {/* header */}
                <CardHeader className="flex-row items-center gap-3 space-y-0 border-b border-border pb-4">
                  <div className="flex items-center gap-2 flex-1">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                    <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">Execution</span>
                  </div>
                  <Badge variant={executionResult.success ? 'success' : 'destructive'} className="gap-1.5 px-2.5 py-1 text-xs font-semibold">
                    {executionResult.success ? (
                      <><Check className="h-3 w-3" />Passed</>
                    ) : (
                      <><AlertCircle className="h-3 w-3" />Failed</>
                    )}
                  </Badge>
                </CardHeader>

                <CardContent className="pt-6 space-y-6">
                  {/* video */}
                  {executionResult.video_url ? (
                    <div className="rounded-xl overflow-hidden bg-black ring-1 ring-white/[0.06]">
                      <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
                        <video
                          controls
                          playsInline
                          className="absolute inset-0 w-full h-full object-contain"
                          src={`${API_BASE}${executionResult.video_url}`}
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
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                      {executionResult.error}
                    </div>
                  )}

                  {/* failure screenshot */}
                  {executionResult.screenshot && (
                    <div className="space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground/60">Failure Screenshot</p>
                      <div className="rounded-xl overflow-hidden ring-1 ring-red-500/20 bg-black">
                        <img
                          src={`${API_BASE}${executionResult.screenshot}`}
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
                        <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                        View logs
                      </summary>
                      <pre className="mt-3 bg-black/40 rounded-xl px-4 py-3 text-xs text-white/50 overflow-x-auto leading-relaxed max-h-60 overflow-y-auto font-mono ring-1 ring-white/[0.04]">
                        {executionResult.logs}
                      </pre>
                    </details>
                  )}

                  {/* run again */}
                  <Button
                    variant="secondary"
                    onClick={() => {
                      setExecutionResult(null)
                      handleRunTest()
                    }}
                    className="w-full py-3 h-auto text-sm font-semibold"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Run Again
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* bottom padding */}
        <div className="h-8" />
      </div>
    </div>
  )
}
