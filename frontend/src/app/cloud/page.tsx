'use client'

import { useState, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import {
  Cloud,
  Upload,
  Smartphone,
  CheckCircle,
  XCircle,
  RefreshCw,
  Loader2,
  Wifi,
  WifiOff,
  Check,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatusBadge } from '@/components/status-badge'
import { PageHeader } from '@/components/page-header'
import { getCloudStatus, getCloudDevices } from '@/lib/api'
import type { RunStatus } from '@/types'

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

const mockCloudRuns: CloudRun[] = [
  { id: '1', testName: 'Login with valid credentials', device: 'iPhone 15 Pro', status: 'Passed', duration: '12s', date: '1 hour ago' },
  { id: '2', testName: 'Add item to cart', device: 'iPhone 14', status: 'Passed', duration: '8s', date: '2 hours ago' },
  { id: '3', testName: 'Payment with invalid card', device: 'iPhone 15 Pro', status: 'Failed', duration: '5s', date: '3 hours ago' },
  { id: '4', testName: 'Biometric authentication', device: 'iPhone 13', status: 'Running', duration: '—', date: 'Just now' },
]

const defaultDevices: Device[] = [
  { name: 'iPhone 15 Pro', os: 'iOS 17.2' },
  { name: 'iPhone 14', os: 'iOS 16.7' },
  { name: 'iPhone 13', os: 'iOS 15.8' },
]

export default function CloudPage() {
  const [cloudStatus, setCloudStatus] = useState<CloudStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [devices, setDevices] = useState<Device[]>(defaultDevices)
  const [selectedDevice, setSelectedDevice] = useState<string>('iPhone 15 Pro')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchCloudStatus()
    fetchDevices()
  }, [])

  const fetchCloudStatus = async () => {
    setStatusLoading(true)
    try {
      const data = await getCloudStatus()
      setCloudStatus(data)
    } catch {
      setCloudStatus({ connected: false })
    } finally {
      setStatusLoading(false)
    }
  }

  const fetchDevices = async () => {
    try {
      const data = await getCloudDevices()
      if (Array.isArray(data) && data.length > 0) setDevices(data)
    } catch {}
  }

  const handleUpload = async () => {
    if (!uploadFile) return
    setUploadLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      const res = await fetch('http://localhost:8000/cloud/upload', {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const data = await res.json()
        const url = data.app_url || data.url || 'Uploaded'
        setUploadedUrl(url)
        setUploadFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
        toast.success('App uploaded successfully')
      } else {
        const err = await res.json().catch(() => ({}))
        toast.error(err.detail || 'Upload failed')
      }
    } catch {
      toast.error('Could not reach the server')
    } finally {
      setUploadLoading(false)
    }
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
        <PageHeader
          title="Cloud"
          description="Manage cloud test execution and device configuration"
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LEFT COLUMN */}
          <div className="space-y-6">
            {/* Connection Status */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Connection Status</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={fetchCloudStatus}
                    disabled={statusLoading}
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${statusLoading ? 'animate-spin' : ''}`} />
                    {statusLoading ? 'Checking' : 'Refresh'}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {statusLoading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Checking connection...
                  </div>
                ) : cloudStatus?.connected ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]" />
                      <span className="text-sm font-medium text-emerald-400">Connected</span>
                      <Badge variant="success" className="ml-auto">BrowserStack</Badge>
                    </div>
                    {cloudStatus.defaultDevice && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Default device</span>
                        <span className="text-foreground">{cloudStatus.defaultDevice}</span>
                      </div>
                    )}
                    {cloudStatus.osVersion && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">OS version</span>
                        <span className="text-foreground">{cloudStatus.osVersion}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <WifiOff className="h-4 w-4 text-red-400" />
                      <span className="text-sm font-medium text-red-400">Not Configured</span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      Set your BrowserStack credentials in{' '}
                      <a href="/settings" className="text-blue-400 hover:underline">Settings &rarr; Cloud</a>.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Upload App */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Upload App</CardTitle>
              </CardHeader>
              <CardContent>
                {uploadedUrl ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                      <CheckCircle className="h-4 w-4" />
                      Upload successful
                    </div>
                    <div className="bg-surface-2 border border-border rounded-lg px-3 py-2">
                      <p className="text-xs text-muted-foreground mb-0.5">App URL</p>
                      <p className="text-xs font-mono text-foreground break-all">{uploadedUrl}</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setUploadedUrl(null)}>
                      Upload another app
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div
                      className="border-2 border-dashed border-border rounded-lg p-8 text-center cursor-pointer hover:border-blue-500/40 hover:bg-blue-500/5 transition-all"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                      {uploadFile ? (
                        <p className="text-sm text-foreground font-medium">{uploadFile.name}</p>
                      ) : (
                        <>
                          <p className="text-sm text-muted-foreground">Click to select or drag &amp; drop</p>
                          <p className="text-xs text-muted-foreground/60 mt-1">.ipa files only</p>
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
                        if (f) setUploadFile(f)
                      }}
                    />
                    <Button
                      onClick={handleUpload}
                      disabled={!uploadFile || uploadLoading}
                      className="w-full"
                    >
                      {uploadLoading ? (
                        <><Loader2 className="h-4 w-4 animate-spin" />Uploading...</>
                      ) : (
                        <><Upload className="h-4 w-4" />Upload App</>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* RIGHT COLUMN */}
          <div className="space-y-6">
            {/* Device Selection */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Device Selection</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {devices.map((device) => (
                    <button
                      key={device.name}
                      onClick={() => setSelectedDevice(device.name)}
                      className={`w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-all text-sm ${
                        selectedDevice === device.name
                          ? 'border-blue-500/40 bg-blue-500/10 text-foreground shadow-sm shadow-blue-500/10'
                          : 'border-border bg-surface-2 text-muted-foreground hover:text-foreground hover:bg-surface-3'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Smartphone className="h-4 w-4 opacity-60" />
                        <span className="font-medium text-foreground">{device.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">{device.os}</span>
                        {selectedDevice === device.name && (
                          <Check className="h-4 w-4 text-blue-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-3">
                  Selected: <span className="text-foreground font-medium">{selectedDevice}</span>
                </p>
              </CardContent>
            </Card>

            {/* Recent Cloud Runs */}
            <Card>
              <CardHeader className="pb-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Recent Cloud Runs</CardTitle>
                  <Badge variant="blue">{mockCloudRuns.length} runs</Badge>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="divide-y divide-border -mx-6">
                  {mockCloudRuns.map((run) => (
                    <div key={run.id} className="px-6 py-3 flex items-center justify-between hover:bg-surface-2/30 transition-colors">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">{run.testName}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{run.device} &middot; {run.date}</p>
                      </div>
                      <div className="flex items-center gap-3 ml-4 shrink-0">
                        <span className="text-xs text-muted-foreground font-mono">{run.duration}</span>
                        <StatusBadge status={run.status} />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
