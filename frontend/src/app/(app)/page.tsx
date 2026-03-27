'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import {
  Zap,
  Copy,
  Check,
  ChevronRight,
  AlertCircle,
  Play,
  RefreshCw,
  Loader2,
  Cloud,
  ChevronDown,
  FolderPlus,
  Plus,
} from 'lucide-react'
import type { TestResult, ExecutionResult } from '@/types'
import { generateTest, runTest, apiFetch, API_BASE } from '@/lib/api'
import { useSuites } from '@/lib/hooks'

type ResultTab = 'code' | 'quality' | 'enrichment'

const EXAMPLES = [
  'Test login with valid credentials navigates to home screen',
  'Verify signup form validation shows errors for invalid email',
  'Test settings screen toggle switches persist after app restart',
]

const ScoreBadge = ({ score, grade }: { score: number; grade: string }) => {
  const variant = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'destructive'
  return (
    <Badge variant={variant} className="flex items-center gap-3 rounded-xl px-4 py-3 text-base">
      <span className="text-3xl font-bold tabular-nums font-mono">{grade}</span>
      <div className="text-sm leading-tight">
        <p className="font-semibold">{score}/100</p>
        <p className="opacity-70">quality score</p>
      </div>
    </Badge>
  )
}

export default function TestGenerator() {
  const searchParams = useSearchParams()
  const preselectedSuiteId = searchParams.get('suiteId')

  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<ResultTab>('code')
  const [copied, setCopied] = useState(false)

  const [executionLoading, setExecutionLoading] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [executionMode, setExecutionMode] = useState<'local' | 'cloud'>('local')

  // Save to Suite state
  const { suites, createSuite } = useSuites()
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [saveTestName, setSaveTestName] = useState('')
  const [selectedSuiteId, setSelectedSuiteId] = useState<string>(preselectedSuiteId || '')
  const [showNewSuiteFields, setShowNewSuiteFields] = useState(false)
  const [newSuiteName, setNewSuiteName] = useState('')
  const [newSuiteDesc, setNewSuiteDesc] = useState('')
  const [savingToSuite, setSavingToSuite] = useState(false)
  const [savedSuiteTestId, setSavedSuiteTestId] = useState<string | null>(null)

  const [settings, setSettings] = useState({
    deviceName: 'iPhone 15 Pro',
    deviceUdid: '',
    iosVersion: '17.0',
    appName: 'YourApp',
    bundleId: '',
  })

  const resultsRef = useRef<HTMLDivElement>(null)
  const executionRef = useRef<HTMLDivElement>(null)

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
    } catch {}
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

  const scrollTo = (ref: React.RefObject<HTMLDivElement>) => {
    setTimeout(() => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
  }

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

  const handleCopy = () => {
    if (!result) return
    navigator.clipboard.writeText(result.test_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleRunTest = async () => {
    if (!result) return
    setExecutionLoading(true)
    setError(null)
    setExecutionResult(null)

    try {
      const cloudDevice = executionMode === 'cloud' ? (localStorage.getItem('testara_cloud_device') || undefined) : undefined
      const cloudOsVersion = executionMode === 'cloud' ? (localStorage.getItem('testara_cloud_os_version') || undefined) : undefined

      const data = await runTest({
        test_code: result.test_code,
        bundle_id: settings.bundleId || undefined,
        device_udid: executionMode === 'local' ? (settings.deviceUdid || '') : '',
        execution_mode: executionMode,
        cloud_device: cloudDevice,
        cloud_os_version: cloudOsVersion,
        langsmith_run_id: result.metadata?.langsmith_run_id || undefined,
        suite_id: selectedSuiteId || undefined,
        suite_test_id: savedSuiteTestId || undefined,
      })
      setExecutionResult(data)
      scrollTo(executionRef)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test')
    } finally {
      setExecutionLoading(false)
    }
  }

  const handleSaveToSuite = async () => {
    if (!result) return
    setSavingToSuite(true)
    try {
      let targetSuiteId = selectedSuiteId

      // Create new suite if requested
      if (showNewSuiteFields && newSuiteName.trim()) {
        const newSuite = await createSuite(newSuiteName.trim(), newSuiteDesc.trim() || undefined)
        targetSuiteId = newSuite.id
      }

      if (!targetSuiteId) {
        toast.error('Please select or create a suite')
        setSavingToSuite(false)
        return
      }

      const created = await apiFetch<any>(`/db/suites/${targetSuiteId}/tests`, {
        method: 'POST',
        body: JSON.stringify({
          name: saveTestName.trim() || result.class_name || 'Untitled Test',
          description: description,
          test_code: result.test_code,
          class_name: result.class_name,
          quality_score: result.metadata?.quality_report?.overall_score,
          quality_grade: result.metadata?.quality_report?.grade,
        }),
      })

      setSavedSuiteTestId(created.id)
      setSelectedSuiteId(targetSuiteId)
      toast.success('Test saved to suite')
      setShowSaveDialog(false)
    } catch (err) {
      toast.error('Failed to save test to suite')
    }
    setSavingToSuite(false)
  }

  const hasQuality = !!result?.metadata?.quality_report
  const hasEnrichment = !!result?.metadata?.enrichment

  return (
    <div className="min-h-full">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">

        {/* -- Hero -- */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
        >
          <h1 className="text-4xl font-extrabold tracking-tight font-headline">Generate iOS Test</h1>
          <p className="mt-1.5 text-on-surface-variant text-sm font-label uppercase tracking-widest">
            Describe what you want to test in plain English
          </p>
        </motion.div>

        {/* SECTION 1 -- Input */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="p-6 space-y-4">
            <div className="flex items-center gap-2">
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/15 text-primary text-xs font-bold">1</span>
              <span className="text-xs font-label uppercase tracking-widest text-zinc-500">Describe your test</span>
            </div>

            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g. Test login with invalid password shows error message"
              rows={5}
              className="w-full resize-none bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary focus:shadow-[0_0_15px_rgba(91,196,214,0.1)] transition-all leading-relaxed"
            />

            <div className="space-y-1.5">
              <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">Quick examples</p>
              <div className="flex flex-col gap-1.5">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setDescription(ex)}
                    className="text-left text-xs text-zinc-500 hover:text-white hover:bg-white/[0.04] px-3 py-1.5 rounded-lg transition-all border border-transparent hover:border-white/[0.06]"
                  >
                    <ChevronRight className="inline h-3 w-3 text-primary/60 mr-1.5" />
                    {ex}
                  </button>
                ))}
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={loading || !description.trim()}
              className="w-full py-3 h-auto text-sm"
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
                  <kbd className="ml-1 hidden sm:inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-mono bg-white/10 text-white/40">
                    {'\u2318\u21B5'}
                  </kbd>
                </>
              )}
            </Button>

            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="flex items-start gap-2 bg-error/10 border border-error/20 rounded-xl px-4 py-3 text-sm text-error">
                    <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </motion.div>

        {/* SECTION 2 -- Results */}
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
                <CardHeader className="pb-0 flex-row items-center gap-2 space-y-0">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-500/15 text-purple-400 text-xs font-bold">2</span>
                  <span className="text-xs font-label uppercase tracking-widest text-zinc-500">Generated test</span>
                  {result && (
                    <span className="ml-auto text-xs text-zinc-600 font-mono">{result.class_name}</span>
                  )}
                </CardHeader>

                {loading && (
                  <CardContent className="pt-4 space-y-3">
                    {[70, 50, 85, 40, 60].map((w, i) => (
                      <Skeleton key={i} className="h-3 rounded-full bg-surface-high" style={{ width: `${w}%` }} />
                    ))}
                  </CardContent>
                )}

                {result && (
                  <>
                    {/* Tab bar */}
                    <div className="px-6 pt-4 flex gap-1 border-b border-white/5">
                      {(['code', 'quality', 'enrichment'] as ResultTab[]).map((tab) => {
                        const disabled = (tab === 'quality' && !hasQuality) || (tab === 'enrichment' && !hasEnrichment)
                        return (
                          <button
                            key={tab}
                            onClick={() => !disabled && setActiveTab(tab)}
                            disabled={disabled}
                            className={`px-4 py-2.5 text-xs font-label uppercase tracking-widest transition-colors border-b-2 ${
                              activeTab === tab
                                ? 'text-primary border-primary'
                                : disabled
                                ? 'text-zinc-700 border-transparent cursor-not-allowed'
                                : 'text-zinc-500 border-transparent hover:text-zinc-300'
                            }`}
                          >
                            {tab}
                          </button>
                        )
                      })}
                    </div>

                    <CardContent className="pt-6">
                      {/* Code tab */}
                      {activeTab === 'code' && (
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">Python / Appium</span>
                            <Button variant="ghost" size="sm" onClick={handleCopy}>
                              {copied ? (
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
                              {result.test_code}
                            </SyntaxHighlighter>
                          </div>
                        </div>
                      )}

                      {/* Quality tab */}
                      {activeTab === 'quality' && result.metadata?.quality_report && (
                        <div className="space-y-5">
                          <div className="flex items-center gap-4">
                            <ScoreBadge
                              score={result.metadata.quality_report.overall_score}
                              grade={result.metadata.quality_report.grade}
                            />
                            <div className="text-sm text-zinc-500">
                              Confidence: <span className="text-white font-medium capitalize">{result.metadata.quality_report.confidence}</span>
                            </div>
                          </div>
                          {result.metadata.quality_report.recommendations.length > 0 && (
                            <div>
                              <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600 mb-3">Recommendations</p>
                              <ul className="space-y-2.5">
                                {result.metadata.quality_report.recommendations.map((rec, i) => (
                                  <li key={i} className="flex items-start gap-2.5 text-sm text-zinc-400">
                                    <ChevronRight className="h-4 w-4 mt-0.5 shrink-0 text-primary/60" />
                                    {rec}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Enrichment tab */}
                      {activeTab === 'enrichment' && result.metadata?.enrichment && (
                        <div className="space-y-4">
                          <div className="space-y-1.5">
                            <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600">Original</p>
                            <p className="text-sm text-zinc-400 leading-relaxed bg-surface-low rounded-xl px-4 py-3 border border-white/[0.04]">
                              {result.metadata.enrichment.original_description}
                            </p>
                          </div>
                          <div className="flex justify-center">
                            <ChevronDown className="h-4 w-4 text-purple-400/40" />
                          </div>
                          <div className="space-y-1.5">
                            <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600 flex items-center gap-1.5">
                              <span className="text-purple-400">&#10022;</span> AI Enriched
                            </p>
                            <p className="text-sm text-white leading-relaxed bg-purple-500/[0.06] rounded-xl px-4 py-3 border border-purple-500/[0.12]">
                              {result.metadata.enrichment.enriched_description}
                            </p>
                          </div>
                        </div>
                      )}
                    </CardContent>

                    {/* Save to Suite + Run buttons */}
                    {!executionResult && (
                      <CardFooter className="flex-col items-stretch border-t border-white/5 pt-6 gap-4">
                        {/* Save to Suite */}
                        <div className="flex items-center gap-2">
                          {savedSuiteTestId ? (
                            <Badge variant="success" className="gap-1.5">
                              <Check className="h-3 w-3" />
                              Saved to suite
                            </Badge>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSaveTestName(result?.class_name || '')
                                setSelectedSuiteId(preselectedSuiteId || '')
                                setShowSaveDialog(true)
                              }}
                            >
                              <FolderPlus className="h-3.5 w-3.5" />
                              Save to Suite
                            </Button>
                          )}
                        </div>

                        {/* Execute section */}
                        <div className="flex items-center gap-2">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                          <span className="text-xs font-label uppercase tracking-widest text-zinc-500 flex-1">Execute test</span>
                        </div>

                        <div className="flex gap-2 p-1 rounded-xl bg-surface-low">
                          <button
                            onClick={() => setExecutionMode('local')}
                            className={`flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-label uppercase tracking-widest transition-all ${
                              executionMode === 'local'
                                ? 'bg-surface-container text-white'
                                : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                          >
                            Local
                          </button>
                          <button
                            onClick={() => setExecutionMode('cloud')}
                            className={`flex-1 flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-label uppercase tracking-widest transition-all ${
                              executionMode === 'cloud'
                                ? 'bg-surface-container text-white'
                                : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                          >
                            <Cloud className="h-3.5 w-3.5" />
                            Cloud
                          </button>
                        </div>

                        <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">
                          {executionMode === 'local' ? (
                            <>Execute on <span className="text-zinc-400">{settings.deviceName}</span> &middot; iOS {settings.iosVersion}</>
                          ) : (
                            <>Execute on <span className="text-zinc-400">{typeof window !== 'undefined' && localStorage.getItem('testara_cloud_device') || 'iPhone 15 Pro'}</span> (cloud)</>
                          )}
                        </p>

                        <Button
                          onClick={handleRunTest}
                          disabled={executionLoading}
                          variant="success"
                          className="w-full py-3 h-auto text-sm"
                        >
                          {executionLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              {executionMode === 'cloud' ? 'Running on Cloud...' : 'Running on Simulator...'}
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4" />
                              {executionMode === 'cloud' ? 'Run on Cloud' : 'Run on Simulator'}
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

        {/* SECTION 3 -- Execution */}
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
                <CardHeader className="flex-row items-center gap-3 space-y-0 border-b border-white/5 pb-4">
                  <div className="flex items-center gap-2 flex-1">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-400 text-xs font-bold">3</span>
                    <span className="text-xs font-label uppercase tracking-widest text-zinc-500">Execution</span>
                  </div>
                  <Badge variant={executionResult.success ? 'success' : 'destructive'} className="gap-1.5 px-2.5 py-1 text-xs">
                    {executionResult.success ? (
                      <><Check className="h-3 w-3" />Passed</>
                    ) : (
                      <><AlertCircle className="h-3 w-3" />Failed</>
                    )}
                  </Badge>
                </CardHeader>

                <CardContent className="pt-6 space-y-6">
                  {executionResult.execution_mode === 'cloud' && executionResult.session_id ? (
                    <div className="rounded-xl overflow-hidden bg-black ring-1 ring-white/[0.06]">
                      <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
                        <video
                          controls
                          playsInline
                          className="absolute inset-0 w-full h-full object-contain"
                          src={`${API_BASE}/cloud/video/${executionResult.session_id}`}
                        />
                      </div>
                    </div>
                  ) : executionResult.video_url ? (
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
                  ) : null}

                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'Device', value: executionResult.device || '—' },
                      { label: 'iOS', value: executionResult.os_version || executionResult.ios_version || '—' },
                      { label: 'Duration', value: `${executionResult.duration?.toFixed(2) || 0}s` },
                      { label: 'Test ID', value: executionResult.test_id, mono: true },
                    ].map(({ label, value, mono }) => (
                      <div key={label} className="bg-surface-low rounded-xl px-4 py-3 border border-white/[0.04]">
                        <p className="text-[10px] text-zinc-600 mb-0.5 font-label uppercase tracking-widest">{label}</p>
                        <p className={`text-sm text-white truncate ${mono ? 'font-mono text-xs' : 'font-medium'}`}>{value}</p>
                      </div>
                    ))}
                  </div>

                  {executionResult.error && (
                    <div className="flex items-start gap-2 bg-error/10 border border-error/20 rounded-xl px-4 py-3 text-sm text-error">
                      <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                      {executionResult.error}
                    </div>
                  )}

                  {executionResult.screenshot && (
                    <div className="space-y-2">
                      <p className="text-[10px] font-label uppercase tracking-widest text-zinc-600">Failure Screenshot</p>
                      <div className="rounded-xl overflow-hidden ring-1 ring-rose-500/20 bg-black">
                        <img
                          src={`${API_BASE}${executionResult.screenshot}`}
                          alt="Failure screenshot"
                          className="w-full h-auto object-contain max-h-[500px]"
                        />
                      </div>
                    </div>
                  )}

                  {executionResult.logs && (
                    <details className="group">
                      <summary className="cursor-pointer text-xs font-label uppercase tracking-widest text-zinc-600 hover:text-white transition-colors flex items-center gap-1.5 select-none">
                        <ChevronRight className="h-3.5 w-3.5 transition-transform group-open:rotate-90" />
                        View logs
                      </summary>
                      <pre className="mt-3 bg-black/40 rounded-xl px-4 py-3 text-xs text-zinc-500 overflow-x-auto leading-relaxed max-h-60 overflow-y-auto font-mono ring-1 ring-white/[0.04]">
                        {executionResult.logs}
                      </pre>
                    </details>
                  )}

                  <Button
                    variant="secondary"
                    onClick={() => {
                      setExecutionResult(null)
                      handleRunTest()
                    }}
                    className="w-full py-3 h-auto text-sm"
                  >
                    <RefreshCw className="h-4 w-4" />
                    Run Again
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="h-8" />
      </div>

      {/* Save to Suite Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent onClose={() => setShowSaveDialog(false)}>
          <DialogHeader>
            <DialogTitle>Save to Suite</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Test Name</label>
              <input
                value={saveTestName}
                onChange={(e) => setSaveTestName(e.target.value)}
                placeholder="e.g. Login with valid credentials"
                autoFocus
                className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
              />
            </div>

            {!showNewSuiteFields ? (
              <div>
                <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Select Suite</label>
                <select
                  value={selectedSuiteId}
                  onChange={(e) => setSelectedSuiteId(e.target.value)}
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary transition-all"
                >
                  <option value="">Choose a suite...</option>
                  {suites.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
                <button
                  onClick={() => setShowNewSuiteFields(true)}
                  className="mt-2 flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  <Plus className="h-3 w-3" />
                  Create new suite
                </button>
              </div>
            ) : (
              <div className="space-y-3 p-3 rounded-xl border border-primary/20 bg-primary/5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-label uppercase tracking-widest text-primary">New Suite</span>
                  <button
                    onClick={() => setShowNewSuiteFields(false)}
                    className="text-xs text-zinc-500 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </div>
                <input
                  value={newSuiteName}
                  onChange={(e) => setNewSuiteName(e.target.value)}
                  placeholder="Suite name"
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
                <input
                  value={newSuiteDesc}
                  onChange={(e) => setNewSuiteDesc(e.target.value)}
                  placeholder="Description (optional)"
                  className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveDialog(false)} className="flex-1">
              Cancel
            </Button>
            <Button
              onClick={handleSaveToSuite}
              disabled={savingToSuite || (!selectedSuiteId && !(showNewSuiteFields && newSuiteName.trim()))}
              className="flex-1"
            >
              {savingToSuite ? 'Saving...' : 'Save Test'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
