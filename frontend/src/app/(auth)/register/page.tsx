'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Loader2, Smartphone } from 'lucide-react'

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
    </svg>
  )
}

export default function RegisterPage() {
  const { register, loginWithGoogle } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password !== confirmPassword) { setError('Passwords do not match'); return }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return }
    setLoading(true)
    try {
      await register(email, password)
      const token = localStorage.getItem('testara_token')
      if (token) { router.replace('/dashboard') } else { setSuccess(true) }
    } catch (err) { setError(err instanceof Error ? err.message : 'Registration failed') }
    finally { setLoading(false) }
  }

  const handleGoogle = async () => {
    setError(null)
    setGoogleLoading(true)
    try { await loginWithGoogle() } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed')
      setGoogleLoading(false)
    }
  }

  if (success) {
    return (
      <div className="glass-card w-full max-w-sm p-8 text-center space-y-4">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-emerald-500/10 rounded-xl">
            <Smartphone className="h-6 w-6 text-emerald-400" />
          </div>
        </div>
        <h1 className="text-xl font-bold font-headline">Check your email</h1>
        <p className="text-sm text-zinc-500">
          We sent a confirmation link to <span className="text-white font-medium">{email}</span>.
          Click the link to activate your account.
        </p>
        <Link href="/login" className="text-sm text-primary hover:underline">Back to sign in</Link>
      </div>
    )
  }

  return (
    <div className="glass-card w-full max-w-sm p-8 space-y-6">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <div className="p-3 bg-primary/10 rounded-xl">
            <Smartphone className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h1 className="text-xl font-bold font-headline">Create an account</h1>
        <p className="text-sm text-zinc-500 mt-1">Get started with Testara</p>
      </div>

      {error && (
        <div className="rounded-xl bg-error/10 border border-error/20 px-3 py-2 text-sm text-error">
          {error}
        </div>
      )}

      <Button type="button" variant="outline" className="w-full" onClick={handleGoogle} disabled={googleLoading}>
        {googleLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <GoogleIcon className="h-4 w-4" />}
        Continue with Google
      </Button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-white/5" /></div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-surface-container px-2 text-zinc-600 font-label uppercase tracking-widest">or</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all" />
        </div>
        <div>
          <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" required className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all" />
        </div>
        <div>
          <label className="text-[10px] font-label uppercase tracking-widest text-zinc-500 mb-1.5 block">Confirm Password</label>
          <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Confirm your password" required className="w-full bg-surface-low border border-outline-variant/20 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-primary transition-all" />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create Account'}
        </Button>
      </form>

      <p className="text-xs text-zinc-500 text-center">
        Already have an account?{' '}
        <Link href="/login" className="text-primary hover:underline">Sign in</Link>
      </p>
    </div>
  )
}
