'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface SimulatorDevice {
  name: string
  udid: string
  ios_version: string
  state: string
}

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

type Tab = 'simulator' | 'cloud'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('simulator')
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
  const [saved, setSaved] = useState(false)
  const [cloudSaved, setCloudSaved] = useState(false)

  useEffect(() => {
    // Load simulator settings
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

    // Load cloud settings
    const storedCloud = localStorage.getItem('testara_cloud_settings')
    if (storedCloud) {
      setCloudSettings(JSON.parse(storedCloud))
    }

    fetchSimulators()
  }, [])

  const fetchSimulators = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulators')
      if (response.ok) {
        const data = await response.json()
        setAvailableDevices(data.devices)

        const stored = localStorage.getItem('testara_settings')
        const parsed = stored ? JSON.parse(stored) : null
        const hasDeviceUdid = parsed?.deviceUdid
        if (!hasDeviceUdid && data.devices.length > 0) {
          const bootedDevice = data.devices.find((d: SimulatorDevice) => d.state === 'Booted')
          const defaultDevice = bootedDevice || data.devices[0]
          setSettings((prev) => ({
            ...prev,
            deviceName: defaultDevice.name,
            deviceUdid: defaultDevice.udid,
            iosVersion: defaultDevice.ios_version,
          }))
        }
      }
    } catch (error) {
      console.error('Failed to fetch simulators:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    localStorage.setItem('testara_settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleCloudSave = () => {
    localStorage.setItem('testara_cloud_settings', JSON.stringify(cloudSettings))
    setCloudSaved(true)
    setTimeout(() => setCloudSaved(false), 2000)
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

  const deviceOptions = [
    'iPhone 15 Pro',
    'iPhone 15',
    'iPhone 14 Pro',
    'iPhone 14',
    'iPhone 13 Pro',
    'iPhone 13',
    'iPhone 12',
    'iPhone SE (3rd gen)',
  ]

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl font-bold mb-2">Settings</h1>
          <p className="text-muted mb-8">
            Configure simulator and test execution preferences
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex gap-1 mb-8 p-1 rounded-lg bg-surface-2 w-fit">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-5 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'simulator'
                ? 'bg-surface-1 text-foreground shadow-sm'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Simulator
          </button>
          <button
            onClick={() => setActiveTab('cloud')}
            className={`px-5 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'cloud'
                ? 'bg-surface-1 text-foreground shadow-sm'
                : 'text-muted hover:text-foreground'
            }`}
          >
            Cloud
          </button>
        </div>

        {/* ── SIMULATOR TAB ── */}
        {activeTab === 'simulator' && (
          <div className="space-y-6">
            {/* Simulator Device */}
            <motion.div
              className="glass p-6 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.6 }}
            >
              <label className="block text-sm font-semibold mb-3">
                Simulator Device
              </label>
              {loading ? (
                <div className="text-center py-3 text-muted">Loading simulators...</div>
              ) : availableDevices.length === 0 ? (
                <div className="text-center py-3 text-red-400">
                  No simulators found. Make sure Xcode is installed.
                </div>
              ) : (
                <>
                  <select
                    value={settings.deviceUdid}
                    onChange={(e) => handleDeviceChange(e.target.value)}
                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {availableDevices.map((device) => (
                      <option key={device.udid} value={device.udid}>
                        {device.name} (iOS {device.ios_version}) [{device.udid.slice(0, 8)}]{' '}
                        {device.state === 'Booted' ? '🟢' : ''}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-2">
                    🟢 = Currently booted • Showing {availableDevices.length} available simulator
                    {availableDevices.length !== 1 ? 's' : ''}
                  </p>
                </>
              )}
            </motion.div>

            {/* Current Selection Display */}
            {settings.deviceUdid && (
              <motion.div
                className="glass p-6 rounded-xl"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.6 }}
              >
                <label className="block text-sm font-semibold mb-3">
                  Selected Configuration
                </label>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Device:</span>
                    <span className="text-foreground">{settings.deviceName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">iOS:</span>
                    <span className="text-foreground">{settings.iosVersion}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">UDID:</span>
                    <span className="text-foreground font-mono text-xs">
                      {settings.deviceUdid.slice(0, 8)}...
                    </span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* App Name */}
            <motion.div
              className="glass p-6 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <label className="block text-sm font-semibold mb-3">App Name</label>
              <input
                type="text"
                value={settings.appName}
                onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
                placeholder="YourApp"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-2">
                Name of the app being tested (used in test context)
              </p>
            </motion.div>

            {/* Bundle ID */}
            <motion.div
              className="glass p-6 rounded-xl"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.6 }}
            >
              <label className="block text-sm font-semibold mb-3">Bundle ID</label>
              <input
                type="text"
                value={settings.bundleId}
                onChange={(e) => setSettings({ ...settings, bundleId: e.target.value })}
                placeholder="com.example.MyApp"
                className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-2">
                Required for Appium live discovery (e.g. com.example.MyApp)
              </p>
            </motion.div>

            {/* Refresh Button */}
            <motion.button
              onClick={fetchSimulators}
              disabled={loading}
              className="w-full glass hover:bg-accent px-6 py-3 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              {loading ? 'Refreshing...' : '🔄 Refresh Simulators'}
            </motion.button>

            {/* Save Button */}
            <motion.button
              onClick={handleSave}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300 hover:scale-105"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {saved ? '✓ Saved!' : 'Save Settings'}
            </motion.button>
          </div>
        )}

        {/* ── CLOUD TAB ── */}
        {activeTab === 'cloud' && (
          <div className="space-y-6">
            {/* Cloud Credentials */}
            <motion.div
              className="rounded-xl border border-border bg-surface-1 p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.5 }}
            >
              <h3 className="text-sm font-semibold mb-4">Cloud Credentials</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-muted mb-1.5">
                    Username
                  </label>
                  <input
                    type="text"
                    value={cloudSettings.username}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, username: e.target.value })
                    }
                    placeholder="Enter your username"
                    className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted mb-1.5">
                    Access Key
                  </label>
                  <input
                    type="password"
                    value={cloudSettings.accessKey}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, accessKey: e.target.value })
                    }
                    placeholder="Enter your access key"
                    className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                  />
                </div>
              </div>
            </motion.div>

            {/* App Configuration */}
            <motion.div
              className="rounded-xl border border-border bg-surface-1 p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.5 }}
            >
              <h3 className="text-sm font-semibold mb-4">App Configuration</h3>
              <div>
                <label className="block text-xs font-medium text-muted mb-1.5">App URL</label>
                <input
                  type="text"
                  value={cloudSettings.appUrl}
                  onChange={(e) =>
                    setCloudSettings({ ...cloudSettings, appUrl: e.target.value })
                  }
                  placeholder="Enter your app URL"
                  className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                />
                <p className="text-xs text-muted mt-2">
                  URL to your uploaded .ipa file (e.g. bs://abc123)
                </p>
              </div>
            </motion.div>

            {/* Device Configuration */}
            <motion.div
              className="rounded-xl border border-border bg-surface-1 p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              <h3 className="text-sm font-semibold mb-4">Default Device</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-muted mb-1.5">Device</label>
                  <select
                    value={cloudSettings.defaultDevice}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, defaultDevice: e.target.value })
                    }
                    className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                  >
                    {deviceOptions.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted mb-1.5">
                    OS Version
                  </label>
                  <input
                    type="text"
                    value={cloudSettings.osVersion}
                    onChange={(e) =>
                      setCloudSettings({ ...cloudSettings, osVersion: e.target.value })
                    }
                    placeholder="e.g. 17"
                    className="w-full bg-surface-2 border border-border rounded-lg px-4 py-2.5 text-sm text-foreground placeholder-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500/40 transition-colors"
                  />
                </div>
              </div>
            </motion.div>

            {/* Note */}
            <div className="flex items-start gap-2 text-xs text-muted bg-surface-2 rounded-lg px-4 py-3 border border-border">
              <svg className="w-4 h-4 mt-0.5 shrink-0 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Credentials are stored securely in your environment configuration</span>
            </div>

            {/* Save Cloud Settings */}
            <motion.button
              onClick={handleCloudSave}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all duration-300"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.5 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {cloudSaved ? '✓ Saved!' : 'Save Cloud Settings'}
            </motion.button>
          </div>
        )}
      </div>
    </div>
  )
}
