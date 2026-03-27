'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  Save,
  User,
  LogOut,
  Smartphone,
  Sparkles,
  ArrowRight,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/page-header'
import { useAuth } from '@/lib/auth-context'

interface Settings {
  appName: string
  bundleId: string
}

export default function SettingsPage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState('general')
  const [settings, setSettings] = useState<Settings>({
    appName: 'YourApp',
    bundleId: '',
  })

  useEffect(() => {
    const stored = localStorage.getItem('testara_settings')
    if (stored) {
      const parsed = JSON.parse(stored)
      setSettings({
        appName: parsed.appName || 'YourApp',
        bundleId: parsed.bundleId || '',
      })
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('testara_settings', JSON.stringify(settings))
    toast.success('Settings saved')
  }

  const tabs = [
    { id: 'general', label: 'General', icon: Smartphone },
    { id: 'account', label: 'Account', icon: User },
  ]

  return (
    <div className="h-full overflow-auto">
      <div className="max-w-3xl mx-auto p-8">
        <PageHeader title="Settings" description="Configure your testing environment" />

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-white/5 mb-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 text-xs font-label uppercase tracking-widest transition-colors border-b-2 flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'text-primary border-primary'
                    : 'text-zinc-500 border-transparent hover:text-zinc-300'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>

        {/* GENERAL TAB */}
        {activeTab === 'general' && (
          <div className="space-y-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">App Configuration</CardTitle>
                <CardDescription>Configure the app under test</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">App Name</label>
                  <input
                    value={settings.appName}
                    onChange={(e) => setSettings({ ...settings, appName: e.target.value })}
                    placeholder="YourApp"
                    className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Bundle ID</label>
                  <input
                    value={settings.bundleId}
                    onChange={(e) => setSettings({ ...settings, bundleId: e.target.value })}
                    placeholder="com.example.MyApp"
                    className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all"
                  />
                  <p className="text-[10px] text-zinc-600 mt-1.5 font-label uppercase tracking-widest">
                    Required for cloud test execution
                  </p>
                </div>
              </CardContent>
            </Card>

            <Button onClick={handleSave} className="w-full">
              <Save className="h-4 w-4" />
              Save Settings
            </Button>
          </div>
        )}

        {/* ACCOUNT TAB */}
        {activeTab === 'account' && (
          <div className="space-y-5">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Your Account</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-[10px] text-zinc-600 mb-1 font-label uppercase tracking-widest">Email</p>
                  <p className="text-sm font-medium text-white">{user?.email || 'Not signed in'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-600 mb-1 font-label uppercase tracking-widest">User ID</p>
                  <p className="text-xs font-mono text-zinc-400">{user?.id || '\u2014'}</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-primary/20 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Plan & Billing
                </CardTitle>
                <CardDescription>Manage your subscription</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-surface-low border border-outline-variant/10">
                  <div>
                    <p className="text-[10px] text-zinc-600 mb-1 font-label uppercase tracking-widest">Current Plan</p>
                    <p className="text-lg font-headline font-bold text-white">Free</p>
                    <p className="text-xs text-zinc-500 mt-1">50 cloud runs / month · 3 suites · 1 device</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-headline font-bold text-white">$0</p>
                    <p className="text-[10px] text-zinc-600 font-label uppercase tracking-widest">/month</p>
                  </div>
                </div>
                <Button
                  onClick={() => router.push('/plans')}
                  className="w-full shadow-glow-cyan"
                  size="lg"
                >
                  Upgrade Your Plan
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            <Button
              variant="destructive"
              onClick={() => { logout(); window.location.href = '/login' }}
              className="w-full"
            >
              <LogOut className="h-4 w-4" />
              Sign Out
            </Button>
          </div>
        )}

        <div className="h-12 md:hidden" />
      </div>
    </div>
  )
}
