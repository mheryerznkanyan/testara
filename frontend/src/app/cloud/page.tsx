'use client'

import { useState, useEffect, useRef } from 'react'

type RunStatus = 'Passed' | 'Failed' | 'Running'

interface CloudStatus {
  connected: boolean
  defaultDevice?: string
  osVersion?: string
}

interface Device {
  name: string
  os: string
}

interface CloudRun {
  id: string
  testName: string
  device: string
  status: RunStatus
  duration: string
  date: string
}

const defaultDevices: Device[] = [
  { name: 'iPhone 15 Pro', os: 'iOS 17.2' },
  { name: 'iPhone 14', os: 'iOS 16.7' },
  { name: 'iPhone 13', os: 'iOS 15.8' },
]

const mockCloudRuns: CloudRun[] = [
  {
    id: '1',
    testName: 'Login with valid credentials',
    device: 'iPhone 15 Pro',
    status: 'Passed',
    duration: '12s',
    date: '1 hour ago',
  },
  {
    id: '2',
    testName: 'Add item to cart',
    device: 'iPhone 14',
    status: 'Passed',
    duration: '8s',
    date: '2 hours ago',
  },
  {
    id: '3',
    testName: 'Payment with invalid card',
    device: 'iPhone 15 Pro',
    status: 'Failed',
    duration: '5s',
    date: '3 hours ago',
  },
  {
    id: '4',
    testName: 'Biometric authentication',
    device: 'iPhone 13',
    status: 'Running',
    duration: '—',
    date: 'Just now',
  },
]

