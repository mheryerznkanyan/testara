'use client'

import { useState, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import {
  Upload,
  Smartphone,
  CheckCircle,
  RefreshCw,
  Loader2,
  WifiOff,
  ScanSearch,
  Layout,
  MousePointerClick,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/page-header'
import { API_BASE, getCloudStatus, getCloudDevices, cloudDiscover, getDiscoveryStatus } from '@/lib/api'

interface CloudStatus {
  enabled: boolean
  credentials_valid?: boolean
  app_url?: string | null
  default_device?: string
  os_version?: string
}

interface Device {
  name: string
  os: string
  os_version?: string
}

interface ScreenDetail {
  name: string
  element_count: number
  navigation_path?: string
}

interface DiscoveryResult {
  screen_count: number
  interactive_count: number
  screens: ScreenDetail[]
}

const defaultDevices: Device[] = [
  { name: 'iPhone 15 Pro', os: 'iOS 17', os_version: '17' },
  { name: 'iPhone 15 Pro Max', os: 'iOS 17', os_version: '17' },
  { name: 'iPhone 14', os: 'iOS 16', os_version: '16' },
  { name: 'iPhone 14 Pro', os: 'iOS 16', os_version: '16' },
  { name: 'iPhone 13', os: 'iOS 15', os_version: '15' },
  { name: 'iPad Pro 12.9 2022', os: 'iOS 16', os_version: '16' },
]

export default function CloudPage() {
  const [cloudStatus, setCloudStatus] = useState<CloudStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [devices, setDevices] = useState<Device[]>(defaultDevices)
  const [selectedDevice, setSelectedDevice] = useState<string>('iPhone 15 Pro')
  const [selectedOsVersion, setSelectedOsVersion] = useState<string>('17')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const [discoveryLoading, setDiscoveryLoading] = useState(false)
  const [discoveryResult, setDiscoveryResult] = useState<DiscoveryResult | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    fetchCloudStatus()
    fetchDevices()
    fetchDiscoveryStatus()
    const stored = localStorage.getItem('testara_cloud_device')
    const storedOs = localStorage.getItem('testara_cloud_os_version')
    if (stored) setSelectedDevice(stored)
    if (storedOs) setSelectedOsVersion(storedOs)
  }, [])

  const fetchDiscoveryStatus = async () => {
    try {
      const data = await getDiscoveryStatus()
      if (data.success) {
        setDiscoveryResult({
          screen_count: data.screen_count,
          interactive_count: data.interactive_count,
          screens: data.screens || [],
        })
      }
    } catch {}
  }

  const fetchCloudStatus = async () => {
    setStatusLoading(true)
    try {
      const data = await getCloudStatus()
      setCloudStatus(data)
      if (data.app_url && !uploadedUrl) {
        setUploadedUrl(data.app_url)
      }
    } catch {
      setCloudStatus({ enabled: false })
    } finally {
      setStatusLoading(false)
    }
  }

  const fetchDevices = async () => {
    try {
      const data = await getCloudDevices()
      if (Array.isArray(data) && data.length > 0) {
        setDevices(data.map((d: any) => ({
          name: d.name || d.device,
          os: `iOS ${d.os_version}`,
          os_version: String(d.os_version),
        })))
      }
    } catch {}
  }

  const handleSelectDevice = (device: Device) => {
    setSelectedDevice(device.name)
    const osVer = device.os_version || device.os?.replace('iOS ', '') || '17'
    setSelectedOsVersion(osVer)
    localStorage.setItem('testara_cloud_device', device.name)
    localStorage.setItem('testara_cloud_os_version', osVer)
  }

  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true) }
  const handleDragLeave = (e: React.DragEvent) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false) }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file && (file.name.endsWith('.ipa') || file.name.endsWith('.zip'))) { setUploadFile(file) } else { toast.error('Please drop a valid .ipa or .zip file') }
  }

  const handleUpload = async () => {
    if (!uploadFile) return
    setUploadLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      const token = typeof window !== 'undefined' ? localStorage.getItem('testara_token') : null
      const res = await fetch(`${API_BASE}/cloud/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })
      if (res.ok) {
        const data = await res.json()
        setUploadedUrl(data.app_url || data.url || 'Uploaded')
        setUploadFile(null)
        if (fileInputRef.current) fileInputRef.current.value = ''
        toast.success('App uploaded to Testara Cloud')
      } else {
        const err = await res.json().catch(() => ({}))
        toast.error(err.detail || 'Upload failed')
      }
    } catch { toast.error('Could not reach the server') }
    finally { setUploadLoading(false) }
  }

  const handleDiscover = async () => {
    setDiscoveryLoading(true)
    setDiscoveryResult(null)
    try {
      const appUrl = uploadedUrl || cloudStatus?.app_url || undefined
      const data = await cloudDiscover({
        app_url: appUrl,
        device_name: selectedDevice,
        os_version: selectedOsVersion,
      })
      if (data.success) {
        setDiscoveryResult({
          screen_count: data.screen_count,
          interactive_count: data.interactive_count,
          screens: data.screens || [],
        })
        toast.success(`Discovered ${data.screen_count} screens, ${data.interactive_count} interactive elements`)
      } else {
        toast.error(data.error || 'Discovery failed')
      }
    } catch (err) { toast.error(err instanceof Error ? err.message : 'Discovery failed') }
    finally { setDiscoveryLoading(false) }
  }

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-[1400px] mx-auto p-8 space-y-6">
        <PageHeader
          title="Testara Cloud"
          description="Run tests on real iOS devices in the cloud"
        />

        {/* Status Banner */}
        <div>
          {statusLoading ? (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="font-label text-xs uppercase tracking-widest">Connecting to cloud infrastructure...</span>
            </div>
          ) : cloudStatus?.enabled && cloudStatus?.credentials_valid ? (
            <div className="flex items-center gap-2 glass-card px-4 py-2.5 border-emerald-500/20">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 shadow-glow-emerald" />
              <span className="text-sm font-medium text-emerald-400">Cloud infrastructure online</span>
              <Button variant="ghost" size="sm" onClick={fetchCloudStatus} className="ml-auto h-7 text-xs">
                <RefreshCw className="h-3 w-3" /> Refresh
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 glass-card px-4 py-2.5 border-amber-500/20">
              <WifiOff className="h-4 w-4 text-amber-400" />
              <span className="text-sm font-medium text-amber-400">Cloud not available</span>
              <span className="text-[10px] text-zinc-500 ml-2 font-label uppercase tracking-widest">Contact support if this persists</span>
              <Button variant="ghost" size="sm" onClick={fetchCloudStatus} className="ml-auto h-7 text-xs">Retry</Button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* APP UPLOAD */}
          <div className="glass-card lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Upload className="h-4 w-4 text-zinc-500" /> Your App
              </CardTitle>
              <CardDescription>Upload your .zip or .ipa to run tests in the cloud</CardDescription>
            </CardHeader>
            <CardContent>
              {uploadedUrl ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                    <CheckCircle className="h-4 w-4" /> Ready to test
                  </div>
                  <div className="bg-surface-low border border-white/5 rounded-xl px-3 py-2">
                    <p className="text-[10px] text-zinc-600 mb-0.5 font-label uppercase tracking-widest">App ID</p>
                    <p className="text-xs font-mono text-white truncate">{uploadedUrl}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => setUploadedUrl(null)}>Replace app</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div
                    className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                      isDragging ? 'border-primary bg-primary/5' : 'border-outline-variant/20 hover:border-primary/40 hover:bg-primary/5'
                    }`}
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                  >
                    <Upload className="h-6 w-6 text-zinc-600 mx-auto mb-2" />
                    {uploadFile ? (
                      <p className="text-sm text-white font-medium">{uploadFile.name}</p>
                    ) : (
                      <>
                        <p className="text-sm text-zinc-500">Drop .zip or .ipa here</p>
                        <p className="text-[10px] text-zinc-700 mt-1 font-label uppercase tracking-widest">or click to browse</p>
                      </>
                    )}
                  </div>
                  <input ref={fileInputRef} type="file" accept=".ipa,.zip" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setUploadFile(f) }} />
                  <Button onClick={handleUpload} disabled={!uploadFile || uploadLoading} className="w-full">
                    {uploadLoading ? <><Loader2 className="h-4 w-4 animate-spin" />Uploading...</> : <><Upload className="h-4 w-4" />Upload</>}
                  </Button>
                </div>
              )}
            </CardContent>
          </div>

          {/* DEVICE PICKER */}
          <div className="glass-card lg:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-zinc-500" /> Device
              </CardTitle>
            </CardHeader>
            <CardContent>
              <select
                value={`${selectedDevice}|${selectedOsVersion}`}
                onChange={(e) => {
                  const [name, osVer] = e.target.value.split('|')
                  const d = devices.find(dev => dev.name === name && (dev.os_version || dev.os?.replace('iOS ', '')) === osVer)
                  if (d) handleSelectDevice(d)
                }}
                className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary transition-all appearance-none"
              >
                {devices.map((device) => (
                  <option key={`${device.name}-${device.os_version || device.os}`} value={`${device.name}|${device.os_version || device.os?.replace('iOS ', '')}`}>
                    {device.name} — {device.os}
                  </option>
                ))}
              </select>
            </CardContent>
          </div>
        </div>

        {/* DISCOVER APP */}
        <div className="glass-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-sm flex items-center gap-2">
                  <ScanSearch className="h-4 w-4 text-zinc-500" /> Discover App
                </CardTitle>
                <CardDescription className="mt-1">
                  Launch your app on a real device and capture the accessibility tree
                </CardDescription>
              </div>
              {discoveryResult && (
                <Badge variant="success">
                  {discoveryResult.screen_count} screens &middot; {discoveryResult.interactive_count} elements
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {discoveryResult ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium">
                  <CheckCircle className="h-4 w-4" /> Discovery complete — ready to generate tests
                </div>

                {/* Summary stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-surface-low rounded-xl px-4 py-3 border border-white/[0.04]">
                    <div className="flex items-center gap-2 mb-1">
                      <Layout className="h-3.5 w-3.5 text-primary" />
                      <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">Screens</p>
                    </div>
                    <p className="text-2xl font-bold font-mono text-white">{discoveryResult.screen_count}</p>
                  </div>
                  <div className="bg-surface-low rounded-xl px-4 py-3 border border-white/[0.04]">
                    <div className="flex items-center gap-2 mb-1">
                      <MousePointerClick className="h-3.5 w-3.5 text-primary" />
                      <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">Interactive Elements</p>
                    </div>
                    <p className="text-2xl font-bold font-mono text-white">{discoveryResult.interactive_count}</p>
                  </div>
                </div>

                {/* Screen breakdown table */}
                {discoveryResult.screens.length > 0 && (
                  <div className="rounded-xl border border-white/5 overflow-hidden">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="bg-surface-high/30">
                          <th className="px-4 py-3 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Screen</th>
                          <th className="px-4 py-3 text-[10px] font-label text-zinc-500 uppercase tracking-widest text-center">Elements</th>
                          <th className="px-4 py-3 text-[10px] font-label text-zinc-500 uppercase tracking-widest">Navigation</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5">
                        {discoveryResult.screens.map((screen, i) => (
                          <tr key={i} className="hover:bg-white/5 transition-colors">
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <Layout className="h-3.5 w-3.5 text-primary/60 shrink-0" />
                                <span className="text-sm font-medium text-white">{screen.name}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <Badge variant="blue">{screen.element_count}</Badge>
                            </td>
                            <td className="px-4 py-3 text-xs text-zinc-500 font-mono">
                              {screen.navigation_path || '—'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <Button variant="outline" size="sm" onClick={() => { setDiscoveryResult(null); handleDiscover() }}>
                  Re-discover
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-zinc-500">
                  {(!uploadedUrl && !cloudStatus?.app_url)
                    ? 'Upload your .zip or .ipa first, then discover the app.'
                    : `Will launch on ${selectedDevice} and capture all screens. Takes 30-90 seconds.`
                  }
                </p>
                <Button onClick={handleDiscover} disabled={discoveryLoading || (!uploadedUrl && !cloudStatus?.app_url)} className="w-full">
                  {discoveryLoading ? <><Loader2 className="h-4 w-4 animate-spin" />Discovering... this takes 30-90s</> : <><ScanSearch className="h-4 w-4" />Discover App</>}
                </Button>
              </div>
            )}
          </CardContent>
        </div>

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
