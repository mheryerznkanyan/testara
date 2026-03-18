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

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({
    deviceName: 'iPhone 15 Pro',
    deviceUdid: '',
    iosVersion: '17.0',
    appName: 'YourApp',
    bundleId: '',
  })
  
  const [availableDevices, setAvailableDevices] = useState<SimulatorDevice[]>([])
  const [loading, setLoading] = useState(true)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // Load settings from localStorage, migrating old format if needed
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

    // Fetch available simulators
    fetchSimulators()
  }, [])
  
  const fetchSimulators = async () => {
    try {
      const response = await fetch('http://localhost:8000/simulators')
      if (response.ok) {
        const data = await response.json()
        console.log('Fetched simulators:', data.devices)
        setAvailableDevices(data.devices)
        
        // Auto-select device if no UDID is set yet
        const stored = localStorage.getItem('testara_settings')
        const parsed = stored ? JSON.parse(stored) : null
        const hasDeviceUdid = parsed?.deviceUdid
        if (!hasDeviceUdid && data.devices.length > 0) {
          const bootedDevice = data.devices.find((d: SimulatorDevice) => d.state === 'Booted')
          const defaultDevice = bootedDevice || data.devices[0]

          setSettings(prev => ({
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
    console.log('Saving settings:', settings)
    localStorage.setItem('testara_settings', JSON.stringify(settings))
    console.log('Settings saved to localStorage')
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }
  
  const handleDeviceChange = (udid: string) => {
    const device = availableDevices.find(d => d.udid === udid)
    if (device) {
      console.log('Device changed to:', device)
      const newSettings = {
        ...settings,
        deviceName: device.name,
        deviceUdid: device.udid,
        iosVersion: device.ios_version,
      }
      console.log('New settings:', newSettings)
      setSettings(newSettings)
    }
  }

  return (
    <div className="h-full bg-background">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <h1 className="text-4xl font-bold mb-2">Settings</h1>
          <p className="text-gray-400 mb-8">
            Configure simulator and test execution preferences
          </p>
        </motion.div>

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
                      {device.name} (iOS {device.ios_version}) [{device.udid.slice(0, 8)}] {device.state === 'Booted' ? '🟢' : ''}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-2">
                  🟢 = Currently booted • Showing {availableDevices.length} available simulator{availableDevices.length !== 1 ? 's' : ''}
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
                  <span className="text-foreground font-mono text-xs">{settings.deviceUdid.slice(0, 8)}...</span>
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
            <label className="block text-sm font-semibold mb-3">
              App Name
            </label>
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
            <label className="block text-sm font-semibold mb-3">
              Bundle ID
            </label>
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
      </div>
    </div>
  )
}
