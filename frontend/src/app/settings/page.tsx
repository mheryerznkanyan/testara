'use client'

import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import {
  Smartphone,
  RefreshCw,
  Save,
  Cloud,
  Key,
  Globe,
  Info,
  Eye,
  EyeOff,
  CheckCircle,
  Loader2,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { PageHeader } from '@/components/page-header'
import { getSimulators } from '@/lib/api'
import type { SimulatorDevice } from '@/types'

interface Settings {
  deviceName: string
  deviceUdid: string
  iosVersion: string
  appName: string
  bundleId: string
}

interface CloudSettings {
  username: string
  accessKey: string
  appUrl: string
  defaultDevice: string
  osVersion: string
}

const cloudDeviceOptions = [
  'iPhone 15 Pro',
  'iPhone 15',
  'iPhone 14 Pro',
  'iPhone 14',
  'iPhone 13 Pro',
  'iPhone 13',
  'iPhone 12',
  'iPhone SE (3rd gen)',
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('simulator')
  const [settings, setSettings] = useState<Settings>({
    deviceName: 'iPhone 15 Pro',
    deviceUdid: '',
    iosVersion: '17.0',
    appName: 'YourApp',
    bundleId: '',
  })
  const [cloudSettings, setCloudSettings] = useState<CloudSettings>({
    username: '',
    accessKey: '',
    appUrl: '',
    defaultDevice: 'iPhone 15 Pro',
    osVersion: '17',
  })
  const [availableDevices, setAvailableDevices] = useState<SimulatorDevice[]>([])
  const [loading, setLoading] = useState(true)
  const [showAccessKey, setShowAccessKey] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('testara_settings')
    if (stored) {
      const parsed = JSON.parse(stored)
      setSettings({
        deviceName: parsed.deviceName || parsed.device || 'iPhone 15 Pro',
        deviceUdid: parsed.deviceUdid || '',
        iosVersion: parsed.iosVersion || '17.0',
        appName: parsed.appName || 'YourApp',
        bundleId: parsed.bundleId || '',
      })
    }
    const storedCloud = localStorage.getItem('testara_cloud_settings')
    if (storedCloud) setCloudSettings(JSON.parse(storedCloud))
    fetchSimulators()
  }, [])

  const fetchSimulators = async () => {
    setLoading(true)
    try {
      const data = await getSimulators()
      setAvailableDevices(data.devices)
      const stored = localStorage.getItem('testara_settings')
      const parsed = stored ? JSON.parse(stored) : null
      if (!parsed?.deviceUdid && data.devices.length > 0) {
        const booted = data.devices.find((d: SimulatorDevice) => d.state === 'Booted')
        const def = booted || data.devices[0]
        setSettings((prev) => ({
          ...prev,
          deviceName: def.name,
          deviceUdid: def.udid,
          iosVersion: def.ios_version,
        }))
      }
    } catch {
      // silent
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    localStorage.setItem('testara_settings', JSON.stringify(settings))
    toast.success('Simulator settings saved')
  }

  const handleCloudSave = () => {
    localStorage.setItem('testara_cloud_settings', JSON.stringify(cloudSettings))
    toast.success('Cloud settings saved')
  }

  const handleDeviceChange = (udid: string) => {
    const device = availableDevices.find((d) => d.udid === udid)
    if (device) {
      setSettings({
        ...settings,
        deviceName: device.name,
        deviceUdid: device.udid,
        iosVersion: device.ios_version,
      })
    }
  }

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <PageHeader
          title="Settings"
          description="Configure simulator and cloud execution preferences"
        />

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-8">
            <TabsTrigger value="simulator">
              <Smartphone className="h-3.5 w-3.5 mr-1.5" />
              Simulator
            </TabsTrigger>
            <TabsTrigger value="cloud">
              <Cloud className="h-3.5 w-3.5 mr-1.5" />
              Cloud
            </TabsTrigger>
          </TabsList>

          {/* ── SIMULATOR TAB ── */}
          <TabsContent value="simulator" className="space-y-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Simulator Device</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading simulators...
                  </div>
                ) : availableDevices.length === 0 ? (
                  <p className="text-sm text-red-400">
                    No simulators found. Make sure Xcode is installed.
                  </p>
                ) : (
                  <>
                    <Select
                      value={settings.deviceUdid}
                      onChange={(e) => handleDeviceChange(e.target.value)}
                    >
                      {availableDevices.map((device) => (
                        <option key={device.udid} value={device.udid}>
                          {device.name} (iOS {device.ios_version}){' '}
                          {device.state === 'Booted' ? '● Booted' : ''}
                        </option>
                      ))}
                    </Select>
                    <p className="text-xs text-muted-foreground mt-2">
                      {availableDevices.length} simulator{availableDevices.length !== 1 ? 's' : ''} available
                    </p>
                  </>
                )}
              </CardContent>
            </Card>

            {settings.deviceUdid && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Selected Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Device</p>
                      <p className="text-sm font-medium">{settings.deviceName}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">iOS Version</p>
                      <p className="text-sm font-medium">{settings.iosVersion}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">UDID</p>
                      <p className="text-sm font-mono text-xs text-muted-foreground">
                        {settings.deviceUdid.slice(0, 12)}...
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">App Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    App Name
                  </label>
                  <Input
                    value={settings.appName}
                    onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
                    placeholder="YourApp"
                  />
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Name of the app being tested
                  </p>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Bundle ID
                  </label>
                  <Input
                    value={settings.bundleId}
                    onChange={(e) => setSettings({ ...settings, bundleId: e.target.value })}
                    placeholder="com.example.MyApp"
                  />
                  <p className="text-xs text-muted-foreground mt-1.5">
                    Required for Appium test execution
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={fetchSimulators}
                disabled={loading}
                className="flex-1"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh Simulators
              </Button>
              <Button onClick={handleSave} className="flex-1">
                <Save className="h-4 w-4" />
                Save Settings
              </Button>
            </div>
          </TabsContent>

          {/* ── CLOUD TAB ── */}
          <TabsContent value="cloud" className="space-y-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Key className="h-4 w-4 text-muted-foreground" />
                  Cloud Credentials
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Username
                  </label>
                  <Input
                    value={cloudSettings.username}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, username: e.target.value })
                    }
                    placeholder="Enter your BrowserStack username"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Access Key
                  </label>
                  <div className="relative">
                    <Input
                      type={showAccessKey ? 'text' : 'password'}
                      value={cloudSettings.accessKey}
                      onChange={(e) =>
                        setCloudSettings({ ...cloudSettings, accessKey: e.target.value })
                      }
                      placeholder="Enter your access key"
                      className="pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowAccessKey(!showAccessKey)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showAccessKey ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  App Configuration
                </CardTitle>
              </CardHeader>
              <CardContent>
                <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                  App URL
                </label>
                <Input
                  value={cloudSettings.appUrl}
                  onChange={(e) =>
                    setCloudSettings({ ...cloudSettings, appUrl: e.target.value })
                  }
                  placeholder="bs://abc123 or leave empty to auto-upload"
                />
                <p className="text-xs text-muted-foreground mt-1.5">
                  URL from a previous BrowserStack upload
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Smartphone className="h-4 w-4 text-muted-foreground" />
                  Default Device
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Device
                  </label>
                  <Select
                    value={cloudSettings.defaultDevice}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, defaultDevice: e.target.value })
                    }
                  >
                    {cloudDeviceOptions.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    OS Version
                  </label>
                  <Input
                    value={cloudSettings.osVersion}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, osVersion: e.target.value })
                    }
                    placeholder="e.g. 17"
                  />
                </div>
              </CardContent>
            </Card>

            <div className="flex items-start gap-2 text-xs text-muted-foreground bg-surface-2 rounded-lg px-4 py-3 border border-border">
              <Info className="h-4 w-4 mt-0.5 shrink-0 text-blue-400" />
              <span>Credentials are stored locally in your browser. For production use, configure them in your .env file.</span>
            </div>

            <Button onClick={handleCloudSave} className="w-full">
              <Save className="h-4 w-4" />
              Save Cloud Settings
            </Button>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