function StatusBadge({ status }: { status: RunStatus }) {
  const styles: Record<RunStatus, string> = {
    Passed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/25',
    Failed: 'bg-red-500/15 text-red-400 border border-red-500/25',
    Running: 'bg-yellow-500/15 text-yellow-400 border border-yellow-500/25',
  }
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

export default function CloudPage() {
  const [cloudStatus, setCloudStatus] = useState<CloudStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [devices, setDevices] = useState<Device[]>(defaultDevices)
  const [selectedDevice, setSelectedDevice] = useState<string>('iPhone 15 Pro')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchCloudStatus()
    fetchDevices()
  }, [])

  const fetchCloudStatus = async () => {
    setStatusLoading(true)
    try {
      const res = await fetch('http://localhost:8000/cloud/status')
      if (res.ok) {
        const data = await res.json()
        setCloudStatus(data)
      } else {
        setCloudStatus({ connected: false })
      }
    } catch {
      setCloudStatus({ connected: false })
    } finally {
      setStatusLoading(false)
    }
  }

  const fetchDevices = async () => {
    try {
      const res = await fetch('http://localhost:8000/cloud/devices/recommended')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) {
          setDevices(data)
        }
      }
    } catch {
      // fall back to defaults already set
    }
  }

  const handleUpload = async () => {
    if (!uploadFile) return
    setUploadLoading(true)
    setUploadError(null)
    setUploadedUrl(null)

    try {
      const formData = new FormData()
      formData.append('file', uploadFile)

      const res = await fetch('http://localhost:8000/cloud/upload', {
        method: 'POST',
        body: formData,
      })

      if (res.ok) {
        const data = await res.json()
        setUploadedUrl(data.app_url || data.url || 'Uploaded successfully')
        setUploadFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
      } else {
        const err = await res.json().catch(() => ({}))
        setUploadError(err.detail || 'Upload failed. Please try again.')
      }
    } catch {
      setUploadError('Could not reach the server. Make sure the backend is running.')
    } finally {
      setUploadLoading(false)
    }
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-1">Cloud</h1>
          <p className="text-muted text-sm">Manage cloud test execution and device configuration</p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* ── LEFT COLUMN ── */}
          <div className="space-y-6">
            {/* Connection Status */}
            <div className="rounded-xl border border-border bg-surface-1 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold">Connection Status</h2>
                <button
                  onClick={fetchCloudStatus}
                  disabled={statusLoading}
                  className="text-xs px-2.5 py-1 rounded-md border border-border text-muted hover:text-foreground hover:bg-surface-2 transition-colors disabled:opacity-50"
                >
                  {statusLoading ? 'Checking...' : 'Refresh'}
                </button>
              </div>

              {statusLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted">
                  <span className="inline-block w-2 h-2 rounded-full bg-muted animate-pulse" />
                  Checking connection…
                </div>
              ) : cloudStatus?.connected ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
                    <span className="text-sm font-medium text-emerald-400">Connected</span>
                  </div>
                  {cloudStatus.defaultDevice && (
                    <div className="text-sm text-muted">
                      Default device:{' '}
                      <span className="text-foreground">{cloudStatus.defaultDevice}</span>
                    </div>
                  )}
                  {cloudStatus.osVersion && (
                    <div className="text-sm text-muted">
                      OS version:{' '}
                      <span className="text-foreground">{cloudStatus.osVersion}</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2.5 h-2.5 rounded-full bg-red-400" />
                    <span className="text-sm font-medium text-red-400">Not Configured</span>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">
                    Cloud credentials are not configured. Add your credentials in{' '}
                    <a href="/settings" className="text-blue-400 hover:underline">
                      Settings → Cloud
                    </a>
                    .
                  </p>
                </div>
              )}
            </div>

            {/* Upload App */}
            <div className="rounded-xl border border-border bg-surface-1 p-6">
              <h2 className="text-base font-semibold mb-4">Upload App</h2>

              {uploadedUrl ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Upload successful
                  </div>
                  <div className="bg-surface-2 border border-border rounded-lg px-3 py-2">
                    <p className="text-xs text-muted mb-0.5">App URL</p>
                    <p className="text-xs font-mono text-foreground break-all">{uploadedUrl}</p>
                  </div>
                  <button
                    onClick={() => setUploadedUrl(null)}
                    className="text-xs text-muted hover:text-foreground transition-colors"
                  >
                    Upload another app
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs text-muted font-medium mb-2">
                      Select .ipa file
                    </label>
                    <div
                      className="border border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-blue-500/40 hover:bg-blue-500/5 transition-colors"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <svg className="w-8 h-8 text-muted mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      {uploadFile ? (
                        <p className="text-sm text-foreground font-medium">{uploadFile.name}</p>
                      ) : (
                        <>
                          <p className="text-sm text-muted">Click to select or drag &amp; drop</p>
                          <p className="text-xs text-muted mt-1">.ipa files only</p>
                        </>
                      )}
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".ipa"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) {
                          setUploadFile(f)
                          setUploadError(null)
                        }
                      }}
                    />
                  </div>

                  {uploadError && (
                    <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                      {uploadError}
                    </p>
                  )}

                  <button
                    onClick={handleUpload}
                    disabled={!uploadFile || uploadLoading}
                    className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {uploadLoading ? (
                      <>
                        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Uploading…
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        Upload App
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ── RIGHT COLUMN ── */}
          <div className="space-y-6">
            {/* Device Selection */}
            <div className="rounded-xl border border-border bg-surface-1 p-6">
              <h2 className="text-base font-semibold mb-4">Device Selection</h2>
              <div className="space-y-2">
                {devices.map((device) => (
                  <button
                    key={device.name}
                    onClick={() => setSelectedDevice(device.name)}
                    className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-colors text-sm ${
                      selectedDevice === device.name
                        ? 'border-blue-500/40 bg-blue-500/10 text-foreground'
                        : 'border-border bg-surface-2 text-muted hover:text-foreground hover:bg-surface-3'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <svg className="w-5 h-5 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <span className="font-medium text-foreground">{device.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted">{device.os}</span>
                      {selectedDevice === device.name && (
                        <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted mt-3">
                Selected: <span className="text-foreground">{selectedDevice}</span>
              </p>
            </div>

            {/* Recent Cloud Runs */}
            <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
              <div className="px-6 py-4 border-b border-border">
                <h2 className="text-base font-semibold">Recent Cloud Runs</h2>
              </div>
              <div className="divide-y divide-border">
                {mockCloudRuns.map((run) => (
                  <div key={run.id} className="px-6 py-3 flex items-center justify-between hover:bg-surface-2/30 transition-colors">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{run.testName}</p>
                      <p className="text-xs text-muted mt-0.5">{run.device} · {run.date}</p>
                    </div>
                    <div className="flex items-center gap-3 ml-4 shrink-0">
                      <span className="text-xs text-muted font-mono">{run.duration}</span>
                      <StatusBadge status={run.status} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
