'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface TestResult {
  swift_code: string
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
  logs: string
  duration: number
  device: string
  ios_version: string
  error?: string
}

export default function TestGenerator() {
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TestResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [executionLoading, setExecutionLoading] = useState(false)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null)
  const [settings, setSettings] = useState({
    deviceName: 'iPhone 15 Pro',
    deviceUdid: '',
    iosVersion: '17.0',
    appName: 'YourApp',
  })

  const loadSettings = () => {
    const stored = localStorage.getItem('testara_settings')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        console.log('Loaded settings from localStorage:', parsed)
        setSettings({
          deviceName: parsed.deviceName || parsed.device || 'iPhone 15 Pro',
          deviceUdid: parsed.deviceUdid || '',
          iosVersion: parsed.iosVersion || '17.0',
          appName: parsed.appName || 'YourApp',
        })
      } catch (e) {
        console.error('Failed to parse settings:', e)
      }
    } else {
      console.log('No settings found in localStorage')
    }
  }

  useEffect(() => {
    // Load settings on mount
    loadSettings()
    
    // Reload settings when page becomes visible (user returns from Settings)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadSettings()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    // Also listen for storage events (in case settings changed in another tab)
    window.addEventListener('storage', (e) => {
      if (e.key === 'testara_settings') {
        loadSettings()
      }
    })
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  const handleGenerate = async () => {
    if (!description.trim()) {
      setError('Please provide a test description')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/generate-test-with-rag', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_description: description,
          test_type: 'ui',
          include_comments: true,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Failed to generate test')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate test')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleGenerate()
    }
  }

  const handleRunTest = async () => {
    if (!result) return

    setExecutionLoading(true)
    setError(null)

    const deviceToUse = settings.deviceUdid || settings.deviceName
    console.log('Running test with settings:', {
      device: deviceToUse,
      deviceUdid: settings.deviceUdid,
      deviceName: settings.deviceName,
      ios_version: settings.iosVersion,
      app_name: settings.appName,
    })

    try {
      const response = await fetch('http://localhost:8000/run-test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          test_code: result.swift_code,
          app_name: settings.appName,
          device: deviceToUse,  // Use UDID if available
          ios_version: settings.iosVersion,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Failed to run test')
      }

      const data = await response.json()
      setExecutionResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test')
    } finally {
      setExecutionLoading(false)
    }
  }

  return (
    <div className="h-full bg-background">
      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Settings Indicator */}
        <div className="mb-6 glass p-3 rounded-lg flex items-center justify-between text-sm">
          <div className="flex items-center gap-4 text-muted">
            <span>📱 {settings.deviceName}</span>
            <span>•</span>
            <span>iOS {settings.iosVersion}</span>
            {settings.deviceUdid && <span className="text-green-400">🟢</span>}
          </div>
          <a
            href="/settings"
            className="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Configure
          </a>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column: Input */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-4xl font-bold mb-2">Generate iOS Test</h1>
              <p className="text-gray-400">
                Describe what you want to test in plain English
              </p>
            </motion.div>

            {/* Test Description */}
            <motion.div
              className="glass p-6 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.6 }}
            >
              <label className="block text-sm font-semibold mb-3">
                Test Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Example: Test login with invalid password shows error message"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={6}
              />
              <p className="text-xs text-gray-500 mt-2">
                Describe what the test should verify • Press ⌘+Enter to generate
              </p>
            </motion.div>

            {/* Example Prompts */}
            <motion.div
              className="glass p-4 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <div className="text-xs font-semibold text-gray-400 mb-2">
                Example prompts:
              </div>
              <div className="space-y-2">
                {[
                  'Test login with valid credentials navigates to home screen',
                  'Verify signup form validation shows errors for invalid email',
                  'Test settings screen toggle switches persist after app restart',
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setDescription(example)}
                    className="w-full text-left text-sm text-gray-400 hover:text-blue-400 transition-colors p-2 rounded hover:bg-gray-800/50"
                  >
                    → {example}
                  </button>
                ))}
              </div>
            </motion.div>

            {/* Generate Button */}
            <motion.button
              onClick={handleGenerate}
              disabled={loading || !description.trim()}
              className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
              whileHover={{ scale: loading ? 1 : 1.02 }}
              whileTap={{ scale: loading ? 1 : 0.98 }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="animate-spin h-5 w-5"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Test'
              )}
            </motion.button>

            {/* Error Message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-red-500/10 border border-red-500/50 rounded-lg p-4"
                >
                  <p className="text-red-400 text-sm">{error}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right Column: Results */}
          <div className="space-y-6">
            <AnimatePresence mode="wait">
              {result ? (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.6 }}
                  className="space-y-6"
                >
                  {/* Quality Score */}
                  {result.metadata?.quality_report && (
                    <div className="glass p-6 rounded-xl">
                      <h3 className="text-lg font-semibold mb-4">Quality Score</h3>
                      <div className="flex items-center gap-4 mb-4">
                        <div className="text-5xl font-bold text-blue-400">
                          {result.metadata.quality_report.grade}
                        </div>
                        <div>
                          <div className="text-2xl font-semibold">
                            {result.metadata.quality_report.overall_score}/100
                          </div>
                          <div className="text-sm text-gray-400">
                            Confidence: {result.metadata.quality_report.confidence}
                          </div>
                        </div>
                      </div>

                      {result.metadata.quality_report.recommendations.length > 0 && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2">
                            Recommendations
                          </h4>
                          <ul className="space-y-1">
                            {result.metadata.quality_report.recommendations.map(
                              (rec, i) => (
                                <li
                                  key={i}
                                  className="text-sm text-gray-400 flex items-start gap-2"
                                >
                                  <span className="text-blue-400 mt-1">•</span>
                                  <span>{rec}</span>
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Enrichment Info */}
                  {result.metadata?.enrichment && (
                    <div className="glass p-4 rounded-xl">
                      <details className="group">
                        <summary className="text-sm font-semibold cursor-pointer text-gray-400 hover:text-white transition-colors">
                          ✨ AI Enrichment Applied
                        </summary>
                        <div className="mt-3 space-y-2 text-xs">
                          <div>
                            <span className="text-gray-500">Original:</span>
                            <p className="text-gray-400 mt-1">
                              {result.metadata.enrichment.original_description}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500">Enriched:</span>
                            <p className="text-gray-400 mt-1">
                              {result.metadata.enrichment.enriched_description}
                            </p>
                          </div>
                        </div>
                      </details>
                    </div>
                  )}

                  {/* Generated Code */}
                  <div className="glass p-6 rounded-xl">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold">
                        {result.class_name}
                      </h3>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(result.swift_code)
                        }}
                        className="text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                        Copy
                      </button>
                    </div>

                    <div className="rounded-lg overflow-hidden">
                      <SyntaxHighlighter
                        language="swift"
                        style={vscDarkPlus}
                        customStyle={{
                          margin: 0,
                          borderRadius: '0.5rem',
                          fontSize: '0.875rem',
                        }}
                      >
                        {result.swift_code}
                      </SyntaxHighlighter>
                    </div>
                  </div>

                  {/* Run in Simulator Button */}
                  {!executionResult && (
                    <motion.button
                      onClick={handleRunTest}
                      disabled={executionLoading}
                      className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 hover:scale-105 disabled:hover:scale-100"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3, duration: 0.6 }}
                      whileHover={{ scale: executionLoading ? 1 : 1.02 }}
                      whileTap={{ scale: executionLoading ? 1 : 0.98 }}
                    >
                      {executionLoading ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Running in Simulator...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Run in Simulator
                        </span>
                      )}
                    </motion.button>
                  )}

                  {/* Execution Results with Video */}
                  {executionResult && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="glass p-6 rounded-xl space-y-4"
                    >
                      <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold">Test Execution</h3>
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          executionResult.success
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-red-500/20 text-red-400'
                        }`}>
                          {executionResult.success ? '✓ Passed' : '✗ Failed'}
                        </span>
                      </div>

                      {/* Video Player */}
                      {executionResult.video_url && (
                        <div className="rounded-lg overflow-hidden bg-gray-900">
                          <video
                            controls
                            className="w-full"
                            src={`http://localhost:8000${executionResult.video_url}`}
                          >
                            Your browser does not support the video tag.
                          </video>
                        </div>
                      )}

                      {/* Execution Details */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Device:</span>
                          <p className="text-white">{executionResult.device}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">iOS Version:</span>
                          <p className="text-white">{executionResult.ios_version}</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Duration:</span>
                          <p className="text-white">{executionResult.duration.toFixed(2)}s</p>
                        </div>
                        <div>
                          <span className="text-gray-400">Test ID:</span>
                          <p className="text-white font-mono text-xs">{executionResult.test_id}</p>
                        </div>
                      </div>

                      {/* Logs */}
                      {executionResult.logs && (
                        <div>
                          <h4 className="text-sm font-semibold mb-2 text-gray-400">Logs</h4>
                          <pre className="bg-gray-900 p-4 rounded-lg text-xs text-gray-300 overflow-x-auto">
                            {executionResult.logs}
                          </pre>
                        </div>
                      )}

                      {/* Error */}
                      {executionResult.error && (
                        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
                          <p className="text-red-400 text-sm">{executionResult.error}</p>
                        </div>
                      )}

                      {/* Run Again Button */}
                      <button
                        onClick={() => {
                          setExecutionResult(null)
                          handleRunTest()
                        }}
                        className="w-full bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg text-sm font-semibold transition-colors"
                      >
                        Run Again
                      </button>
                    </motion.div>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  key="placeholder"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="glass p-12 rounded-xl text-center h-full flex items-center justify-center"
                >
                  <div>
                    <div className="text-6xl mb-4">⚡</div>
                    <p className="text-gray-400">
                      Your generated test will appear here
                    </p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
